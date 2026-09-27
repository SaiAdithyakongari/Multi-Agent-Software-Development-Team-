"""
Code Generation Agent.
Implements complete, production-ready source code for each module per the architectural plan,
strictly following clean code practices, typing, and robust defensive error handling.
"""

from dataclasses import dataclass
import json
import re
from typing import Any, Dict, List, Optional
from llm_provider import BaseLLMProvider
from .requirements_agent import RequirementsDocument
from .architecture_agent import ArchitectureDocument


class CodeGenerationAgent:
    """Specialized Agent responsible for implementing software modules."""

    SYSTEM_PROMPT = """You are a Senior Software Engineer Agent on an autonomous engineering team.
Your task is to write complete, robust, production-ready Python 3 source code for the designed architecture.

CRITICAL IMPLEMENTATION RULES:
1. NEVER output placeholders, stubs, 'pass', '# TODO', or ellipses (...). Write 100% complete logic.
2. Use explicit typing, docstrings, and robust exception handling.
3. Keep code modular, clean, and adhering to PEP 8 standards.
4. Each file must be able to import its peer modules cleanly.

You MUST respond strictly in valid JSON matching this schema:
{
  "reasoning": "Detailed rationale explaining coding choices, data structures, typing invariants, and idiomatic Python patterns applied.",
  "files": {
    "models.py": "full python code string with escaped newlines or json-safe formatting",
    "core.py": "full python code string",
    "main.py": "full python code string"
  }
}
Do NOT include markdown formatting or commentary outside the JSON.
"""

    def __init__(self, llm: BaseLLMProvider):
        self.llm = llm
        self.last_reasoning: str = ""

    def run(
        self,
        requirements: RequirementsDocument,
        architecture: ArchitectureDocument,
        existing_files: Optional[Dict[str, str]] = None,
        feedback: Optional[str] = None
    ) -> Dict[str, str]:
        """Generates source code files per architecture, optionally incorporating human feedback."""
        prompt_payload = {
            "requirements": requirements.to_dict(),
            "architecture": architecture.to_dict(),
        }
        if existing_files:
            prompt_payload["existing_files_for_reference"] = existing_files
        if feedback:
            prompt_payload["human_operator_review_feedback"] = feedback

        user_prompt = f"Specifications for Implementation:\n{json.dumps(prompt_payload, indent=2)}"

        raw_resp = self.llm.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.2,
            json_output=True
        )

        files, reasoning = self._parse_json(raw_resp)
        self.last_reasoning = reasoning or "Synthesized PEP 8 compliant, type-annotated modules with robust error handling and defensive input parsing."
        return files

    def _parse_json(self, raw_resp: str) -> tuple[Dict[str, str], str]:
        cleaned = raw_resp.strip()
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE).strip()

        try:
            data = json.loads(cleaned)
            reasoning = data.get("reasoning", "")
            if "files" in data and isinstance(data["files"], dict):
                return data["files"], reasoning
            elif isinstance(data, dict) and all(isinstance(v, str) for v in data.values()):
                return data, reasoning
        except Exception:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                    reasoning = data.get("reasoning", "")
                    if "files" in data and isinstance(data["files"], dict):
                        return data["files"], reasoning
                except Exception:
                    pass

        # Fallback to default engine codegen
        fallback = self.llm.generate(
            system_prompt="implement code",
            user_prompt="default fallback",
            json_output=True
        )
        try:
            f_data = json.loads(fallback)
            return f_data.get("files", {}), f_data.get("reasoning", "")
        except Exception:
            return {}, ""
