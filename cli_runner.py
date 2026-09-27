"""
CLI / Bridge Runner for Multi-Agent Software Development Team.
Invoked by the backend server to run the LangGraph pipeline with structured JSON input/output.
"""

import argparse
import json
import os
import sys
from orchestrator import MultiAgentOrchestrator
from git_manager import GitManager


def main():
    parser = argparse.ArgumentParser(description="Run Multi-Agent Pipeline")
    parser.add_argument("--action", type=str, default="run", choices=["run", "approve", "request-changes", "reject"])
    parser.add_argument("--requirement", type=str, default=None, help="Software requirement prompt")
    parser.add_argument("--provider", type=str, default="deterministic", choices=["deterministic", "gemini", "openai", "anthropic"])
    parser.add_argument("--api-key", type=str, default=None, help="LLM API key")
    parser.add_argument("--max-iterations", type=int, default=3, help="Max bug-fix iterations")
    parser.add_argument("--project-dir", type=str, default=None, help="Custom project directory")
    parser.add_argument("--require-approval", action="store_true", default=False, help="Pause at approval gates")
    parser.add_argument("--feedback", type=str, default=None, help="Feedback for request-changes")
    parser.add_argument("--reason", type=str, default=None, help="Reason for rejection")
    parser.add_argument("--reviewer", type=str, default="Human Operator", help="Reviewer identity")
    args = parser.parse_args()

    orchestrator = MultiAgentOrchestrator(
        provider_type=args.provider,
        api_key=args.api_key,
        max_iterations=args.max_iterations,
    )

    if args.action == "run":
        if not args.requirement:
            print("Error: --requirement is required for action 'run'", file=sys.stderr)
            sys.exit(1)
        result_state = orchestrator.run_pipeline(
            requirement=args.requirement,
            custom_project_dir=args.project_dir,
            require_approval=args.require_approval
        )
    elif args.action == "approve":
        if not args.project_dir:
            print("Error: --project-dir is required for action 'approve'", file=sys.stderr)
            sys.exit(1)
        result_state = orchestrator.approve_and_continue(
            project_dir=args.project_dir,
            reviewer=args.reviewer
        )
    elif args.action == "request-changes":
        if not args.project_dir or not args.feedback:
            print("Error: --project-dir and --feedback are required for action 'request-changes'", file=sys.stderr)
            sys.exit(1)
        result_state = orchestrator.request_changes(
            project_dir=args.project_dir,
            feedback=args.feedback,
            reviewer=args.reviewer
        )
    elif args.action == "reject":
        if not args.project_dir:
            print("Error: --project-dir is required for action 'reject'", file=sys.stderr)
            sys.exit(1)
        result_state = orchestrator.reject_and_stop(
            project_dir=args.project_dir,
            reason=args.reason,
            reviewer=args.reviewer
        )
    else:
        print(f"Error: unknown action {args.action}", file=sys.stderr)
        sys.exit(1)

    # Clean up non-serializable fields if any
    safe_state = dict(result_state)
    
    # Enrich git history with diffs if requested
    if safe_state.get("project_dir"):
        gm = GitManager(safe_state["project_dir"])
        safe_state["git_commits"] = gm.get_commit_history()

    # Print pure JSON output
    print("=== PIPELINE_JSON_START ===")
    print(json.dumps(safe_state, indent=2, default=str))
    print("=== PIPELINE_JSON_END ===")


if __name__ == "__main__":
    main()
