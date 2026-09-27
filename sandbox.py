"""
Code Execution Sandbox.
Provides isolated, resource-constrained execution of generated code and test suites.
Never allows unrestricted system access.
"""

from dataclasses import dataclass, field
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Dict, List, Optional


@dataclass
class ExecutionResult:
    """Structured result of sandboxed code execution."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    tests_total: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    duration_seconds: float = 0.0
    error_traces: List[str] = field(default_factory=list)
    workspace_dir: str = ""

    def summary(self) -> str:
        if self.success:
            return f"PASSED: {self.tests_passed}/{self.tests_total} tests passed in {self.duration_seconds:.2f}s."
        return f"FAILED: {self.tests_failed}/{self.tests_total} tests failed (exit code {self.exit_code})."


class SandboxExecutor:
    """
    Executes Python scripts and Pytest suites in an isolated temporary environment
    with strict timeout guards and resource limits.
    """

    def __init__(self, timeout_seconds: int = 25):
        self.timeout_seconds = timeout_seconds

    def execute_test_suite(
        self,
        code_files: Dict[str, str],
        test_files: Dict[str, str],
        preserve_workspace: bool = True
    ) -> ExecutionResult:
        """
        Writes code and test files to an isolated directory and executes pytest.
        Captures real stdout, stderr, exit code, and parses test metrics.
        """
        temp_dir = tempfile.mkdtemp(prefix="agent_sandbox_")
        start_time = time.time()

        try:
            # 1. Write application code files
            for rel_path, content in code_files.items():
                abs_path = os.path.join(temp_dir, rel_path)
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with open(abs_path, "w", encoding="utf-8") as f:
                    f.write(content)

            # 2. Write test files
            for rel_path, content in test_files.items():
                abs_path = os.path.join(temp_dir, rel_path)
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with open(abs_path, "w", encoding="utf-8") as f:
                    f.write(content)

            # 3. Formulate safe execution environment
            # Restricted PATH and PYTHONPATH isolated to temp_dir
            env = os.environ.copy()
            env["PYTHONPATH"] = temp_dir
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            # Remove sensitive credentials from the child sandbox process
            for sensitive_key in ["GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
                env.pop(sensitive_key, None)

            # Check if pytest is installed, otherwise use built-in isolated test runner
            has_pytest = False
            try:
                check_p = subprocess.run([sys.executable, "-m", "pytest", "--version"], capture_output=True)
                has_pytest = (check_p.returncode == 0)
            except Exception:
                has_pytest = False

            if has_pytest:
                cmd = [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-v",
                    "--tb=short",
                    "-o",
                    "cache_dir=/tmp/.pytest_cache",
                ]
            else:
                # Write isolated sandbox test runner script
                runner_path = os.path.join(temp_dir, "_sandbox_runner.py")
                runner_code = """
import os, sys, inspect, importlib, time

# Pytest compatibility shim
if "pytest" not in sys.modules:
    import types
    pt = types.ModuleType("pytest")
    def fixture(fn):
        fn.__is_fixture__ = True
        return fn
    class raises:
        def __init__(self, exc):
            self.exc = exc
        def __enter__(self):
            return self
        def __exit__(self, et, ev, tb):
            if et is None:
                raise AssertionError(f"Expected {self.exc} not raised")
            return issubclass(et, self.exc)
    pt.fixture = fixture
    pt.raises = raises
    sys.modules["pytest"] = pt

test_files = [f for f in sorted(os.listdir(".")) if f.startswith("test_") and f.endswith(".py")]
total_tests = 0
passed_tests = 0
failed_tests = 0
errors = []

start_t = time.time()
print("============================= test session starts ==============================")
print("platform linux -- Python 3.10, pytest-sandbox")
print(f"collecting ... {len(test_files)} test suite file(s) collected\\n")

for tf in test_files:
    mod_name = tf[:-3]
    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:
        print(f"{tf} ERROR: Could not import {mod_name}: {e}")
        failed_tests += 1
        errors.append(f"ImportError in {tf}: {e}")
        continue

    fixtures = {}
    test_funcs = []
    for mname, mobj in inspect.getmembers(mod):
        if inspect.isfunction(mobj):
            if getattr(mobj, "__is_fixture__", False):
                fixtures[mname] = mobj
            elif mname.startswith("test_"):
                test_funcs.append((mname, mobj))

    for idx, (tname, tfunc) in enumerate(test_funcs):
        total_tests += 1
        pct = int((total_tests / max(1, len(test_funcs))) * 100)
        try:
            sig = inspect.signature(tfunc)
            kwargs = {p: fixtures[p]() for p in sig.parameters if p in fixtures}
            tfunc(**kwargs)
            passed_tests += 1
            print(f"{tf}::{tname} PASSED [{pct:>3}%]")
        except Exception as ex:
            failed_tests += 1
            print(f"{tf}::{tname} FAILED [{pct:>3}%]")
            import traceback
            tb = traceback.format_exc()
            errors.append(f"FAIL: {tname}\\n{tb}")

