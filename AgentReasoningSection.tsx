import React, { useState } from 'react';
import { Brain, ChevronDown, ChevronUp, Sparkles, Terminal, ShieldAlert, Cpu } from 'lucide-react';

interface AgentReasoningSectionProps {
  agentName: string;
  stageName: string;
  reasoning?: string | null;
  defaultExpanded?: boolean;
}

export const AgentReasoningSection: React.FC<AgentReasoningSectionProps> = ({
  agentName,
  stageName,
  reasoning,
  defaultExpanded = true
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(defaultExpanded);

  if (!reasoning || !reasoning.trim()) {
    return null;
  }

  return (
    <div className="mb-5 rounded-xl border border-indigo-100 bg-gradient-to-r from-indigo-50/50 via-white to-violet-50/30 overflow-hidden shadow-2xs">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-indigo-50/40 transition-colors"
      >
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-lg bg-indigo-600/10 text-indigo-600 flex items-center justify-center shrink-0">
            <Brain className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-zinc-900 tracking-tight">
                Agent Reasoning & Decision Rationale
              </span>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-100 text-indigo-800 border border-indigo-200">
                <Sparkles className="w-2.5 h-2.5 mr-1" />
                {agentName}
              </span>
            </div>
            <p className="text-[11px] text-zinc-500">
              Autonomous cognitive deliberation, trade-off analysis, and architectural justifications for {stageName}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-zinc-400">
          <span className="text-[11px] font-medium hidden sm:inline text-zinc-500">
            {isExpanded ? 'Collapse thoughts' : 'Expand thoughts'}
          </span>
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 pt-1 border-t border-indigo-100/60">
          <div className="relative rounded-lg bg-zinc-900 text-zinc-100 p-3.5 sm:p-4 text-xs font-mono leading-relaxed shadow-inner overflow-x-auto border border-zinc-800">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-zinc-800 text-[11px] text-zinc-400">
              <span className="flex items-center space-x-1.5 text-indigo-400 font-semibold">
                <Terminal className="w-3.5 h-3.5" />
                <span>deliberation_trace.log</span>
              </span>
              <span className="text-zinc-500 font-mono text-[10px]">
                Stage: {stageName} • Persona: {agentName}
              </span>
            </div>
            <p className="whitespace-pre-wrap text-zinc-200 leading-normal selection:bg-indigo-600 selection:text-white">
              {reasoning}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
