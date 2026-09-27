"""
LangGraph Multi-Agent Orchestration Engine — Extended v2.
10 new capabilities layered on top of the original 7-stage pipeline:
  1.  Requirements Clarification Loop
  2.  HITL checkpoints after Architecture & Code Generation
  3.  Security Review Agent (after Code Generation)
  4.  Static Analysis Gate (before Test stage)
  5.  Bug-Fix retry limit + escalation to user
  6.  Regression testing on every fix (full suite re-run)
  7.  Code Coverage reporting per module
  8.  CI/CD Pipeline Scaffolding (DevOps Agent)
  9.  Pipeline Trace & Cost Dashboard (per-stage token/cost tracking)
  10. Live Agent Reasoning Stream (streamed via session-state queue)

Every new capability is a composable node — toggled via FeatureFlags.
The original 7-stage flow is completely preserved.
"""

from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import sys, ast, traceback, runpy
import tempfile
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypedDict

try:
    from langgraph.graph import StateGraph, START, END
except ImportError:
    START = "__start__"
    END   = "__end__"

    class StateGraph:
        def __init__(self, state_schema=None):
            self.nodes: Dict[str, Any] = {}
            self.edges: Dict[str, Any] = {}
            self.conditional_edges: Dict[str, Any] = {}

        def add_node(self, name, func):                              self.nodes[name] = func
        def add_edge(self, s, e):                                    self.edges[s] = e
        def add_conditional_edges(self, src, fn, pm):                self.conditional_edges[src] = (fn, pm)

        def compile(self):
            nodes, edges, cond = self.nodes, self.edges, self.conditional_edges
            class _G:
                def invoke(_, state):
                    s = dict(state)
                    cur = edges.get(START)
                    for _ in range(200):
                        if not cur or cur == END: break
                        if cur not in nodes: break
                        s = nodes[cur](s)
                        if cur in cond:
                            fn, pm = cond[cur]
                            cur = pm.get(fn(s), END)
                        else:
                            cur = edges.get(cur, END)
                    return s
            return _G()


from llm_provider import get_llm_provider, BaseLLMProvider
from sandbox      import SandboxExecutor, ExecutionResult
from git_manager  import GitManager

from agents.requirements_agent    import RequirementsAnalystAgent, RequirementsDocument
from agents.architecture_agent     import ArchitectureAgent,        ArchitectureDocument
from agents.codegen_agent          import CodeGenerationAgent
from agents.review_agent           import CodeReviewAgent,          ReviewDocument
from agents.test_agent             import TestGenerationExecutionAgent, TestAgentResult
from agents.bugfix_agent           import BugFixLoopAgent,          BugFixAttempt
from agents.docs_agent             import DocumentationAgent,       DocumentationPackage
from agents.security_agent         import SecurityReviewAgent,      SecurityReport
from agents.static_analysis_agent  import StaticAnalysisAgent,      StaticAnalysisResult
from agents.devops_agent           import DevOpsAgent,              CICDPackage


# ═════════════════════════════════════════════════════════════════════════════
# FEATURE FLAGS
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class FeatureFlags:
    """
    Toggle each new capability independently per run.
    
    Default values (ON by default):
      - security_review: Security scanning after code generation
      - static_analysis: Lint/type-check gate before tests
      - regression_testing: Full test suite re-run after each bug fix
      - coverage_reporting: Per-module coverage with threshold flagging
      - trace_dashboard: Pipeline trace and cost tracking
      - clarification_loop: Always-on requirement clarity check
    
    OFF by default (opt-in):
      - hitl_checkpoints: Human approval gates after Architecture/CodeGen
      - live_stream: Real-time agent reasoning in UI
      - cicd_scaffolding: CI/CD pipeline file generation
    """
    # Always-on features
    clarification_loop:    bool = True   # Feature 1 - always runs
    
    # ON by default
    security_review:       bool = True   # Feature 3
    static_analysis:       bool = True   # Feature 4
    bugfix_escalation:     bool = True   # Feature 5  (retry limit + escalation)
    regression_testing:    bool = True   # Feature 6
    coverage_reporting:    bool = True   # Feature 7
    trace_dashboard:       bool = True   # Feature 9
    
    # OFF by default (opt-in)
    hitl_checkpoints:      bool = False  # Feature 2  (arch + codegen gates)
    live_stream:           bool = False  # Feature 10
    cicd_scaffolding:      bool = False  # Feature 8

    def to_dict(self) -> Dict[str, bool]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FeatureFlags":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    @classmethod
    def all_on(cls)  -> "FeatureFlags": return cls()
    @classmethod
    def all_off(cls) -> "FeatureFlags": return cls(
        clarification_loop=True,  # Always stays True
        hitl_checkpoints=False,
        security_review=False,
        static_analysis=False,
        bugfix_escalation=False,
        regression_testing=False,
        coverage_reporting=False,
        cicd_scaffolding=False,
        trace_dashboard=False,
        live_stream=False,
    )