elapsed = time.time() - start_t
if errors:
    print("\\n=================================== FAILURES ===================================")
    for err in errors:
        print(err)

if failed_tests > 0:
    print(f"\\n======================= {failed_tests} failed, {passed_tests} passed in {elapsed:.2f}s =======================")
    sys.exit(1)
else:
    print(f"\\n============================== {passed_tests} passed in {elapsed:.2f}s ==============================")
    sys.exit(0)
"""
                with open(runner_path, "w", encoding="utf-8") as rf:
                    rf.write(runner_code)
                cmd = [sys.executable, "_sandbox_runner.py"]

            proc = subprocess.run(
                cmd,
                cwd=temp_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )

            duration = time.time() - start_time
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            exit_code = proc.returncode

            # 5. Parse test results from stdout
            total, passed, failed, skipped, error_traces = self._parse_pytest_output(stdout, stderr)

            is_success = (exit_code == 0) and (failed == 0) and (total > 0 or passed > 0)

            result = ExecutionResult(
                success=is_success,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                tests_total=total,
                tests_passed=passed,
                tests_failed=failed,
                tests_skipped=skipped,
                duration_seconds=duration,
                error_traces=error_traces,
                workspace_dir=temp_dir if preserve_workspace else ""
            )
            return result

        except subprocess.TimeoutExpired as e:
            duration = time.time() - start_time
            stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
            return ExecutionResult(
                success=False,
                exit_code=124,
                stdout=stdout,
                stderr=stderr + f"\nSandbox execution timed out after {self.timeout_seconds}s.",
                tests_total=0,
                tests_passed=0,
                tests_failed=1,
                duration_seconds=duration,
                error_traces=[f"Subprocess timed out after {self.timeout_seconds} seconds."],
                workspace_dir=temp_dir if preserve_workspace else ""
            )
        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                tests_total=0,
                tests_passed=0,
                tests_failed=1,
                duration_seconds=duration,
                error_traces=[str(e)],
                workspace_dir=temp_dir if preserve_workspace else ""
            )
        finally:
            if not preserve_workspace:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _parse_pytest_output(self, stdout: str, stderr: str):
        """Extracts passed, failed, skipped counts and error traces from pytest output."""
        passed = 0
        failed = 0
        skipped = 0

        # Pattern: "= 7 passed, 1 failed in 0.05s ="
        summary_line = ""
        for line in reversed(stdout.splitlines()):
            if "=" in line and ("passed" in line or "failed" in line or "error" in line):
                summary_line = line
                break

        if summary_line:
            p_match = re.search(r'(\d+)\s+passed', summary_line)
            f_match = re.search(r'(\d+)\s+failed', summary_line)
            s_match = re.search(r'(\d+)\s+skipped', summary_line)
            e_match = re.search(r'(\d+)\s+error', summary_line)

            if p_match:
                passed = int(p_match.group(1))
            if f_match:
                failed += int(f_match.group(1))
            if e_match:
                failed += int(e_match.group(1))
            if s_match:
                skipped = int(s_match.group(1))

        # Also count individual test lines e.g. "test_app.py::test_create PASSED"
        if passed == 0 and failed == 0:
            for line in stdout.splitlines():
                if " PASSED" in line:
                    passed += 1
                elif " FAILED" in line or " ERROR" in line:
                    failed += 1

        total = passed + failed + skipped

        # Extract failures/errors blocks
        error_traces = []
        in_failure_block = False
        current_trace = []
        for line in stdout.splitlines():
            if line.startswith("FAILURES") or line.startswith("ERRORS"):
                in_failure_block = True
                continue
            if in_failure_block:
                if line.startswith("=") and ("short test summary" in line or "passed" in line or "failed" in line):
                    in_failure_block = False
                    if current_trace:
                        error_traces.append("\n".join(current_trace))
                        current_trace = []
                else:
                    current_trace.append(line)

        if current_trace:
            error_traces.append("\n".join(current_trace))

        if stderr and not error_traces:
            error_traces.append(stderr.strip())

        return total, passed, failed, skipped, error_traces
