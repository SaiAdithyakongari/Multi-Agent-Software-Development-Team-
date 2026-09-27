import React from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, ShieldCheck, Sparkles } from 'lucide-react';
import { CodeReviewDoc } from '../types';
import { AgentReasoningSection } from './AgentReasoningSection';

interface CodeReviewViewProps {
  doc: CodeReviewDoc | null;
}

export const CodeReviewView: React.FC<CodeReviewViewProps> = ({ doc }) => {
  if (!doc) {
    return (
      <div className="bg-white border border-zinc-200 rounded-xl p-8 text-center text-zinc-500">
        <ShieldCheck className="w-8 h-8 text-zinc-400 mx-auto mb-2" />
        <p className="text-sm">Code review audit has not been conducted yet.</p>
        <p className="text-xs text-zinc-400 mt-1">Run the pipeline to activate the Code Review Agent.</p>
      </div>
    );
  }

  const scoreColor =
    doc.overall_score >= 8.5
      ? 'text-emerald-600 border-emerald-200 bg-emerald-50'
      : doc.overall_score >= 7.0
      ? 'text-amber-600 border-amber-200 bg-amber-50'
      : 'text-rose-600 border-rose-200 bg-rose-50';

  return (
    <div className="bg-white border border-zinc-200 rounded-xl p-5 sm:p-6 shadow-xs space-y-6">
      {/* Top Banner: Score & Verdict */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-100 pb-5">
        <div>
          <div className="flex items-center space-x-2 text-indigo-600 mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wider">
              Code Review & Security Audit Agent
            </span>
          </div>
          <h3 className="text-lg font-bold text-zinc-900 tracking-tight">
            Comprehensive Static & Architectural Audit Report
          </h3>
          <p className="text-xs text-zinc-600 mt-1">
            {doc.summary}
          </p>
        </div>

        {/* Score & Verdict Badges */}
        <div className="flex items-center space-x-3">
          <div className={`flex flex-col items-center justify-center p-3 rounded-xl border ${scoreColor} min-w-[90px]`}>
            <span className="text-2xl font-bold font-mono tracking-tight leading-none">
              {doc.overall_score.toFixed(1)}
            </span>
            <span className="text-[10px] uppercase font-bold tracking-wider mt-1 opacity-80">
              Score / 10
            </span>
          </div>

          <div className="flex flex-col space-y-1">
            <span
              className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${
                doc.passed
                  ? 'bg-emerald-100 text-emerald-800'
                  : 'bg-rose-100 text-rose-800'
              }`}
            >
              {doc.passed ? 'VERDICT: PASSED' : 'VERDICT: REJECTED'}
            </span>
            <span className="text-[11px] text-zinc-500 font-medium">
              Architecture Adherence: {doc.architecture_adherence ? 'Verified' : 'Deviations Detected'}
            </span>
          </div>
        </div>
      </div>

      {/* Agent Reasoning Section */}
      <AgentReasoningSection
        agentName="Code Review Agent"
        stageName="Code Review"
        reasoning={doc.reasoning}
      />

      {/* Strengths */}
      {doc.strengths?.length > 0 && (
        <div className="p-4 rounded-lg bg-emerald-50/50 border border-emerald-100">
          <h4 className="text-xs font-bold text-emerald-900 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            <span>Architecture & Code Strengths</span>
          </h4>
          <ul className="space-y-1 text-xs text-emerald-800">
            {doc.strengths.map((str, idx) => (
              <li key={idx} className="flex items-start space-x-1.5">
                <span className="text-emerald-500 font-bold">•</span>
                <span>{str}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Issues Breakdown */}
      <div>
        <h4 className="text-xs font-bold text-zinc-900 uppercase tracking-wider mb-3 flex items-center justify-between">
          <span>Identified Code Issues & Smells ({doc.issues?.length || 0})</span>
        </h4>

        {(!doc.issues || doc.issues.length === 0) ? (
          <div className="p-4 rounded-lg border border-emerald-200 bg-emerald-50/30 text-xs text-emerald-800 flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>Clean code! Zero critical or major architectural issues detected.</span>
          </div>
        ) : (
          <div className="space-y-3">
            {doc.issues.map((issue, idx) => {
              const isCrit = issue.severity === 'CRITICAL';
              const isMajor = issue.severity === 'MAJOR';
              const isMinor = issue.severity === 'MINOR';

              const badgeColor = isCrit
                ? 'bg-rose-100 text-rose-800 border-rose-200'
                : isMajor
                ? 'bg-amber-100 text-amber-800 border-amber-200'
                : isMinor
                ? 'bg-blue-50 text-blue-800 border-blue-200'
                : 'bg-zinc-100 text-zinc-800 border-zinc-200';

              return (
                <div
                  key={idx}
                  className="p-3.5 rounded-lg border border-zinc-200 bg-zinc-50/40 space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${badgeColor}`}>
                        {issue.severity}
                      </span>
                      <span className="text-xs font-mono font-semibold text-zinc-800">
                        {issue.file} {issue.line_number ? `(Line ${issue.line_number})` : ''}
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-zinc-700">
                    {issue.description}
                  </p>

                  <div className="text-[11px] text-zinc-600 bg-white border border-zinc-200/80 rounded p-2 flex items-start space-x-1.5">
                    <span className="font-semibold text-indigo-600 shrink-0">Recommendation:</span>
                    <span>{issue.recommendation}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