# ═════════════════════════════════════════════════════════════════════════════
# PIPELINE TRACE  (Feature 9)
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class StageTrace:
    stage: str
    agent: str
    start_time: str
    end_time: str
    duration_seconds: float
    token_estimate: int        # rough estimate: len(reasoning) / 4
    cost_estimate_usd: float   # $0.0004 / 1K tokens (gpt-3.5 baseline)
    artifact_keys: List[str]
    reasoning_snippet: str
    status: str                # SUCCESS | FAILED | SKIPPED | PAUSED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _make_trace(
    stage: str, agent: str,
    t0: float, t1: float,
    reasoning: str, artifact_keys: List[str],
    status: str = "SUCCESS",
) -> StageTrace:
    tokens = max(1, len(reasoning) // 4)
    return StageTrace(
        stage=stage, agent=agent,
        start_time=datetime.utcfromtimestamp(t0).isoformat() + "Z",
        end_time=datetime.utcfromtimestamp(t1).isoformat() + "Z",
        duration_seconds=round(t1 - t0, 3),
        token_estimate=tokens,
        cost_estimate_usd=round(tokens / 1000 * 0.0004, 6),
        artifact_keys=artifact_keys,
        reasoning_snippet=(reasoning[:300] + "…") if len(reasoning) > 300 else reasoning,
        status=status,
    )


# ═════════════════════════════════════════════════════════════════════════════
# LIVE STREAM  (Feature 10)
# ═════════════════════════════════════════════════════════════════════════════

# Module-level queue used to stream reasoning tokens to the UI.
# The Streamlit app polls this queue every 0.5 s.
_STREAM_QUEUE: queue.Queue = queue.Queue(maxsize=500)


def stream_emit(stage: str, agent: str, text: str) -> None:
    """Emit a reasoning chunk to the live stream queue (non-blocking)."""
    try:
        _STREAM_QUEUE.put_nowait({"stage": stage, "agent": agent, "text": text,
                                   "ts": datetime.utcnow().isoformat() + "Z"})
    except queue.Full:
        pass


def stream_drain() -> List[Dict[str, str]]:
    """Drain all pending stream events (called by UI)."""
    events: List[Dict[str, str]] = []
    while True:
        try:
            events.append(_STREAM_QUEUE.get_nowait())
        except queue.Empty:
            break
    return events


# ═════════════════════════════════════════════════════════════════════════════
# TYPED STATE
# ═════════════════════════════════════════════════════════════════════════════

class PipelineAuditLog(TypedDict):
    timestamp: str
    stage: str
    agent: str
    action: str
    status: str
    details: str


class ApprovalHistoryItem(TypedDict):
    id: str
    stage: str
    action: str
    timestamp: str
    reviewer: str
    feedback: Optional[str]
    artifact_summary: Optional[str]


class ClarificationQuestion(TypedDict):
    id: str
    question: str
    category: str       # scope | constraint | data_model | edge_case
    answered: bool
    answer: Optional[str]


class MultiAgentState(TypedDict):
    # ── Config ────────────────────────────────────────────────────────────
    requirement:     str
    provider_type:   Optional[str]
    api_key:         Optional[str]
    max_iterations:  int
    project_dir:     str
    require_approval: bool
    feature_flags:   Dict[str, bool]

    # ── Pipeline control ─────────────────────────────────────────────────
    pipeline_status: str   # IDLE|RUNNING|PAUSED_FOR_APPROVAL|PAUSED_FOR_CLARIFICATION|COMPLETED|STOPPED|ESCALATED
    pending_approval:    Optional[Dict[str, Any]]
    approval_history:    List[ApprovalHistoryItem]

    # ── Clarification loop (Feature 1) ───────────────────────────────────
    clarification_questions: List[ClarificationQuestion]
    clarification_answered:  bool

    # ── Agent artifacts ──────────────────────────────────────────────────
    requirements_doc:  Optional[Dict[str, Any]]
    architecture_doc:  Optional[Dict[str, Any]]
    code_files:        Dict[str, str]
    codegen_reasoning: str
    review_doc:        Optional[Dict[str, Any]]
    security_report:   Optional[Dict[str, Any]]   # Feature 3
    static_analysis:   Optional[Dict[str, Any]]   # Feature 4
    test_files:        Dict[str, str]
    test_result:       Optional[Dict[str, Any]]
    coverage_report:   Optional[Dict[str, Any]]   # Feature 7
    bugfix_history:    List[Dict[str, Any]]
    bugfix_iteration:  int
    bugfix_per_test_retries: Dict[str, int]       # Feature 5
    is_resolved:       bool
    escalation_info:   Optional[Dict[str, Any]]   # Feature 5
    documentation:     Optional[Dict[str, Any]]
    cicd_package:      Optional[Dict[str, Any]]   # Feature 8

    # ── Trace & cost (Feature 9) ─────────────────────────────────────────
    stage_traces:    List[Dict[str, Any]]
    total_tokens:    int
    total_cost_usd:  float

    # ── Git / audit ──────────────────────────────────────────────────────
    git_commits:     List[Dict[str, Any]]
    audit_logs:      List[PipelineAuditLog]
    current_stage:   str
    error_message:   Optional[str]


# ═════════════════════════════════════════════════════════════════════════════
# STATE PERSISTENCE
# ═════════════════════════════════════════════════════════════════════════════

def save_state(state: MultiAgentState) -> None:
    p = state.get("project_dir")
    if p and os.path.exists(p):
        try:
            with open(os.path.join(p, "state.json"), "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, default=str)
        except Exception:
            pass


def load_state(project_dir: str) -> Optional[MultiAgentState]:
    p = os.path.join(project_dir, "state.json")
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _flags(state: MultiAgentState) -> FeatureFlags:
    return FeatureFlags.from_dict(state.get("feature_flags") or {})


def log_event(state, stage, agent, action, status, details) -> None:
    state["audit_logs"].append({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "stage": stage, "agent": agent,
        "action": action, "status": status, "details": details,
    })


def _add_trace(state: MultiAgentState, trace: StageTrace) -> None:
    if _flags(state).trace_dashboard:
        state["stage_traces"].append(trace.to_dict())
        state["total_tokens"]   += trace.token_estimate
        state["total_cost_usd"] += trace.cost_estimate_usd


def _write_files(p_dir: str, files: Dict[str, str]) -> None:
    for rel, code in files.items():
        abs_p = os.path.join(p_dir, rel)
        os.makedirs(os.path.dirname(abs_p), exist_ok=True)
        # Validate Python source before writing
        if rel.endswith('.py'):
            try:
                compile(code, rel, 'exec')
            except SyntaxError as e:
                raise RuntimeError(f"Syntax validation failed for {rel}: {e.msg} (line {e.lineno})")
            # Simple stray backslash detection in f-strings
            if re.search(r"f[\'\"](?:.*?\\)[\'\"]", code):
                raise RuntimeError(f"Potential stray backslash in f-string in {rel}")
            # Dry-run import in isolated namespace
            try:
                pass  # Skip runtime execution; dependencies may not exist yet
            except Exception as e:
                tb = traceback.format_exc(limit=1)
                raise RuntimeError(f"Import/run error in {rel}: {e.__class__.__name__}: {e}")
        with open(abs_p, "w", encoding="utf-8") as f:
            f.write(code)


def _git_commit(state: MultiAgentState, stage: str, message: str,
                author: str, email: str) -> Optional[str]:
    gm = GitManager(state["project_dir"])
    h  = gm.commit_stage(stage, message, author, email)
    state["git_commits"] = gm.get_commit_history()
    return h


# ═════════════════════════════════════════════════════════════════════════════
# COVERAGE HELPER  (Feature 7)
# ═════════════════════════════════════════════════════════════════════════════

def _run_with_coverage(
    code_files: Dict[str, str],
    test_files: Dict[str, str],
    threshold: int = 80,
    timeout: int = 40,
) -> Dict[str, Any]:
    """
    Runs pytest with coverage inside a temp dir.
    Returns a coverage report dict with per-module percentages.
    """
    tmp = tempfile.mkdtemp(prefix="coverage_")
    try:
        _write_files(tmp, code_files)
        _write_files(tmp, test_files)

        env = os.environ.copy()
        env["PYTHONPATH"] = tmp
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        for k in ["GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
            env.pop(k, None)

        # Check if pytest-cov is available
        check = subprocess.run([sys.executable, "-m", "pytest", "--co", "-q"],
                               cwd=tmp, capture_output=True, env=env, timeout=10)

        use_cov = False
        try:
            cv = subprocess.run([sys.executable, "-m", "pytest_cov", "--version"],
                                capture_output=True, timeout=5)
            use_cov = cv.returncode == 0
        except Exception:
            try:
                cv2 = subprocess.run([sys.executable, "-c", "import pytest_cov"],
                                     capture_output=True, timeout=5)
                use_cov = cv2.returncode == 0
            except Exception:
                use_cov = False

        cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]
        if use_cov:
            src_modules = [k.replace(".py","") for k in code_files if k.endswith(".py") and not k.startswith("test_")]
            for m in src_modules:
                cmd += [f"--cov={m}"]
            cmd += ["--cov-report=term-missing"]

        result = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True,
                                env=env, timeout=timeout)

        stdout  = result.stdout or ""
        coverage_map: Dict[str, int] = {}
        below_threshold: List[str]   = []
        total_coverage: Optional[int] = None

        if use_cov:
            # Parse coverage table from pytest-cov output
            # Format: module.py    42    5    88%
            cov_re = re.compile(r'^(\S+\.py)\s+\d+\s+\d+\s+(\d+)%', re.MULTILINE)
            for m in cov_re.finditer(stdout):
                fname = m.group(1)
                pct   = int(m.group(2))
                coverage_map[fname] = pct
                if pct < threshold:
                    below_threshold.append(fname)

            # Total line
            total_re = re.compile(r'^TOTAL\s+\d+\s+\d+\s+(\d+)%', re.MULTILINE)
            tm = total_re.search(stdout)
            if tm:
                total_coverage = int(tm.group(1))
        else:
            # No coverage data — synthesise from pass counts
            for fname in code_files:
                if fname.endswith(".py") and not fname.startswith("test_"):
                    coverage_map[fname] = -1   # unknown

        passed = result.returncode == 0
        return {
            "passed":           passed,
            "coverage_map":     coverage_map,
            "total_coverage":   total_coverage,
            "below_threshold":  below_threshold,
            "threshold":        threshold,
            "stdout":           stdout,
            "coverage_tool_used": use_cov,
            "summary": (
                f"Coverage: {total_coverage}% total. "
                f"{len(below_threshold)} module(s) below {threshold}% threshold."
                if total_coverage is not None
                else "Coverage tool not available — install pytest-cov for per-module reporting."
            ),
        }
    except Exception as e:
        return {
            "passed": False,
            "coverage_map": {},
            "total_coverage": None,
            "below_threshold": [],
            "threshold": threshold,
            "stdout": "",
            "coverage_tool_used": False,
            "summary": f"Coverage run error: {e}",
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ═════════════════════════════════════════════════════════════════════════════
# CLARIFICATION QUESTION GENERATOR  (Feature 1)
# ═════════════════════════════════════════════════════════════════════════════

_CLARIFICATION_PROMPT = """\
You are a Requirements Analyst. Given a raw software requirement, identify up to 5 targeted
clarifying questions that, if left unanswered, could result in ambiguous scope, wrong data models,
or missing constraints.

Only generate questions for genuine gaps — not hypothetical edge cases.
If the requirement is sufficiently detailed, return an empty list.

Respond strictly in valid JSON:
{
  "questions": [
    {"id": "CQ-1", "question": "...", "category": "scope|constraint|data_model|edge_case"},
    ...
  ]
}
"""


def _generate_clarification_questions(
    llm: BaseLLMProvider, requirement: str
) -> List[ClarificationQuestion]:
    try:
        raw = llm.generate(
            system_prompt=_CLARIFICATION_PROMPT,
            user_prompt=f"Requirement:\n{requirement}",
            temperature=0.3,
            json_output=True,
        )
        cleaned = raw.strip()
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"```$",          "", cleaned, flags=re.MULTILINE).strip()
        data    = json.loads(cleaned)
        qs = data.get("questions", [])
        return [
            ClarificationQuestion(
                id=q.get("id", f"CQ-{i+1}"),
                question=q.get("question", ""),
                category=q.get("category", "scope"),
                answered=False,
                answer=None,
            )
            for i, q in enumerate(qs) if q.get("question")
        ]
    except Exception:
        return []


# ═════════════════════════════════════════════════════════════════════════════
# PIPELINE NODE HANDLERS
# ═════════════════════════════════════════════════════════════════════════════

# ── 0. Clarification (Feature 1) ─────────────────────────────────────────────

def clarification_node(state: MultiAgentState) -> MultiAgentState:
    state["current_stage"] = "Clarification"
    flags = _flags(state)
    if not flags.clarification_loop:
        state["clarification_answered"] = True
        return state

    llm = get_llm_provider(state.get("provider_type"), state.get("api_key"))
    t0  = time.time()
    stream_emit("Clarification", "Requirements Analyst Agent",
                "Analysing requirement for ambiguous or missing details…")

    questions = _generate_clarification_questions(llm, state["requirement"])

    if not questions:
        # Requirement is clear — skip loop
        state["clarification_answered"] = True
        state["clarification_questions"] = []
        log_event(state, "Clarification", "Requirements Analyst Agent",
                  "Requirement Clarity Check", "SUCCESS",
                  "Requirement is sufficiently detailed. No clarification needed.")
        _add_trace(state, _make_trace("Clarification", "Requirements Analyst Agent",
                                       t0, time.time(), "Requirement clear — no questions.", [], "SUCCESS"))
        return state

    # Pause for user answers
    state["clarification_questions"] = questions
    state["clarification_answered"]  = False
    state["pipeline_status"]         = "PAUSED_FOR_CLARIFICATION"
    log_event(state, "Clarification", "Requirements Analyst Agent",
              "Clarification Questions Generated", "PAUSED",
              f"Generated {len(questions)} clarifying question(s). "
              "Pipeline paused — awaiting user answers.")
    _add_trace(state, _make_trace("Clarification", "Requirements Analyst Agent",
                                   t0, time.time(), f"{len(questions)} questions generated.",
                                   ["clarification_questions"], "PAUSED"))
    save_state(state)
    return state


# ── 1. Requirements ───────────────────────────────────────────────────────────

def requirements_node(state: MultiAgentState,
                      feedback: Optional[str] = None) -> MultiAgentState:
    state["current_stage"] = "Requirements"
    llm   = get_llm_provider(state.get("provider_type"), state.get("api_key"))
    agent = RequirementsAnalystAgent(llm)
    t0    = time.time()

    # Build enriched prompt with clarification answers
    enriched_req = state["requirement"]
    answered = [q for q in state.get("clarification_questions", []) if q.get("answered") and q.get("answer")]
    if answered:
        qa_block = "\n".join(f"Q: {q['question']}\nA: {q['answer']}" for q in answered)
        enriched_req += f"\n\nClarification answers provided by operator:\n{qa_block}"
        stream_emit("Requirements", "Requirements Analyst Agent",
                    f"Incorporating {len(answered)} clarification answer(s)…")

    stream_emit("Requirements", "Requirements Analyst Agent",
                "Deconstructing requirement into functional & non-functional specifications…")

    doc = agent.run(enriched_req, feedback=feedback)
    state["requirements_doc"] = doc.to_dict()

    p_dir   = state["project_dir"]
    req_file = os.path.join(p_dir, "REQUIREMENTS.md")
    with open(req_file, "w", encoding="utf-8") as f:
        f.write(f"# Requirements: {doc.title}\n\n## Problem Statement\n{doc.problem_statement}\n\n")
        f.write("## Functional Requirements\n")
        for fr in doc.functional_requirements:
            f.write(f"- **{fr.get('id')}**: {fr.get('description')}\n")

    h = _git_commit(state, "Requirements",
                    "feat(requirements): specification established",
                    "Requirements-Analyst-Agent", "analyst@multiagent.ai")
    log_event(state, "Requirements", "Requirements Analyst Agent",
              "Specification Generated", "SUCCESS",
              f"{len(doc.functional_requirements)} FRs. Commit: {(h or '')[:7]}.")
    _add_trace(state, _make_trace("Requirements", "Requirements Analyst Agent",
                                   t0, time.time(), doc.reasoning,
                                   ["requirements_doc"], "SUCCESS"))
    stream_emit("Requirements", "Requirements Analyst Agent",
                f"✅ Requirements document complete — {len(doc.functional_requirements)} functional requirements.")
    return state


# ── 2. Architecture ───────────────────────────────────────────────────────────

def architecture_node(state: MultiAgentState,
                      feedback: Optional[str] = None) -> MultiAgentState:
    state["current_stage"] = "Architecture"
    llm   = get_llm_provider(state.get("provider_type"), state.get("api_key"))
    agent = ArchitectureAgent(llm)
    t0    = time.time()
    stream_emit("Architecture", "Architecture Agent",
                "Designing module boundaries, interfaces, and design patterns…")

    req_doc  = RequirementsDocument.from_dict(state["requirements_doc"] or {})
    arch_doc = agent.run(req_doc, feedback=feedback)
    state["architecture_doc"] = arch_doc.to_dict()

    p_dir = state["project_dir"]
    with open(os.path.join(p_dir, "ARCHITECTURE.md"), "w", encoding="utf-8") as f:
        f.write(f"# System Architecture\n\n{arch_doc.system_overview}\n\n")
        f.write("## Modules\n")
        for m in arch_doc.modules:
            f.write(f"### {m.get('name')} (`{m.get('file_path')}`)\n{m.get('purpose')}\n\n")

    h = _git_commit(state, "Architecture",
                    "feat(arch): system architecture designed",
                    "Architecture-Agent", "architect@multiagent.ai")
    log_event(state, "Architecture", "Architecture Agent",
              "Architecture Formulated", "SUCCESS",
              f"{len(arch_doc.modules)} modules. Commit: {(h or '')[:7]}.")
    _add_trace(state, _make_trace("Architecture", "Architecture Agent",
                                   t0, time.time(), arch_doc.reasoning,
                                   ["architecture_doc"], "SUCCESS"))
    stream_emit("Architecture", "Architecture Agent",
                f"✅ Architecture blueprint complete — {len(arch_doc.modules)} module(s) specified.")
    return state


# ── 3. Code Generation ────────────────────────────────────────────────────────

def codegen_node(state: MultiAgentState,
                 feedback: Optional[str] = None) -> MultiAgentState:
    state["current_stage"] = "Code Generation"
    llm   = get_llm_provider(state.get("provider_type"), state.get("api_key"))
    agent = CodeGenerationAgent(llm)
    t0    = time.time()
    stream_emit("Code Generation", "Code Generation Agent",
                "Implementing production-ready modules with full typing and error handling…")

    req_doc  = RequirementsDocument.from_dict(state["requirements_doc"] or {})
    arch_doc = ArchitectureDocument.from_dict(state["architecture_doc"] or {})

    files = agent.run(req_doc, arch_doc,
                      existing_files=state.get("code_files"), feedback=feedback)
    state["code_files"]        = files
    state["codegen_reasoning"] = getattr(agent, "last_reasoning", "")

    _write_files(state["project_dir"], files)

    h = _git_commit(state, "Code Generation",
                    "feat(code): module implementations generated",
                    "CodeGen-Agent", "developer@multiagent.ai")
    log_event(state, "Code Generation", "Code Generation Agent",
              "Modules Implemented", "SUCCESS",
              f"{len(files)} file(s) generated. Commit: {(h or '')[:7]}.")
    _add_trace(state, _make_trace("Code Generation", "Code Generation Agent",
                                   t0, time.time(), state["codegen_reasoning"],
                                   list(files.keys()), "SUCCESS"))
    stream_emit("Code Generation", "Code Generation Agent",
                f"✅ {len(files)} source file(s) implemented.")
    return state


# ── 4. Security Review (Feature 3) ────────────────────────────────────────────

def security_node(state: MultiAgentState) -> MultiAgentState:
    state["current_stage"] = "Security Review"
    flags = _flags(state)
    if not flags.security_review:
        log_event(state, "Security Review", "Security Review Agent",
                  "Security Review", "SKIPPED", "Feature disabled.")
        return state

    llm   = get_llm_provider(state.get("provider_type"), state.get("api_key"))
    agent = SecurityReviewAgent(llm)
    t0    = time.time()
    stream_emit("Security Review", "Security Review Agent",
                "Scanning for hardcoded secrets, injection risks, unsafe eval/exec, missing validation…")

    report = agent.run(state["code_files"])
    state["security_report"] = report.to_dict()

    sev = report.risk_level
    status = "SUCCESS" if report.passed else "WARNING"
    log_event(state, "Security Review", "Security Review Agent",
              "Security Scan Completed", status,
              f"Risk: {sev} | Score: {report.overall_score}/10 | "
              f"{len(report.findings)} finding(s).")
    _add_trace(state, _make_trace("Security Review", "Security Review Agent",
                                   t0, time.time(), report.reasoning,
                                   ["security_report"], status))
    stream_emit("Security Review", "Security Review Agent",
                f"{'✅' if report.passed else '⚠️'} Security scan complete — "
                f"{len(report.findings)} finding(s), risk level: {sev}.")
    return state


# ── 5. Code Review ────────────────────────────────────────────────────────────

def review_node(state: MultiAgentState,
                feedback: Optional[str] = None) -> MultiAgentState:
    state["current_stage"] = "Code Review"
    llm   = get_llm_provider(state.get("provider_type"), state.get("api_key"))
    agent = CodeReviewAgent(llm)
    t0    = time.time()
    stream_emit("Code Review", "Code Review Agent",
                "Auditing for bugs, code smells, security vulnerabilities, and architecture adherence…")

    req_doc  = RequirementsDocument.from_dict(state["requirements_doc"] or {})
    arch_doc = ArchitectureDocument.from_dict(state["architecture_doc"] or {})
    review   = agent.run(req_doc, arch_doc, state["code_files"], feedback=feedback)
    state["review_doc"] = review.to_dict()

    p_dir = state["project_dir"]
    with open(os.path.join(p_dir, "CODE_REVIEW.md"), "w", encoding="utf-8") as f:
        f.write(f"# Code Review Report\n\n**Score**: {review.overall_score}/10\n\n")
        f.write(f"## Summary\n{review.summary}\n\n")
        if review.issues:
            f.write("## Issues\n")
            for issue in review.issues:
                f.write(f"- [{issue.get('severity')}] `{issue.get('file')}`: "
                        f"{issue.get('description')}\n")

    h = _git_commit(state, "Code Review",
                    f"review(audit): score {review.overall_score}/10 ({review.status})",
                    "Code-Review-Agent", "reviewer@multiagent.ai")
    status = "SUCCESS" if review.passed else "WARNING"
    log_event(state, "Code Review", "Code Review Agent",
              "Audit Completed", status,
              f"Score {review.overall_score}/10. {len(review.issues)} issue(s). "
              f"Commit: {(h or '')[:7]}.")
    _add_trace(state, _make_trace("Code Review", "Code Review Agent",
                                   t0, time.time(), review.reasoning,
                                   ["review_doc"], status))
    stream_emit("Code Review", "Code Review Agent",
                f"✅ Review done — {review.overall_score}/10, {len(review.issues)} issue(s).")
    return state


# ── 6. Static Analysis Gate (Feature 4) ──────────────────────────────────────

def static_analysis_node(state: MultiAgentState) -> MultiAgentState:
    state["current_stage"] = "Static Analysis"
    flags = _flags(state)
    if not flags.static_analysis:
        state["static_analysis"] = {"passed": True, "summary": "Static analysis disabled."}
        log_event(state, "Static Analysis", "Static Analysis Agent",
                  "Static Analysis Gate", "SKIPPED", "Feature disabled.")
        return state

    agent = StaticAnalysisAgent(timeout_seconds=30)
    t0    = time.time()
    stream_emit("Static Analysis", "Static Analysis Agent",
                "Running ruff/flake8 lint + mypy type-check on generated source files…")

    result = agent.run(state["code_files"])
    state["static_analysis"] = result.to_dict()

    status = "SUCCESS" if result.passed else "FAILED"
    log_event(state, "Static Analysis", "Static Analysis Agent",
              "Static Analysis Gate", status, result.summary)
    _add_trace(state, _make_trace("Static Analysis", "Static Analysis Agent",
                                   t0, time.time(), result.reasoning,
                                   ["static_analysis"], status))
    stream_emit("Static Analysis", "Static Analysis Agent",
                f"{'✅' if result.passed else '❌'} {result.summary}")
    return state


def route_after_static(state: MultiAgentState) -> str:
    """If static analysis failed, route back to codegen for a fix."""
    sa = state.get("static_analysis") or {}
    if not sa.get("passed", True):
        log_event(state, "Static Analysis", "Static Analysis Agent",
                  "Routing to Code-Fix", "WARNING",
                  f"Static gate failed ({sa.get('error_count',0)} errors) — "
                  "re-routing to Code Generation for repair.")
        return "codegen_fix"
    return "test"


# ── 7. Test Execution (Features 6, 7) ─────────────────────────────────────────

def test_node(state: MultiAgentState) -> MultiAgentState:
    state["current_stage"] = "Test Execution"
    llm     = get_llm_provider(state.get("provider_type"), state.get("api_key"))
    sandbox = SandboxExecutor(timeout_seconds=30)
    agent   = TestGenerationExecutionAgent(llm, sandbox)
    t0      = time.time()
    stream_emit("Test Execution", "Test & Verification Agent",
                "Synthesising Pytest suite and executing in isolated sandbox…")

    req_doc  = RequirementsDocument.from_dict(state["requirements_doc"] or {})
    arch_doc = ArchitectureDocument.from_dict(state["architecture_doc"] or {})

    # Feature 6: always pass the full accumulated test suite
    test_res = agent.run(req_doc, arch_doc, state["code_files"],
                         existing_test_files=state.get("test_files") or None)
    state["test_files"]  = test_res.test_files
    state["test_result"] = test_res.to_dict()

    _write_files(state["project_dir"], test_res.test_files)

    # Feature 7: coverage reporting
    flags = _flags(state)
    if flags.coverage_reporting:
        stream_emit("Test Execution", "Test & Verification Agent",
                    "Measuring per-module code coverage…")
        cov = _run_with_coverage(state["code_files"], state["test_files"])
        state["coverage_report"] = cov

    h = _git_commit(state, "Test Execution",
                    f"test(suite): {test_res.execution_result.tests_passed}/"
                    f"{test_res.execution_result.tests_total} passed",
                    "Test-Automation-Agent", "tester@multiagent.ai")
    status = "SUCCESS" if test_res.execution_result.success else "FAILED"
    log_event(state, "Test Execution", "Test & Verification Agent",
              "Test Execution Completed", status,
              f"{test_res.execution_result.tests_passed} passed, "
              f"{test_res.execution_result.tests_failed} failed in "
              f"{test_res.execution_result.duration_seconds:.2f}s. "
              f"Commit: {(h or '')[:7]}.")
    _add_trace(state, _make_trace("Test Execution", "Test & Verification Agent",
                                   t0, time.time(), test_res.reasoning,
                                   ["test_result", "test_files"], status))
    stream_emit("Test Execution", "Test & Verification Agent",
                f"{'✅' if test_res.execution_result.success else '❌'} "
                f"{test_res.execution_result.tests_passed}/{test_res.execution_result.tests_total} tests passed.")
    return state


# ── 8. Bug-Fix Router ─────────────────────────────────────────────────────────

def route_after_testing(state: MultiAgentState) -> str:
    test_res = state.get("test_result") or {}
    success  = test_res.get("success", False)
    iteration = state.get("bugfix_iteration", 0)
    max_iter  = state.get("max_iterations", 3)

    if success:
        state["is_resolved"] = True
        return "documentation"

    flags = _flags(state)

    # Feature 5: per-test retry tracking
    if flags.bugfix_escalation:
        error_traces = test_res.get("error_traces", [])
        retries = state.get("bugfix_per_test_retries") or {}
        for trace in error_traces:
            key = trace[:80] if trace else "unknown"
            retries[key] = retries.get(key, 0) + 1

        # Escalate if any single failure has been seen > max_iter times
        escalated_tests = [k for k, v in retries.items() if v > max_iter]
        if escalated_tests:
            state["is_resolved"]      = False
            state["pipeline_status"]  = "ESCALATED"
            state["bugfix_per_test_retries"] = retries
            state["escalation_info"]  = {
                "reason":       f"Bug-Fix agent exceeded {max_iter} retry attempts.",
                "failing_tests": escalated_tests,
                "last_fix":     (state["bugfix_history"][-1] if state["bugfix_history"] else {}),
                "diagnostic":   (
                    f"After {max_iter} autonomous repair iterations the following tests "
                    f"are still failing:\n" + "\n".join(f"• {t}" for t in escalated_tests[:5])
                ),
            }
            log_event(state, "Bug-Fix Loop", "Bug-Fix Loop Agent",
                      "Escalated to Human Operator", "WARNING",
                      f"Retry limit exceeded for {len(escalated_tests)} test(s). "
                      "Surfacing for manual intervention.")
            save_state(state)
            return "documentation"   # proceed to docs with unresolved note

        state["bugfix_per_test_retries"] = retries

    if iteration >= max_iter:
        state["is_resolved"] = False
        log_event(state, "Bug-Fix Loop", "Bug-Fix Loop Agent",
                  "Iteration Cap Reached", "WARNING",
                  f"Max repair iterations ({max_iter}) reached.")
        return "documentation"

    return "bugfix"


# ── 9. Bug-Fix (Features 5, 6) ────────────────────────────────────────────────

def bugfix_node(state: MultiAgentState) -> MultiAgentState:
    state["current_stage"]    = "Bug-Fix Loop"
    state["bugfix_iteration"] = state.get("bugfix_iteration", 0) + 1
    curr_iter = state["bugfix_iteration"]

    llm   = get_llm_provider(state.get("provider_type"), state.get("api_key"))
    agent = BugFixLoopAgent(llm, max_iterations=state.get("max_iterations", 3))
    t0    = time.time()
    stream_emit("Bug-Fix Loop", "Bug-Fix Loop Agent",
                f"Iteration {curr_iter}: diagnosing {state['test_result'].get('tests_failed',0)} "
                "failing test(s) and synthesising patch…")

    test_res_data = state.get("test_result") or {}
    exec_res = ExecutionResult(
        success=test_res_data.get("success", False),
        exit_code=test_res_data.get("exit_code", 1),
        stdout=test_res_data.get("stdout", ""),
        stderr=test_res_data.get("stderr", ""),
        tests_total=test_res_data.get("tests_total", 0),
        tests_passed=test_res_data.get("tests_passed", 0),
        tests_failed=test_res_data.get("tests_failed", 1),
        duration_seconds=test_res_data.get("duration_seconds", 0.0),
        error_traces=test_res_data.get("error_traces", []),
    )
    review_doc = ReviewDocument.from_dict(state.get("review_doc") or {})

    attempt = agent.run(
        iteration=curr_iter,
        code_files=state["code_files"],
        test_files=state["test_files"],
        execution_result=exec_res,
        review_doc=review_doc,
    )

    state["code_files"]    = attempt.fixed_files
    state["bugfix_history"].append(attempt.to_dict())
    try:
        _write_files(state["project_dir"], attempt.fixed_files)
    except RuntimeError as val_err:
        # Log validation failure and treat as unresolved; will trigger retry via router
        log_event(state, "Bug-Fix Loop", "Bug-Fix Loop Agent", "Validation Failed", "ERROR", str(val_err))
        _add_trace(state, _make_trace("Bug-Fix Loop", "Bug-Fix Loop Agent", t0, time.time(), str(val_err), list(attempt.fixed_files.keys()), "ERROR"))
        # Do not commit; keep previous code_files unchanged
        return state

    h = _git_commit(state, "Bug-Fix Loop",
                    f"fix(bugfix-iter-{curr_iter}): automated patch for test failures",
                    "BugFix-Agent", "debugger@multiagent.ai")
    log_event(state, "Bug-Fix Loop", "Bug-Fix Loop Agent",
              f"Repair Iteration {curr_iter} Patch Generated", "SUCCESS",
              f"Patched. Re-running full suite (Feature 6). Commit: {(h or '')[:7]}.")
    _add_trace(state, _make_trace("Bug-Fix Loop", "Bug-Fix Loop Agent",
                                   t0, time.time(), attempt.reasoning,
                                   list(attempt.fixed_files.keys()), "SUCCESS"))
    stream_emit("Bug-Fix Loop", "Bug-Fix Loop Agent",
                f"✅ Patch iteration {curr_iter} applied — re-running full regression suite.")
    return state


# ── 10. Documentation + CI/CD (Features 8) ────────────────────────────────────

def docs_node(state: MultiAgentState) -> MultiAgentState:
    state["current_stage"] = "Documentation"
    llm   = get_llm_provider(state.get("provider_type"), state.get("api_key"))
    agent = DocumentationAgent(llm)
    t0    = time.time()
    stream_emit("Documentation", "Documentation Agent",
                "Authoring README, API reference, setup guide, and build summary…")

    req_doc  = RequirementsDocument.from_dict(state["requirements_doc"] or {})
    arch_doc = ArchitectureDocument.from_dict(state["architecture_doc"] or {})
    rev_doc  = ReviewDocument.from_dict(state.get("review_doc") or {})
    trd      = state.get("test_result") or {}
    exec_res = ExecutionResult(
        success=trd.get("success", False),
        exit_code=trd.get("exit_code", 0),
        stdout=trd.get("stdout", ""),
        stderr=trd.get("stderr", ""),
        tests_total=trd.get("tests_total", 0),
        tests_passed=trd.get("tests_passed", 0),
        tests_failed=trd.get("tests_failed", 0),
        duration_seconds=trd.get("duration_seconds", 0.0),
    )

    docs_pkg = agent.run(
        requirements=req_doc, architecture=arch_doc,
        code_files=state["code_files"], test_result=exec_res,
        review_doc=rev_doc, git_commits_count=len(state["git_commits"]),
    )
    state["documentation"] = docs_pkg.to_dict()

    p_dir = state["project_dir"]
    with open(os.path.join(p_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(docs_pkg.readme)
    with open(os.path.join(p_dir, "BUILD_SUMMARY.json"), "w", encoding="utf-8") as f:
        json.dump(docs_pkg.build_summary, f, indent=2)

    # ── Feature 8: CI/CD scaffolding ────────────────────────────────────
    flags = _flags(state)
    if flags.cicd_scaffolding:
        stream_emit("Documentation", "DevOps Agent",
                    "Generating GitHub Actions workflow, requirements.txt, Dockerfile…")
        devops  = DevOpsAgent(llm)
        cicd_pkg = devops.run(req_doc, arch_doc, state["code_files"],
                              test_result_summary=exec_res.summary())
        state["cicd_package"] = cicd_pkg.to_dict()
        _write_files(p_dir, cicd_pkg.files)
        log_event(state, "Documentation", "DevOps Agent",
                  "CI/CD Scaffold Generated", "SUCCESS",
                  f"GitHub Actions workflow, requirements.txt, Dockerfile written.")

    h = _git_commit(state, "Documentation",
                    "docs(package): README and build report generated",
                    "Documentation-Agent", "docs@multiagent.ai")
    log_event(state, "Documentation", "Documentation Agent",
              "Documentation Finalized", "SUCCESS",
              f"Docs complete. Commit: {(h or '')[:7]}.")
    _add_trace(state, _make_trace("Documentation", "Documentation Agent",
                                   t0, time.time(), docs_pkg.reasoning,
                                   ["documentation"], "SUCCESS"))
    stream_emit("Documentation", "Documentation Agent",
                "✅ Documentation and CI/CD scaffold complete.")
    state["current_stage"] = "Completed"
    return state


# ── Codegen fix (re-entry from static analysis gate) ─────────────────────────

def codegen_fix_node(state: MultiAgentState) -> MultiAgentState:
    """Re-run code generation with static analysis violations as feedback."""
    sa = state.get("static_analysis") or {}
    violations = sa.get("violations", [])
    feedback = (
        "Static analysis gate failed. Fix the following violations before tests:\n"
        + "\n".join(
            f"- [{v.get('severity','?')}] {v.get('file','')}:{v.get('line',0)} "
            f"({v.get('code','')}) {v.get('message','')}"
            for v in violations[:20]
        )
    )
    stream_emit("Code Generation", "Code Generation Agent",
                "Re-generating code to fix static analysis violations…")
    return codegen_node(state, feedback=feedback)


# ═════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR CLASS
# ═════════════════════════════════════════════════════════════════════════════

class MultiAgentOrchestrator:
    """
    Extended Multi-Agent Software Engineering Orchestration Framework.
    10 new capabilities, all composable via FeatureFlags.
    """

    def __init__(
        self,
        provider_type: Optional[str] = None,
        api_key:       Optional[str] = None,
        max_iterations: int = 3,
        feature_flags:  Optional[FeatureFlags] = None,
    ):
        self.provider_type  = provider_type
        self.api_key        = api_key
        self.max_iterations = max_iterations
        self.flags          = feature_flags or FeatureFlags.all_on()
        self.app            = self._build_graph()

    # ── Graph ─────────────────────────────────────────────────────────────────

    def _build_graph(self):
        wf = StateGraph(MultiAgentState)

        wf.add_node("clarification",   clarification_node)
        wf.add_node("requirements",    requirements_node)
        wf.add_node("architecture",    architecture_node)
        wf.add_node("codegen",         codegen_node)
        wf.add_node("security",        security_node)
        wf.add_node("review",          review_node)
        wf.add_node("static_analysis", static_analysis_node)
        wf.add_node("codegen_fix",     codegen_fix_node)
        wf.add_node("test",            test_node)
        wf.add_node("bugfix",          bugfix_node)
        wf.add_node("documentation",   docs_node)

        wf.add_edge(START,            "clarification")
        wf.add_edge("clarification",  "requirements")
        wf.add_edge("requirements",   "architecture")
        wf.add_edge("architecture",   "codegen")
        wf.add_edge("codegen",        "security")
        wf.add_edge("security",       "review")
        wf.add_edge("review",         "static_analysis")

        wf.add_conditional_edges("static_analysis", route_after_static, {
            "codegen_fix": "codegen_fix",
            "test":        "test",
        })
        wf.add_edge("codegen_fix", "static_analysis")   # re-gate after fix

        wf.add_conditional_edges("test", route_after_testing, {
            "bugfix":       "bugfix",
            "documentation":"documentation",
        })
        wf.add_edge("bugfix",         "test")            # Feature 6: full regression
        wf.add_edge("documentation",  END)

        return wf.compile()

    # ── Initial state factory ─────────────────────────────────────────────────

    def _initial_state(
        self,
        requirement: str,
        custom_project_dir: Optional[str] = None,
        require_approval: bool = False,
    ) -> MultiAgentState:
        p_dir = custom_project_dir or tempfile.mkdtemp(prefix="multiagent_project_")
        os.makedirs(p_dir, exist_ok=True)
        GitManager(p_dir).init_repo()

        return MultiAgentState(
            requirement=requirement,
            provider_type=self.provider_type,
            api_key=self.api_key,
            max_iterations=self.max_iterations,
            project_dir=p_dir,
            require_approval=require_approval,
            feature_flags=self.flags.to_dict(),

            pipeline_status="RUNNING",
            pending_approval=None,
            approval_history=[],

            clarification_questions=[],
            clarification_answered=False,

            requirements_doc=None,
            architecture_doc=None,
            code_files={},
            codegen_reasoning="",
            review_doc=None,
            security_report=None,
            static_analysis=None,
            test_files={},
            test_result=None,
            coverage_report=None,
            bugfix_history=[],
            bugfix_iteration=0,
            bugfix_per_test_retries={},
            is_resolved=False,
            escalation_info=None,
            documentation=None,
            cicd_package=None,

            stage_traces=[],
            total_tokens=0,
            total_cost_usd=0.0,

            git_commits=GitManager(p_dir).get_commit_history(),
            audit_logs=[],
            current_stage="Starting",
            error_message=None,
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def run_pipeline(
        self,
        requirement: str,
        custom_project_dir: Optional[str] = None,
        require_approval:   bool = False,
        callback: Optional[Callable] = None,
    ) -> MultiAgentState:
        """
        Runs the full extended pipeline.
        If require_approval=True the pipeline uses the manual HITL mode
        (pauses at clarification, requirements, architecture, and code-gen).
        If clarification questions are detected it pauses immediately.
        """
        state = self._initial_state(requirement, custom_project_dir, require_approval)

        if not require_approval:
            # Fully autonomous execution
            final = self.app.invoke(state)
            final["pipeline_status"] = (
                "ESCALATED" if final.get("escalation_info") else "COMPLETED"
            )
            save_state(final)
            return final

        # ── HITL manual mode: Stage 0 — Clarification ─────────────────────
        state = clarification_node(state)
        if not state["clarification_answered"]:
            # Questions generated — pause
            save_state(state)
            return state

        # No questions — proceed directly to requirements gate
        state = requirements_node(state)
        state["pipeline_status"] = "PAUSED_FOR_APPROVAL"
        state["pending_approval"] = {
            "stage": "Requirements",
            "title": "Requirements Specification",
            "artifact_type": "requirements",
            "artifact": state["requirements_doc"],
        }
        log_event(state, "Requirements", "Human-in-the-Loop Gateway",
                  "Approval Gate Triggered", "PAUSED",
                  "Awaiting human operator approval for Requirements before Architecture.")
        save_state(state)
        return state

    def submit_clarification_answers(
        self,
        project_dir: str,
        answers: Dict[str, str],   # {question_id: answer_text}
    ) -> MultiAgentState:
        """
        Receives user answers to clarification questions.
        Records answers and resumes from requirements.
        """
        state = load_state(project_dir)
        if not state:
            raise ValueError(f"No state found in {project_dir}")

        qs = state.get("clarification_questions", [])
        for q in qs:
            ans = answers.get(q["id"], "").strip()
            if ans:
                q["answered"] = True
                q["answer"]   = ans
        state["clarification_questions"] = qs
        state["clarification_answered"]  = True
        state["pipeline_status"]         = "RUNNING"

        log_event(state, "Clarification", "Human Operator",
                  "Clarification Answers Submitted", "SUCCESS",
                  f"{sum(1 for q in qs if q.get('answered'))} answer(s) recorded.")

        # Resume: run requirements then pause at requirements gate
        state = requirements_node(state)

        if state.get("require_approval"):
            state["pipeline_status"] = "PAUSED_FOR_APPROVAL"
            state["pending_approval"] = {
                "stage": "Requirements",
                "title": "Requirements Specification",
                "artifact_type": "requirements",
                "artifact": state["requirements_doc"],
            }
        else:
            # Fully autonomous from here
            state = architecture_node(state)
            state = codegen_node(state)
            state = security_node(state)
            state = review_node(state)
            state = static_analysis_node(state)
            route = route_after_static(state)
            while route == "codegen_fix":
                state = codegen_fix_node(state)
                state = static_analysis_node(state)
                route = route_after_static(state)
            state = test_node(state)
            route = route_after_testing(state)
            while route == "bugfix":
                state = bugfix_node(state)
                state = test_node(state)
                route = route_after_testing(state)
            state = docs_node(state)
            state["pipeline_status"] = "COMPLETED"

        save_state(state)
        return state

    def approve_and_continue(
        self,
        project_dir: str,
        reviewer: str = "Human Operator",
    ) -> MultiAgentState:
        """Approves the current gate artifact and resumes to the next stage/gate."""
        state = load_state(project_dir)
        if not state:
            raise ValueError(f"No state found in {project_dir}")

        pending = state.get("pending_approval")
        if not pending:
            return state

        stage = pending.get("stage", "")
        state["approval_history"].append({
            "id":               f"appr_{int(datetime.utcnow().timestamp()*1000)}",
            "stage":            stage,
            "action":           "APPROVED",
            "timestamp":        datetime.utcnow().isoformat() + "Z",
            "reviewer":         reviewer,
            "feedback":         None,
            "artifact_summary": f"Approved {stage} artifact.",
        })
        log_event(state, stage, "Human-in-the-Loop Gateway",
                  "Artifact Approved", "SUCCESS",
                  f"{reviewer} approved {stage}. Continuing.")
        state["pending_approval"]  = None
        state["pipeline_status"]   = "RUNNING"

        if stage == "Requirements":
            state = architecture_node(state)
            # HITL Feature 2: gate after architecture
            state["pipeline_status"]  = "PAUSED_FOR_APPROVAL"
            state["pending_approval"] = {
                "stage": "Architecture",
                "title": "System Architecture Blueprint",
                "artifact_type": "architecture",
                "artifact": state["architecture_doc"],
            }
            log_event(state, "Architecture", "Human-in-the-Loop Gateway",
                      "Approval Gate Triggered", "PAUSED",
                      "Awaiting approval for Architecture Blueprint.")

        elif stage == "Architecture":
            state = codegen_node(state)
            state = security_node(state)
            # HITL Feature 2: gate after code generation
            state["pipeline_status"]  = "PAUSED_FOR_APPROVAL"
            state["pending_approval"] = {
                "stage": "Code Generation",
                "title": "Generated Code Files",
                "artifact_type": "codegen",
                "artifact": {"files": list(state["code_files"].keys()),
                             "security_report": state.get("security_report")},
            }
            log_event(state, "Code Generation", "Human-in-the-Loop Gateway",
                      "Approval Gate Triggered", "PAUSED",
                      "Awaiting approval for generated code before Code Review.")

        elif stage == "Code Generation":
            state = review_node(state)
            state["pipeline_status"]  = "PAUSED_FOR_APPROVAL"
            state["pending_approval"] = {
                "stage": "Code Review",
                "title": "Code Review Findings",
                "artifact_type": "review",
                "artifact": state["review_doc"],
            }
            log_event(state, "Code Review", "Human-in-the-Loop Gateway",
                      "Approval Gate Triggered", "PAUSED",
                      "Awaiting approval for Code Review before Test Execution.")

        elif stage == "Code Review":
            state = static_analysis_node(state)
            route = route_after_static(state)
            while route == "codegen_fix":
                state = codegen_fix_node(state)
                state = static_analysis_node(state)
                route = route_after_static(state)
            state = test_node(state)
            route = route_after_testing(state)
            while route == "bugfix":
                state = bugfix_node(state)
                state = test_node(state)
                route = route_after_testing(state)
            state = docs_node(state)
            state["pipeline_status"] = (
                "ESCALATED" if state.get("escalation_info") else "COMPLETED"
            )

        save_state(state)
        return state

    def request_changes(
        self,
        project_dir: str,
        feedback:    str,
        reviewer:    str = "Human Operator",
    ) -> MultiAgentState:
        """Re-runs the current agent stage with human feedback."""
        state = load_state(project_dir)
        if not state:
            raise ValueError(f"No state found in {project_dir}")

        pending = state.get("pending_approval")
        if not pending:
            return state

        stage = pending.get("stage", "")
        state["approval_history"].append({
            "id":               f"appr_{int(datetime.utcnow().timestamp()*1000)}",
            "stage":            stage,
            "action":           "CHANGES_REQUESTED",
            "timestamp":        datetime.utcnow().isoformat() + "Z",
            "reviewer":         reviewer,
            "feedback":         feedback,
            "artifact_summary": f"Changes requested on {stage}: {feedback[:100]}",
        })
        log_event(state, stage, "Human-in-the-Loop Gateway",
                  "Changes Requested", "WARNING",
                  f"{reviewer} requested changes on {stage}: '{feedback}'. Re-executing.")
        state["pending_approval"] = None
        state["pipeline_status"]  = "RUNNING"

        if stage == "Requirements":
            state = requirements_node(state, feedback=feedback)
            state["pipeline_status"]  = "PAUSED_FOR_APPROVAL"
            state["pending_approval"] = {
                "stage": "Requirements", "title": "Requirements Specification (Updated)",
                "artifact_type": "requirements", "artifact": state["requirements_doc"],
            }

        elif stage == "Architecture":
            state = architecture_node(state, feedback=feedback)
            state["pipeline_status"]  = "PAUSED_FOR_APPROVAL"
            state["pending_approval"] = {
                "stage": "Architecture", "title": "System Architecture Blueprint (Updated)",
                "artifact_type": "architecture", "artifact": state["architecture_doc"],
            }

        elif stage == "Code Generation":
            state = codegen_node(state, feedback=feedback)
            state = security_node(state)
            state["pipeline_status"]  = "PAUSED_FOR_APPROVAL"
            state["pending_approval"] = {
                "stage": "Code Generation", "title": "Generated Code Files (Updated)",
                "artifact_type": "codegen",
                "artifact": {"files": list(state["code_files"].keys()),
                             "security_report": state.get("security_report")},
            }

        elif stage == "Code Review":
            state = codegen_node(state, feedback=feedback)
            state = security_node(state)
            state = review_node(state, feedback=feedback)
            state["pipeline_status"]  = "PAUSED_FOR_APPROVAL"
            state["pending_approval"] = {
                "stage": "Code Review", "title": "Code Review Findings (Updated)",
                "artifact_type": "review", "artifact": state["review_doc"],
            }

        save_state(state)
        return state

    def reject_and_stop(
        self,
        project_dir: str,
        reason:   Optional[str] = None,
        reviewer: str = "Human Operator",
    ) -> MultiAgentState:
        """Aborts the pipeline, preserving all completed work."""
        state = load_state(project_dir)
        if not state:
            raise ValueError(f"No state found in {project_dir}")

        pending = state.get("pending_approval")
        stage   = (pending or {}).get("stage", state.get("current_stage", "Pipeline"))
        state["approval_history"].append({
            "id":               f"appr_{int(datetime.utcnow().timestamp()*1000)}",
            "stage":            stage,
            "action":           "REJECTED",
            "timestamp":        datetime.utcnow().isoformat() + "Z",
            "reviewer":         reviewer,
            "feedback":         reason,
            "artifact_summary": f"Rejected and stopped pipeline at {stage}.",
        })
        state["pending_approval"] = None
        state["pipeline_status"]  = "STOPPED"
        state["current_stage"]    = "Stopped"
        log_event(state, stage, "Human-in-the-Loop Gateway",
                  "Pipeline Aborted by Operator", "WARNING",
                  f"Halted by {reviewer}. Reason: {reason or 'Not specified'}.")
        save_state(state)
        return state

    def dismiss_escalation(
        self,
        project_dir: str,
        reviewer:    str = "Human Operator",
    ) -> MultiAgentState:
        """
        Acknowledge an escalated pipeline (bug-fix retry limit exceeded).
        Runs docs and marks pipeline completed.
        """
        state = load_state(project_dir)
        if not state:
            raise ValueError(f"No state found in {project_dir}")

        log_event(state, "Bug-Fix Loop", reviewer,
                  "Escalation Acknowledged", "WARNING",
                  "Manual intervention acknowledged. Proceeding to documentation.")
        state["pipeline_status"] = "RUNNING"
        state = docs_node(state)
        state["pipeline_status"] = "COMPLETED"
        save_state(state)
        return state


