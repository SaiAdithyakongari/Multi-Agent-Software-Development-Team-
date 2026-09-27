import React, { useState } from 'react';
import {
  X,
  Github,
  Key,
  FolderGit2,
  Lock,
  Globe,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Loader2,
  Eye,
  EyeOff,
  Sparkles,
  Shield
} from 'lucide-react';
import { PipelineState, GitHubPushResult } from '../types';

interface GitHubPushModalProps {
  isOpen: boolean;
  onClose: () => void;
  pipeline: PipelineState | null;
}

export const GitHubPushModal: React.FC<GitHubPushModalProps> = ({
  isOpen,
  onClose,
  pipeline
}) => {
  // Derive a clean default repository name from the requirement/pipeline title
  const defaultRepoName = React.useMemo(() => {
    const raw = pipeline?.requirements_doc?.title || pipeline?.requirement || 'multi-agent-software-project';
    return raw
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 36) || 'multi-agent-app';
  }, [pipeline]);

  const [token, setToken] = useState<string>('');
  const [showToken, setShowToken] = useState<boolean>(false);
  const [repoName, setRepoName] = useState<string>(defaultRepoName);
  const [createNew, setCreateNew] = useState<boolean>(true);
  const [isPrivate, setIsPrivate] = useState<boolean>(false);
  const [isPushing, setIsPushing] = useState<boolean>(false);
  const [pushResult, setPushResult] = useState<GitHubPushResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  React.useEffect(() => {
    if (isOpen) {
      setRepoName(defaultRepoName);
      setPushResult(null);
      setErrorMessage(null);
    }
  }, [isOpen, defaultRepoName]);

  if (!isOpen) return null;

  const handlePushSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pipeline?.project_dir) {
      setErrorMessage('No active project directory available to push.');
      return;
    }
    if (!token.trim()) {
      setErrorMessage('GitHub Personal Access Token is required.');
      return;
    }
    if (!repoName.trim()) {
      setErrorMessage('Target repository name is required.');
      return;
    }

    setIsPushing(true);
    setErrorMessage(null);
    setPushResult(null);

    try {
      const res = await fetch('/api/git/push-github', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          projectDir: pipeline.project_dir,
          token: token.trim(),
          repoName: repoName.trim(),
          createNew,
          isPrivate
        })
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || 'Failed to push repository to GitHub.');
      }

      setPushResult(data);
    } catch (err: any) {
      console.error('GitHub push error:', err);
      setErrorMessage(err.message || 'An unexpected error occurred during the GitHub push.');
    } finally {
      setIsPushing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-900/60 backdrop-blur-xs p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl border border-zinc-200 shadow-2xl max-w-lg w-full overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-zinc-100 flex items-center justify-between bg-zinc-50/70">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-zinc-900 text-white flex items-center justify-center">
              <Github className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-zinc-900">
                Push to GitHub
              </h3>
              <p className="text-[11px] text-zinc-500">
                Publish repository with complete atomic commit history
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-600 p-1 rounded-lg hover:bg-zinc-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5">
          {/* Success State Banner */}
          {pushResult && (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/70 p-4 space-y-3">
              <div className="flex items-start space-x-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-bold text-emerald-900">
                    Repository Successfully Published!
                  </h4>
                  <p className="text-xs text-emerald-800 mt-0.5">
                    {pushResult.message || `Successfully pushed ${pushResult.commits_pushed ?? 0} commits to GitHub.`}
                  </p>
                </div>
              </div>

              {pushResult.repo_url && (
                <div className="pt-2 flex items-center space-x-3">
                  <a
                    href={pushResult.repo_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs transition-colors"
                  >
                    <span>View Repository on GitHub</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                  <button
                    type="button"
                    onClick={onClose}
                    className="text-xs text-emerald-800 hover:text-emerald-950 font-medium"
                  >
                    Close
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Error Message */}
          {errorMessage && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-3.5 text-xs text-rose-800 space-y-1">
              <div className="flex items-center space-x-2 font-bold text-rose-900">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>GitHub Push Failed</span>
              </div>
              <p className="pl-6 text-zinc-700">{errorMessage}</p>
              <div className="pl-6 pt-1 text-[11px] text-zinc-500">
                Troubleshooting: Ensure your token has the <code className="bg-rose-100 px-1 py-0.5 rounded text-rose-900 font-mono">repo</code> scope checked and that your account has write permissions.
              </div>
            </div>
          )}

          {!pushResult && (
            <form onSubmit={handlePushSubmit} className="space-y-4">
              {/* Commit count badge */}
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-zinc-50 border border-zinc-200 text-xs">
                <span className="text-zinc-600 flex items-center space-x-1.5">
                  <FolderGit2 className="w-4 h-4 text-indigo-600" />
                  <span>Staged Commits:</span>
                </span>
                <span className="font-bold font-mono text-zinc-900">
                  {pipeline?.git_commits?.length || 0} autonomous atomic commits
                </span>
              </div>

              {/* Personal Access Token (Masked input) */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-zinc-800 flex items-center justify-between">
                  <span className="flex items-center space-x-1.5">
                    <Key className="w-3.5 h-3.5 text-indigo-600" />
                    <span>GitHub Personal Access Token (PAT):</span>
                  </span>
                  <a
                    href="https://github.com/settings/tokens/new?scopes=repo"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] text-indigo-600 hover:text-indigo-800 flex items-center space-x-1"
                  >
                    <span>Generate token</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                </label>
                <div className="relative">
                  <input
                    type={showToken ? 'text' : 'password'}
                    id="github-pat-input"
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    disabled={isPushing}
                    required
                    placeholder="ghp_xxxxxxxxxxxxxxxxxxxx or github_pat_..."
                    className="w-full text-xs font-mono bg-zinc-50 border border-zinc-200 rounded-lg py-2.5 pl-3 pr-10 text-zinc-900 placeholder-zinc-400 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:bg-white"
                  />
                  <button
                    type="button"
                    onClick={() => setShowToken(!showToken)}
                    className="absolute right-2.5 top-2.5 text-zinc-400 hover:text-zinc-600"
                    title={showToken ? 'Hide token' : 'Show token'}
                  >
                    {showToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                <p className="text-[11px] text-zinc-400">
                  Requires <code className="bg-zinc-100 text-zinc-700 px-1 py-0.5 rounded font-mono">repo</code> scope. Your token is transmitted securely over HTTPS and never stored on the server.
                </p>
              </div>

              {/* Target Repository Name */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-zinc-800 flex items-center space-x-1.5">
                  <FolderGit2 className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Target Repository Name:</span>
                </label>
                <input
                  type="text"
                  id="github-repo-name-input"
                  value={repoName}
                  onChange={(e) => setRepoName(e.target.value)}
                  disabled={isPushing}
                  required
                  placeholder="e.g. cli-calculator or owner/repo"
                  className="w-full text-xs font-mono bg-zinc-50 border border-zinc-200 rounded-lg py-2.5 px-3 text-zinc-900 placeholder-zinc-400 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:bg-white"
                />
              </div>

              {/* Repository Creation Option */}
              <div className="space-y-2 pt-1">
                <span className="text-xs font-semibold text-zinc-700 block">Repository Destination:</span>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <label
                    className={`flex items-center space-x-2 p-2.5 rounded-lg border cursor-pointer transition-all ${
                      createNew
                        ? 'border-indigo-500 bg-indigo-50/50 text-indigo-900 font-medium ring-1 ring-indigo-500'
                        : 'border-zinc-200 bg-zinc-50 text-zinc-600'
                    }`}
                  >
                    <input
                      type="radio"
                      name="repoMode"
                      checked={createNew}
                      onChange={() => setCreateNew(true)}
                      className="text-indigo-600"
                    />
                    <span>Create new repo</span>
                  </label>

                  <label
                    className={`flex items-center space-x-2 p-2.5 rounded-lg border cursor-pointer transition-all ${
                      !createNew
                        ? 'border-indigo-500 bg-indigo-50/50 text-indigo-900 font-medium ring-1 ring-indigo-500'
                        : 'border-zinc-200 bg-zinc-50 text-zinc-600'
                    }`}
                  >
                    <input
                      type="radio"
                      name="repoMode"
                      checked={!createNew}
                      onChange={() => setCreateNew(false)}
                      className="text-indigo-600"
                    />
                    <span>Push to existing repo</span>
                  </label>
                </div>
              </div>

              {/* Public vs Private toggle if createNew is true */}
              {createNew && (
                <div className="flex items-center space-x-4 pt-1 text-xs">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isPrivate}
                      onChange={(e) => setIsPrivate(e.target.checked)}
                      className="rounded border-zinc-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="flex items-center space-x-1 font-medium text-zinc-700">
                      {isPrivate ? <Lock className="w-3.5 h-3.5 text-zinc-500" /> : <Globe className="w-3.5 h-3.5 text-zinc-500" />}
                      <span>Make repository Private</span>
                    </span>
                  </label>
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-3 flex items-center justify-end space-x-2.5 border-t border-zinc-100">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isPushing}
                  className="px-4 py-2 text-xs font-medium text-zinc-600 hover:text-zinc-800 rounded-lg hover:bg-zinc-100 transition-colors"
                >
                  Cancel
                </button>

                <button
                  id="github-submit-push-btn"
                  type="submit"
                  disabled={isPushing || !token.trim() || !repoName.trim()}
                  className="inline-flex items-center space-x-2 px-5 py-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
                >
                  {isPushing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin text-white" />
                      <span>Pushing Git Tree...</span>
                    </>
                  ) : (
                    <>
                      <Github className="w-4 h-4" />
                      <span>Push to GitHub</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
