import React from 'react';
import { FlaskConical, CheckCircle2, XCircle, Clock, Terminal, Play, RotateCw, Wrench, ShieldAlert } from 'lucide-react';
import { TestResult, BugFixEntry } from '../types';
import { AgentReasoningSection } from './AgentReasoningSection';

interface TestSandboxViewProps {
  testResult: TestResult | null;
  onRunPytest: () => void;
  isTesting: boolean;
  bugfixHistory?: BugFixEntry[];
}

export const TestSandboxView: React.FC<TestSandboxViewProps> = ({
  testResult,
  onRunPytest,
  isTesting,
  bugfixHistory = []
}) => {
  if (!testResult) {
    return (
      <div className="bg-white border border-zinc-200 rounded-xl p-8 text-center text-zinc-500">
        <FlaskConical className="w-8 h-8 text-zinc-400 mx-auto mb-2" />
        <p className="text-sm">Sandbox test suite has not been executed yet.</p>
        <p className="text-xs text-zinc-400 mt-1">Run the pipeline to trigger automated pytest execution.</p>
      </div>
    );
  }

  const passRate =
    testResult.tests_total > 0
      ? Math.round((testResult.tests_passed / testResult.tests_total) * 100)
      : 0;

  const latestBugfix = bugfixHistory.length > 0 ? bugfixHistory[bugfixHistory.length - 1] : null;

  return (
    <div className="space-y-6">
      {/* Agent Reasoning: Test & Verification Agent */}
      <AgentReasoningSection
        agentName="Test & Verification Agent"
        stageName="Test Automation"
        reasoning={testResult.reasoning}
      />

      {/* Agent Reasoning: Bug-Fix Loop Agent (if bugfix occurred or reasoning available) */}
      {latestBugfix?.reasoning && (
        <AgentReasoningSection
          agentName="Autonomous Bug-Fix Agent"
          stageName="Bug-Fix Loop"
          reasoning={latestBugfix.reasoning}
        />
      )}

      <div className="bg-white border border-zinc-200 rounded-xl p-5 sm:p-6 shadow-xs space-y-5">
        {/* Header with status & rerun CTA */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-100 pb-4">
          <div>
            <div className="flex items-center space-x-2 text-indigo-600 mb-1">
              <FlaskConical className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">
                Pytest Automated Sandbox Environment
              </span>
            </div>
            <h3 className="text-lg font-bold text-zinc-900 tracking-tight flex items-center space-x-2">
              <span>Test Suite Verification Dashboard</span>
              {testResult.success ? (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>ALL TESTS PASSED</span>
                </span>
              ) : (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800">
                  <XCircle className="w-3.5 h-3.5" />
                  <span>TEST FAILURES DETECTED</span>
                </span>
              )}
            </h3>
            <p className="text-xs text-zinc-600 mt-0.5">
              Isolated execution container running real Python pytest assertions.
            </p>
          </div>

          <button
            id="sandbox-rerun-btn"
            onClick={onRunPytest}
            disabled={isTesting}
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-all disabled:opacity-50 shrink-0"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isTesting ? 'animate-spin' : ''}`} />
            <span>{isTesting ? 'Running Pytest...' : 'Execute Pytest Again'}</span>
          </button>
        </div>

        {/* BugFix Iteration summary badge if any */}
        {bugfixHistory.length > 0 && (
          <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-lg text-xs space-y-1">
            <div className="flex items-center justify-between text-amber-900 font-bold">
              <span className="flex items-center space-x-1.5">
                <Wrench className="w-3.5 h-3.5 text-amber-600" />
                <span>Autonomous Self-Healing Bug-Fix Cycle ({bugfixHistory.length} iterations)</span>
              </span>
              <span className="font-mono text-[11px] bg-amber-200/80 px-2 py-0.5 rounded">
                Test Pass Before: {latestBugfix?.test_pass_before} → After: {latestBugfix?.test_pass_after}
              </span>
            </div>
            {latestBugfix?.diagnosis && (
              <p className="text-zinc-600 text-[11px]">
                <strong className="text-zinc-800">Diagnosis:</strong> {latestBugfix.diagnosis}
              </p>
            )}
          </div>
        )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-lg bg-zinc-50 border border-zinc-200">
          <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider block">
            Tests Passed
          </span>
          <div className="flex items-baseline space-x-1.5 mt-1">
            <span className="text-2xl font-bold font-mono text-emerald-600">
              {testResult.tests_passed}
            </span>
            <span className="text-xs text-zinc-400 font-mono">/ {testResult.tests_total}</span>
          </div>
        </div>

        <div className="p-3.5 rounded-lg bg-zinc-50 border border-zinc-200">
          <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider block">
            Failed / Errored
          </span>
          <div className="flex items-baseline space-x-1.5 mt-1">
            <span className={`text-2xl font-bold font-mono ${testResult.tests_failed > 0 ? 'text-rose-600' : 'text-zinc-700'}`}>
              {testResult.tests_failed}
            </span>
            <span className="text-xs text-zinc-400 font-mono">failed</span>
          </div>
        </div>

        <div className="p-3.5 rounded-lg bg-zinc-50 border border-zinc-200">
          <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider block">
            Pass Rate
          </span>
          <div className="flex items-baseline space-x-1 mt-1">
            <span className="text-2xl font-bold font-mono text-indigo-600">
              {passRate}%
            </span>
          </div>
        </div>

        <div className="p-3.5 rounded-lg bg-zinc-50 border border-zinc-200">
          <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider block">
            Execution Duration
          </span>
          <div className="flex items-center space-x-1.5 mt-1 text-zinc-800">
            <Clock className="w-4 h-4 text-zinc-500" />
            <span className="text-xl font-bold font-mono">
              {testResult.duration_seconds.toFixed(2)}s
            </span>
          </div>
        </div>
      </div>

      {/* Pass Rate Progress Bar */}
      <div>
        <div className="flex justify-between text-xs text-zinc-600 mb-1">
          <span>Pytest Verification Progress</span>
          <span className="font-mono font-bold text-zinc-900">{passRate}% Complete</span>
        </div>
        <div className="w-full h-2 bg-zinc-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              testResult.success ? 'bg-emerald-500' : 'bg-rose-500'
            }`}
            style={{ width: `${passRate}%` }}
          />
        </div>
      </div>

      {/* Terminal Sandbox Execution Output */}
      <div className="rounded-xl overflow-hidden border border-zinc-800 bg-zinc-950 font-mono text-xs shadow-inner">
        <div className="bg-zinc-900 px-4 py-2 border-b border-zinc-800 flex items-center justify-between text-zinc-400">
          <div className="flex items-center space-x-2">
            <Terminal className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-[11px] font-bold tracking-wider">PYTEST SANDBOX EXECUTION LOGS</span>
          </div>
          <span className="text-[10px] text-zinc-500">pytest -v test_suite.py</span>
        </div>

        <pre className="p-4 text-zinc-300 leading-relaxed overflow-x-auto max-h-80 whitespace-pre-wrap selection:bg-indigo-900/80">
          {testResult.stdout || testResult.stderr || 'No stdout output produced.'}
        </pre>

        {testResult.stderr && testResult.stderr.trim() && (
          <div className="border-t border-zinc-800 p-4 bg-rose-950/20 text-rose-300">
            <span className="text-rose-400 font-bold block mb-1">Standard Error (stderr):</span>
            <pre className="text-xs whitespace-pre-wrap">{testResult.stderr}</pre>
          </div>
        )}
      </div>
    </div>
  </div>
  );
};
