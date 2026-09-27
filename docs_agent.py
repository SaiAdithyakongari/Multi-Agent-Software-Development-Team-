"""
Documentation Agent.
Synthesizes comprehensive user documentation, module API reference, setup guides,
and a pipeline build summary upon successful verification.
"""

from dataclasses import dataclass, asdict, field
import json
import re
from typing import Any, Dict, List, Optional
from llm_provider import BaseLLMProvider
from .requirements_agent import RequirementsDocument
from .architecture_agent import ArchitectureDocument
from .review_agent import ReviewDocument
from sandbox import ExecutionResult


@dataclass
class DocumentationPackage:
    readme: str
    setup_instructions: str
    module_documentation: Dict[str, str] = field(default_factory=dict)
    build_summary: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentationPackage":
        return cls(
            readme=data.get("readme", "# Project Documentation\n"),
            setup_instructions=data.get("setup_instructions", ""),
            module_documentation=data.get("module_documentation", {}),
            build_summary=data.get("build_summary", {}),
            reasoning=data.get("reasoning", ""),
        )


class DocumentationAgent:
    """Specialized Agent responsible for authoring documentation and build reports."""

    SYSTEM_PROMPT = """You are a Technical Writer & Documentation Lead Agent on an autonomous engineering team.
Your task is to write comprehensive, elegant markdown documentation for the verified software project.

You MUST respond strictly in valid JSON matching this schema:
{
  "reasoning": "Detailed rationale explaining documentation structure, API exposure clarity, setup simplicity, and developer onboarding strategy.",
  "readme": "# Project Title\\n\\n## Overview\\n...\\n\\n## Architecture\\n...\\n\\n## Quickstart\\n...\\n\\n## Verification & Tests\\n...",
  "setup_instructions": "1. Step one...\\n2. Step two...",
  "module_documentation": {
    "models.py": "Documentation of models...",
    "core.py": "Documentation of services...",
    "main.py": "Documentation of entrypoints..."
  },
  "build_summary": {
    "status": "SUCCESSFUL_BUILD",
    "total_modules": 3,
    "test_pass_rate": "100%",
    "pipeline_verdict": "Production-Ready"
  }
}
Do NOT include markdown formatting or commentary outside the JSON.
"""

    def __init__(self, llm: BaseLLMProvider):
        self.llm = llm

    def run(
        self,
        requirements: RequirementsDocument,
        architecture: ArchitectureDocument,
        code_files: Dict[str, str],
        test_result: ExecutionResult,
        review_doc: Optional[ReviewDocument] = None,
        git_commits_count: int = 7
    ) -> DocumentationPackage:
        """Generates comprehensive documentation package."""
        payload = {
            "requirements": requirements.to_dict(),
            "architecture": architecture.to_dict(),
            "code_files_summary": list(code_files.keys()),
            "tests_passed": test_result.tests_passed,
            "tests_total": test_result.tests_total,
            "test_success": test_result.success,
            "review_score": review_doc.overall_score if review_doc else None,
            "git_commits_count": git_commits_count,
        }

        user_prompt = f"System Artifacts for Documentation:\n{json.dumps(payload, indent=2)}"

        raw_resp = self.llm.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.2,
            json_output=True
        )

        data = self._parse_json(raw_resp, requirements, test_result, git_commits_count)
        return DocumentationPackage.from_dict(data)

    def _parse_json(
        self,
        raw_resp: str,
        requirements: RequirementsDocument,
        test_result: ExecutionResult,
        git_commits_count: int
    ) -> Dict[str, Any]:
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

        # Robust programmatic fallback
        readme_md = f"""# {requirements.title}

## Overview
{requirements.problem_statement}

## Multi-Agent Pipeline Verification
- **Test Status**: {'PASSED' if test_result.success else 'WARNING'} ({test_result.tests_passed}/{test_result.tests_total} passing)
- **Execution Time**: {test_result.duration_seconds:.2f} seconds
- **Version Control**: {git_commits_count} commits logged

## Getting Started
### Running Tests
```bash
pytest -v
```

### Running the App
```bash
python main.py
```
"""
        return {
            "readme": readme_md,
            "setup_instructions": "1. Ensure Python 3.10+ is installed.\n2. Install pytest.\n3. Run `pytest -v` to execute verification suite.",
            "module_documentation": {
                "models.py": "Entity definitions and validators.",
                "core.py": "Core business execution services.",
                "main.py": "Dispatcher and entrypoints."
            },
            "build_summary": {
                "status": "SUCCESSFUL_BUILD" if test_result.success else "PARTIAL_BUILD",
                "tests_passed": test_result.tests_passed,
                "tests_total": test_result.tests_total,
                "git_commits_count": git_commits_count
            }
        }
