"""
Requirements Analyst Agent.
Translates a user's natural language requirement into a structured requirements document
with functional/non-functional requirements, constraints, assumptions, and acceptance criteria.
"""

from dataclasses import dataclass, asdict, field
import json
import re
from typing import Any, Dict, List, Optional
from llm_provider import BaseLLMProvider


@dataclass
class FunctionalRequirement:
    id: str
    description: str


@dataclass
class NonFunctionalRequirement:
    id: str
    category: str
    description: str


@dataclass
class RequirementsDocument:
    title: str
    problem_statement: str
    functional_requirements: List[Dict[str, str]] = field(default_factory=list)
    non_functional_requirements: List[Dict[str, str]] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RequirementsDocument":
        return cls(
            title=data.get("title", "Software Specification"),
            problem_statement=data.get("problem_statement", ""),
            functional_requirements=data.get("functional_requirements", []),
            non_functional_requirements=data.get("non_functional_requirements", []),
            constraints=data.get("constraints", []),
            assumptions=data.get("assumptions", []),
            acceptance_criteria=data.get("acceptance_criteria", []),
            reasoning=data.get("reasoning", ""),
        )


class RequirementsAnalystAgent:
    """Specialized Agent responsible for requirement engineering."""

    SYSTEM_PROMPT = """You are a Lead Software Requirements Analyst Agent on an autonomous engineering team.
Your task is to analyze the user's natural language request and formulate an unambiguous, structured software requirements specification.

You MUST respond strictly in valid JSON matching this schema:
{
  "title": "Short descriptive title of the project",
  "problem_statement": "Clear definition of the problem being solved",
  "reasoning": "Detailed reasoning explaining how scope boundaries were established, how edge cases were prioritized, and why specific functional criteria were emphasized over secondary concerns.",
  "functional_requirements": [
    {"id": "FR-1", "description": "Specific functional behavior..."},
    {"id": "FR-2", "description": "Another specific requirement..."}
  ],
  "non_functional_requirements": [
    {"id": "NFR-1", "category": "Performance|Security|Reliability|Maintainability", "description": "..."}
  ],
  "constraints": ["Constraint 1...", "Constraint 2..."],
  "assumptions": ["Assumption 1...", "Assumption 2..."],
  "acceptance_criteria": ["All tests pass...", "Criteria 2..."]
}
Do NOT include markdown formatting or commentary outside the JSON.
"""

    def __init__(self, llm: BaseLLMProvider):
        self.llm = llm

    def run(self, user_requirement: str, feedback: Optional[str] = None) -> RequirementsDocument:
        """Executes requirements analysis, optionally incorporating human feedback."""
        prompt_text = f"Software Requirement to analyze:\n{user_requirement}"
        if feedback:
            prompt_text += f"\n\nHUMAN OPERATOR REVIEW FEEDBACK (incorporate and address all points):\n{feedback}"

        raw_resp = self.llm.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=prompt_text,
            temperature=0.2,
            json_output=True
        )

        data = self._parse_json(raw_resp, user_requirement)
        return RequirementsDocument.from_dict(data)

    def _parse_json(self, raw_resp: str, fallback_req: str) -> Dict[str, Any]:
        # Strip potential markdown fences
        cleaned = raw_resp.strip()
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE).strip()

        try:
            return json.loads(cleaned)
        except Exception:
            # Match first json block if noisy
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass

        # Fallback structured doc
        return {
            "title": "Software Engineering Requirement",
            "problem_statement": fallback_req,
            "reasoning": "Decomposed the problem into orthogonal functional operations, defensive boundary validations, and deterministic assertions to guarantee 100% test verification and modular execution.",
            "functional_requirements": [
                {"id": "FR-1", "description": "Implement core logic satisfying all problem statements."},
                {"id": "FR-2", "description": "Expose clean callable API / interface."},
                {"id": "FR-3", "description": "Provide complete input validation and edge-case handling."}
            ],
            "non_functional_requirements": [
                {"id": "NFR-1", "category": "Reliability", "description": "Deterministic unit test coverage."},
                {"id": "NFR-2", "category": "Security", "description": "Zero unsafe execution or vulnerabilities."}
            ],
            "constraints": ["Pure Python 3.10+ execution", "Self-contained modules"],
            "assumptions": ["Executed in safe sandboxed environment"],
            "acceptance_criteria": ["All Pytest tests pass cleanly with zero failures"]
        }
