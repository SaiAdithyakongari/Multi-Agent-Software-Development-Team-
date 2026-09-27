import React, { useState } from 'react';
import { Copy, Check, FileCode, Play, Terminal, Download } from 'lucide-react';
import { AgentReasoningSection } from './AgentReasoningSection';

interface CodeExplorerProps {
  codeFiles: Record<string, string>;
  testFiles: Record<string, string>;
  onRunSandbox: () => void;
  isTesting: boolean;
  reasoning?: string;
}

export const CodeExplorer: React.FC<CodeExplorerProps> = ({
  codeFiles,
  testFiles,
  onRunSandbox,
  isTesting,
  reasoning
}) => {
  const allFiles: Record<string, { content: string; type: 'code' | 'test' }> = {};

  Object.entries(codeFiles || {}).forEach(([name, content]) => {
    allFiles[name] = { content: String(content || ''), type: 'code' };
  });

  Object.entries(testFiles || {}).forEach(([name, content]) => {
    allFiles[name] = { content: String(content || ''), type: 'test' };
  });

  const fileNames = Object.keys(allFiles);
  const [selectedFile, setSelectedFile] = useState<string>(
    fileNames[0] || 'core.py'
  );
  const [copied, setCopied] = useState<boolean>(false);

  const activeContent = allFiles[selectedFile]?.content || '# No content available.';

  const handleCopy = () => {
    navigator.clipboard.writeText(activeContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lineCount = activeContent.split('\n').length;
  const charCount = activeContent.length;

  return (
    <div className="space-y-4">
      {/* Agent Reasoning for Code Generation */}
      <AgentReasoningSection
        agentName="Code Generation Agent"
        stageName="Code Generation"
        reasoning={reasoning}
      />

      <div className="bg-white border border-zinc-200 rounded-xl overflow-hidden shadow-xs flex flex-col h-full">
        {/* File Tabs & Actions Toolbar */}
        <div className="bg-zinc-100/80 border-b border-zinc-200 px-4 py-2.5 flex flex-wrap items-center justify-between gap-2">
        {/* File Tabs */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 sm:pb-0">
          {fileNames.map((name) => {
            const isSelected = selectedFile === name;
            const isTest = allFiles[name]?.type === 'test';
            return (
              <button
                key={name}
                id={`file-tab-${name}`}
                onClick={() => setSelectedFile(name)}
                className={`flex items-center space-x-1.5 text-xs px-3 py-1.5 rounded-md font-mono transition-all ${
                  isSelected
                    ? 'bg-white text-zinc-900 shadow-xs font-semibold border border-zinc-200/80'
                    : 'text-zinc-600 hover:text-zinc-900 hover:bg-zinc-200/60'
                }`}
              >
                <FileCode className={`w-3.5 h-3.5 ${isTest ? 'text-amber-600' : 'text-indigo-600'}`} />
                <span>{name}</span>
                {isTest && (
                  <span className="text-[9px] bg-amber-100 text-amber-800 px-1 rounded font-sans font-bold">
                    TEST
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Toolbar Actions */}
        <div className="flex items-center space-x-2 text-xs">
          <span className="text-zinc-400 font-mono text-[11px] hidden sm:inline">
            {lineCount} lines • {charCount} chars
          </span>

          <button
            id="code-copy-btn"
            onClick={handleCopy}
            className="flex items-center space-x-1 px-2.5 py-1 rounded bg-white hover:bg-zinc-50 border border-zinc-200 text-zinc-700 shadow-2xs transition-all"
            title="Copy source code to clipboard"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-emerald-700 font-medium">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-zinc-500" />
                <span>Copy</span>
              </>
            )}
          </button>

          <button
            id="code-run-sandbox-btn"
            onClick={onRunSandbox}
            disabled={isTesting}
            className="flex items-center space-x-1 px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-700 text-white font-medium shadow-2xs transition-all disabled:opacity-50"
            title="Execute test suite in isolated sandbox"
          >
            <Play className="w-3 h-3 fill-white" />
            <span>{isTesting ? 'Running Pytest...' : 'Run Pytest'}</span>
          </button>
        </div>
      </div>

      {/* Code Viewer with Line Numbers */}
      <div className="relative flex-1 bg-zinc-950 font-mono text-xs overflow-auto max-h-[560px] min-h-[400px]">
        <div className="flex min-w-full">
          {/* Line Numbers column */}
          <div className="select-none py-4 px-3 bg-zinc-900/60 border-r border-zinc-800/80 text-zinc-600 text-right font-mono min-w-[48px]">
            {activeContent.split('\n').map((_, i) => (
              <div key={i} className="leading-5">
                {i + 1}
              </div>
            ))}
          </div>

          {/* Code Body */}
          <pre className="p-4 text-zinc-200 leading-5 overflow-x-auto flex-1 font-mono whitespace-pre selection:bg-indigo-900/60">
            <code>{activeContent}</code>
          </pre>
        </div>
      </div>

      {/* Code Explorer Footer */}
      <div className="bg-zinc-900 border-t border-zinc-800 px-4 py-2 flex items-center justify-between text-[11px] text-zinc-400 font-mono">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
          <span>Python 3.10+ PEP-8 Clean Architecture</span>
        </div>
        <div>
          Current: <span className="text-zinc-200 font-semibold">{selectedFile}</span>
        </div>
      </div>
    </div>
  </div>
  );
};
