"""
Security Review Agent.
Dedicated security scanner that runs after Code Generation.
Scans for: hardcoded secrets, SQL injection, insecure deserialization,
unsafe eval/exec usage, missing input validation, path traversal,
and produces a structured findings report (severity, location, remediation).
"""

import ast
import re
from dataclasses import dataclass, asdict, field
import json
from typing import Any, Dict, List, Optional
from llm_provider import BaseLLMProvider


@dataclass
class SecurityFinding:
    severity: str          # CRITICAL | HIGH | MEDIUM | LOW | INFO
    category: str          # e.g. "Hardcoded Secret", "SQL Injection"
    file: str
    line_number: Optional[int]
    code_snippet: str
    description: str
    remediation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SecurityReport:
    risk_level: str                        # CRITICAL | HIGH | MEDIUM | LOW | CLEAR
    overall_score: float                   # 0-10, higher = safer
    passed: bool
    summary: str
    findings: List[Dict[str, Any]] = field(default_factory=list)
    hardcoded_secrets: List[str]  = field(default_factory=list)
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecurityReport":
        return cls(
            risk_level=data.get("risk_level", "CLEAR"),
            overall_score=float(data.get("overall_score", 9.0)),
            passed=data.get("passed", True),
            summary=data.get("summary", "Security review completed."),
            findings=data.get("findings", []),
            hardcoded_secrets=data.get("hardcoded_secrets", []),
            reasoning=data.get("reasoning", ""),
        )


# ── Static heuristic scanners (run without LLM) ────────────────────────────

