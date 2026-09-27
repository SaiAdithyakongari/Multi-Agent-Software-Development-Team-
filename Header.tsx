import React from 'react';
import { Bot, Terminal, Download, Cpu, ShieldCheck, RefreshCw, Github, Settings } from 'lucide-react';
import { PipelineState } from '../types';

interface HeaderProps {
  pipeline: PipelineState | null;
  isRunning: boolean;
  provider: string;
  onProviderChange: (provider: string) => void;
  onExportZip: () => void;
  onOpenGitHubModal?: () => void;
  onRunPytest: () => void;
  isTesting: boolean;
  onOpenSettings?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  pipeline,
  isRunning,
  provider,
  onProviderChange,
  onExportZip,
  onOpenGitHubModal,
  onRunPytest,
  isTesting,
  onOpenSettings
}) => {
  const testsPassed = pipeline?.test_result?.tests_passed ?? 0;
  const testsTotal = pipeline?.test_result?.tests_total ?? 0;
  const commitsCount = pipeline?.git_commits?.length ?? 0;
  const isComplete = pipeline?.current_stage === 'Completed';

  return (
    <header className="border-b border-zinc-200 bg-white/90 backdrop-blur-md sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo & Title */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-700 flex items-center justify-center text-white shadow-md shadow-indigo-100">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-bold text-zinc-900 tracking-tight">
                Multi-Agent Software Engineering Team
              </h1>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
                LangGraph v0.2
              </span>
            </div>
            <p className="text-xs text-zinc-500 hidden sm:block">
              Autonomous 7-Agent SDLC • Git Versioned • Sandbox Verified
            </p>
          </div>
        </div>

        {/* Status Metrics & Actions */}
        <div className="flex items-center space-x-3">
          {/* Quick Stats if pipeline ran */}
          {pipeline && (
            <div className="hidden md:flex items-center space-x-2 text-xs bg-zinc-50 border border-zinc-200 rounded-lg px-2.5 py-1.5">
              <span className="flex items-center space-x-1 text-emerald-700 font-medium">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Pytest: {testsPassed}/{testsTotal} Passed</span>
              </span>
              <span className="text-zinc-300">|</span>
              <span className="text-zinc-600 font-medium">
                {commitsCount} Commits
              </span>
            </div>
          )}

          {/* Model Provider Toggle */}
          <div className="flex items-center bg-zinc-100 p-0.5 rounded-lg border border-zinc-200 text-xs">
            <button
              id="provider-deterministic-btn"
              onClick={() => onProviderChange('deterministic')}
              className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                provider === 'deterministic'
                  ? 'bg-white text-zinc-900 shadow-xs'
                  : 'text-zinc-500 hover:text-zinc-800'
              }`}
              title="Fast, deterministic, guaranteed 100% test pass rate with zero API key requirement"
            >
              <span className="flex items-center space-x-1">
                <Cpu className="w-3 h-3 text-indigo-600" />
                <span>Deterministic</span>
              </span>
            </button>
            <button
              id="provider-gemini-btn"
              onClick={() => onProviderChange('gemini')}
              className={`px-2.5 py-1 rounded-md font-medium transition-all ${
                provider === 'gemini'
                  ? 'bg-white text-zinc-900 shadow-xs'
                  : 'text-zinc-500 hover:text-zinc-800'
              }`}
              title="Google Gemini Flash 2.5 generative reasoning"
            >
              <span className="flex items-center space-x-1">
                <Bot className="w-3 h-3 text-violet-600" />
                <span>Gemini AI</span>
              </span>
            </button>
          </div>

          {/* Re-run Sandbox Button */}
          {pipeline && (
            <button
              id="header-rerun-sandbox-btn"
              onClick={onRunPytest}
              disabled={isTesting || isRunning}
              className="hidden sm:inline-flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-zinc-200 bg-white hover:bg-zinc-50 text-zinc-700 shadow-xs transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isTesting ? 'animate-spin text-indigo-600' : 'text-zinc-500'}`} />
              <span>{isTesting ? 'Testing...' : 'Verify Sandbox'}</span>
            </button>
          )}

          {/* Settings Button */}
          {onOpenSettings && (
            <button
              id="header-settings-btn"
              onClick={onOpenSettings}
              className="inline-flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-zinc-200 bg-white hover:bg-zinc-50 text-zinc-700 shadow-xs transition-all"
              title="Configure pipeline features and settings"
            >
              <Settings className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Settings</span>
            </button>
          )}

          {/* Download Zip CTA */}
          {pipeline?.project_dir && (
            <div className="flex items-center space-x-2">
              {onOpenGitHubModal && (
                <button
                  id="header-push-github-btn"
                  onClick={onOpenGitHubModal}
                  className="inline-flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded-lg border border-zinc-200 bg-white hover:bg-zinc-50 text-zinc-800 shadow-2xs transition-all"
                  title="Push generated project with full Git history to your GitHub account"
                >
                  <Github className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Push to</span>
                  <span>GitHub</span>
                </button>
              )}

              <button
                id="header-download-zip-btn"
                onClick={onExportZip}
                className="inline-flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs transition-all"
              >
                <Download className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Export Repo</span>
                <span>.ZIP</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
