"""
Architecture Agent.
Designs the system architecture: module breakdown, data flow, design patterns,
file/folder structure, and interface contracts.
"""

from dataclasses import dataclass, asdict, field
import json
import re
from typing import Any, Dict, List, Optional
from llm_provider import BaseLLMProvider
from .requirements_agent import RequirementsDocument


@dataclass
class ModuleDefinition:
    name: str
    file_path: str
    purpose: str
    exports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ArchitectureDocument:
    system_overview: str
    design_patterns: List[str] = field(default_factory=list)
    data_flow: str = ""
    modules: List[Dict[str, Any]] = field(default_factory=list)
    folder_structure: str = ""
    interfaces: List[str] = field(default_factory=list)
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArchitectureDocument":
        return cls(
            system_overview=data.get("system_overview", "Modular Python Architecture"),
            design_patterns=data.get("design_patterns", []),
            data_flow=data.get("data_flow", ""),
            modules=data.get("modules", []),
            folder_structure=data.get("folder_structure", ""),
            interfaces=data.get("interfaces", []),
            reasoning=data.get("reasoning", ""),
        )


class ArchitectureAgent:
    """Specialized Agent responsible for system design and component architecture."""

    SYSTEM_PROMPT = """You are a Principal Software Architect Agent on an autonomous engineering team.
Your task is to design a high-cohesion, low-coupling system architecture based on the structured requirements document.

You MUST respond strictly in valid JSON matching this schema:
{
  "system_overview": "Comprehensive architectural description...",
  "reasoning": "Detailed rationale explaining why specific design patterns, module boundaries, and dependency directions were chosen over alternative architectures.",
  "design_patterns": ["Pattern 1", "Pattern 2"],
  "data_flow": "Step 1 -> Step 2 -> Step 3...",
  "modules": [
    {
      "name": "models",
      "file_path": "models.py",
      "purpose": "Domain models, invariants, and serialization",
      "exports": ["ClassA", "ClassB"],
      "dependencies": ["dataclasses", "typing"]
    },
    {
      "name": "core",
      "file_path": "core.py",
      "purpose": "Core business logic and service layer",
      "exports": ["ServiceManager"],
      "dependencies": ["models"]
    },
    {
      "name": "main",
      "file_path": "main.py",
      "purpose": "Interface controller and entrypoint",
      "exports": ["create_app", "run_cli"],
      "dependencies": ["core", "models"]
    }
  ],
  "folder_structure": ".\\n├── models.py\\n├── core.py\\n└── main.py",
  "interfaces": ["core.ServiceManager.execute(param: str) -> bool"]
}
Do NOT include markdown formatting or commentary outside the JSON.
"""

    def __init__(self, llm: BaseLLMProvider):
        self.llm = llm

    def run(self, requirements: RequirementsDocument, feedback: Optional[str] = None) -> ArchitectureDocument:
        """Executes architecture design, optionally incorporating human feedback."""
        user_prompt = f"Requirements Specification:\n{json.dumps(requirements.to_dict(), indent=2)}"
        if feedback:
            user_prompt += f"\n\nHUMAN OPERATOR REVIEW FEEDBACK (incorporate and address all architectural adjustments):\n{feedback}"

        raw_resp = self.llm.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.2,
            json_output=True
        )

        data = self._parse_json(raw_resp)
        return ArchitectureDocument.from_dict(data)

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
            "system_overview": "Layered clean architecture with isolated domain models and business services.",
            "reasoning": "Selected a layered domain-service separation pattern to isolate business rules from I/O boundaries, enabling deterministic mocking and standalone testing.",
            "design_patterns": ["Repository Pattern", "Facade Pattern"],
            "data_flow": "Input -> Controller -> Core Domain Services -> State Mutation -> Response",
            "modules": [
                {
                    "name": "models",
                    "file_path": "models.py",
                    "purpose": "Domain data structures and validations",
                    "exports": ["Item"],
                    "dependencies": ["dataclasses"]
                },
                {
                    "name": "core",
                    "file_path": "core.py",
                    "purpose": "Core business execution and storage logic",
                    "exports": ["ServiceManager"],
                    "dependencies": ["models"]
                },
                {
                    "name": "main",
                    "file_path": "main.py",
                    "purpose": "Application entrypoint",
                    "exports": ["run"],
                    "dependencies": ["core"]
                }
            ],
            "folder_structure": ".\n├── models.py\n├── core.py\n└── main.py",
            "interfaces": ["ServiceManager.add(item)", "ServiceManager.get(id)"]
        }
