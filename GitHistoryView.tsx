import React, { useState } from 'react';
import { GitCommit as GitCommitIcon, Download, FileText, ChevronRight, Check, Sparkles, Eye, X, Github } from 'lucide-react';
import { GitCommit } from '../types';

interface GitHistoryViewProps {
  commits: GitCommit[];
  projectDir: string;
  onExportZip: () => void;
  onOpenGitHubModal?: () => void;
}

export const GitHistoryView: React.FC<GitHistoryViewProps> = ({
  commits,
  projectDir,
  onExportZip,
  onOpenGitHubModal
}) => {
  const [selectedCommit, setSelectedCommit] = useState<GitCommit | null>(
    commits[0] || null
  );
  const [diffContent, setDiffContent] = useState<string>('');
  const [isLoadingDiff, setIsLoadingDiff] = useState<boolean>(false);

  const handleInspectCommit = async (commit: GitCommit) => {
    setSelectedCommit(commit);
    if (!projectDir) return;

    setIsLoadingDiff(true);
    try {
      const res = await fetch(`/api/git/diff?projectDir=${encodeURIComponent(projectDir)}&commitHash=${encodeURIComponent(commit.hash)}`);
      const data = await res.json();
      setDiffContent(data.diff || 'No diff content available.');
    } catch (err) {
      setDiffContent('Error fetching unified diff for commit.');
    } finally {
      setIsLoadingDiff(false);
    }
  };

  if (!commits || commits.length === 0) {
    return (
      <div className="bg-white border border-zinc-200 rounded-xl p-8 text-center text-zinc-500">
        <GitCommitIcon className="w-8 h-8 text-zinc-400 mx-auto mb-2" />
        <p className="text-sm">Git repository history is empty.</p>
        <p className="text-xs text-zinc-400 mt-1">Run the pipeline to generate staged commits across agents.</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-zinc-200 rounded-xl p-5 sm:p-6 shadow-xs space-y-6">
      {/* Header & Export CTA */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-100 pb-4">
        <div>
          <div className="flex items-center space-x-2 text-indigo-600 mb-1">
            <GitCommitIcon className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wider">
              Git Version Control & Provenance
            </span>
          </div>
          <h3 className="text-lg font-bold text-zinc-900 tracking-tight">
            Atomic Stage Commit Timeline ({commits.length} commits)
          </h3>
          <p className="text-xs text-zinc-600 mt-0.5">
            Every autonomous agent commits isolated deliverables under its verified persona.
          </p>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          {onOpenGitHubModal && (
            <button
              id="git-push-github-btn"
              onClick={onOpenGitHubModal}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-lg border border-zinc-300 bg-white hover:bg-zinc-50 text-zinc-800 text-xs font-semibold shadow-2xs transition-all"
            >
              <Github className="w-3.5 h-3.5" />
              <span>Push to GitHub</span>
            </button>
          )}

          <button
            id="git-download-full-repo-btn"
            onClick={onExportZip}
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Repo (.ZIP)</span>
          </button>
        </div>
      </div>

      {/* Grid: Commit List on Left, Diff Viewer on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Commits List (5 cols) */}
        <div className="lg:col-span-5 space-y-2.5">
          <span className="text-xs font-bold text-zinc-500 uppercase tracking-wider block mb-1">
            Commit Log
          </span>
          <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
            {commits.map((commit, idx) => {
              const isSelected = selectedCommit?.hash === commit.hash;
              return (
                <div
                  key={commit.hash || idx}
                  onClick={() => handleInspectCommit(commit)}
                  className={`p-3 rounded-lg border text-left cursor-pointer transition-all ${
                    isSelected
                      ? 'border-indigo-500 bg-indigo-50/60 shadow-2xs'
                      : 'border-zinc-200 bg-zinc-50/40 hover:bg-zinc-100/60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center space-x-1.5">
                      <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-100/70 px-1.5 py-0.5 rounded">
                        {commit.short_hash}
                      </span>
                      <span className="text-[11px] font-semibold text-zinc-800">
                        {commit.stage}
                      </span>
                    </div>
                    <span className="text-[10px] text-zinc-400 font-mono">
                      {commit.timestamp ? new Date(commit.timestamp).toLocaleTimeString() : ''}
                    </span>
                  </div>

                  <p className="text-xs font-medium text-zinc-800 mb-1.5 line-clamp-1">
                    {commit.message}
                  </p>

                  <div className="flex items-center justify-between text-[11px] text-zinc-500">
                    <span>By: <strong className="text-zinc-700 font-normal">{commit.author}</strong></span>
                    {commit.files_changed?.length > 0 && (
                      <span className="text-[10px] bg-zinc-200/60 px-1.5 py-0.5 rounded font-mono">
                        {commit.files_changed.length} files
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Diff & Commit Details (7 cols) */}
        <div className="lg:col-span-7 flex flex-col">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-zinc-500 uppercase tracking-wider">
              Unified Git Diff Inspector
            </span>
            {selectedCommit && (
              <span className="text-xs font-mono text-zinc-600">
                Commit: <strong>{selectedCommit.short_hash}</strong>
              </span>
            )}
          </div>

          <div className="border border-zinc-800 rounded-xl overflow-hidden bg-zinc-950 flex-1 flex flex-col min-h-[380px]">
            {/* Diff Header */}
            <div className="bg-zinc-900 px-4 py-2.5 border-b border-zinc-800 flex items-center justify-between text-xs text-zinc-300 font-mono">
              <span className="truncate max-w-[320px]">
                {selectedCommit?.message || 'Select a commit to view unified patch'}
              </span>
              <span className="text-zinc-500 text-[11px]">
                Author: {selectedCommit?.author}
              </span>
            </div>

            {/* Changed files chips */}
            {selectedCommit?.files_changed && selectedCommit.files_changed.length > 0 && (
              <div className="bg-zinc-900/40 px-4 py-2 border-b border-zinc-800/80 flex flex-wrap gap-1.5">
                {selectedCommit.files_changed.map((f, i) => (
                  <span key={i} className="text-[11px] font-mono text-zinc-300 bg-zinc-800 px-2 py-0.5 rounded">
                    {f}
                  </span>
                ))}
              </div>
            )}

            {/* Diff Text */}
            <div className="p-4 flex-1 overflow-auto max-h-[420px] font-mono text-xs leading-5">
              {isLoadingDiff ? (
                <div className="text-zinc-500 flex items-center justify-center h-48 space-x-2">
                  <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                  <span>Loading commit diff...</span>
                </div>
              ) : diffContent ? (
                <pre className="text-zinc-300 whitespace-pre">
                  {diffContent.split('\n').map((line, idx) => {
                    let lineClass = 'text-zinc-300';
                    if (line.startsWith('+') && !line.startsWith('+++')) {
                      lineClass = 'text-emerald-400 bg-emerald-950/30';
                    } else if (line.startsWith('-') && !line.startsWith('---')) {
                      lineClass = 'text-rose-400 bg-rose-950/30';
                    } else if (line.startsWith('@@')) {
                      lineClass = 'text-indigo-400 font-bold';
                    } else if (line.startsWith('diff ') || line.startsWith('index ')) {
                      lineClass = 'text-zinc-500 font-semibold';
                    }
                    return (
                      <div key={idx} className={`${lineClass} px-1 rounded-2xs`}>
                        {line}
                      </div>
                    );
                  })}
                </pre>
              ) : (
                <div className="text-zinc-500 text-center py-20">
                  Click any commit on the left to inspect its unified diff patch.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
