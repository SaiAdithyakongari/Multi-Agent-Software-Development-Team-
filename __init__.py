"""
Specialized Software Engineering Multi-Agent Team.
"""

from .requirements_agent   import RequirementsAnalystAgent, RequirementsDocument
from .architecture_agent    import ArchitectureAgent, ArchitectureDocument
from .codegen_agent         import CodeGenerationAgent
from .review_agent          import CodeReviewAgent, ReviewDocument
from .test_agent            import TestGenerationExecutionAgent, TestAgentResult
from .bugfix_agent          import BugFixLoopAgent, BugFixAttempt
from .docs_agent            import DocumentationAgent, DocumentationPackage
from .security_agent        import SecurityReviewAgent, SecurityReport
from .static_analysis_agent import StaticAnalysisAgent, StaticAnalysisResult
from .devops_agent          import DevOpsAgent, CICDPackage

__all__ = [
    "RequirementsAnalystAgent", "RequirementsDocument",
    "ArchitectureAgent",        "ArchitectureDocument",
    "CodeGenerationAgent",
    "CodeReviewAgent",          "ReviewDocument",
    "TestGenerationExecutionAgent", "TestAgentResult",
    "BugFixLoopAgent",          "BugFixAttempt",
    "DocumentationAgent",       "DocumentationPackage",
    "SecurityReviewAgent",      "SecurityReport",
    "StaticAnalysisAgent",      "StaticAnalysisResult",
    "DevOpsAgent",              "CICDPackage",
]
