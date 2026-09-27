"""
Static Analysis Gate.
Runs automated linting (ruff/flake8) and type-checking (mypy) on generated
Python code inside the sandbox before the Test stage.
Failures route back to Code Generation for a fix — tests are never attempted
on code that fails static analysis.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import shutil
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LintViolation:
    tool: str            # "ruff" | "flake8" | "mypy"
    file: str
    line: int
    col: int
    code: str            # e.g. E501, F841, error
    message: str
    severity: str        # "error" | "warning" | "note"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StaticAnalysisResult:
    passed: bool
    lint_passed: bool
    type_passed: bool
    violations: List[Dict[str, Any]] = field(default_factory=list)
    lint_output: str = ""
    type_output: str = ""
    error_count: int = 0
    warning_count: int = 0
    tools_used: List[str] = field(default_factory=list)
    summary: str = ""
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StaticAnalysisResult":
        return cls(
            passed=data.get("passed", True),
            lint_passed=data.get("lint_passed", True),
            type_passed=data.get("type_passed", True),
            violations=data.get("violations", []),
            lint_output=data.get("lint_output", ""),
            type_output=data.get("type_output", ""),
            error_count=data.get("error_count", 0),
            warning_count=data.get("warning_count", 0),
            tools_used=data.get("tools_used", []),
            summary=data.get("summary", ""),
            reasoning=data.get("reasoning", ""),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _tool_available(name: str) -> bool:
    """Return True if `name` is importable as a Python module (runnable via -m)."""
    try:
        r = subprocess.run(
            [sys.executable, "-m", name, "--version"],
            capture_output=True, timeout=8,
        )
        return r.returncode == 0
    except Exception:
        return False


def _parse_ruff_output(output: str, filename: str) -> List[LintViolation]:
    viols: List[LintViolation] = []
    # ruff: path/file.py:line:col: CODE message
    pattern = re.compile(r"^(.+?):(\d+):(\d+):\s+([A-Z]\d+)\s+(.+)$", re.MULTILINE)
    for m in pattern.finditer(output):
        viols.append(LintViolation(
            tool="ruff",
            file=filename,
            line=int(m.group(2)),
            col=int(m.group(3)),
            code=m.group(4),
            message=m.group(5).strip(),
            severity="error" if m.group(4).startswith("E") else "warning",
        ))
    return viols


def _parse_flake8_output(output: str, filename: str) -> List[LintViolation]:
    viols: List[LintViolation] = []
    # flake8: file.py:line:col: CODE message
    pattern = re.compile(r"^(.+?):(\d+):(\d+):\s+([A-Z]\d+)\s+(.+)$", re.MULTILINE)
    for m in pattern.finditer(output):
        viols.append(LintViolation(
            tool="flake8",
            file=filename,
            line=int(m.group(2)),
            col=int(m.group(3)),
            code=m.group(4),
            message=m.group(5).strip(),
            severity="error" if m.group(4).startswith("E") else "warning",
        ))
    return viols


def _parse_mypy_output(output: str, filename: str) -> List[LintViolation]:
    viols: List[LintViolation] = []
    # mypy: file.py:line: error/warning/note: message
    pattern = re.compile(r"^(.+?):(\d+):\s+(error|warning|note):\s+(.+)$", re.MULTILINE)
    for m in pattern.finditer(output):
        viols.append(LintViolation(
            tool="mypy",
            file=filename,
            line=int(m.group(2)),
            col=0,
            code="mypy",
            message=m.group(4).strip(),
            severity=m.group(3),
        ))
    return viols


# ─────────────────────────────────────────────────────────────────────────────
# Cyclomatic Complexity Checker
# ─────────────────────────────────────────────────────────────────────────────

def _check_complexity(
    filename: str, 
    code: str, 
    viols: List[LintViolation],
    threshold: int = 10
) -> None:
    """
    Calculate cyclomatic complexity per function/method.
    Complexity = 1 + number of decision points (if, while, for, except, and, or)
    Functions exceeding threshold are flagged as warnings.
    """
    # Find all function definitions
    func_pattern = re.compile(
        r'^(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\).*?:$',
        re.MULTILINE
    )
    
    lines = code.splitlines()
    
    for match in func_pattern.finditer(code):
        func_name = match.group(1)
        func_start = code[:match.start()].count("\n")
        
        # Find the end of this function (next def/class or dedent)
        func_lines = []
        for i in range(func_start, len(lines)):
            line = lines[i]
            # Stop at next function or class at same or lower indent
            if i > func_start and (line.startswith('def ') or line.startswith('class ')):
                break
            func_lines.append(line)
        
        func_code = "\n".join(func_lines)
        
        # Count decision points
        complexity = 1
        complexity += len(re.findall(r'\bif\b', func_code))
        complexity += len(re.findall(r'\bwhile\b', func_code))
        complexity += len(re.findall(r'\bfor\b', func_code))
        complexity += len(re.findall(r'\bexcept\b', func_code))
        complexity += len(re.findall(r'\band\b', func_code))
        complexity += len(re.findall(r'\bor\b', func_code))
        
        if complexity > threshold:
            viols.append(LintViolation(
                tool="builtin",
                file=filename,
                line=func_start + 1,
                col=0,
                code="C901",
                message=f"Function '{func_name}' has complexity {complexity} (threshold {threshold})",
                severity="warning",
            ))


# ─────────────────────────────────────────────────────────────────────────────
# Fallback pure-Python lint (no external tools required)
# ─────────────────────────────────────────────────────────────────────────────

def _builtin_lint(code_files: Dict[str, str]) -> Tuple[List[LintViolation], str]:
    """
    Lightweight built-in checks when ruff/flake8/mypy are unavailable.
    Uses Python's own `compile()` for syntax errors and regex for common smells.
    """
    viols: List[LintViolation] = []
    output_lines: List[str] = []

    # Smell patterns: (regex, code, message, severity)
    # Note: bare_except moved to advanced checks below for better detection
    smell_rules = [
        # Code style issues (warnings)
        (re.compile(r'\bprint\s*\('),              "W001", "print() statement found (use logging)", "warning"),
        (re.compile(r'(?<!\w)lambda\s+\w+\s*:'),   "W002", "Lambda assigned to variable; use def instead", "warning"),
        (re.compile(r'\t'),                         "W191", "Tab character found; use 4 spaces", "warning"),
        (re.compile(r'.{121}'),                     "E501", "Line exceeds 120 characters", "warning"),
        (re.compile(r'==\s*(?:True|False)\b'),      "E712", "Comparison to True/False; use 'if cond:' or 'if not cond:'", "warning"),
        (re.compile(r'is\s+(?:not\s+)?["\']'),     "E721", "Type comparison using 'is'; use isinstance()", "warning"),
    ]

    # Advanced checks: unused imports, missing type hints, bare except, complexity
    advanced_rules = [
        # Unused imports (F401) - warn if imported but not used in the file
        (re.compile(r'^import\s+(\w+)(?:\s+as\s+\w+)?$', re.MULTILINE), 
         "F401", "Import may be unused (verify with full analysis)", "warning"),
        
        # Missing type hints on public functions (ANN401)
        (re.compile(r'^def\s+([a-z_][a-z0-9_]*)\s*\([^)]*\)\s*(?!->).*:$', re.MULTILINE),
         "ANN401", "Public function missing return type annotation", "warning"),
        
        # Bare except clause - CRITICAL (moved from smell_rules as error)
        (re.compile(r'except\s*:\s*$', re.MULTILINE), 
         "E722", "Bare except clause catches all exceptions", "error"),
        (re.compile(r'except\s+\w+\s*,\s*\w+\s*:', re.MULTILINE),
         "E722", "Bare except with legacy syntax; use 'except Exception as e:'", "error"),
        
        # Cyclomatic complexity check - count if/while/for/except/and/or
        # This is a heuristic: flag functions with too many decision points
    ]

    for filename, code in code_files.items():
        # 1. Syntax check
        try:
            compile(code, filename, "exec")
        except SyntaxError as e:
            viols.append(LintViolation(
                tool="builtin",
                file=filename,
                line=e.lineno or 0,
                col=e.offset or 0,
                code="E999",
                message=f"SyntaxError: {e.msg}",
                severity="error",
            ))
            output_lines.append(f"{filename}:{e.lineno}:{e.offset}: E999 SyntaxError: {e.msg}")
            continue  # no point linting further on syntax error

        # 2. Basic smell checks
        lines = code.splitlines()
        for lineno, line in enumerate(lines, start=1):
            for pattern, code_str, msg, sev in smell_rules:
                if pattern.search(line):
                    viols.append(LintViolation(
                        tool="builtin",
                        file=filename,
                        line=lineno,
                        col=0,
                        code=code_str,
                        message=msg,
                        severity=sev,
                    ))
                    output_lines.append(f"{filename}:{lineno}:0: {code_str} {msg}")

        # 3. Advanced checks (unused imports, missing type hints, bare except)
        for pattern, code_str, msg, sev in advanced_rules:
            for m in pattern.finditer(code):
                lineno = code[:m.start()].count("\n") + 1
                viols.append(LintViolation(
                    tool="builtin",
                    file=filename,
                    line=lineno,
                    col=0,
                    code=code_str,
                    message=msg,
                    severity=sev,
                ))
                output_lines.append(f"{filename}:{lineno}:0: {code_str} {msg}")

        # 4. Cyclomatic complexity check (threshold = 10)
        _check_complexity(filename, code, viols, threshold=10)

    return viols, "\n".join(output_lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main agent class
# ─────────────────────────────────────────────────────────────────────────────

class StaticAnalysisAgent:
    """
    Static Analysis Gate agent.
    Writes generated code to a temp workspace, discovers available tools
    (ruff → flake8 → builtin), runs mypy if available, collects violations,
    and returns a StaticAnalysisResult.
    Composable: can be toggled off per run via feature_flags["static_analysis"].
    """

    # Ruff configuration written into the temp workspace so it doesn't fail
    # on missing pyproject.toml.
    _RUFF_CONFIG = """
