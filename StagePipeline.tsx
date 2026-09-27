import React from 'react';
import {
  FileText,
  Layers,
  Code2,
  CheckCircle2,
  FlaskConical,
  Wrench,
  BookOpen,
  Loader2,
  AlertCircle,
  ShieldAlert,
  XCircle,
  UserCheck
} from 'lucide-react';
import { PipelineState } from '../types';

interface StagePipelineProps {
  pipeline: PipelineState | null;
  isRunning: boolean;
  activeStageIndex: number;
  selectedStageId: string;
  onSelectStage: (stageId: string) => void;
}

interface StageConfig {
  id: string;
  name: string;
  agentTitle: string;
  icon: React.ElementType;
  description: string;
}

const STAGES: StageConfig[] = [
  {
    id: 'requirements',
    name: 'Requirements',
    agentTitle: 'Requirements Analyst Agent',
    icon: FileText,
    description: 'Deconstructs user prompt into acceptance criteria and constraints'
  },
  {
    id: 'architecture',
    name: 'Architecture',
    agentTitle: 'Architecture Agent',
    icon: Layers,
    description: 'Formulates domain models, design patterns, and module boundaries'
  },
  {
    id: 'codegen',
    name: 'Code Generation',
    agentTitle: 'Code Generation Agent',
    icon: Code2,
    description: 'Synthesizes clean PEP-8 domain, service, and interface code'
  },
  {
    id: 'review',
    name: 'Code Review',
    agentTitle: 'Code Review Agent',
    icon: CheckCircle2,
    description: 'Performs static audit, edge cases, and architectural compliance'
  },
  {
    id: 'testing',
    name: 'Test Automation',
    agentTitle: 'Test & Verification Agent',
    icon: FlaskConical,
    description: 'Runs real sandboxed pytest assertions in isolated process'
  },
  {
    id: 'bugfix',
    name: 'Bug-Fix Loop',
    agentTitle: 'Autonomous Bug-Fix Agent',
    icon: Wrench,
    description: 'Self-heals and patches code failures until tests pass'
  },
  {
    id: 'documentation',
    name: 'Documentation',
    agentTitle: 'Documentation & Release Agent',
    icon: BookOpen,
    description: 'Generates comprehensive README, setup guides, and Git manifest'
  }
];