_SECRET_PATTERNS = [
    (re.compile(r'(?:password|passwd|secret|api_key|apikey|token|auth_token|access_token)\s*=\s*["\'][^"\']{6,}["\']', re.I), "Hardcoded Secret"),
    (re.compile(r'(?:AWS_SECRET|PRIVATE_KEY|GITHUB_TOKEN|GH_TOKEN)\s*=\s*["\'][^"\']+["\']', re.I), "Hardcoded Cloud Credential"),
    (re.compile(r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----'), "Embedded Private Key"),
]

_INJECTION_PATTERNS = [
    (re.compile(r'(?:execute|cursor\.execute)\s*\(\s*[f"\'`].*\%s.*[f"\'`]', re.I), "SQL Injection Risk"),
    (re.compile(r'(?:execute|cursor\.execute)\s*\(\s*f["\']'), "SQL Injection Risk (f-string)"),
    (re.compile(r'(?:os\.system|subprocess\.call|subprocess\.run)\s*\(\s*.*\+'), "Shell Injection Risk"),
]

_UNSAFE_PATTERNS = [
    (re.compile(r'\beval\s*\('), "Unsafe eval() Usage"),
    (re.compile(r'\bexec\s*\('), "Unsafe exec() Usage"),
    (re.compile(r'pickle\.loads?\s*\('), "Insecure Deserialization (pickle)"),
    (re.compile(r'marshal\.loads?\s*\('), "Insecure Deserialization (marshal)"),
    (re.compile(r'yaml\.load\s*\([^,)]+\)'), "Insecure YAML load (use safe_load)"),
    (re.compile(r'__import__\s*\('), "Dynamic Import Risk"),
]

_VALIDATION_PATTERNS = [
    (re.compile(r'def\s+\w+\s*\([^)]+\)\s*:\s*\n(?:\s+(?!if|try|assert|raise|validate).+\n)*\s+(?:self\._(?:store|data|db)|return)'), "Possible Missing Input Validation"),
]

_PATH_TRAVERSAL_PATTERNS = [
    (re.compile(r'open\s*\(\s*(?:request\.|user_input|input\(|args\.|kwargs\.)'), "Path Traversal Risk"),
    (re.compile(r'os\.path\.join\s*\(.*(?:request\.|user_input|args\.)'), "Path Traversal Risk"),
]


def _static_scan(code_files: Dict[str, str]) -> List[SecurityFinding]:
    """Runs fast regex + AST heuristic scans on every generated file."""
    findings: List[SecurityFinding] = []
    all_patterns = (
        _SECRET_PATTERNS
        + _INJECTION_PATTERNS
        + _UNSAFE_PATTERNS
        + _PATH_TRAVERSAL_PATTERNS
    )
    sev_map = {
        "Hardcoded Secret": "CRITICAL",
        "Hardcoded Cloud Credential": "CRITICAL",
        "Embedded Private Key": "CRITICAL",
        "SQL Injection Risk": "HIGH",
        "SQL Injection Risk (f-string)": "HIGH",
        "Shell Injection Risk": "HIGH",
        "Unsafe eval() Usage": "HIGH",
        "Unsafe exec() Usage": "HIGH",
        "Insecure Deserialization (pickle)": "HIGH",
        "Insecure Deserialization (marshal)": "HIGH",
        "Insecure YAML load (use safe_load)": "MEDIUM",
        "Dynamic Import Risk": "MEDIUM",
        "Path Traversal Risk": "MEDIUM",
        "Possible Missing Input Validation": "LOW",
    }
    remediation_map = {
        "Hardcoded Secret": "Move secrets to environment variables or a vault (e.g. os.environ.get).",
        "Hardcoded Cloud Credential": "Use IAM roles / environment variables. Never embed credentials in source.",
        "Embedded Private Key": "Remove the key from source immediately. Rotate the key and use secrets management.",
        "SQL Injection Risk": "Use parameterised queries: cursor.execute(sql, (param,)).",
        "SQL Injection Risk (f-string)": "Use parameterised queries — never interpolate user input into SQL.",
        "Shell Injection Risk": "Pass arguments as a list to subprocess, not as a joined string.",
        "Unsafe eval() Usage": "Replace eval() with ast.literal_eval() or an explicit parser.",
        "Unsafe exec() Usage": "Remove exec(). Use importlib or well-defined function dispatch instead.",
        "Insecure Deserialization (pickle)": "Never unpickle untrusted data. Use JSON or a safe serialization library.",
        "Insecure Deserialization (marshal)": "Never unmarshal untrusted data. Use JSON instead.",
        "Insecure YAML load (use safe_load)": "Replace yaml.load() with yaml.safe_load().",
        "Dynamic Import Risk": "Whitelist allowed module names and validate before importing.",
        "Path Traversal Risk": "Validate and normalise paths; use os.path.realpath and reject paths outside allowed root.",
        "Possible Missing Input Validation": "Add explicit type and range validation before processing user-supplied values.",
    }

    for filename, code in code_files.items():
        lines = code.splitlines()
        for pattern, category in all_patterns:
            for m in pattern.finditer(code):
                line_num = code[:m.start()].count("\n") + 1
                snippet = lines[line_num - 1].strip()[:120] if line_num <= len(lines) else m.group(0)[:120]
                findings.append(SecurityFinding(
                    severity=sev_map.get(category, "INFO"),
                    category=category,
                    file=filename,
                    line_number=line_num,
                    code_snippet=snippet,
                    description=f"{category} detected in `{filename}` at line {line_num}.",
                    remediation=remediation_map.get(category, "Review and remediate this pattern."),
                ))
    return findings


def _derive_risk_level(findings: List[SecurityFinding]) -> str:
    severities = [f.severity for f in findings]
    if "CRITICAL" in severities: return "CRITICAL"
    if "HIGH"     in severities: return "HIGH"
    if "MEDIUM"   in severities: return "MEDIUM"
    if "LOW"      in severities: return "LOW"
    return "CLEAR"


def _derive_score(findings: List[SecurityFinding]) -> float:
    deductions = {"CRITICAL": 3.0, "HIGH": 1.5, "MEDIUM": 0.5, "LOW": 0.2}
    score = 10.0
    for f in findings:
        score -= deductions.get(f.severity, 0.0)
    return max(0.0, round(score, 1))


class SecurityReviewAgent:
    """
    Dedicated Security Review agent.
    Always runs fast static heuristic scan first, then optionally
    calls the LLM for deeper reasoning and hardcoded-secret detection.
    Fully composable — can be toggled off per run.
    """

    SYSTEM_PROMPT = """You are a Principal Application Security Engineer Agent on an autonomous engineering team.
You are given Python source files and must produce a comprehensive security audit.

Scan for ALL of the following:
1. Hardcoded secrets, API keys, passwords, tokens (any literal credential)
2. SQL/Command injection attack surfaces
3. Insecure deserialization (pickle, marshal, yaml.load)
4. Unsafe use of eval() or exec()
5. Missing input validation on public API boundaries
6. Path traversal risks via unvalidated file paths
7. IDOR (Insecure Direct Object Reference) risks
8. Any other OWASP Top-10 relevant patterns

You MUST respond strictly in valid JSON matching this schema:
{
  "risk_level": "CRITICAL|HIGH|MEDIUM|LOW|CLEAR",
  "overall_score": 9.5,
  "passed": true,
  "reasoning": "Detailed security reasoning explaining threat model, attack vectors identified, and exploitability assessment.",
  "summary": "Executive summary of security posture...",
  "hardcoded_secrets": ["list of any literal credential strings found (redacted)"],
  "findings": [
    {
      "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
      "category": "e.g. Hardcoded Secret",
      "file": "core.py",
      "line_number": 42,
      "code_snippet": "password = 'admin123'",
      "description": "Plain-text password literal found...",
      "remediation": "Move to os.environ.get('PASSWORD')..."
    }
  ]
}
Do NOT include markdown formatting or commentary outside the JSON.
"""

    def __init__(self, llm: BaseLLMProvider):
        self.llm = llm

    def run(self, code_files: Dict[str, str]) -> SecurityReport:
        """
        1. Runs fast static heuristic scans (always).
        2. Calls LLM for deeper analysis and merges findings.
        Returns a SecurityReport with all findings deduplicated.
        """
        # Phase 1: static heuristic scan
        static_findings = _static_scan(code_files)

        # Phase 2: LLM deep analysis
        llm_report = self._llm_scan(code_files)

        # Merge: LLM findings + static findings (deduplicate by file+line)
        seen = set()
        merged: List[SecurityFinding] = []

        # LLM findings first (richer descriptions)
        for f_dict in (llm_report.get("findings") or []):
            key = (f_dict.get("file",""), f_dict.get("line_number"), f_dict.get("category",""))
            if key not in seen:
                seen.add(key)
                merged.append(SecurityFinding(
                    severity=f_dict.get("severity","INFO"),
                    category=f_dict.get("category","Unknown"),
                    file=f_dict.get("file",""),
                    line_number=f_dict.get("line_number"),
                    code_snippet=f_dict.get("code_snippet",""),
                    description=f_dict.get("description",""),
                    remediation=f_dict.get("remediation",""),
                ))

        # Static findings (fill gaps)
        for sf in static_findings:
            key = (sf.file, sf.line_number, sf.category)
            if key not in seen:
                seen.add(key)
                merged.append(sf)

        risk_level = _derive_risk_level(merged) if merged else llm_report.get("risk_level","CLEAR")
        score      = _derive_score(merged) if merged else float(llm_report.get("overall_score",9.5))
        passed     = risk_level not in ("CRITICAL","HIGH")

        return SecurityReport(
            risk_level=risk_level,
            overall_score=score,
            passed=passed,
            summary=llm_report.get("summary", self._auto_summary(merged, risk_level)),
            findings=[f.to_dict() for f in merged],
            hardcoded_secrets=llm_report.get("hardcoded_secrets",[]),
            reasoning=llm_report.get("reasoning","Static heuristic scan completed. No LLM augmentation used."),
        )

    # ── private ─────────────────────────────────────────────────────────────

    def _llm_scan(self, code_files: Dict[str, str]) -> Dict[str, Any]:
        # Truncate large files to keep prompt size manageable
        truncated = {k: v[:3000] for k, v in code_files.items()}
        user_prompt = f"Python source files to audit:\n{json.dumps(truncated, indent=2)}"
        try:
            raw = self.llm.generate(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.1,
                json_output=True,
            )
            return self._parse_json(raw)
        except Exception:
            return {}

    def _parse_json(self, raw: str) -> Dict[str, Any]:
        cleaned = raw.strip()
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"```$",          "", cleaned, flags=re.MULTILINE).strip()
        try:
            return json.loads(cleaned)
        except Exception:
            m = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if m:
                try: return json.loads(m.group(0))
                except Exception: pass
        return {}

    def _auto_summary(self, findings: List[SecurityFinding], risk_level: str) -> str:
        if not findings:
            return "No security issues detected. Code appears clean across all scanned patterns."
        counts: Dict[str, int] = {}
        for f in findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        parts = [f"{v} {k}" for k, v in sorted(counts.items())]
        return (
            f"Security scan found {len(findings)} issue(s): {', '.join(parts)}. "
            f"Overall risk level: {risk_level}. Review findings and apply remediations before deployment."
        )
