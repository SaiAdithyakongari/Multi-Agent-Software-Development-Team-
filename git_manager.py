"""
Git Version Control & Repository Audit Manager.
Provides atomic commits at each pipeline stage, visual commit history,
unified diff inspections, and complete project repository ZIP exports.
"""

from dataclasses import dataclass, field
from datetime import datetime
import json
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional


@dataclass
class GitCommitInfo:
    commit_hash: str
    short_hash: str
    author: str
    email: str
    timestamp: str
    message: str
    stage: str
    files_changed: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hash": self.commit_hash,
            "short_hash": self.short_hash,
            "author": self.author,
            "email": self.email,
            "timestamp": self.timestamp,
            "message": self.message,
            "stage": self.stage,
            "files_changed": self.files_changed,
        }


class GitManager:
    """Manages Git repository initialization, staged commits, log history, and exports."""

    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
        self._meta_file = os.path.join(self.repo_path, ".git_stages.json")

    def _read_stages_meta(self) -> Dict[str, str]:
        if os.path.exists(self._meta_file):
            try:
                with open(self._meta_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _write_stages_meta(self, meta: Dict[str, str]) -> None:
        try:
            with open(self._meta_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
        except Exception:
            pass

    def init_repo(self) -> str:
        """Initializes a clean Git repository if not present."""
        os.makedirs(self.repo_path, exist_ok=True)
        git_dir = os.path.join(self.repo_path, ".git")
        if not os.path.exists(git_dir):
            subprocess.run(["git", "init"], cwd=self.repo_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "MultiAgent-Orchestrator"], cwd=self.repo_path, capture_output=True)
            subprocess.run(["git", "config", "user.email", "orchestrator@multiagent.ai"], cwd=self.repo_path, capture_output=True)
            
            # Create standard .gitignore
            gitignore_path = os.path.join(self.repo_path, ".gitignore")
            if not os.path.exists(gitignore_path):
                with open(gitignore_path, "w", encoding="utf-8") as f:
                    f.write("__pycache__/\n*.pyc\n.pytest_cache/\n.git_stages.json\n")
            
            subprocess.run(["git", "add", ".gitignore"], cwd=self.repo_path, capture_output=True)
            subprocess.run(["git", "commit", "-m", "chore(init): repository initialized"], cwd=self.repo_path, capture_output=True)
            
            res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_path, capture_output=True, text=True)
            h = res.stdout.strip()
            meta = {h: "Initialization"}
            self._write_stages_meta(meta)
            return h

        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_path, capture_output=True, text=True)
        return res.stdout.strip()

    def commit_stage(
        self,
        stage_name: str,
        message: str,
        author_name: str = "MultiAgent-Bot",
        author_email: str = "bot@multiagent.ai"
    ) -> Optional[str]:
        """Stages all current changes and records an atomic commit for the pipeline stage."""
        self.init_repo()

        # Add all changed files
        subprocess.run(["git", "add", "."], cwd=self.repo_path, capture_output=True)

        # Check if there is anything to commit
        status_res = subprocess.run(["git", "status", "--porcelain"], cwd=self.repo_path, capture_output=True, text=True)
        if not status_res.stdout.strip():
            # Nothing staged
            res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_path, capture_output=True, text=True)
            return res.stdout.strip() if res.stdout.strip() else None

        # Execute atomic commit with specified agent identity
        commit_cmd = [
            "git",
            "-c", f"user.name={author_name}",
            "-c", f"user.email={author_email}",
            "commit",
            "-m", message
        ]
        res = subprocess.run(commit_cmd, cwd=self.repo_path, capture_output=True, text=True)
        if res.returncode != 0 and "nothing to commit" in res.stdout.lower():
            head_res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_path, capture_output=True, text=True)
            return head_res.stdout.strip()

        # Retrieve new HEAD commit
        head_res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_path, capture_output=True, text=True)
        commit_hash = head_res.stdout.strip()
        if commit_hash:
            stages_meta = self._read_stages_meta()
            stages_meta[commit_hash] = stage_name
            self._write_stages_meta(stages_meta)
            return commit_hash

        return None

    def get_commit_history(self) -> List[Dict[str, Any]]:
        """Extracts complete ordered commit history from git log."""
        if not os.path.exists(os.path.join(self.repo_path, ".git")):
            return []

        stages_meta = self._read_stages_meta()
        history: List[Dict[str, Any]] = []

        log_format = "%H|%h|%an|%ae|%aI|%s"
        res = subprocess.run(["git", "log", f"--pretty=format:{log_format}"], cwd=self.repo_path, capture_output=True, text=True)
        if res.returncode != 0 or not res.stdout.strip():
            return []

        for line in res.stdout.strip().splitlines():
            parts = line.split("|", 5)
            if len(parts) == 6:
                full_h, short_h, author, email, timestamp, msg = parts
                
                # Retrieve files changed in this commit
                files_res = subprocess.run(
                    ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", full_h],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True
                )
                files_changed = [f for f in files_res.stdout.strip().splitlines() if f]
                
                # Determine stage
                stage = stages_meta.get(full_h)
                if not stage:
                    if "feat(requirements)" in msg:
                        stage = "Requirements"
                    elif "feat(arch)" in msg:
                        stage = "Architecture"
                    elif "feat(code)" in msg:
                        stage = "Code Generation"
                    elif "review" in msg:
                        stage = "Code Review"
                    elif "test" in msg:
                        stage = "Test Generation"
                    elif "fix" in msg:
                        stage = "Bug-Fix Loop"
                    elif "docs" in msg:
                        stage = "Documentation"
                    elif "init" in msg:
                        stage = "Initialization"
                    else:
                        stage = "Pipeline"

                history.append({
                    "hash": full_h,
                    "short_hash": short_h,
                    "author": author,
                    "email": email,
                    "timestamp": timestamp,
                    "message": msg,
                    "stage": stage,
                    "files_changed": files_changed
                })

        return history

    def get_diff(self, commit_hash: str) -> str:
        """Returns the unified diff patch for a given commit hash."""
        if not os.path.exists(os.path.join(self.repo_path, ".git")):
            return ""
        res = subprocess.run(["git", "show", "--stat", "-p", commit_hash], cwd=self.repo_path, capture_output=True, text=True)
        return res.stdout if res.returncode == 0 else f"Could not retrieve diff for commit {commit_hash}."

    def export_zip(self, output_zip_path: Optional[str] = None) -> str:
        """Archives the complete repository (including .git) into a .zip file."""
        if not output_zip_path:
            import tempfile
            temp_target = tempfile.mktemp(prefix="multiagent_repo_export_")
            zip_file = shutil.make_archive(temp_target, "zip", self.repo_path)
            return zip_file
        else:
            base_name = output_zip_path[:-4] if output_zip_path.endswith(".zip") else output_zip_path
            return shutil.make_archive(base_name, "zip", self.repo_path)

    def push_to_github(
        self,
        token: str,
        repo_name: str,
        create_new: bool = True,
        is_private: bool = False
    ) -> Dict[str, Any]:
        """
        Pushes the complete repository with all staged commits to a GitHub repository.
        Handles authentication verification, repository creation (if requested),
        and remote branch synchronization while preserving full commit history.
        """
        import urllib.request
        import urllib.error
        import urllib.parse

        token = token.strip()
        repo_name = repo_name.strip()

        if not token:
            return {"success": False, "error": "GitHub Personal Access Token is required."}
        if not repo_name:
            return {"success": False, "error": "Target repository name is required."}

        # 1. Verify GitHub Token & determine user identity
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MultiAgent-SDLC-App"
        }

        user_req = urllib.request.Request("https://api.github.com/user", headers=headers)
        try:
            with urllib.request.urlopen(user_req, timeout=15) as resp:
                user_data = json.loads(resp.read().decode("utf-8"))
                username = user_data.get("login")
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return {"success": False, "error": "Invalid GitHub Personal Access Token. Please verify your token has 'repo' scope and has not expired."}
            elif e.code == 403:
                return {"success": False, "error": "GitHub API access forbidden or rate limit exceeded. Verify your token permissions."}
            return {"success": False, "error": f"GitHub user verification failed (HTTP {e.code})."}
        except Exception as e:
            return {"success": False, "error": f"Failed to connect to GitHub API: {str(e)}"}

        if not username:
            return {"success": False, "error": "Unable to resolve GitHub user profile for the provided token."}

        # Parse target owner / repo
        if "/" in repo_name:
            parts = repo_name.split("/", 1)
            target_owner = parts[0].strip()
            clean_repo_name = parts[1].strip()
        else:
            target_owner = username
            clean_repo_name = repo_name

        # Sanitize clean_repo_name
        clean_repo_name = re.sub(r"[^a-zA-Z0-9_\.-]", "-", clean_repo_name)

        # 2. Check repository status or create repository
        repo_url_api = f"https://api.github.com/repos/{target_owner}/{clean_repo_name}"
        repo_exists = False

        check_req = urllib.request.Request(repo_url_api, headers=headers)
        try:
            with urllib.request.urlopen(check_req, timeout=15) as resp:
                repo_exists = True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                repo_exists = False
            elif e.code == 401 or e.code == 403:
                return {"success": False, "error": "Permission denied accessing repository. Please check your token scope."}
        except Exception:
            pass

        if create_new:
            if repo_exists:
                # Repo already exists when create_new is requested:
                # We can either push to it or warn, let's proceed to push while noting existing repo
                pass
            else:
                # Create the repository
                create_endpoint = "https://api.github.com/user/repos"
                if target_owner.lower() != username.lower():
                    create_endpoint = f"https://api.github.com/orgs/{target_owner}/repos"

                payload = json.dumps({
                    "name": clean_repo_name,
                    "description": "Multi-agent autonomous software engineering project with complete atomic SDLC commit history.",
                    "private": is_private,
                    "auto_init": False
                }).encode("utf-8")

                post_req = urllib.request.Request(create_endpoint, data=payload, headers=headers, method="POST")
                try:
                    with urllib.request.urlopen(post_req, timeout=15) as resp:
                        created_data = json.loads(resp.read().decode("utf-8"))
                        target_owner = created_data.get("owner", {}).get("login", target_owner)
                        clean_repo_name = created_data.get("name", clean_repo_name)
                except urllib.error.HTTPError as e:
                    try:
                        err_body = json.loads(e.read().decode("utf-8"))
                        msg = err_body.get("message", f"HTTP {e.code}")
                    except Exception:
                        msg = f"HTTP {e.code}"
                    if e.code == 422:
                        return {"success": False, "error": f"Repository '{clean_repo_name}' already exists or name is invalid: {msg}"}
                    return {"success": False, "error": f"Failed to create GitHub repository: {msg}"}
                except Exception as e:
                    return {"success": False, "error": f"Failed to create GitHub repository: {str(e)}"}
        else:
            if not repo_exists:
                return {
                    "success": False,
                    "error": f"Repository '{target_owner}/{clean_repo_name}' does not exist on GitHub. Check the name or enable 'Create new repository'."
                }

        # 3. Push Git repository using authenticated remote URL
        self.init_repo()

        # Ensure branch is main
        subprocess.run(["git", "branch", "-M", "main"], cwd=self.repo_path, capture_output=True)

        # Build authenticated remote push URL
        # Format: https://x-access-token:<token>@github.com/<owner>/<repo>.git
        auth_remote = f"https://x-access-token:{token}@github.com/{target_owner}/{clean_repo_name}.git"

        push_cmd = ["git", "push", "-u", auth_remote, "main", "--force"]
        push_res = subprocess.run(push_cmd, cwd=self.repo_path, capture_output=True, text=True)

        if push_res.returncode != 0:
            err_msg = push_res.stderr.strip() or push_res.stdout.strip()
            # Clean sensitive token from error message if present
            err_msg = err_msg.replace(token, "[REDACTED_TOKEN]")
            if "Authentication failed" in err_msg or "Invalid username or password" in err_msg:
                return {"success": False, "error": "GitHub authentication failed during push. Verify token permissions."}
            elif "Repository not found" in err_msg:
                return {"success": False, "error": f"Repository '{target_owner}/{clean_repo_name}' not found or access denied."}
            return {"success": False, "error": f"Git push failed: {err_msg}"}

        commits = self.get_commit_history()
        html_url = f"https://github.com/{target_owner}/{clean_repo_name}"

        return {
            "success": True,
            "repo_url": html_url,
            "owner": target_owner,
            "repo_name": clean_repo_name,
            "commits_pushed": len(commits),
            "message": f"Successfully pushed {len(commits)} commits to {html_url}"
        }

