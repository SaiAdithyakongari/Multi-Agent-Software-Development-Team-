import React from 'react';
import { CheckCircle2, Shield, AlertTriangle, FileText, Info } from 'lucide-react';
import { RequirementsDoc } from '../types';
import { AgentReasoningSection } from './AgentReasoningSection';

interface RequirementsViewProps {
  doc: RequirementsDoc | null;
}

export const RequirementsView: React.FC<RequirementsViewProps> = ({ doc }) => {
  if (!doc) {
    return (
      <div className="bg-white border border-zinc-200 rounded-xl p-8 text-center text-zinc-500">
        <FileText className="w-8 h-8 text-zinc-400 mx-auto mb-2" />
        <p className="text-sm">Requirements specification has not been generated yet.</p>
        <p className="text-xs text-zinc-400 mt-1">Run the pipeline to activate the Requirements Analyst Agent.</p>
      </div>
    );
  }

  const overviewText = doc.overview || doc.problem_statement || 'Deconstructed software specification and acceptance matrix.';

  return (
    <div className="bg-white border border-zinc-200 rounded-xl p-5 sm:p-6 shadow-xs space-y-6">
      {/* Title & Overview */}
      <div className="border-b border-zinc-100 pb-4">
        <div className="flex items-center space-x-2 text-indigo-600 mb-1">
          <FileText className="w-4 h-4" />
          <span className="text-xs font-semibold uppercase tracking-wider">
            Requirements Analyst Specification
          </span>
        </div>
        <h3 className="text-lg font-bold text-zinc-900 tracking-tight">
          {doc.title}
        </h3>
        <p className="text-xs text-zinc-600 mt-1 leading-relaxed">
          {overviewText}
        </p>
      </div>

      {/* Agent Reasoning Section */}
      <AgentReasoningSection
        agentName="Requirements Analyst Agent"
        stageName="Requirements"
        reasoning={doc.reasoning}
      />

      {/* Functional Requirements */}
      <div>
        <h4 className="text-xs font-bold text-zinc-900 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Functional Requirements ({doc.functional_requirements?.length || 0})</span>
        </h4>
        <div className="space-y-3">
          {doc.functional_requirements?.map((req) => (
            <div
              key={req.id}
              className="p-3.5 rounded-lg border border-zinc-200 bg-zinc-50/50 hover:bg-zinc-50 transition-colors"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-mono font-bold text-indigo-700 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded">
                  {req.id}
                </span>
                <span className="text-xs font-semibold text-zinc-800">
                  {req.title}
                </span>
              </div>
              <p className="text-xs text-zinc-600 mb-2">
                {req.description}
              </p>
              {req.acceptance_criteria?.length > 0 && (
                <div className="pl-3 border-l-2 border-indigo-200 space-y-1">
                  <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider block">
                    Acceptance Criteria:
                  </span>
                  {req.acceptance_criteria.map((crit, i) => (
                    <div key={i} className="text-xs text-zinc-700 flex items-start space-x-1.5">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span>{crit}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Non-Functional Requirements & Constraints Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        {/* Non-Functional Requirements */}
        <div className="border border-zinc-200 rounded-lg p-4 bg-zinc-50/30">
          <h4 className="text-xs font-bold text-zinc-900 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
            <Shield className="w-4 h-4 text-blue-600" />
            <span>Non-Functional Criteria</span>
          </h4>
          <div className="space-y-2">
            {doc.non_functional_requirements?.map((nfr, idx) => (
              <div key={idx} className="text-xs border-b border-zinc-100 pb-1.5 last:border-0 last:pb-0">
                <span className="font-semibold text-zinc-700">{nfr.category}: </span>
                <span className="text-zinc-600">{nfr.requirement}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Constraints & Assumptions */}
        <div className="border border-zinc-200 rounded-lg p-4 bg-zinc-50/30">
          <h4 className="text-xs font-bold text-zinc-900 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>Constraints & Boundaries</span>
          </h4>
          <ul className="space-y-1.5 text-xs text-zinc-600">
            {doc.constraints?.map((c, i) => (
              <li key={i} className="flex items-start space-x-1.5">
                <span className="text-amber-500 font-bold">•</span>
                <span>{c}</span>
              </li>
            ))}
            {doc.assumptions?.map((a, i) => (
              <li key={`a-${i}`} className="flex items-start space-x-1.5 text-zinc-500">
                <span className="text-zinc-400 font-bold">•</span>
                <span>Assumption: {a}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
