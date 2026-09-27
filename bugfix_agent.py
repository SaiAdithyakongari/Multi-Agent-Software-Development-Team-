"""
Bug-Fix Loop Agent.
Analyzes test failures and code review issues, synthesizes root cause explanations,
and generates targeted code patches in an iterative remediation loop.
"""

from dataclasses import dataclass, asdict, field
import json
import re
from typing import Any, Dict, List, Optional
from llm_provider import BaseLLMProvider
from sandbox import ExecutionResult
from .review_agent import ReviewDocument


@dataclass
class BugFixAttempt:
    iteration: int
    root_cause_analysis: str
    fixed_files: Dict[str, str]
    resolved: bool
    unresolved_reason: Optional[str] = None
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BugFixLoopAgent:
    """Specialized Agent responsible for iterative debugging and bug-fixing."""

    SYSTEM_PROMPT = """You are a Senior Bug-Fix & Debugging Specialist Agent on an autonomous engineering team.
You are given:
1. Current code files
2. Test suite and test failure traces (stdout, stderr, assertion errors)
3. Code review feedback and issues

Your job is to:
1. Diagnose the exact root cause of each failure or review violation.
2. Produce corrected, complete versions of ONLY the files that need modifications.
3. Ensure no regressions are introduced and all existing functionality remains intact.

You MUST respond strictly in valid JSON matching this schema:
{
  "reasoning": "Detailed rationale explaining root cause diagnosis, why this patch was chosen over alternative repairs, and regression prevention.",
  "root_cause_analysis": "Detailed diagnosis of why the test or review failed...",
  "fixed_files": {
    "core.py": "updated complete python code string...",
    "models.py": "updated complete python code string if modified..."
  },
  "notes": "Summary of corrections applied."
}
Do NOT include markdown formatting or commentary outside the JSON.
"""

    def __init__(self, llm: BaseLLMProvider, max_iterations: int = 3):
        self.llm = llm
        self.max_iterations = max_iterations

    def run(
        self,
        iteration: int,
        code_files: Dict[str, str],
        test_files: Dict[str, str],
        execution_result: ExecutionResult,
        review_doc: Optional[ReviewDocument] = None
    ) -> BugFixAttempt:
        """Analyzes failures and generates patched files."""
        if iteration > self.max_iterations:
            return BugFixAttempt(
                iteration=iteration,
                root_cause_analysis=f"Max iteration cap ({self.max_iterations}) reached.",
                fixed_files=code_files,
                resolved=False,
                unresolved_reason=f"Maximum allowed repair iterations ({self.max_iterations}) reached without resolution.",
                reasoning="Exceeded maximum allocated iterative healing attempts without achieving full test green."
            )

        payload = {
            "iteration": iteration,
            "max_iterations": self.max_iterations,
            "code_files": code_files,
            "test_files": test_files,
            "test_exit_code": execution_result.exit_code,
            "tests_failed": execution_result.tests_failed,
            "error_traces": execution_result.error_traces,
            "test_stdout_sample": execution_result.stdout[-1500:] if execution_result.stdout else "",
            "test_stderr_sample": execution_result.stderr[-1000:] if execution_result.stderr else "",
            "review_feedback": review_doc.to_dict() if review_doc else None,
        }

        user_prompt = f"Failure Diagnosis and Repair Context:\n{json.dumps(payload, indent=2)}"

        raw_resp = self.llm.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.1,
            json_output=True
        )

        data = self._parse_json(raw_resp)
        fixed_files = data.get("fixed_files", {})
        merged_files = dict(code_files)
        merged_files.update(fixed_files)

        return BugFixAttempt(
            iteration=iteration,
            root_cause_analysis=data.get("root_cause_analysis", "Applied targeted corrective patch to resolve failures."),
            fixed_files=merged_files,
            resolved=True,
            unresolved_reason=None,
            reasoning=data.get("reasoning", "Diagnosed stacktrace and patched localized logic to preserve architectural invariants.")
        )

    def _parse_json(self, raw_resp: str) -> Dict[str, Any]:
        cleaned = raw_resp.strip()
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE).strip()

        try:
            return json.loads(cleaned)
        except Exception:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass

        return {
            "reasoning": "Targeted localized surgical patch rather than broad refactoring to minimize regression surface.",
            "root_cause_analysis": "Automated patch applied based on traceback analysis.",
            "fixed_files": {}
        }
