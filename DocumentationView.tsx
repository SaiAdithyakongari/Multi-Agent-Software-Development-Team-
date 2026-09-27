import React, { useState } from 'react';
import { BookOpen, Terminal, CheckCircle2, Copy, Check } from 'lucide-react';
import { DocumentationBundle } from '../types';
import { AgentReasoningSection } from './AgentReasoningSection';

interface DocumentationViewProps {
  docs: DocumentationBundle | null;
}

export const DocumentationView: React.FC<DocumentationViewProps> = ({ docs }) => {
  const [copied, setCopied] = useState<boolean>(false);

  if (!docs) {
    return (
      <div className="bg-white border border-zinc-200 rounded-xl p-8 text-center text-zinc-500">
        <BookOpen className="w-8 h-8 text-zinc-400 mx-auto mb-2" />
        <p className="text-sm">Documentation bundle has not been generated yet.</p>
        <p className="text-xs text-zinc-400 mt-1">Run the pipeline to activate the Documentation & Release Agent.</p>
      </div>
    );
  }

  const handleCopyReadme = () => {
    navigator.clipboard.writeText(docs.readme || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white border border-zinc-200 rounded-xl p-5 sm:p-6 shadow-xs space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-100 pb-4">
        <div>
          <div className="flex items-center space-x-2 text-indigo-600 mb-1">
            <BookOpen className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wider">
              Documentation & Packaging Agent
            </span>
          </div>
          <h3 className="text-lg font-bold text-zinc-900 tracking-tight">
            Generated Project Documentation & Developer Guides
          </h3>
          <p className="text-xs text-zinc-600 mt-0.5">
            Auto-generated comprehensive README, setup instructions, and release build manifest.
          </p>
        </div>

        <button
          id="docs-copy-readme-btn"
          onClick={handleCopyReadme}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-zinc-200 bg-white hover:bg-zinc-50 text-zinc-700 text-xs font-medium shadow-2xs transition-all shrink-0"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-600" />
              <span className="text-emerald-700 font-medium">Copied README</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5 text-zinc-500" />
              <span>Copy README.md</span>
            </>
          )}
        </button>
      </div>

      {/* Agent Reasoning Section */}
      <AgentReasoningSection
        agentName="Documentation & Release Agent"
        stageName="Documentation"
        reasoning={docs.reasoning}
      />

      {/* Build Summary Metrics */}
      {docs.build_summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3 bg-zinc-50 border border-zinc-200 rounded-lg">
            <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider block">
              Total Modules
            </span>
            <span className="text-xl font-bold font-mono text-zinc-900 mt-0.5 block">
              {docs.build_summary.total_modules}
            </span>
          </div>

          <div className="p-3 bg-zinc-50 border border-zinc-200 rounded-lg">
            <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider block">
              Stages Completed
            </span>
            <span className="text-xl font-bold font-mono text-indigo-600 mt-0.5 block">
              {docs.build_summary.pipeline_stages_completed} / 7
            </span>
          </div>

          <div className="p-3 bg-zinc-50 border border-zinc-200 rounded-lg">
            <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider block">
              Test Pass Rate
            </span>
            <span className="text-xl font-bold font-mono text-emerald-600 mt-0.5 block">
              {docs.build_summary.test_pass_rate}
            </span>
          </div>

          <div className="p-3 bg-zinc-50 border border-zinc-200 rounded-lg">
            <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider block">
              Git Commits
            </span>
            <span className="text-xl font-bold font-mono text-zinc-900 mt-0.5 block">
              {docs.build_summary.git_commits_created}
            </span>
          </div>
        </div>
      )}

      {/* Quick Setup Instructions */}
      {docs.setup_instructions && (
        <div className="p-4 rounded-lg bg-zinc-900 text-zinc-200 font-mono text-xs border border-zinc-800">
          <div className="flex items-center space-x-2 text-indigo-400 mb-2 font-sans font-semibold text-xs uppercase tracking-wider">
            <Terminal className="w-3.5 h-3.5" />
            <span>Developer Setup & Quickstart</span>
          </div>
          <pre className="p-3 bg-zinc-950 rounded border border-zinc-800 text-zinc-300 whitespace-pre-wrap">
            {docs.setup_instructions}
          </pre>
        </div>
      )}

      {/* Module Descriptions */}
      {docs.module_documentation && Object.keys(docs.module_documentation).length > 0 && (
        <div>
          <h4 className="text-xs font-bold text-zinc-900 uppercase tracking-wider mb-2">
            Module API Reference
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {Object.entries(docs.module_documentation).map(([mod, desc]) => (
              <div key={mod} className="p-3 rounded-lg border border-zinc-200 bg-zinc-50/50">
                <span className="text-xs font-mono font-bold text-indigo-700 block mb-1">
                  {mod}
                </span>
                <p className="text-xs text-zinc-600 leading-relaxed">
                  {desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* README Preview */}
      <div>
        <h4 className="text-xs font-bold text-zinc-900 uppercase tracking-wider mb-2">
          README.md File Preview
        </h4>
        <div className="border border-zinc-200 rounded-lg p-5 bg-zinc-50/30 text-xs font-mono whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto">
          {docs.readme}
        </div>
      </div>
    </div>
  );
};