export const StagePipeline: React.FC<StagePipelineProps> = ({
  pipeline,
  isRunning,
  activeStageIndex,
  selectedStageId,
  onSelectStage
}) => {
  const isPaused = pipeline?.pipeline_status === 'PAUSED_FOR_APPROVAL';
  const isStopped = pipeline?.pipeline_status === 'STOPPED';
  const pendingStage = pipeline?.pending_approval?.stage;

  // Determine status for each stage
  const getStageStatus = (stage: StageConfig, index: number) => {
    if (isPaused && pendingStage && stage.name.toLowerCase() === pendingStage.toLowerCase()) {
      return 'awaiting_approval';
    }
    if (isStopped) {
      if (pendingStage && stage.name.toLowerCase() === pendingStage.toLowerCase()) {
        return 'rejected';
      }
    }
    if (!pipeline && !isRunning) return 'idle';
    if (isRunning) {
      if (index < activeStageIndex) return 'completed';
      if (index === activeStageIndex) return 'running';
      return 'pending';
    }
    // Pipeline finished
    if (pipeline?.current_stage === 'Completed') return 'completed';
    if (pipeline?.current_stage === 'Failed') {
      return index <= activeStageIndex ? 'failed' : 'pending';
    }
    return 'completed';
  };

  return (
    <div className="bg-white border border-zinc-200 rounded-xl p-4 sm:p-5 shadow-xs mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h2 className="text-sm font-semibold text-zinc-900 tracking-tight flex flex-wrap items-center gap-2">
            <span>LangGraph Multi-Agent Orchestration Workflow</span>
            {isRunning && (
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200 animate-pulse">
                <Loader2 className="w-3 h-3 animate-spin" />
                <span>Running Pipeline</span>
              </span>
            )}
            {isPaused && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-300 animate-pulse">
                <ShieldAlert className="w-3.5 h-3.5 text-amber-700" />
                <span>Paused for Approval: {pendingStage}</span>
              </span>
            )}
            {isStopped && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-900 border border-rose-300">
                <XCircle className="w-3.5 h-3.5 text-rose-700" />
                <span>Stopped by Operator</span>
              </span>
            )}
            {!isPaused && !isStopped && pipeline?.current_stage === 'Completed' && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3 h-3" />
                <span>Autonomous Pipeline Passed</span>
              </span>
            )}
          </h2>
          <p className="text-xs text-zinc-500">
            Click any agent stage to inspect its specific generated artifacts, code review reports, or audit events.
          </p>
        </div>

        {pipeline?.git_commits && pipeline.git_commits.length > 0 && (
          <div className="text-xs text-zinc-600 bg-zinc-50 px-3 py-1 rounded-md border border-zinc-200 font-mono">
            HEAD: <span className="text-indigo-600 font-bold">{pipeline.git_commits[0]?.short_hash}</span> ({pipeline.git_commits.length} commits)
          </div>
        )}
      </div>

      {/* Stepper Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
        {STAGES.map((stage, idx) => {
          const status = getStageStatus(stage, idx);
          const isSelected = selectedStageId === stage.id;
          const Icon = stage.icon;

          // Check if this stage has an approval record in history
          const approvalRecord = pipeline?.approval_history?.find(
            (h) => h.stage.toLowerCase() === stage.name.toLowerCase() && h.action === 'APPROVED'
          );

          let badgeStyles = 'border-zinc-200 bg-zinc-50/70 text-zinc-500 hover:bg-zinc-100/70';
          let iconStyles = 'text-zinc-400 bg-zinc-200/60';

          if (status === 'awaiting_approval') {
            badgeStyles = 'border-amber-500 bg-amber-50 text-amber-950 ring-2 ring-amber-400/40 animate-pulse';
            iconStyles = 'text-amber-700 bg-amber-200';
          } else if (status === 'rejected') {
            badgeStyles = 'border-rose-400 bg-rose-50 text-rose-950 ring-2 ring-rose-400/30';
            iconStyles = 'text-rose-700 bg-rose-200';
          } else if (status === 'completed') {
            badgeStyles = isSelected
              ? 'border-indigo-500 bg-indigo-50/80 text-indigo-900 ring-2 ring-indigo-500/20'
              : 'border-emerald-200 bg-emerald-50/60 text-emerald-900 hover:bg-emerald-100/50';
            iconStyles = 'text-emerald-600 bg-emerald-100';
          } else if (status === 'running') {
            badgeStyles = 'border-amber-400 bg-amber-50/80 text-amber-900 ring-2 ring-amber-400/30';
            iconStyles = 'text-amber-600 bg-amber-100 animate-pulse';
          } else if (status === 'failed') {
            badgeStyles = 'border-rose-300 bg-rose-50 text-rose-900';
            iconStyles = 'text-rose-600 bg-rose-100';
          } else if (isSelected) {
            badgeStyles = 'border-indigo-400 bg-indigo-50/50 text-zinc-800 ring-2 ring-indigo-400/20';
          }

          return (
            <button
              key={stage.id}
              id={`stage-card-${stage.id}`}
              onClick={() => onSelectStage(stage.id)}
              className={`flex flex-col p-2.5 rounded-lg border text-left transition-all relative ${badgeStyles}`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className={`w-7 h-7 rounded-md flex items-center justify-center ${iconStyles}`}>
                  {status === 'awaiting_approval' ? (
                    <ShieldAlert className="w-4 h-4 text-amber-700" />
                  ) : status === 'rejected' ? (
                    <XCircle className="w-4 h-4 text-rose-700" />
                  ) : status === 'running' ? (
                    <Loader2 className="w-4 h-4 animate-spin text-amber-700" />
                  ) : status === 'failed' ? (
                    <AlertCircle className="w-4 h-4 text-rose-600" />
                  ) : (
                    <Icon className="w-4 h-4" />
                  )}
                </div>
                <span className="text-[10px] font-mono text-zinc-400">
                  0{idx + 1}
                </span>
              </div>

              <span className="text-xs font-semibold truncate block">
                {stage.name}
              </span>
              <span className="text-[11px] text-zinc-500 truncate block mt-0.5">
                {stage.agentTitle.replace(' Agent', '')}
              </span>

              {/* Status footer inside badge */}
              <div className="mt-2 flex flex-col gap-0.5 text-[10px]">
                {status === 'awaiting_approval' && (
                  <span className="text-amber-800 font-bold flex items-center gap-0.5">
                    <ShieldAlert className="w-3 h-3 text-amber-600" /> Awaiting Approval
                  </span>
                )}
                {status === 'rejected' && (
                  <span className="text-rose-800 font-bold flex items-center gap-0.5">
                    <XCircle className="w-3 h-3 text-rose-600" /> Rejected
                  </span>
                )}
                {status === 'completed' && (
                  <span className="text-emerald-700 font-medium flex items-center gap-0.5">
                    <CheckCircle2 className="w-3 h-3" /> Ready
                  </span>
                )}
                {approvalRecord && (
                  <span className="text-[9px] text-indigo-700 font-medium truncate" title={`Approved by ${approvalRecord.reviewer}`}>
                    ✓ Approved by {approvalRecord.reviewer}
                  </span>
                )}
                {status === 'running' && (
                  <span className="text-amber-700 font-medium animate-pulse">
                    Executing...
                  </span>
                )}
                {status === 'idle' && (
                  <span className="text-zinc-400">
                    Standby
                  </span>
                )}
                {status === 'failed' && (
                  <span className="text-rose-700 font-medium">
                    Needs Attention
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
