"""
Multi-Agent Software Development Team — Extended Streamlit UI v2
All 10 new capabilities surfaced: clarification loop, live stream, trace dashboard,
coverage, security, static analysis, CI/CD, escalation, feature flags, HITL.
"""

import os, sys, json, time, re
from datetime import datetime
from typing import Optional, Dict, Any, List

import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from orchestrator import (
    MultiAgentOrchestrator, FeatureFlags,
    load_state, save_state, stream_drain,
)
from git_manager import GitManager
from sandbox     import SandboxExecutor

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Multi-Agent Software Engineering Team",
    page_icon="⚡", layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',-apple-system,sans-serif!important;-webkit-font-smoothing:antialiased}
.stApp{background:#080c14}
section[data-testid="stSidebar"]{background:#0d1117!important;border-right:1px solid #1e2937}
.stMain .block-container{padding-top:1.5rem!important;max-width:1440px}
header[data-testid="stHeader"]{background:transparent!important}
h1,h2,h3,h4{color:#f0f6fc!important;letter-spacing:-.02em}
p,li,label,.stMarkdown{color:#8b949e!important}
strong{color:#e6edf3!important}
code{font-family:'JetBrains Mono',monospace!important}
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:#0d1117}
::-webkit-scrollbar-thumb{background:#30363d;border-radius:4px}
.kpi-card{background:linear-gradient(145deg,#0d1117,#111827);border:1px solid #1e2937;border-radius:12px;padding:18px 20px;transition:border-color .2s,transform .15s}
.kpi-card:hover{border-color:#3d8bfd;transform:translateY(-1px)}
.kpi-value{font-size:1.9rem;font-weight:800;font-family:'JetBrains Mono',monospace;color:#f0f6fc;line-height:1;margin:4px 0}
.kpi-label{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#484f58;margin-top:6px}
.kpi-sub{font-size:.7rem;color:#6e7681;margin-top:2px}
.stage-card{background:#0d1117;border:1px solid #1e2937;border-radius:10px;padding:11px 8px;text-align:center;transition:all .2s;position:relative}
.stage-card.wait{opacity:.5}
.stage-card.run{border-color:#d29922;background:#1c1600;animation:pb 1.5s infinite}
.stage-card.done{border-color:#238636;background:#0a1f0a}
.stage-card.pause{border-color:#db6d28;background:#1a0d00;animation:pbo 1.5s infinite}
.stage-card.fail{border-color:#da3633;background:#1a0000}
.stage-card.skip{border-color:#30363d;background:#0d1117;opacity:.4}
.stage-num{font-size:.58rem;font-family:'JetBrains Mono',monospace;color:#484f58;position:absolute;top:5px;right:7px}
.stage-icon{font-size:1.2rem;margin-bottom:3px}
.stage-name{font-size:.7rem;font-weight:700;color:#e6edf3;margin:2px 0}
.stage-agent{font-size:.58rem;color:#6e7681}
.stage-badge{font-size:.56rem;font-weight:700;margin-top:3px;padding:1px 5px;border-radius:20px;display:inline-block}
.badge-done{background:#0d2f16;color:#3fb950;border:1px solid #238636}
.badge-run{background:#2d1b00;color:#e3b341;border:1px solid #d29922}
.badge-wait{background:#161b22;color:#484f58;border:1px solid #30363d}
.badge-pause{background:#2d1500;color:#f0883e;border:1px solid #db6d28}
.badge-fail{background:#2d0000;color:#f85149;border:1px solid #da3633}
.badge-skip{background:#161b22;color:#484f58;border:1px solid #30363d}
@keyframes pb{0%,100%{box-shadow:0 0 0 0 rgba(210,153,34,.3)}50%{box-shadow:0 0 0 4px rgba(210,153,34,.1)}}
@keyframes pbo{0%,100%{box-shadow:0 0 0 0 rgba(219,109,40,.3)}50%{box-shadow:0 0 0 4px rgba(219,109,40,.1)}}
.terminal{background:#010409;border:1px solid #1e2937;border-radius:10px;overflow:hidden;font-family:'JetBrains Mono',monospace;font-size:.73rem}
.terminal-bar{background:#161b22;border-bottom:1px solid #1e2937;padding:7px 12px;display:flex;align-items:center;gap:8px}
.tdot{width:9px;height:9px;border-radius:50%;display:inline-block}
.tbody{padding:12px 16px;color:#c9d1d9;line-height:1.6;white-space:pre-wrap;word-break:break-all;max-height:400px;overflow-y:auto}
.diff-add{color:#3fb950;background:rgba(63,185,80,.07);display:block;padding:0 4px}
.diff-del{color:#f85149;background:rgba(248,81,73,.07);display:block;padding:0 4px}
.diff-hunk{color:#79c0ff;font-weight:700;display:block;padding:0 4px}
.diff-meta{color:#484f58;display:block;padding:0 4px}
.diff-norm{color:#8b949e;display:block;padding:0 4px}
.chip{display:inline-flex;align-items:center;gap:4px;padding:2px 9px;border-radius:20px;font-size:.68rem;font-weight:600}
.chip-green{background:#0d2f16;color:#3fb950;border:1px solid #238636}
.chip-yellow{background:#2d1b00;color:#e3b341;border:1px solid #d29922}
.chip-orange{background:#2d1500;color:#f0883e;border:1px solid #db6d28}
.chip-red{background:#2d0000;color:#f85149;border:1px solid #da3633}
.chip-blue{background:#031d2e;color:#79c0ff;border:1px solid #1f6feb}
.chip-purple{background:#1a0a2e;color:#d2a8ff;border:1px solid #8957e5}
.chip-grey{background:#161b22;color:#6e7681;border:1px solid #30363d}
.gate-card{background:linear-gradient(135deg,#1a0d00,#110800);border:1.5px solid #db6d28;border-radius:14px;padding:20px 22px;margin:12px 0}
.audit-row{display:flex;justify-content:space-between;align-items:flex-start;padding:10px 14px;border:1px solid #1e2937;border-radius:8px;margin-bottom:5px;background:#0d1117;gap:10px;transition:border-color .15s}
.audit-row:hover{border-color:#30363d}
.fr-card{background:#0d1117;border:1px solid #1e2937;border-radius:10px;padding:13px 15px;margin-bottom:8px}
.module-card{background:#0d1117;border:1px solid #1e2937;border-radius:10px;padding:13px 15px;transition:border-color .2s}
.module-card:hover{border-color:#30363d}
.module-name{font-family:'JetBrains Mono',monospace;font-size:.78rem;font-weight:600;color:#79c0ff}
.module-desc{font-size:.72rem;color:#6e7681;margin-top:4px;line-height:1.5}
.issue-card{background:#0d1117;border:1px solid #1e2937;border-radius:10px;padding:13px 15px;margin-bottom:8px}
.sev-critical{border-left:3px solid #da3633}
.sev-high{border-left:3px solid #d29922}
.sev-medium{border-left:3px solid #1f6feb}
.sev-low{border-left:3px solid #238636}
.sev-info{border-left:3px solid #30363d}
.tag{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:.6rem;padding:1px 6px;border-radius:4px;margin:2px 2px 0 0}
.tag-api{background:#031d2e;color:#79c0ff;border:1px solid #1f6feb}
.tag-dep{background:#161b22;color:#6e7681;border:1px solid #30363d}
.sec-critical{border-left:3px solid #da3633}
.sec-high{border-left:3px solid #d29922}
.sec-medium{border-left:3px solid #1f6feb}
.sec-low{border-left:3px solid #238636}
.coverage-bar-bg{background:#1e2937;border-radius:4px;height:8px;overflow:hidden;margin-top:4px}
.stream-line{padding:3px 0;border-bottom:1px solid #0f1621;font-family:'JetBrains Mono',monospace;font-size:.72rem;color:#c9d1d9;line-height:1.5}
.stream-ts{color:#484f58;font-size:.62rem;margin-right:8px}
.stream-stage{padding:1px 6px;border-radius:4px;font-size:.62rem;font-weight:700;margin-right:6px;background:#031d2e;color:#79c0ff;border:1px solid #1f6feb}
.trace-row{background:#0d1117;border:1px solid #1e2937;border-radius:9px;padding:12px 16px;margin-bottom:6px;transition:border-color .15s}
.trace-row:hover{border-color:#30363d}
.sec-row{background:#0d1117;border:1px solid #1e2937;border-radius:10px;padding:12px 15px;margin-bottom:8px}
.cq-card{background:#0d1117;border:1px solid #1e2937;border-radius:10px;padding:14px 16px;margin-bottom:8px}
.cq-id{font-family:'JetBrains Mono',monospace;font-size:.68rem;color:#79c0ff;background:#031d2e;border:1px solid #1f6feb;border-radius:5px;padding:1px 7px;display:inline-block}
.esc-card{background:linear-gradient(135deg,#2d0000,#1a0000);border:2px solid #da3633;border-radius:14px;padding:20px 22px;margin:12px 0}
section[data-testid="stSidebar"] .stMarkdown p{color:#6e7681!important;font-size:.77rem}
section[data-testid="stSidebar"] h1,section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3{color:#e6edf3!important}
section[data-testid="stSidebar"] hr{border-color:#1e2937!important}
.stTextArea textarea,.stTextInput input{background:#0d1117!important;border:1px solid #30363d!important;color:#e6edf3!important;border-radius:8px!important}
.stTextArea textarea:focus,.stTextInput input:focus{border-color:#1f6feb!important;box-shadow:0 0 0 2px rgba(31,111,235,.15)!important}
.stButton button{border-radius:8px!important;font-weight:600!important;font-size:.79rem!important;transition:all .15s!important}
.stButton button[kind="primary"]{background:linear-gradient(135deg,#1f6feb,#7c3aed)!important;border:none!important;color:#fff!important}
.stButton button[kind="primary"]:hover{filter:brightness(1.12)!important;transform:translateY(-1px)!important}
.stButton button[kind="secondary"]{background:#161b22!important;border:1px solid #30363d!important;color:#c9d1d9!important}
.stButton button[kind="secondary"]:hover{border-color:#58a6ff!important;color:#58a6ff!important}
.stTabs [data-baseweb="tab-list"]{background:#0d1117!important;border-bottom:1px solid #1e2937!important;gap:0!important}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:#6e7681!important;font-size:.77rem!important;font-weight:600!important;border-bottom:2px solid transparent!important;padding:9px 14px!important}
.stTabs [aria-selected="true"]{color:#58a6ff!important;border-bottom-color:#1f6feb!important;background:transparent!important}
.stExpander{background:#0d1117!important;border:1px solid #1e2937!important;border-radius:10px!important}
div[data-testid="stMetric"]{background:#0d1117;border:1px solid #1e2937;border-radius:10px;padding:12px 16px}
div[data-testid="stMetricValue"]{color:#f0f6fc!important;font-family:'JetBrains Mono',monospace!important}
div[data-testid="stMetricLabel"]{color:#6e7681!important;font-size:.68rem!important;text-transform:uppercase;letter-spacing:.06em}
.stProgress>div>div{background:linear-gradient(90deg,#1f6feb,#3fb950)!important;border-radius:4px!important}
div[data-testid="stProgress"]>div{background:#1e2937!important;border-radius:4px!important}
.stDownloadButton button{background:#161b22!important;border:1px solid #238636!important;color:#3fb950!important}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# STATIC DATA
# ─────────────────────────────────────────────────────────────────────────────
PRESETS = [
    {"id":"cli-calculator","title":"Scientific & Financial CLI Calculator","badge":"CLI Tool",
     "prompt":"Build a production-grade Scientific and Financial CLI Calculator with memory registers, trigonometry, compound interest formulas, error handling for division-by-zero, and full unit test coverage."},
    {"id":"kv-store","title":"In-Memory Key-Value Store with TTL","badge":"Core Engine",
     "prompt":"Build a high-performance in-memory Key-Value store with TTL key expiration, periodic background cleanup, atomic transactions (MULTI/EXEC), disk snapshotting/persistence, and comprehensive unit tests."},
    {"id":"rest-todo","title":"RESTful Task API with Priority Matrix","badge":"Web Service",
     "prompt":"Build a clean RESTful Task & Project Management API with priority levels (URGENT, HIGH, MEDIUM, LOW), due date validators, tag filtering, pagination, and thorough pytest assertions."},
    {"id":"event-bus","title":"Publish-Subscribe Event Bus","badge":"System Pattern",
     "prompt":"Build an asynchronous publish-subscribe Event Bus engine supporting hierarchical wildcard subscriptions, synchronous/async handler dispatch, and dead-letter queues."},
]

STAGES = [
    ("clarification",   "Clarification",    "Requirements Analyst", "00"),
    ("requirements",    "Requirements",     "Requirements Analyst", "01"),
    ("architecture",    "Architecture",     "Architecture Agent",   "02"),
    ("codegen",         "Code Gen",         "Code Gen Agent",       "03"),
    ("security",        "Security",         "Security Agent",       "04"),
    ("review",          "Code Review",      "Review Agent",         "05"),
    ("static_analysis", "Static Analysis",  "Lint + mypy",          "06"),
    ("testing",         "Test Suite",       "Test Agent",           "07"),
    ("bugfix",          "Bug-Fix",          "Bug-Fix Agent",        "08"),
    ("documentation",   "Docs + CI/CD",     "Docs + DevOps Agent",  "09"),
]

STAGE_ICONS = {
    "clarification":"❓","requirements":"📋","architecture":"🏗️","codegen":"💻",
    "security":"🔒","review":"🔍","static_analysis":"📐","testing":"🧪",
    "bugfix":"🔧","documentation":"📚",
}

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE BOOTSTRAP
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULTS: Dict[str, Any] = {
    "pipeline":None,"is_running":False,"is_testing":False,"is_processing":False,
    "provider":"deterministic","error_message":None,"require_approval":False,
    "active_stage_idx":0,"show_advanced":False,
    "prompt":PRESETS[0]["prompt"],"selected_preset_id":PRESETS[0]["id"],
    "max_iterations":3,
    # feature flags
    "ff_clarification":True,"ff_hitl":True,"ff_security":True,
    "ff_static":True,"ff_bugfix_esc":True,"ff_regression":True,
    "ff_coverage":True,"ff_cicd":True,"ff_trace":True,"ff_stream":True,
    # UI state
    "show_github_modal":False,"selected_commit":None,"diff_content":{},
    "github_token":"","github_repo":"","github_create_new":True,
    "github_private":False,"github_result":None,"github_error":None,
    "reviewer_name":"Human Operator","show_feedback_form":False,"show_reject_form":False,
    "selected_code_file":None,
    # live stream buffer
    "stream_events":[],"stream_paused":False,
    # clarification answers
    "clarification_answers":{},
    # tab memory
    "active_main_tab":0,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE FLAGS HELPER
# ─────────────────────────────────────────────────────────────────────────────
def _build_flags() -> FeatureFlags:
    s = st.session_state
    return FeatureFlags(
        clarification_loop = s.ff_clarification,
        hitl_checkpoints   = s.ff_hitl,
        security_review    = s.ff_security,
        static_analysis    = s.ff_static,
        bugfix_escalation  = s.ff_bugfix_esc,
        regression_testing = s.ff_regression,
        coverage_reporting = s.ff_coverage,
        cicd_scaffolding   = s.ff_cicd,
        trace_dashboard    = s.ff_trace,
        live_stream        = s.ff_stream,
    )

# ─────────────────────────────────────────────────────────────────────────────
# BACKEND CALLS
# ─────────────────────────────────────────────────────────────────────────────
def run_pipeline(requirement: str, max_iterations: int, require_approval: bool) -> None:
    st.session_state.is_running = True
    st.session_state.error_message = None
    st.session_state.stream_events = []
    try:
        orch = MultiAgentOrchestrator(
            provider_type=st.session_state.provider,
            max_iterations=max_iterations,
            feature_flags=_build_flags(),
        )
        result = orch.run_pipeline(requirement=requirement, require_approval=require_approval)
        st.session_state.pipeline = result
    except Exception as e:
        st.session_state.error_message = str(e)
    finally:
        st.session_state.is_running = False

def run_sandbox() -> None:
    p = st.session_state.pipeline
    if not p:
        return
    st.session_state.is_testing = True
    try:
        r = SandboxExecutor(timeout_seconds=30).execute_test_suite(
            p.get("code_files",{}), p.get("test_files",{}))
        st.session_state.pipeline["test_result"] = {
            "success":r.success,"exit_code":r.exit_code,
            "stdout":r.stdout,"stderr":r.stderr,
            "tests_total":r.tests_total,"tests_passed":r.tests_passed,
            "tests_failed":r.tests_failed,"duration_seconds":r.duration_seconds,
        }
    except Exception as e:
        st.session_state.error_message = str(e)
    finally:
        st.session_state.is_testing = False

def do_approve() -> None:
    p = st.session_state.pipeline
    if not p or not p.get("project_dir"):
        return
    st.session_state.is_processing = True
    try:
        orch = MultiAgentOrchestrator(
            provider_type=st.session_state.provider,
            feature_flags=_build_flags(),
        )
        st.session_state.pipeline = orch.approve_and_continue(
            project_dir=p["project_dir"],
            reviewer=st.session_state.reviewer_name or "Human Operator",
        )
    except Exception as e:
        st.session_state.error_message = str(e)
    finally:
        st.session_state.is_processing = False

def do_request_changes(feedback: str) -> None:
    p = st.session_state.pipeline
    if not p or not p.get("project_dir"):
        return
    st.session_state.is_processing = True
    try:
        orch = MultiAgentOrchestrator(
            provider_type=st.session_state.provider,
            feature_flags=_build_flags(),
        )
        st.session_state.pipeline = orch.request_changes(
            project_dir=p["project_dir"], feedback=feedback,
            reviewer=st.session_state.reviewer_name or "Human Operator",
        )
    except Exception as e:
        st.session_state.error_message = str(e)
    finally:
        st.session_state.is_processing = False
        st.session_state.show_feedback_form = False

def do_reject(reason: str) -> None:
    p = st.session_state.pipeline
    if not p or not p.get("project_dir"):
        return
    st.session_state.is_processing = True
    try:
        orch = MultiAgentOrchestrator(provider_type=st.session_state.provider)
        st.session_state.pipeline = orch.reject_and_stop(
            project_dir=p["project_dir"], reason=reason,
            reviewer=st.session_state.reviewer_name or "Human Operator",
        )
    except Exception as e:
        st.session_state.error_message = str(e)
    finally:
        st.session_state.is_processing = False
        st.session_state.show_reject_form = False

def do_submit_clarifications(answers: Dict[str, str]) -> None:
    p = st.session_state.pipeline
    if not p or not p.get("project_dir"):
        return
    st.session_state.is_processing = True
    try:
        orch = MultiAgentOrchestrator(
            provider_type=st.session_state.provider,
            feature_flags=_build_flags(),
        )
        st.session_state.pipeline = orch.submit_clarification_answers(
            project_dir=p["project_dir"], answers=answers,
        )
    except Exception as e:
        st.session_state.error_message = str(e)
    finally:
        st.session_state.is_processing = False

def do_dismiss_escalation() -> None:
    p = st.session_state.pipeline
    if not p or not p.get("project_dir"):
        return
    st.session_state.is_processing = True
    try:
        orch = MultiAgentOrchestrator(provider_type=st.session_state.provider)
        st.session_state.pipeline = orch.dismiss_escalation(
            project_dir=p["project_dir"],
            reviewer=st.session_state.reviewer_name or "Human Operator",
        )
    except Exception as e:
        st.session_state.error_message = str(e)
    finally:
        st.session_state.is_processing = False

def export_zip_bytes() -> Optional[bytes]:
    p = st.session_state.pipeline
    if not p or not p.get("project_dir"):
        return None
    try:
        z = GitManager(p["project_dir"]).export_zip()
        data = open(z,"rb").read()
        os.unlink(z)
        return data
    except Exception:
        return None

def load_diff(project_dir: str, commit_hash: str) -> str:
    try:
        return GitManager(project_dir).get_diff(commit_hash)
    except Exception as e:
        return f"Error: {e}"

# ─────────────────────────────────────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def chip(label: str, variant: str = "grey") -> str:
    return f'<span class="chip chip-{variant}">{label}</span>'

def kpi(value: str, label: str, color: str = "#f0f6fc", sub: str = "") -> str:
    s = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value" style="color:{color}">{value}</div>{s}</div>')

def section_hdr(title: str, badge: str = "") -> None:
    b = f'<span style="font-size:.65rem;background:#161b22;color:#6e7681;border:1px solid #30363d;border-radius:20px;padding:1px 8px;margin-left:8px">{badge}</span>' if badge else ""
    st.markdown(
        f'<div style="display:flex;align-items:center;padding:10px 0;border-bottom:1px solid #1e2937;margin-bottom:14px">'
        f'<span style="font-size:.82rem;font-weight:700;color:#e6edf3;text-transform:uppercase;letter-spacing:.06em">{title}</span>{b}</div>',
        unsafe_allow_html=True)

def empty_state(icon: str, title: str, sub: str) -> None:
    st.markdown(
        f'<div style="text-align:center;padding:50px 20px;border:1px dashed #1e2937;border-radius:14px;background:#0d1117">'
        f'<div style="font-size:2.2rem;margin-bottom:10px">{icon}</div>'
        f'<div style="font-size:.9rem;font-weight:700;color:#e6edf3;margin-bottom:5px">{title}</div>'
        f'<div style="font-size:.75rem;color:#6e7681">{sub}</div></div>',
        unsafe_allow_html=True)

def render_reasoning(agent: str, stage: str, reasoning: Optional[str]) -> None:
    if not reasoning or not str(reasoning).strip():
        return
    with st.expander(f"🧠  {agent}  ·  Reasoning Trace", expanded=False):
        st.markdown(
            f'<div style="background:#010409;border:1px solid #1e2937;border-left:3px solid #7c3aed;'
            f'border-radius:0 10px 10px 0;padding:14px 18px;font-family:\'JetBrains Mono\',monospace;'
            f'font-size:.72rem;color:#c9d1d9;white-space:pre-wrap;line-height:1.65;max-height:280px;overflow-y:auto">'
            f'<span style="color:#818cf8;font-weight:700"># {stage} · {agent}</span>\n'
            f'{"─"*60}\n{reasoning}</div>',
            unsafe_allow_html=True)

def _sev_chip(sev: str) -> str:
    vm = {"CRITICAL":"red","HIGH":"yellow","MEDIUM":"blue","LOW":"green","INFO":"grey",
          "error":"red","warning":"yellow","note":"grey"}
    return chip(sev, vm.get(sev.lower() if sev else "info","grey"))

def _diff_html(diff_text: str) -> str:
    lines = diff_text.splitlines()
    out = []
    for ln in lines:
        e = ln.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        if ln.startswith("+") and not ln.startswith("+++"): out.append(f'<span class="diff-add">{e}</span>')
        elif ln.startswith("-") and not ln.startswith("---"): out.append(f'<span class="diff-del">{e}</span>')
        elif ln.startswith("@@"): out.append(f'<span class="diff-hunk">{e}</span>')
        elif ln.startswith(("diff ","index ")): out.append(f'<span class="diff-meta">{e}</span>')
        else: out.append(f'<span class="diff-norm">{e}</span>')
    return "".join(out)

def _terminal(title: str, body: str, height: int = 380) -> None:
    st.markdown(
        f'<div class="terminal">'
        f'<div class="terminal-bar">'
        f'<span class="tdot" style="background:#ff5f57"></span>'
        f'<span class="tdot" style="background:#febc2e"></span>'
        f'<span class="tdot" style="background:#28c840"></span>'
        f'<span style="font-size:.68rem;color:#484f58;margin-left:8px">{title}</span></div>'
        f'<div class="tbody" style="max-height:{height}px">{body}</div></div>',
        unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("""
        <div style="padding:14px 0 18px">
          <div style="display:flex;align-items:center;gap:10px">
            <div style="width:34px;height:34px;border-radius:9px;background:linear-gradient(135deg,#1f6feb,#7c3aed);display:flex;align-items:center;justify-content:center;font-size:17px">⚡</div>
            <div>
              <div style="font-size:.85rem;font-weight:800;color:#f0f6fc;line-height:1.2">Multi-Agent Team</div>
              <div style="font-size:.65rem;color:#484f58">10-Stage SDLC · Git Versioned</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
        st.divider()

        # Pipeline status
        p = st.session_state.pipeline
        if p:
            status = p.get("pipeline_status","IDLE")
            sv = {"COMPLETED":"green","RUNNING":"yellow","PAUSED_FOR_APPROVAL":"orange",
                  "PAUSED_FOR_CLARIFICATION":"purple","STOPPED":"red","ESCALATED":"red"}.get(status,"grey")
            stage = p.get("current_stage","—")
            st.markdown(f"""
            <div style="background:#0d1117;border:1px solid #1e2937;border-radius:10px;padding:12px 14px;margin-bottom:12px">
              <div style="font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#484f58;margin-bottom:5px">Status</div>
              <div style="display:flex;align-items:center;justify-content:space-between">
                {chip(status,sv)}<span style="font-size:.65rem;color:#6e7681">{stage}</span>
              </div>
            </div>""", unsafe_allow_html=True)
            tr = p.get("test_result") or {}
            tp,tt = tr.get("tests_passed",0), tr.get("tests_total",0)
            cov_total = (p.get("coverage_report") or {}).get("total_coverage","—")
            stats = [
                ("🧪","Tests",f"{tp}/{tt}"),
                ("📊","Coverage",f"{cov_total}%" if cov_total != "—" else "—"),
                ("🔀","Commits",str(len(p.get("git_commits",[])))),
                ("📁","Files",str(len(p.get("code_files",{})))),
                ("🔒","Sec Findings",str(len((p.get("security_report") or {}).get("findings",[])))),
                ("📐","Lint Errors",str((p.get("static_analysis") or {}).get("error_count",0))),
                ("🔧","Bug-Fix Iter",str(p.get("bugfix_iteration",0))),
                ("💰","Est. Cost",f"${p.get('total_cost_usd',0.0):.4f}"),
            ]
            for icon,lbl,val in stats:
                st.markdown(f'<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #0f1621"><span style="font-size:.71rem;color:#6e7681">{icon} {lbl}</span><span style="font-size:.71rem;font-weight:700;color:#e6edf3;font-family:\'JetBrains Mono\',monospace">{val}</span></div>',unsafe_allow_html=True)
            st.markdown("")
            st.divider()

        # Provider
        st.markdown('<div style="font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#484f58;margin-bottom:7px">LLM Provider</div>',unsafe_allow_html=True)
        prov = st.radio("p",["deterministic","gemini"],
                        index=0 if st.session_state.provider=="deterministic" else 1,
                        label_visibility="collapsed", key="sb_prov",
                        captions=["No API key","Google Gemini"])
        st.session_state.provider = prov
        st.divider()

        # Feature flags
        st.markdown('<div style="font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#484f58;margin-bottom:8px">Feature Flags</div>',unsafe_allow_html=True)
        flags_cfg = [
            ("ff_clarification","❓ Clarification Loop"),
            ("ff_hitl","🛡️ HITL Checkpoints"),
            ("ff_security","🔒 Security Review"),
            ("ff_static","📐 Static Analysis"),
            ("ff_bugfix_esc","⚠️ Bug-Fix Escalation"),
            ("ff_regression","🔁 Regression Testing"),
            ("ff_coverage","📊 Coverage Reports"),
            ("ff_cicd","🚀 CI/CD Scaffolding"),
            ("ff_trace","📈 Trace Dashboard"),
            ("ff_stream","📡 Live Stream"),
        ]
        for key, label in flags_cfg:
            st.session_state[key] = st.toggle(label, value=st.session_state[key], key=f"tog_{key}")
        st.divider()

        # Stage directory
        st.markdown('<div style="font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#484f58;margin-bottom:8px">Pipeline Stages</div>',unsafe_allow_html=True)
        for sid,sname,atitle,num in STAGES:
            ico = STAGE_ICONS.get(sid,"•")
            st.markdown(f'<div style="display:flex;align-items:center;gap:7px;padding:4px 0;border-bottom:1px solid #0f1621"><span style="font-size:.85rem">{ico}</span><div><div style="font-size:.71rem;font-weight:600;color:#c9d1d9">{sname}</div><div style="font-size:.59rem;color:#484f58">{atitle}</div></div><span style="margin-left:auto;font-family:\'JetBrains Mono\',monospace;font-size:.58rem;color:#30363d">{num}</span></div>',unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
def render_header() -> None:
    p = st.session_state.pipeline
    c1,c2,c3 = st.columns([5,3,4])
    with c1:
        st.markdown("""
        <div style="padding:4px 0">
          <h1 style="font-size:1.2rem;font-weight:800;color:#f0f6fc;margin:0;letter-spacing:-.03em">Multi-Agent Software Engineering Team</h1>
          <p style="font-size:.73rem;color:#484f58;margin:3px 0 0">10-Stage Autonomous SDLC · Security + Static Analysis · CI/CD Scaffolding · Git Versioned</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        if p:
            tr  = p.get("test_result") or {}
            tp,tt = tr.get("tests_passed",0),tr.get("tests_total",0)
            rate  = round(tp/tt*100) if tt else 0
            cost  = p.get("total_cost_usd",0.0)
            tokens= p.get("total_tokens",0)
            color = "#3fb950" if rate==100 else ("#e3b341" if rate>=50 else "#f85149")
            st.markdown(f"""
            <div style="display:flex;gap:14px;align-items:center;padding:8px 0">
              <div style="text-align:center"><div style="font-size:1.05rem;font-weight:800;font-family:'JetBrains Mono',monospace;color:{color}">{rate}%</div><div style="font-size:.6rem;color:#484f58;text-transform:uppercase">Test Pass</div></div>
              <div style="width:1px;height:28px;background:#1e2937"></div>
              <div style="text-align:center"><div style="font-size:1.05rem;font-weight:800;font-family:'JetBrains Mono',monospace;color:#79c0ff">{tokens:,}</div><div style="font-size:.6rem;color:#484f58;text-transform:uppercase">Tokens</div></div>
              <div style="width:1px;height:28px;background:#1e2937"></div>
              <div style="text-align:center"><div style="font-size:1.05rem;font-weight:800;font-family:'JetBrains Mono',monospace;color:#d2a8ff">${cost:.4f}</div><div style="font-size:.6rem;color:#484f58;text-transform:uppercase">Est. Cost</div></div>
            </div>""", unsafe_allow_html=True)
    with c3:
        a1,a2,a3 = st.columns(3)
        with a1:
            if p and not st.session_state.is_testing:
                if st.button("🔁 Verify",use_container_width=True,key="hdr_verify"):
                    run_sandbox(); st.rerun()
            else:
                st.button("🔁 Verify",disabled=True,use_container_width=True,key="hdr_verify_d")
        with a2:
            if st.button("🐙 GitHub",use_container_width=True,key="hdr_github",disabled=not p):
                st.session_state.show_github_modal=True; st.rerun()
        with a3:
            if p and p.get("project_dir"):
                zb = export_zip_bytes()
                if zb:
                    st.download_button("📦 Export",data=zb,
                        file_name="multiagent_project.zip",mime="application/zip",
                        use_container_width=True,key="hdr_zip")
            else:
                st.button("📦 Export",disabled=True,use_container_width=True,key="hdr_exp_d")
    st.markdown('<hr style="border:none;border-top:1px solid #1e2937;margin:10px 0 14px">',unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# MISSION CONTROL
# ─────────────────────────────────────────────────────────────────────────────
def render_mission_control() -> None:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0d1117,#111827);border:1px solid #1e2937;border-radius:14px;padding:20px 22px;margin-bottom:18px">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
        <span style="font-size:1rem">⚡</span>
        <span style="font-size:.86rem;font-weight:700;color:#e6edf3">Mission Control</span>
        <span style="margin-left:auto;font-size:.65rem;background:#031d2e;color:#79c0ff;border:1px solid #1f6feb;border-radius:20px;padding:2px 9px">Software Requirement Interface</span>
      </div>""", unsafe_allow_html=True)

    # Preset chips
    cols = st.columns(4)
    for i, preset in enumerate(PRESETS):
        with cols[i]:
            sel = st.session_state.selected_preset_id == preset["id"]
            bc  = "#1f6feb" if sel else "#1e2937"
            bg  = "#0d1f35" if sel else "#0d1117"
            tc  = "#79c0ff" if sel else "#8b949e"
            st.markdown(f'<div style="background:{bg};border:1.5px solid {bc};border-radius:9px;padding:10px 12px;margin-bottom:6px"><div style="font-size:.6rem;font-weight:700;text-transform:uppercase;color:#1f6feb;margin-bottom:3px">[{preset["badge"]}]</div><div style="font-size:.73rem;font-weight:600;color:{tc}">{preset["title"]}</div></div>',unsafe_allow_html=True)
            if st.button("✓ Selected" if sel else "Select",use_container_width=True,
                         key=f"ps_{preset['id']}",type="primary" if sel else "secondary",
                         disabled=st.session_state.is_running):
                st.session_state.prompt = preset["prompt"]
                st.session_state.selected_preset_id = preset["id"]
                st.rerun()

    st.markdown('<div style="height:4px"></div>',unsafe_allow_html=True)
    prompt_val = st.text_area("Requirement",value=st.session_state.prompt,height=100,
        placeholder="Describe any software system — the 10-stage agent team will architect, secure, code, review, test and deploy it…",
        disabled=st.session_state.is_running,key="prompt_inp")
    if prompt_val != st.session_state.prompt:
        st.session_state.prompt = prompt_val
        m = next((p for p in PRESETS if p["prompt"].strip()==prompt_val.strip()),None)
        st.session_state.selected_preset_id = m["id"] if m else None

    cl, cr = st.columns([5,3])
    with cl:
        show_adv = st.toggle("⚙️  Pipeline Settings",value=st.session_state.show_advanced,key="adv_tog")
        st.session_state.show_advanced = show_adv
        if show_adv:
            sa1,sa2 = st.columns(2)
            with sa1:
                mi = st.slider("Max Bug-Fix Iterations",1,5,st.session_state.max_iterations,key="mi_sl")
                st.session_state.max_iterations = mi
            with sa2:
                ra = st.toggle("🛡️  Human Approval Gates",value=st.session_state.require_approval,key="ra_tog")
                st.session_state.require_approval = ra
                if ra: st.caption("Pauses at Requirements → Architecture → Code Gen → Code Review")
    with cr:
        st.markdown('<div style="height:4px"></div>',unsafe_allow_html=True)
        lbl = "⏳ Orchestrating…" if st.session_state.is_running else "⚡  Launch 10-Stage Pipeline"
        if st.button(lbl,type="primary",use_container_width=True,
                     disabled=st.session_state.is_running or not st.session_state.prompt.strip(),
                     key="launch_btn"):
            run_pipeline(st.session_state.prompt.strip(),
                         st.session_state.max_iterations,
                         st.session_state.require_approval)
            st.rerun()
    st.markdown("</div>",unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# STAGE STEPPER
# ─────────────────────────────────────────────────────────────────────────────
def render_stage_pipeline() -> None:
    p          = st.session_state.pipeline
    is_running = st.session_state.is_running
    idx        = st.session_state.active_stage_idx
    pending    = (p or {}).get("pending_approval") or {}
    psn        = pending.get("stage","") if pending else ""
    ps_map     = {"PAUSED_FOR_CLARIFICATION":"Clarification","PAUSED_FOR_APPROVAL": psn}
    paused_stage = ps_map.get((p or {}).get("pipeline_status",""),"")
    is_done    = (p or {}).get("current_stage")=="Completed"
    is_stopped = (p or {}).get("pipeline_status")=="STOPPED"
    is_esc     = (p or {}).get("pipeline_status")=="ESCALATED"
    ah         = (p or {}).get("approval_history",[])

    status_str = (p or {}).get("pipeline_status","IDLE")
    sv = {"COMPLETED":"green","RUNNING":"yellow","PAUSED_FOR_APPROVAL":"orange",
          "PAUSED_FOR_CLARIFICATION":"purple","STOPPED":"red","ESCALATED":"red","IDLE":"grey"}.get(status_str,"grey")
    st.markdown(f'<div style="margin-bottom:12px">{chip(status_str,sv)}</div>',unsafe_allow_html=True)

    cols = st.columns(len(STAGES))
    for i,(sid,sname,atitle,num) in enumerate(STAGES):
        if   is_stopped and paused_stage.lower()==sname.lower(): st_s="fail"
        elif paused_stage and paused_stage.lower()==sname.lower(): st_s="pause"
        elif not p and not is_running: st_s="wait"
        elif is_running:
            st_s = "done" if i<idx else ("run" if i==idx else "wait")
        elif is_done: st_s="done"
        else: st_s="done"

        # Mark security/static/cicd as skipped if flag off
        ff = _build_flags()
        skip_map = {
            "security":not ff.security_review,
            "static_analysis":not ff.static_analysis,
            "clarification":not ff.clarification_loop,
        }
        if skip_map.get(sid,False): st_s="skip"

        badge_txt = {"done":"Done","run":"Running","wait":"Standby","pause":"Awaiting",
                     "fail":"Failed","skip":"Skipped"}.get(st_s,"—")
        ico = STAGE_ICONS.get(sid,"•")
        approved = any(h.get("stage","").lower()==sname.lower() and h.get("action")=="APPROVED" for h in ah)
        with cols[i]:
            st.markdown(f"""
            <div class="stage-card {st_s}">
              <span class="stage-num">{num}</span>
              <div class="stage-icon">{ico}</div>
              <div class="stage-name">{sname}</div>
              <div class="stage-agent">{atitle}</div>
              <span class="stage-badge badge-{st_s}">{badge_txt}</span>
              {"<div style='font-size:.56rem;color:#79c0ff;margin-top:3px'>✓ Approved</div>" if approved else ""}
            </div>""",unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# LIVE STREAM PANEL  (Feature 10)
# ─────────────────────────────────────────────────────────────────────────────
def render_live_stream() -> None:
    if not st.session_state.ff_stream:
        return

    # Drain new events from orchestrator queue
    new_events = stream_drain()
    if new_events:
        st.session_state.stream_events = (st.session_state.stream_events + new_events)[-200:]

    events = st.session_state.stream_events
    if not events and not st.session_state.is_running:
        return

    with st.expander("📡  Live Agent Reasoning Stream", expanded=st.session_state.is_running):
        c1,c2 = st.columns([8,2])
        with c1:
            st.markdown(f'{chip("LIVE","green") if st.session_state.is_running else chip("IDLE","grey")}  '
                        f'<span style="font-size:.7rem;color:#484f58">{len(events)} events captured</span>',
                        unsafe_allow_html=True)
        with c2:
            if st.button("🗑  Clear",key="stream_clr",use_container_width=True):
                st.session_state.stream_events=[]; st.rerun()

        if events:
            lines = []
            for ev in reversed(events[-60:]):
                ts = ev.get("ts","")
                try: ts = datetime.fromisoformat(ts.replace("Z","")).strftime("%H:%M:%S")
                except: pass
                text = ev.get("text","").replace("<","&lt;").replace(">","&gt;")
                stage = ev.get("stage","")
                lines.append(
                    f'<div class="stream-line">'
                    f'<span class="stream-ts">{ts}</span>'
                    f'<span class="stream-stage">{stage}</span>'
                    f'{text}</div>'
                )
            st.markdown(
                f'<div style="background:#010409;border:1px solid #1e2937;border-radius:10px;'
                f'padding:12px 14px;max-height:300px;overflow-y:auto">{"".join(lines)}</div>',
                unsafe_allow_html=True)
        else:
            st.caption("Stream events will appear here as agents execute…")

        if st.session_state.is_running:
            time.sleep(0.4)
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# CLARIFICATION LOOP PANEL  (Feature 1)
# ─────────────────────────────────────────────────────────────────────────────
def render_clarification_panel() -> None:
    p = st.session_state.pipeline
    if not p:
        return
    if p.get("pipeline_status") != "PAUSED_FOR_CLARIFICATION":
        return

    qs = p.get("clarification_questions",[])
    if not qs:
        return

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1a0a2e,#110820);border:1.5px solid #8957e5;border-radius:14px;padding:20px 22px;margin:12px 0">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
        <div style="width:34px;height:34px;border-radius:9px;background:#8957e5;display:flex;align-items:center;justify-content:center;font-size:1rem">❓</div>
        <div>
          <div style="font-size:.92rem;font-weight:700;color:#f0f6fc">Requirements Clarification Loop</div>
          <div style="font-size:.74rem;color:#d2a8ff;margin-top:2px">The Requirements Analyst Agent detected {len(qs)} ambiguity/gap(s). Please answer before the pipeline proceeds.</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    answers: Dict[str,str] = {}
    cat_colors = {"scope":"blue","constraint":"yellow","data_model":"purple","edge_case":"orange"}

    with st.form("clarification_form"):
        for q in qs:
            qid = q.get("id","")
            cat = q.get("category","scope")
            cv  = cat_colors.get(cat,"grey")
            st.markdown(
                f'<div class="cq-card">'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">'
                f'<span class="cq-id">{qid}</span>{chip(cat,cv)}</div>'
                f'<div style="font-size:.82rem;font-weight:600;color:#e6edf3">{q.get("question","")}</div>'
                f'</div>', unsafe_allow_html=True)
            answers[qid] = st.text_input(
                f"Answer for {qid}",
                placeholder="Your answer (or type 'N/A' to skip this question)…",
                key=f"cq_{qid}", label_visibility="collapsed")

        c1,c2 = st.columns(2)
        with c1:
            submitted = st.form_submit_button("✅  Submit Answers & Continue",type="primary",use_container_width=True)
        with c2:
            skip_all  = st.form_submit_button("⏭  Skip All (Use Defaults)",use_container_width=True)

        if submitted or skip_all:
            final_answers = {qid: (ans if ans.strip() else "N/A") for qid,ans in answers.items()}
            do_submit_clarifications(final_answers)
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# ESCALATION PANEL  (Feature 5)
# ─────────────────────────────────────────────────────────────────────────────
def render_escalation_panel() -> None:
    p = st.session_state.pipeline
    if not p:
        return
    esc = p.get("escalation_info")
    if not esc:
        return
    if p.get("pipeline_status") not in ("ESCALATED","COMPLETED"):
        return

    st.markdown(f"""
    <div class="esc-card">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
        <div style="width:34px;height:34px;border-radius:9px;background:#da3633;display:flex;align-items:center;justify-content:center;font-size:1rem">⚠️</div>
        <div>
          <div style="font-size:.92rem;font-weight:700;color:#f0f6fc">Bug-Fix Escalation — Manual Intervention Required</div>
          <div style="font-size:.74rem;color:#f85149;margin-top:2px">{esc.get("reason","Retry limit exceeded.")}</div>
        </div>
      </div>
      <div style="background:#1a0000;border:1px solid #da3633;border-radius:9px;padding:12px 14px;margin-bottom:12px;font-family:'JetBrains Mono',monospace;font-size:.72rem;color:#c9d1d9;white-space:pre-wrap">{esc.get("diagnostic","")}</div>
    </div>""", unsafe_allow_html=True)

    c1,c2 = st.columns(2)
    with c1:
        if st.button("✅  Acknowledge & Generate Docs",type="primary",use_container_width=True,
                     disabled=st.session_state.is_processing,key="esc_ack"):
            do_dismiss_escalation(); st.rerun()
    with c2:
        st.info("Review the failing tests in the Pytest Sandbox tab and apply a manual fix.")

# ─────────────────────────────────────────────────────────────────────────────
# APPROVAL GATE PANEL  (Feature 2)
# ─────────────────────────────────────────────────────────────────────────────
def render_approval_gate() -> None:
    p = st.session_state.pipeline
    if not p:
        return
    ps  = p.get("pipeline_status","")
    is_paused  = ps == "PAUSED_FOR_APPROVAL"
    is_stopped = ps == "STOPPED"
    ah         = p.get("approval_history",[])
    if not is_paused and not is_stopped and not ah:
        return

    if is_paused and p.get("pending_approval"):
        pend  = p["pending_approval"]
        stage = pend.get("stage","")
        art_type = pend.get("artifact_type","")

        st.markdown(f"""
        <div class="gate-card">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
            <div style="width:34px;height:34px;border-radius:9px;background:#db6d28;display:flex;align-items:center;justify-content:center;font-size:1rem">🛡️</div>
            <div>
              <div style="font-size:.92rem;font-weight:700;color:#f0f6fc">HITL Approval Gate  ·  {pend.get('title','')}</div>
              <div style="font-size:.74rem;color:#f0883e;margin-top:2px">Stage: {stage}  ·  Inspect the artifact then choose an action</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        with st.expander("📄  Generated Artifact Preview", expanded=True):
            if art_type == "requirements" and p.get("requirements_doc"):
                doc = p["requirements_doc"]
                st.markdown(f"**{doc.get('title','')}**")
                st.caption(doc.get("problem_statement",""))
                for fr in (doc.get("functional_requirements") or [])[:8]:
                    st.markdown(f"- `{fr.get('id','')}` {fr.get('description','')}")
            elif art_type == "architecture" and p.get("architecture_doc"):
                doc = p["architecture_doc"]
                st.markdown(doc.get("system_overview","")[:600])
                if doc.get("folder_structure"): st.code(doc["folder_structure"])
            elif art_type == "codegen":
                art = pend.get("artifact",{})
                files = art.get("files",[])
                st.markdown(f"**Generated files:** {', '.join(f'`{f}`' for f in files)}")
                sec = art.get("security_report")
                if sec:
                    risk = sec.get("risk_level","CLEAR")
                    rv = {"CRITICAL":"red","HIGH":"yellow","MEDIUM":"blue","LOW":"green","CLEAR":"green"}.get(risk,"grey")
                    st.markdown(f"Security scan: {chip(risk,rv)}  {len(sec.get('findings',[]))} finding(s)",
                                unsafe_allow_html=True)
            elif art_type == "review" and p.get("review_doc"):
                doc = p["review_doc"]
                m1,m2 = st.columns(2)
                m1.metric("Review Score",f"{doc.get('overall_score',0)}/10")
                m2.metric("Verdict","✅ PASSED" if doc.get("passed") else "❌ NEEDS WORK")
                st.caption(doc.get("summary",""))

        rev = st.text_input("Reviewer / Operator",value=st.session_state.reviewer_name,key="rev_inp")
        st.session_state.reviewer_name = rev

        b1,b2,b3 = st.columns(3)
        with b1:
            if st.button("✅  Approve & Continue",type="primary",use_container_width=True,
                         disabled=st.session_state.is_processing,key="approve_btn"):
                do_approve(); st.rerun()
        with b2:
            if st.button("🔄  Request Changes",use_container_width=True,
                         disabled=st.session_state.is_processing,key="rc_btn"):
                st.session_state.show_feedback_form = not st.session_state.show_feedback_form
                st.session_state.show_reject_form   = False
        with b3:
            if st.button("❌  Reject & Stop",use_container_width=True,
                         disabled=st.session_state.is_processing,key="rej_btn"):
                st.session_state.show_reject_form   = not st.session_state.show_reject_form
                st.session_state.show_feedback_form = False

        if st.session_state.show_feedback_form:
            with st.form("fb_form"):
                st.markdown(f"**💬  Feedback for {stage} Agent**")
                fb = st.text_area("What to change",height=85,placeholder=f"Tell the {stage} Agent what to adjust…",key="fb_area")
                if st.form_submit_button("🚀  Re-run Stage with Feedback",type="primary") and fb.strip():
                    do_request_changes(fb.strip()); st.rerun()

        if st.session_state.show_reject_form:
            with st.form("rej_form"):
                st.markdown("**⛔  Confirm Pipeline Abort**")
                reason = st.text_input("Reason (optional)",placeholder="e.g. Requirement cancelled…",key="rej_reason")
                if st.form_submit_button("🛑  Halt Pipeline",type="primary"):
                    do_reject(reason.strip()); st.rerun()

    if is_stopped:
        st.markdown('<div style="background:#2d0000;border:1px solid #da3633;border-radius:10px;padding:13px 16px;margin:10px 0"><span style="font-size:.8rem;font-weight:700;color:#f85149">🛑  Pipeline Stopped</span><div style="font-size:.73rem;color:#8b949e;margin-top:3px">All generated files and Git commits are preserved.</div></div>',unsafe_allow_html=True)

    if ah:
        with st.expander(f"📋  Approval History  ({len(ah)} events)", expanded=False):
            for item in ah:
                action = item.get("action","")
                cv = {"APPROVED":"green","CHANGES_REQUESTED":"yellow","REJECTED":"red"}.get(action,"grey")
                ts = item.get("timestamp","")
                try: ts = datetime.fromisoformat(ts.replace("Z","")).strftime("%H:%M:%S")
                except: pass
                fb_txt = f'<div style="font-size:.7rem;color:#6e7681;font-style:italic;margin-top:2px">"{item.get("feedback","")}"</div>' if item.get("feedback") else ""
                st.markdown(f'<div class="audit-row"><div>{chip(action.replace("_"," "),cv)}<span style="font-size:.71rem;color:#6e7681;margin-left:8px">{item.get("stage","")} · {item.get("reviewer","")}</span>{fb_txt}</div><span style="font-size:.65rem;font-family:\'JetBrains Mono\',monospace;color:#484f58;white-space:nowrap">{ts}</span></div>',unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: SOURCE CODE
# ─────────────────────────────────────────────────────────────────────────────
def render_code_tab() -> None:
    p  = st.session_state.pipeline
    cf = (p or {}).get("code_files",{})
    tf = (p or {}).get("test_files",{})
    render_reasoning("Code Generation Agent","Code Generation",(p or {}).get("codegen_reasoning",""))
    all_files = {**{k:{"c":v,"t":"code"} for k,v in cf.items()},
                 **{k:{"c":v,"t":"test"} for k,v in tf.items()}}
    if not all_files:
        empty_state("💻","No source files yet","Run the pipeline to generate code"); return

    fnames = list(all_files.keys())
    col_tree, col_editor = st.columns([2,9])
    with col_tree:
        st.markdown('<div style="background:#0d1117;border:1px solid #1e2937;border-radius:10px;padding:11px 12px"><div style="font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#484f58;margin-bottom:9px">Explorer</div>',unsafe_allow_html=True)
        for fn in fnames:
            is_t = all_files[fn]["t"]=="test"
            is_s = st.session_state.selected_code_file == fn
            ico  = "🧪" if is_t else "🐍"
            st.markdown(f'<div style="background:{"#1c2333" if is_s else "transparent"};border:{"1px solid #1f6feb" if is_s else "1px solid transparent"};border-radius:6px;padding:5px 8px;margin-bottom:2px;cursor:pointer"><span style="font-family:\'JetBrains Mono\',monospace;font-size:.7rem;color:{"#79c0ff" if is_s else "#8b949e"}">{ico} {fn}</span></div>',unsafe_allow_html=True)
            if st.button(fn,key=f"fb_{fn}",use_container_width=True,type="primary" if is_s else "secondary"):
                st.session_state.selected_code_file=fn; st.rerun()
        st.markdown("</div>",unsafe_allow_html=True)

    sel = st.session_state.selected_code_file or fnames[0]
    if sel not in all_files: sel = fnames[0]
    content = all_files[sel]["c"]
    is_test = all_files[sel]["t"]=="test"
    lc = len(content.splitlines())

    with col_editor:
        h1,h2,h3 = st.columns([6,2,2])
        with h1:
            st.markdown(f'<div style="display:flex;align-items:center;gap:8px;padding:5px 0">{chip("TEST","yellow") if is_test else chip("SOURCE","blue")}<span style="font-family:\'JetBrains Mono\',monospace;font-size:.77rem;color:#e6edf3;font-weight:600">{sel}</span><span style="font-size:.67rem;color:#484f58">{lc} lines</span></div>',unsafe_allow_html=True)
        with h3:
            if st.button("▶ Run Pytest" if not st.session_state.is_testing else "⏳…",
                         type="primary",disabled=st.session_state.is_testing,
                         use_container_width=True,key="code_run"):
                run_sandbox(); st.rerun()
        st.code(content,language="python",line_numbers=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: REQUIREMENTS
# ─────────────────────────────────────────────────────────────────────────────
def render_requirements_tab() -> None:
    p   = st.session_state.pipeline
    doc = (p or {}).get("requirements_doc")
    if not doc:
        empty_state("📋","No requirements yet","Run the pipeline to generate the specification"); return
    render_reasoning("Requirements Analyst Agent","Requirements",doc.get("reasoning"))
    section_hdr("Requirements Specification",f"{len(doc.get('functional_requirements',[]))} FRs")
    st.markdown(f"### {doc.get('title','')}")
    ov = doc.get("problem_statement","")
    if ov: st.markdown(f'<div style="background:#0d1117;border-left:3px solid #1f6feb;border-radius:0 8px 8px 0;padding:11px 14px;margin-bottom:18px;font-size:.79rem;color:#8b949e;line-height:1.6">{ov}</div>',unsafe_allow_html=True)
    section_hdr("Functional Requirements",str(len(doc.get("functional_requirements",[]))))
    for req in (doc.get("functional_requirements") or []):
        ac_html = "".join(
            f'<div style="font-size:.71rem;color:#3fb950;padding-left:12px;margin-top:2px">✔ {ac}</div>'
            for ac in (req.get("acceptance_criteria") or [])
        )
        st.markdown(
            f'<div class="fr-card">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:5px">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:.68rem;color:#79c0ff;background:#031d2e;border:1px solid #1f6feb;border-radius:5px;padding:1px 7px">{req.get("id","")}</span>'
            f'<span style="font-size:.79rem;font-weight:600;color:#e6edf3">{req.get("title","") or ""}</span>'
            f'</div>'
            f'<div style="font-size:.74rem;color:#8b949e;line-height:1.5">{req.get("description","")}</div>'
            f'{ac_html}</div>',
            unsafe_allow_html=True)
    nc,cc = st.columns(2)
    with nc:
        section_hdr("Non-Functional Requirements")
        for nfr in (doc.get("non_functional_requirements") or []):
            st.markdown(f'<div style="display:flex;gap:8px;padding:6px 0;border-bottom:1px solid #0f1621">{chip(nfr.get("category",""),"blue")}<span style="font-size:.73rem;color:#8b949e">{nfr.get("description","") or nfr.get("requirement","")}</span></div>',unsafe_allow_html=True)
    with cc:
        section_hdr("Constraints & Assumptions")
        for c in (doc.get("constraints") or []):
            st.markdown(f'<div style="font-size:.73rem;color:#8b949e;padding:5px 0;border-bottom:1px solid #0f1621">⚠️ {c}</div>',unsafe_allow_html=True)
        for a in (doc.get("assumptions") or []):
            st.markdown(f'<div style="font-size:.73rem;color:#6e7681;font-style:italic;padding:5px 0;border-bottom:1px solid #0f1621">💡 {a}</div>',unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: ARCHITECTURE
# ─────────────────────────────────────────────────────────────────────────────
def render_architecture_tab() -> None:
    p   = st.session_state.pipeline
    doc = (p or {}).get("architecture_doc")
    if not doc:
        empty_state("🏗️","No architecture yet","Run the pipeline to generate the blueprint"); return
    render_reasoning("Architecture Agent","Architecture",doc.get("reasoning"))
    section_hdr("System Architecture Blueprint")
    st.markdown(f'<div style="font-size:.8rem;color:#8b949e;line-height:1.7;margin-bottom:14px">{doc.get("system_overview","")}</div>',unsafe_allow_html=True)
    if doc.get("design_patterns"):
        st.markdown("".join(f'<span class="tag tag-api">⚙️ {p}</span>' for p in doc["design_patterns"]),unsafe_allow_html=True)
    st.markdown('<div style="height:12px"></div>',unsafe_allow_html=True)
    section_hdr("Data Flow")
    _terminal("execution_data_flow.txt",doc.get("data_flow",""),260)
    modules = doc.get("module_specifications") or doc.get("modules") or []
    if modules:
        st.markdown('<div style="height:12px"></div>',unsafe_allow_html=True)
        section_hdr("Module Specifications",str(len(modules)))
        mc = st.columns(min(len(modules),3))
        for i,mod in enumerate(modules):
            nm  = mod.get("name") or mod.get("file_path","Module")
            rs  = mod.get("responsibility") or mod.get("purpose","")
            ex  = mod.get("public_interfaces") or mod.get("exports") or []
            dp  = mod.get("dependencies") or []
            with mc[i%3]:
                apis = "".join(f'<span class="tag tag-api">{e}</span>' for e in ex)
                deps = "".join(f'<span class="tag tag-dep">{d}</span>' for d in dp)
                apis_block = f'<div style="margin-top:7px">{apis}</div>' if apis else ""
                deps_block = f'<div style="margin-top:3px">{deps}</div>' if deps else ""
                st.markdown(
                    f'<div class="module-card"><div class="module-name">{nm}</div>'
                    f'<div class="module-desc">{rs}</div>{apis_block}{deps_block}</div>',
                    unsafe_allow_html=True)
    if doc.get("folder_structure"):
        st.markdown('<div style="height:12px"></div>',unsafe_allow_html=True)
        section_hdr("Package Hierarchy")
        st.code(doc["folder_structure"],language=None)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: SECURITY REVIEW  (Feature 3)
# ─────────────────────────────────────────────────────────────────────────────
def render_security_tab() -> None:
    p    = st.session_state.pipeline
    rpt  = (p or {}).get("security_report")
    if not st.session_state.ff_security:
        st.info("Security Review feature is disabled. Enable it in the sidebar Feature Flags."); return
    if not rpt:
        empty_state("🔒","No security report yet","Security scan runs automatically after Code Generation"); return
    render_reasoning("Security Review Agent","Security Review",rpt.get("reasoning"))

    risk    = rpt.get("risk_level","CLEAR")
    score   = rpt.get("overall_score",9.5)
    passed  = rpt.get("passed",True)
    findings= rpt.get("findings",[])
    rc = "#3fb950" if passed else ("#e3b341" if risk=="MEDIUM" else "#f85149")
    rv = {"CRITICAL":"red","HIGH":"yellow","MEDIUM":"blue","LOW":"green","CLEAR":"green"}.get(risk,"grey")

    k1,k2,k3,k4 = st.columns(4)
    k1.markdown(kpi(f"{score:.1f}","Security Score",rc,"out of 10"),unsafe_allow_html=True)
    k2.markdown(kpi(risk,"Risk Level",rc),unsafe_allow_html=True)
    k3.markdown(kpi(str(len(findings)),"Findings","#e3b341" if findings else "#3fb950"),unsafe_allow_html=True)
    k4.markdown(kpi("✅ PASS" if passed else "❌ FAIL","Gate Status",rc),unsafe_allow_html=True)
    st.markdown(f'<div style="background:#0d1117;border-left:3px solid {"#238636" if passed else "#da3633"};border-radius:0 8px 8px 0;padding:11px 14px;margin:14px 0;font-size:.79rem;color:#8b949e;line-height:1.6">{rpt.get("summary","")}</div>',unsafe_allow_html=True)

    secrets = rpt.get("hardcoded_secrets",[])
    if secrets:
        st.markdown('<div style="background:#2d0000;border:1px solid #da3633;border-radius:9px;padding:12px 14px;margin-bottom:12px"><span style="font-size:.8rem;font-weight:700;color:#f85149">🚨  Hardcoded Credentials Detected</span><div style="font-size:.73rem;color:#8b949e;margin-top:4px">' + " | ".join(f"<code>{s}</code>" for s in secrets[:5]) + "</div></div>",unsafe_allow_html=True)

    section_hdr("Security Findings",str(len(findings)))
    if not findings:
        st.markdown('<div style="background:#0a1f0a;border:1px solid #238636;border-radius:10px;padding:14px;text-align:center"><span style="font-size:.83rem;color:#3fb950;font-weight:700">✅  Zero security issues detected</span></div>',unsafe_allow_html=True)
        return

    sev_cls = {"CRITICAL":"sec-critical","HIGH":"sec-high","MEDIUM":"sec-medium","LOW":"sec-low","INFO":"sev-info"}
    for f in findings:
        sev  = f.get("severity","INFO")
        cls  = sev_cls.get(sev,"")
        cat  = f.get("category","")
        fn   = f.get("file","")
        ln   = f.get("line_number")
        snip = (f.get("code_snippet","") or "")[:100]
        desc = f.get("description","")
        rem  = f.get("remediation","")
        st.markdown(
            f'<div class="sec-row {cls}">'
            f'<div style="display:flex;align-items:center;gap:7px;margin-bottom:6px">'
            f'{_sev_chip(sev)}{chip(cat,"purple")}'
            f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:.71rem;color:#e6edf3">{fn}{":" + str(ln) if ln else ""}</span>'
            f'</div>'
            f'{"<div style=\'font-family:JetBrains Mono,monospace;font-size:.68rem;background:#010409;border:1px solid #1e2937;border-radius:6px;padding:5px 8px;color:#e3b341;margin-bottom:6px\'>" + snip + "</div>" if snip else ""}'
            f'<div style="font-size:.75rem;color:#8b949e;margin-bottom:5px">{desc}</div>'
            f'<div style="background:#161b22;border:1px solid #1e2937;border-radius:7px;padding:8px 11px;font-size:.72rem;color:#8b949e">'
            f'<span style="color:#79c0ff;font-weight:600">Remediation:  </span>{rem}</div>'
            f'</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: CODE REVIEW
# ─────────────────────────────────────────────────────────────────────────────
def render_review_tab() -> None:
    p   = st.session_state.pipeline
    doc = (p or {}).get("review_doc")
    if not doc:
        empty_state("🔍","No review yet","Run the pipeline to conduct the code audit"); return
    render_reasoning("Code Review Agent","Code Review",doc.get("reasoning"))
    score=doc.get("overall_score",0); passed=doc.get("passed",False); adh=doc.get("architecture_adherence",False)
    sc="#3fb950" if score>=8.5 else ("#e3b341" if score>=7 else "#f85149")
    k1,k2,k3,k4=st.columns(4)
    k1.markdown(kpi(f"{score:.1f}","Quality Score",sc,"/ 10"),unsafe_allow_html=True)
    k2.markdown(kpi("PASSED" if passed else "NEEDS WORK","Verdict","#3fb950" if passed else "#f85149"),unsafe_allow_html=True)
    k3.markdown(kpi("✓ Verified" if adh else "⚠ Deviations","Arch Adherence","#3fb950" if adh else "#e3b341"),unsafe_allow_html=True)
    k4.markdown(kpi(str(len(doc.get("issues",[]))),"Issues","#e3b341" if doc.get("issues") else "#3fb950"),unsafe_allow_html=True)
    st.markdown(f'<div style="background:#0d1117;border-left:3px solid {"#238636" if passed else "#da3633"};border-radius:0 8px 8px 0;padding:11px 14px;margin:14px 0;font-size:.79rem;color:#8b949e;line-height:1.6">{doc.get("summary","")}</div>',unsafe_allow_html=True)
    for s in (doc.get("strengths") or []):
        st.markdown(f'<div style="font-size:.75rem;color:#3fb950;padding:4px 0;border-bottom:1px solid #0f1621">✅ {s}</div>',unsafe_allow_html=True)
    section_hdr("Issues",str(len(doc.get("issues",[]))))
    sev_cls={"HIGH":"sev-critical","CRITICAL":"sev-critical","MEDIUM":"sev-high","LOW":"sev-medium","INFO":"sev-info"}
    for issue in (doc.get("issues") or []):
        sev=issue.get("severity","INFO")
        cls=sev_cls.get(sev,"")
        st.markdown(f'<div class="issue-card {cls}"><div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">{_sev_chip(sev)}<span style="font-family:\'JetBrains Mono\',monospace;font-size:.72rem;color:#e6edf3">{issue.get("file","")} {issue.get("line_or_location","")}</span></div><div style="font-size:.75rem;color:#8b949e;margin-bottom:7px">{issue.get("description","")}</div><div style="background:#161b22;border:1px solid #1e2937;border-radius:7px;padding:8px 11px;font-size:.72rem;color:#8b949e"><span style="color:#79c0ff;font-weight:600">Fix:  </span>{issue.get("suggestion","") or issue.get("recommendation","")}</div></div>',unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: STATIC ANALYSIS  (Feature 4)
# ─────────────────────────────────────────────────────────────────────────────
def render_static_tab() -> None:
    p  = st.session_state.pipeline
    sa = (p or {}).get("static_analysis")
    if not st.session_state.ff_static:
        st.info("Static Analysis feature is disabled. Enable it in the sidebar Feature Flags."); return
    if not sa:
        empty_state("📐","No static analysis yet","Static gate runs automatically before Test Execution"); return

    passed  = sa.get("passed",True)
    lp      = sa.get("lint_passed",True)
    tp2     = sa.get("type_passed",True)
    errs    = sa.get("error_count",0)
    warns   = sa.get("warning_count",0)
    tools   = sa.get("tools_used",[])

    k1,k2,k3,k4 = st.columns(4)
    k1.markdown(kpi("✅ PASS" if passed else "❌ FAIL","Gate Status","#3fb950" if passed else "#f85149"),unsafe_allow_html=True)
    k2.markdown(kpi(str(errs),"Lint Errors","#f85149" if errs else "#3fb950"),unsafe_allow_html=True)
    k3.markdown(kpi(str(warns),"Warnings","#e3b341" if warns else "#3fb950"),unsafe_allow_html=True)
    k4.markdown(kpi(", ".join(tools) or "—","Tools Used","#79c0ff"),unsafe_allow_html=True)

    if passed:
        st.markdown(f'<div style="background:#0a1f0a;border:1px solid #238636;border-radius:10px;padding:13px;text-align:center;margin:12px 0"><span style="font-size:.83rem;font-weight:700;color:#3fb950">✅  {sa.get("summary","Static analysis passed.")}</span></div>',unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="background:#2d1b00;border:1px solid #d29922;border-radius:10px;padding:13px;margin:12px 0"><span style="font-size:.8rem;font-weight:700;color:#e3b341">❌  {sa.get("summary","")}</span><div style="font-size:.73rem;color:#8b949e;margin-top:3px">{sa.get("reasoning","")}</div></div>',unsafe_allow_html=True)

    viols = sa.get("violations",[])
    if viols:
        section_hdr("Violations",str(len(viols)))
        err_viols  = [v for v in viols if v.get("severity")=="error"]
        warn_viols = [v for v in viols if v.get("severity")!="error"]
        for group, label in [(err_viols,"❌ Errors"),(warn_viols,"⚠️ Warnings")]:
            if not group: continue
            with st.expander(f"{label} ({len(group)})", expanded=(label.startswith("❌"))):
                for v in group:
                    sv = "red" if v.get("severity")=="error" else "yellow"
                    st.markdown(f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #0f1621">{chip(v.get("code",""),sv)}<span style="font-family:\'JetBrains Mono\',monospace;font-size:.7rem;color:#8b949e">{v.get("file","")}:{v.get("line",0)}</span><span style="font-size:.72rem;color:#c9d1d9">{v.get("message","")}</span></div>',unsafe_allow_html=True)

    lint_out = sa.get("lint_output","")
    type_out = sa.get("type_output","")
    if lint_out:
        st.markdown('<div style="height:10px"></div>',unsafe_allow_html=True)
        section_hdr("Lint Output")
        _terminal(f"ruff / flake8 / builtin  ·  {', '.join(tools)}",lint_out.replace("<","&lt;").replace(">","&gt;"),220)
    if type_out and "mypy" in tools:
        st.markdown('<div style="height:10px"></div>',unsafe_allow_html=True)
        section_hdr("mypy Output")
        _terminal("mypy --ignore-missing-imports",type_out.replace("<","&lt;").replace(">","&gt;"),200)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: PYTEST SANDBOX + COVERAGE  (Features 6, 7)
# ─────────────────────────────────────────────────────────────────────────────
def render_testing_tab() -> None:
    p  = st.session_state.pipeline
    tr = (p or {}).get("test_result")
    bh = (p or {}).get("bugfix_history",[])
    cov= (p or {}).get("coverage_report")
    render_reasoning("Test & Verification Agent","Test Automation",(tr or {}).get("reasoning"))
    if bh: render_reasoning("Bug-Fix Agent","Bug-Fix Loop",bh[-1].get("reasoning"))

    if not tr:
        empty_state("🧪","No test results yet","Run the pipeline to execute the Pytest suite")
        c,_ = st.columns([2,5])
        with c:
            if st.button("▶ Run Pytest Now",type="primary",key="tr_init"): run_sandbox(); st.rerun()
        return

    tp=tr.get("tests_passed",0); tf=tr.get("tests_failed",0); tt=tr.get("tests_total",0)
    dur=tr.get("duration_seconds",0.0); ok=tr.get("success",False)
    rate=round(tp/tt*100) if tt else 0
    rc="#3fb950" if rate==100 else ("#e3b341" if rate>=50 else "#f85149")

    k1,k2,k3,k4 = st.columns(4)
    k1.markdown(kpi(f"{tp}/{tt}","Tests Passed",None or "#3fb950"),unsafe_allow_html=True)
    k2.markdown(kpi(str(tf),"Tests Failed","#f85149" if tf else "#6e7681"),unsafe_allow_html=True)
    k3.markdown(kpi(f"{rate}%","Pass Rate",rc),unsafe_allow_html=True)
    k4.markdown(kpi(f"{dur:.2f}s","Duration","#e6edf3"),unsafe_allow_html=True)
    st.progress(rate/100)
    st.markdown('<div style="height:4px"></div>',unsafe_allow_html=True)

    if ok: st.markdown('<div style="background:#0a1f0a;border:1px solid #238636;border-radius:10px;padding:13px 16px;font-size:.81rem;font-weight:700;color:#3fb950">✅ ALL TESTS PASSED — Isolated sandbox execution verified.</div>',unsafe_allow_html=True)
    else:  st.markdown('<div style="background:#2d0000;border:1px solid #da3633;border-radius:10px;padding:13px 16px;font-size:.81rem;font-weight:700;color:#f85149">❌ TEST FAILURES DETECTED</div>',unsafe_allow_html=True)

    if bh:
        latest=bh[-1]
        st.markdown(f'<div style="background:#2d1b00;border:1px solid #d29922;border-radius:10px;padding:12px 15px;margin:10px 0"><span style="font-size:.79rem;font-weight:700;color:#e3b341">🔧 Bug-Fix Loop — {len(bh)} iteration(s)</span><span style="font-size:.72rem;color:#8b949e;margin-left:10px">{latest.get("test_pass_before","?")} → {latest.get("test_pass_after","?")} passing tests</span>{"<div style=\'font-size:.72rem;color:#8b949e;margin-top:3px\'>" + latest.get("root_cause_analysis","") + "</div>" if latest.get("root_cause_analysis") else ""}</div>',unsafe_allow_html=True)

    # Coverage (Feature 7)
    if st.session_state.ff_coverage and cov:
        st.markdown('<div style="height:10px"></div>',unsafe_allow_html=True)
        section_hdr("Code Coverage Report",f"{cov.get('total_coverage','—')}% total")
        threshold = cov.get("threshold",80)
        cov_map   = cov.get("coverage_map",{})
        below     = cov.get("below_threshold",[])
        if cov.get("coverage_tool_used") and cov_map:
            for fname, pct in cov_map.items():
                if pct < 0:
                    st.markdown(f'<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #0f1621"><span style="font-family:\'JetBrains Mono\',monospace;font-size:.73rem;color:#8b949e">{fname}</span><span style="font-size:.7rem;color:#484f58">Unknown</span></div>',unsafe_allow_html=True)
                else:
                    bar_w = pct
                    bar_c = "#3fb950" if pct>=threshold else ("#e3b341" if pct>=60 else "#f85149")
                    st.markdown(f'<div style="padding:7px 0;border-bottom:1px solid #0f1621"><div style="display:flex;justify-content:space-between;margin-bottom:3px"><span style="font-family:\'JetBrains Mono\',monospace;font-size:.73rem;color:#{"f85149" if fname in below else "8b949e"}">{fname}</span><span style="font-size:.73rem;font-weight:700;font-family:\'JetBrains Mono\',monospace;color:{bar_c}">{pct}%</span></div><div class="coverage-bar-bg"><div style="width:{bar_w}%;height:100%;background:{bar_c};border-radius:4px"></div></div></div>',unsafe_allow_html=True)
            if below:
                st.markdown(f'<div style="background:#2d1b00;border:1px solid #d29922;border-radius:9px;padding:10px 13px;margin-top:10px"><span style="font-size:.78rem;font-weight:700;color:#e3b341">⚠️ {len(below)} module(s) below {threshold}% coverage threshold</span><div style="font-size:.72rem;color:#8b949e;margin-top:3px">{", ".join(below)}</div></div>',unsafe_allow_html=True)
        else:
            st.caption(cov.get("summary","Install pytest-cov for per-module coverage: pip install pytest-cov"))

    bc,_ = st.columns([2,5])
    with bc:
        if st.button("⏳ Running…" if st.session_state.is_testing else "🔄 Execute Pytest Again",
                     type="primary",disabled=st.session_state.is_testing,key="tr_rerun"):
            run_sandbox(); st.rerun()

    section_hdr("Sandbox Output")
    stdout = tr.get("stdout","") or tr.get("stderr","") or "No output."
    _terminal(f"pytest -v --tb=short  ·  exit {tr.get('exit_code',0)}",
              stdout.replace("<","&lt;").replace(">","&gt;"))
    if tr.get("stderr","").strip():
        with st.expander("⚠️ stderr",expanded=False):
            st.code(tr["stderr"],language=None)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: GIT COMMITS
# ─────────────────────────────────────────────────────────────────────────────
def render_git_tab() -> None:
    p   = st.session_state.pipeline
    commits = (p or {}).get("git_commits",[])
    pd      = (p or {}).get("project_dir","")
    if not commits:
        empty_state("🔀","No commits yet","Run the pipeline to generate staged Git commits"); return
    section_hdr("Atomic Stage Commit Timeline",f"{len(commits)} commits")
    b1,b2,_ = st.columns([2,2,7])
    with b1:
        zb = export_zip_bytes()
        if zb:
            st.download_button("📦 Download .ZIP",data=zb,file_name="multiagent_project.zip",
                               mime="application/zip",key="git_zip",use_container_width=True)
    with b2:
        if st.button("🐙 Push to GitHub",use_container_width=True,key="git_gh"):
            st.session_state.show_github_modal=True; st.rerun()
    st.markdown('<div style="height:6px"></div>',unsafe_allow_html=True)
    cl,cd = st.columns([4,7])
    with cl:
        st.markdown('<div style="font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#484f58;margin-bottom:9px">Commit Log</div>',unsafe_allow_html=True)
        for c in commits:
            is_sel = st.session_state.selected_commit==c["hash"]
            ts=c.get("timestamp","")
            try: ts=datetime.fromisoformat(ts.replace("Z","")).strftime("%H:%M")
            except: pass
            st.markdown(f'<div style="background:{"#0d1f35" if is_sel else "#0d1117"};border:1px solid {"#1f6feb" if is_sel else "#1e2937"};border-radius:8px;padding:9px 12px;margin-bottom:5px"><div style="display:flex;align-items:center;gap:5px;margin-bottom:3px"><span style="font-family:\'JetBrains Mono\',monospace;font-size:.66rem;color:#79c0ff;background:#031d2e;border:1px solid #1f6feb;border-radius:4px;padding:0 5px">{c.get("short_hash","")}</span><span style="font-size:.63rem;color:#3fb950;background:#0d2f16;border:1px solid #238636;border-radius:4px;padding:0 5px">{c.get("stage","")}</span><span style="margin-left:auto;font-size:.62rem;color:#484f58">{ts}</span></div><div style="font-size:.74rem;color:#e6edf3;font-weight:500;margin:2px 0">{c.get("message","")[:58]}</div><div style="font-size:.65rem;color:#6e7681">{c.get("author","")}</div></div>',unsafe_allow_html=True)
            if st.button(f"Inspect `{c.get('short_hash','')}`",key=f"cm_{c['hash']}",
                         use_container_width=True,type="secondary"):
                st.session_state.selected_commit=c["hash"]
                if pd: st.session_state.diff_content[c["hash"]]=load_diff(pd,c["hash"])
                st.rerun()
    with cd:
        sh = st.session_state.selected_commit
        if not sh:
            st.markdown('<div style="height:380px;display:flex;align-items:center;justify-content:center;border:1px dashed #1e2937;border-radius:10px;background:#0d1117"><div style="text-align:center"><div style="font-size:1.6rem;margin-bottom:7px">🔍</div><div style="font-size:.78rem;color:#484f58">Select a commit to inspect unified diff</div></div></div>',unsafe_allow_html=True)
        else:
            cobj=next((c for c in commits if c["hash"]==sh),None)
            if cobj:
                fch=" ".join(f'<span class="tag tag-api">{f}</span>' for f in (cobj.get("files_changed") or []))
                st.markdown(f'<div style="background:#0d1117;border:1px solid #1e2937;border-radius:10px;padding:12px 14px;margin-bottom:9px"><div style="font-size:.79rem;font-weight:600;color:#e6edf3;margin-bottom:5px">{cobj.get("message","")}</div><div style="display:flex;gap:7px;flex-wrap:wrap">{fch}</div></div>',unsafe_allow_html=True)
            diff = st.session_state.diff_content.get(sh,"")
            if diff:
                _terminal(f"git show {sh[:8]}",_diff_html(diff),500)
            else:
                st.info("No diff available.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB: CI/CD SCAFFOLDING  (Feature 8)
# ─────────────────────────────────────────────────────────────────────────────
def render_cicd_tab() -> None:
    p    = st.session_state.pipeline
    cicd = (p or {}).get("cicd_package")
    if not st.session_state.ff_cicd:
        st.info("CI/CD Scaffolding feature is disabled. Enable it in the sidebar Feature Flags."); return
    if not cicd:
        empty_state("🚀","No CI/CD scaffold yet","CI/CD generation runs automatically in the Documentation stage"); return
    render_reasoning("DevOps Agent","CI/CD Scaffolding",cicd.get("reasoning"))

    files = cicd.get("files",{})
    section_hdr("Generated CI/CD Files",str(len(files)))

    # Download all
    b1,b2 = st.columns(2)
    gha = cicd.get("github_actions_workflow","")
    req = cicd.get("requirements_txt","")
    if gha:
        with b1:
            st.download_button("⬇️ ci.yml",data=gha,file_name="ci.yml",mime="text/plain",key="dl_ci",use_container_width=True)
    if req:
        with b2:
            st.download_button("⬇️ requirements.txt",data=req,file_name="requirements.txt",mime="text/plain",key="dl_req",use_container_width=True)

    file_tabs = list(files.keys())
    if file_tabs:
        sel = st.selectbox("View file",file_tabs,key="cicd_file_sel")
        content = files.get(sel,"")
        lang = "yaml" if sel.endswith((".yml",".yaml")) else ("docker" if "Dockerfile" in sel else "text")
        st.code(content,language=lang)

    rme = cicd.get("readme_ci_section","")
    if rme:
        with st.expander("📄 README CI/CD Section",expanded=False):
            st.markdown(rme)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: DOCUMENTATION
# ─────────────────────────────────────────────────────────────────────────────
def render_documentation_tab() -> None:
    p    = st.session_state.pipeline
    docs = (p or {}).get("documentation")
    if not docs:
        empty_state("📚","No documentation yet","Run the pipeline to generate docs & README"); return
    render_reasoning("Documentation Agent","Documentation",docs.get("reasoning"))
    bs = docs.get("build_summary",{})
    if bs:
        k1,k2,k3,k4 = st.columns(4)
        k1.markdown(kpi(str(bs.get("total_modules",0)),"Total Modules"),unsafe_allow_html=True)
        k2.markdown(kpi(f"{bs.get('pipeline_stages_completed',0)}/10","Stages","#79c0ff"),unsafe_allow_html=True)
        k3.markdown(kpi(str(bs.get("test_pass_rate","N/A")),"Pass Rate","#3fb950"),unsafe_allow_html=True)
        k4.markdown(kpi(str(bs.get("git_commits_created",0)),"Commits"),unsafe_allow_html=True)
        st.markdown('<div style="height:6px"></div>',unsafe_allow_html=True)
    if docs.get("setup_instructions"):
        section_hdr("Developer Setup")
        _terminal("setup.sh",docs["setup_instructions"].replace("<","&lt;").replace(">","&gt;"),200)
    md = docs.get("module_documentation",{})
    if md:
        st.markdown('<div style="height:10px"></div>',unsafe_allow_html=True)
        section_hdr("Module API Reference",str(len(md)))
        mc = st.columns(min(len(md),2))
        for i,(mod,desc) in enumerate(md.items()):
            with mc[i%2]:
                st.markdown(f'<div class="module-card" style="margin-bottom:9px"><div class="module-name">{mod}</div><div class="module-desc">{desc}</div></div>',unsafe_allow_html=True)
    if docs.get("readme"):
        st.markdown('<div style="height:10px"></div>',unsafe_allow_html=True)
        rh1,rh2 = st.columns([7,1])
        with rh1: section_hdr("README.md Preview")
        with rh2:
            st.download_button("⬇️",data=docs["readme"],file_name="README.md",mime="text/markdown",key="dl_readme")
        with st.expander("View README.md",expanded=True):
            st.code(docs["readme"],language="markdown")

# ─────────────────────────────────────────────────────────────────────────────
# TAB: TRACE DASHBOARD  (Feature 9)
# ─────────────────────────────────────────────────────────────────────────────
def render_trace_tab() -> None:
    p      = st.session_state.pipeline
    traces = (p or {}).get("stage_traces",[])
    if not st.session_state.ff_trace:
        st.info("Trace Dashboard feature is disabled. Enable it in the sidebar Feature Flags."); return
    if not traces:
        empty_state("📈","No trace data yet","Trace data is recorded as each pipeline stage completes"); return

    total_tokens = p.get("total_tokens",0)
    total_cost   = p.get("total_cost_usd",0.0)
    total_dur    = sum(t.get("duration_seconds",0) for t in traces)
    n_stages     = len(traces)

    k1,k2,k3,k4 = st.columns(4)
    k1.markdown(kpi(str(n_stages),"Stages Traced","#79c0ff"),unsafe_allow_html=True)
    k2.markdown(kpi(f"{total_dur:.1f}s","Total Duration","#e6edf3"),unsafe_allow_html=True)
    k3.markdown(kpi(f"{total_tokens:,}","Token Estimate","#d2a8ff"),unsafe_allow_html=True)
    k4.markdown(kpi(f"${total_cost:.4f}","Est. Cost USD","#3fb950"),unsafe_allow_html=True)
    st.markdown('<div style="height:10px"></div>',unsafe_allow_html=True)
    section_hdr("Per-Stage Trace")

    for tr in traces:
        status = tr.get("status","SUCCESS")
        sv={"SUCCESS":"green","FAILED":"red","SKIPPED":"grey","PAUSED":"orange"}.get(status,"grey")
        dur_s = f"{tr.get('duration_seconds',0):.2f}s"
        tok_s = f"{tr.get('token_estimate',0):,} tok"
        cost_s= f"${tr.get('cost_estimate_usd',0):.5f}"
        arts  = tr.get("artifact_keys",[])
        snip  = tr.get("reasoning_snippet","")
        st.markdown(f"""
        <div class="trace-row">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
            {chip(status,sv)}
            <span style="font-size:.82rem;font-weight:700;color:#e6edf3">{tr.get("stage","")}</span>
            <span style="font-size:.72rem;color:#6e7681">·  {tr.get("agent","")}</span>
            <span style="margin-left:auto;display:flex;gap:8px">
              {chip(dur_s,"blue")}{chip(tok_s,"purple")}{chip(cost_s,"green")}
            </span>
          </div>
          {"<div style='display:flex;flex-wrap:wrap;gap:4px;margin-bottom:5px'>" + "".join(f'<span class="tag tag-api">{a}</span>' for a in arts) + "</div>" if arts else ""}
          {"<div style='font-size:.71rem;color:#6e7681;font-style:italic;line-height:1.5'>" + snip + "</div>" if snip else ""}
          <div style="display:flex;gap:8px;margin-top:5px">
            <span style="font-size:.64rem;font-family:\'JetBrains Mono\',monospace;color:#484f58">start: {tr.get("start_time","")[:19]}</span>
            <span style="font-size:.64rem;font-family:\'JetBrains Mono\',monospace;color:#484f58">end: {tr.get("end_time","")[:19]}</span>
          </div>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB: AUDIT TRAIL
# ─────────────────────────────────────────────────────────────────────────────
def render_audit_tab() -> None:
    p    = st.session_state.pipeline
    logs = (p or {}).get("audit_logs",[])
    if not logs:
        empty_state("🛡️","No audit events yet","Events are logged as agents execute"); return
    section_hdr("Pipeline Execution Audit Trail",f"{len(logs)} events")
    fc1,fc2,_ = st.columns([2,3,4])
    with fc1:
        stages = ["ALL"] + list(dict.fromkeys(l.get("stage","") for l in logs))
        fs = st.selectbox("Stage",stages,key="afs",label_visibility="collapsed")
    with fc2:
        srch = st.text_input("Search",key="ais",placeholder="Search actions, agents, details…",label_visibility="collapsed")
    filtered = [l for l in logs
                if (fs=="ALL" or l.get("stage")==fs)
                and (not srch.strip()
                     or srch.lower() in l.get("action","").lower()
                     or srch.lower() in l.get("agent","").lower()
                     or srch.lower() in l.get("details","").lower())]
    st.markdown(f'<div style="margin-bottom:9px">{chip(f"Showing {len(filtered)} of {len(logs)} events","grey")}</div>',unsafe_allow_html=True)
    sv_map={"SUCCESS":"green","IN_PROGRESS":"yellow","WARNING":"orange","FAILED":"red","PAUSED":"orange","SKIPPED":"grey"}
    for log in filtered:
        sv=sv_map.get(log.get("status",""),"grey")
        ic={"SUCCESS":"✅","IN_PROGRESS":"⏳","WARNING":"⚠️","FAILED":"❌","PAUSED":"🛑","SKIPPED":"⏭"}.get(log.get("status",""),"🔘")
        ts=log.get("timestamp","")
        try: ts=datetime.fromisoformat(ts.replace("Z","")).strftime("%H:%M:%S")
        except: pass
        st.markdown(f'<div class="audit-row"><div style="flex:1;min-width:0"><div style="display:flex;align-items:center;gap:7px;flex-wrap:wrap"><span style="font-size:.79rem;font-weight:700;color:#e6edf3">{ic} {log.get("action","")}</span>{chip(log.get("stage",""),sv)}</div><div style="font-size:.72rem;color:#6e7681;margin-top:2px;line-height:1.4">{log.get("details","")}</div><div style="font-size:.65rem;color:#484f58;margin-top:2px">Agent: {log.get("agent","")}</div></div><span style="font-size:.64rem;font-family:\'JetBrains Mono\',monospace;color:#484f58;white-space:nowrap">{ts}</span></div>',unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# GITHUB MODAL
# ─────────────────────────────────────────────────────────────────────────────
def render_github_modal() -> None:
    if not st.session_state.show_github_modal: return
    p  = st.session_state.pipeline
    nc = len((p or {}).get("git_commits",[]))
    st.markdown(f'<div style="background:#0d1117;border:1px solid #1e2937;border-radius:14px;padding:22px;margin-bottom:14px"><div style="display:flex;align-items:center;gap:9px;margin-bottom:14px"><div style="width:32px;height:32px;border-radius:8px;background:#161b22;border:1px solid #30363d;display:flex;align-items:center;justify-content:center;font-size:16px">🐙</div><div><div style="font-size:.88rem;font-weight:700;color:#f0f6fc">Push to GitHub</div><div style="font-size:.71rem;color:#484f58">Publish with complete atomic commit history</div></div></div>',unsafe_allow_html=True)
    if st.session_state.github_result:
        res=st.session_state.github_result
        st.success(f"✅ Published! {res.get('message','')}")
        if res.get("repo_url"): st.markdown(f"[View on GitHub ↗]({res['repo_url']})")
        if st.button("✕ Close",key="gh_cls"):
            st.session_state.show_github_modal=False; st.session_state.github_result=None; st.rerun()
        st.markdown("</div>",unsafe_allow_html=True); return
    if st.session_state.github_error:
        st.markdown(f'<div style="background:#2d0000;border:1px solid #da3633;border-radius:9px;padding:11px 14px;margin-bottom:12px"><span style="font-size:.79rem;font-weight:700;color:#f85149">❌ Push Failed</span><div style="font-size:.73rem;color:#8b949e;margin-top:3px">{st.session_state.github_error}</div></div>',unsafe_allow_html=True)
    st.markdown(f'<div style="margin-bottom:12px">{chip(f"📦 {nc} commits staged","blue")}</div>',unsafe_allow_html=True)
    ga,gb = st.columns(2)
    with ga:
        token = st.text_input("GitHub PAT",type="password",value=st.session_state.github_token,placeholder="ghp_…",key="gh_tok")
        st.caption("Requires `repo` scope.")
    with gb:
        repo = st.text_input("Repository Name",value=st.session_state.github_repo,placeholder="my-project",key="gh_rp")
    oc1,oc2 = st.columns(2)
    with oc1:
        create_new = st.radio("Destination",["Create new repo","Push to existing repo"],key="gh_cr")
        st.session_state.github_create_new=(create_new=="Create new repo")
    with oc2:
        if st.session_state.github_create_new:
            priv=st.checkbox("Private repo",value=st.session_state.github_private,key="gh_priv")
            st.session_state.github_private=priv
    pb,cb = st.columns(2)
    with pb:
        if st.button("🚀 Push to GitHub",type="primary",use_container_width=True,
                     disabled=not token.strip() or not repo.strip(),key="gh_push"):
            if not p or not p.get("project_dir"):
                st.session_state.github_error="No active project directory."; st.rerun()
            else:
                res=GitManager(p["project_dir"]).push_to_github(
                    token=token.strip(),repo_name=repo.strip(),
                    create_new=st.session_state.github_create_new,
                    is_private=st.session_state.github_private)
                if res.get("success"): st.session_state.github_result=res; st.session_state.github_error=None
                else: st.session_state.github_error=res.get("error","Push failed.")
                st.rerun()
    with cb:
        if st.button("Cancel",use_container_width=True,key="gh_can"):
            st.session_state.show_github_modal=False; st.session_state.github_error=None; st.rerun()
    st.markdown("</div>",unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    render_sidebar()
    render_header()

    if st.session_state.error_message:
        st.markdown(f'<div style="background:#2d0000;border:1px solid #da3633;border-left:3px solid #da3633;border-radius:0 10px 10px 0;padding:13px 16px;margin-bottom:14px"><span style="font-size:.81rem;font-weight:700;color:#f85149">⚠️ Pipeline Error</span><div style="font-size:.75rem;color:#8b949e;margin-top:3px">{st.session_state.error_message}</div></div>',unsafe_allow_html=True)

    render_mission_control()

    # Pipeline stepper
    st.markdown('<div style="background:#0d1117;border:1px solid #1e2937;border-radius:14px;padding:18px 20px;margin-bottom:14px"><div style="display:flex;align-items:center;gap:9px;margin-bottom:13px"><span style="font-size:.83rem;font-weight:700;color:#e6edf3">⚡ 10-Stage LangGraph Multi-Agent Orchestration</span></div>',unsafe_allow_html=True)
    render_stage_pipeline()
    st.markdown("</div>",unsafe_allow_html=True)

    # Live stream (Feature 10)
    render_live_stream()

    # Clarification loop (Feature 1)
    render_clarification_panel()

    # Escalation panel (Feature 5)
    render_escalation_panel()

    # Approval gate (Feature 2)
    render_approval_gate()

    # GitHub modal
    render_github_modal()

    # ── Tabs ──────────────────────────────────────────────────────────────
    p  = st.session_state.pipeline or {}
    cc = len(p.get("code_files",{}))
    rs = (p.get("review_doc") or {}).get("overall_score","")
    tok= (p.get("test_result") or {}).get("success",False)
    nc = len(p.get("git_commits",[]))
    al = len(p.get("audit_logs",[]))
    sf = len((p.get("security_report") or {}).get("findings",[]))
    sa_pass = (p.get("static_analysis") or {}).get("passed",True)
    cicd_ok = bool(p.get("cicd_package"))
    tr_n = len(p.get("stage_traces",[]))

    tabs = st.tabs([
        f"💻 Source Code{f' ({cc})' if cc else ''}",
        "📋 Requirements",
        "🏗️ Architecture",
        f"🔒 Security{f' ({sf})' if sf else ''}",
        f"🔍 Code Review{f' ({rs}/10)' if rs else ''}",
        f"📐 Static Analysis{'  ✅' if sa_pass and p.get('static_analysis') else ('  ❌' if p.get('static_analysis') and not sa_pass else '')}",
        f"🧪 Pytest Sandbox{'  ✅' if tok else ''}",
        f"🔀 Git Commits{f' ({nc})' if nc else ''}",
        f"🚀 CI/CD Scaffold{'  ✅' if cicd_ok else ''}",
        "📚 Documentation",
        f"📈 Trace Dashboard{f' ({tr_n})' if tr_n else ''}",
        f"🛡️ Audit Trail{f' ({al})' if al else ''}",
    ])

    with tabs[0]:  render_code_tab()
    with tabs[1]:  render_requirements_tab()
    with tabs[2]:  render_architecture_tab()
    with tabs[3]:  render_security_tab()
    with tabs[4]:  render_review_tab()
    with tabs[5]:  render_static_tab()
    with tabs[6]:  render_testing_tab()
    with tabs[7]:  render_git_tab()
    with tabs[8]:  render_cicd_tab()
    with tabs[9]:  render_documentation_tab()
    with tabs[10]: render_trace_tab()
    with tabs[11]: render_audit_tab()


if __name__ == "__main__":
    main()