[tool.ruff]
line-length = 120
select = ["E", "F", "W", "C90"]
ignore = ["E501", "F401"]

[tool.ruff.per-file-ignores]
"test_*.py" = ["F811", "S101"]
"""

    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
        self._lint_tool: Optional[str] = None   # resolved lazily

    # ── public ───────────────────────────────────────────────────────────────

    def run(self, code_files: Dict[str, str]) -> StaticAnalysisResult:
        """
        Runs linting + type-checking on code_files.
        Returns StaticAnalysisResult; result.passed == False routes back to codegen.
        """
        temp_dir = tempfile.mkdtemp(prefix="static_analysis_")
        try:
            return self._analyse(code_files, temp_dir)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # ── private ──────────────────────────────────────────────────────────────

    def _analyse(self, code_files: Dict[str, str], temp_dir: str) -> StaticAnalysisResult:
        # Write Python source files only (skip test files for lint gate)
        src_files: Dict[str, str] = {
            k: v for k, v in code_files.items()
            if k.endswith(".py") and not k.startswith("test_")
        }
        if not src_files:
            return StaticAnalysisResult(
                passed=True, lint_passed=True, type_passed=True,
                summary="No Python source files to analyse.",
                reasoning="Gate skipped — no .py source files in code_files.",
                tools_used=["none"],
            )

        for fname, content in src_files.items():
            fpath = os.path.join(temp_dir, fname)
            os.makedirs(os.path.dirname(fpath), exist_ok=True)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)

        # Write ruff config
        toml_path = os.path.join(temp_dir, "pyproject.toml")
        with open(toml_path, "w") as f:
            f.write(self._RUFF_CONFIG)

        all_violations: List[LintViolation] = []
        lint_output = ""
        type_output = ""
        tools_used: List[str] = []

        # ── Lint pass ────────────────────────────────────────────────────────
        lint_viols, lint_output, lint_tool = self._run_lint(temp_dir, src_files)
        all_violations.extend(lint_viols)
        tools_used.append(lint_tool)

        # ── Type-check pass ──────────────────────────────────────────────────
        type_viols, type_output, used_mypy = self._run_typecheck(temp_dir, src_files)
        all_violations.extend(type_viols)
        if used_mypy:
            tools_used.append("mypy")

        # ── Counts ───────────────────────────────────────────────────────────
        errors   = [v for v in all_violations if v.severity == "error"]
        warnings = [v for v in all_violations if v.severity == "warning"]

        # Gate rule: fail only on errors, not warnings
        lint_passed = not any(v.severity == "error" for v in lint_viols)
        type_passed = not any(v.severity == "error" for v in type_viols)
        passed      = lint_passed and type_passed

        summary = self._build_summary(all_violations, tools_used, passed)

        return StaticAnalysisResult(
            passed=passed,
            lint_passed=lint_passed,
            type_passed=type_passed,
            violations=[v.to_dict() for v in all_violations],
            lint_output=lint_output,
            type_output=type_output,
            error_count=len(errors),
            warning_count=len(warnings),
            tools_used=tools_used,
            summary=summary,
            reasoning=(
                f"Ran {', '.join(tools_used)} on {len(src_files)} source file(s). "
                f"Found {len(errors)} error(s) and {len(warnings)} warning(s). "
                f"Gate {'passed' if passed else 'FAILED — routing back to Code Generation'}."
            ),
        )

    def _run_lint(
        self, temp_dir: str, src_files: Dict[str, str]
    ) -> Tuple[List[LintViolation], str, str]:
        """Try ruff → flake8 → builtin in order."""
        file_args = list(src_files.keys())

        if _tool_available("ruff"):
            try:
                r = subprocess.run(
                    [sys.executable, "-m", "ruff", "check", "--output-format=text"] + file_args,
                    cwd=temp_dir, capture_output=True, text=True,
                    timeout=self.timeout_seconds,
                )
                output = r.stdout + r.stderr
                viols: List[LintViolation] = []
                for fn in file_args:
                    viols.extend(_parse_ruff_output(output, fn))
                return viols, output, "ruff"
            except Exception:
                pass

        if _tool_available("flake8"):
            try:
                r = subprocess.run(
                    [sys.executable, "-m", "flake8",
                     "--max-line-length=120", "--ignore=E501,W503,W504"] + file_args,
                    cwd=temp_dir, capture_output=True, text=True,
                    timeout=self.timeout_seconds,
                )
                output = r.stdout + r.stderr
                viols = []
                for fn in file_args:
                    viols.extend(_parse_flake8_output(output, fn))
                return viols, output, "flake8"
            except Exception:
                pass

        # Built-in fallback — always works
        code_map = {}
        for fn in file_args:
            fpath = os.path.join(temp_dir, fn)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    code_map[fn] = f.read()
            except Exception:
                pass
        viols, output = _builtin_lint(code_map)
        return viols, output, "builtin"

    def _run_typecheck(
        self, temp_dir: str, src_files: Dict[str, str]
    ) -> Tuple[List[LintViolation], str, bool]:
        """Run mypy if available; return empty result otherwise."""
        if not _tool_available("mypy"):
            return [], "mypy not installed — type-check skipped.", False

        file_args = list(src_files.keys())
        try:
            r = subprocess.run(
                [sys.executable, "-m", "mypy",
                 "--ignore-missing-imports",
                 "--no-strict-optional",
                 "--allow-untyped-defs"] + file_args,
                cwd=temp_dir, capture_output=True, text=True,
                timeout=self.timeout_seconds,
            )
            output = r.stdout + r.stderr
            viols: List[LintViolation] = []
            for fn in file_args:
                viols.extend(_parse_mypy_output(output, fn))
            return viols, output, True
        except Exception as e:
            return [], f"mypy execution error: {e}", False

    def _build_summary(
        self, violations: List[LintViolation], tools: List[str], passed: bool
    ) -> str:
        if not violations:
            return f"✅ Static analysis passed with zero violations ({', '.join(tools)})."
        errors   = sum(1 for v in violations if v.severity == "error")
        warnings = sum(1 for v in violations if v.severity == "warning")
        status   = "✅ PASSED" if passed else "❌ FAILED"
        return (
            f"{status} — {errors} error(s), {warnings} warning(s) "
            f"across {len({v.file for v in violations})} file(s). "
            f"Tools: {', '.join(tools)}."
        )
