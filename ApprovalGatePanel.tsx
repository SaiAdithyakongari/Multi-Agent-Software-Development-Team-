import React, { useState } from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  RotateCcw,
  XCircle,
  Clock,
  UserCheck,
  FileText,
  Layers,
  CheckSquare,
  MessageSquare,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  History,
  Send,
  Loader2
} from 'lucide-react';
import { PipelineState, PendingApproval, ApprovalHistoryItem } from '../types';

interface ApprovalGatePanelProps {
  pipeline: PipelineState;
  onApprove: (reviewer: string) => Promise<void>;
  onRequestChanges: (feedback: string, reviewer: string) => Promise<void>;
  onReject: (reason: string, reviewer: string) => Promise<void>;
  isProcessing: boolean;
}

export const ApprovalGatePanel: React.FC<ApprovalGatePanelProps> = ({
  pipeline,
  onApprove,
  onRequestChanges,
  onReject,
  isProcessing
}) => {
  const [showFeedbackInput, setShowFeedbackInput] = useState<boolean>(false);
  const [feedbackText, setFeedbackText] = useState<string>('');
  const [showRejectInput, setShowRejectInput] = useState<boolean>(false);
  const [rejectReason, setRejectReason] = useState<string>('');
  const [reviewerName, setReviewerName] = useState<string>('Human Operator');
  const [showHistory, setShowHistory] = useState<boolean>(false);
  const [showArtifactPreview, setShowArtifactPreview] = useState<boolean>(true);

  const pending = pipeline.pending_approval;
  const history = pipeline.approval_history || [];
  const isPaused = pipeline.pipeline_status === 'PAUSED_FOR_APPROVAL' && !!pending;
  const isStopped = pipeline.pipeline_status === 'STOPPED';

  if (!isPaused && !isStopped && history.length === 0) {
    return null;
  }

  const handleApproveSubmit = async () => {
    if (isProcessing) return;
    await onApprove(reviewerName);
  };

  const handleChangesSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedbackText.trim() || isProcessing) return;
    await onRequestChanges(feedbackText.trim(), reviewerName);
    setFeedbackText('');
    setShowFeedbackInput(false);
  };

  const handleRejectSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isProcessing) return;
    await onReject(rejectReason.trim(), reviewerName);
    setShowRejectInput(false);
  };

  return (
    <div className="mb-6 space-y-4">
      {/* Active Paused Gate Card */}
      {isPaused && pending && (
        <div className="rounded-xl border-2 border-amber-400 bg-amber-50/40 shadow-md p-5 sm:p-6 transition-all animate-in fade-in duration-300">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-amber-200/80 pb-4 mb-4">
            <div className="flex items-start sm:items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500 text-white flex items-center justify-center shadow-sm shrink-0">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-amber-900 bg-amber-200/80 px-2 py-0.5 rounded-md">
                    HITL Approval Gate Active
                  </span>
                  <span className="text-xs font-semibold text-amber-800">
                    Stage: {pending.stage}
                  </span>
                </div>
                <h3 className="text-base font-bold text-zinc-900 mt-0.5">
                  Pipeline Paused: Review & Approve {pending.title}
                </h3>
              </div>
            </div>

            {/* Reviewer identity input */}
            <div className="flex items-center space-x-2 text-xs">
              <label className="text-zinc-500 font-medium whitespace-nowrap">Operator:</label>
              <input
                type="text"
                value={reviewerName}
                onChange={(e) => setReviewerName(e.target.value)}
                disabled={isProcessing}
                placeholder="Reviewer Name"
                className="bg-white border border-amber-300 rounded-lg px-2.5 py-1 text-xs text-zinc-900 font-medium focus:ring-2 focus:ring-amber-400 focus:outline-hidden"
              />
            </div>
          </div>

          <p className="text-xs text-zinc-700 mb-4">
            The autonomous LangGraph execution has halted before proceeding to the next agent. Inspect the generated artifact below, then select an action to continue, request revisions with feedback, or halt execution.
          </p>

          {/* Artifact Preview Accordion */}
          <div className="mb-5 rounded-lg border border-amber-200 bg-white overflow-hidden shadow-2xs">
            <button
              type="button"
              onClick={() => setShowArtifactPreview(!showArtifactPreview)}
              className="w-full px-4 py-2.5 flex items-center justify-between text-left bg-zinc-50/80 hover:bg-zinc-100/80 border-b border-amber-100 transition-colors"
            >
              <div className="flex items-center space-x-2 text-xs font-semibold text-zinc-800">
                {pending.stage === 'Requirements' && <FileText className="w-4 h-4 text-indigo-600" />}
                {pending.stage === 'Architecture' && <Layers className="w-4 h-4 text-violet-600" />}
                {pending.stage === 'Code Review' && <CheckSquare className="w-4 h-4 text-emerald-600" />}
                <span>Generated Artifact Summary: {pending.title}</span>
              </div>
              <div className="flex items-center space-x-1 text-zinc-400 text-xs">
                <span>{showArtifactPreview ? 'Hide preview' : 'View preview'}</span>
                {showArtifactPreview ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </div>
            </button>

            {showArtifactPreview && (
              <div className="p-4 text-xs font-mono max-h-64 overflow-y-auto bg-zinc-950 text-zinc-200">
                {pending.stage === 'Requirements' && pipeline.requirements_doc && (
                  <div className="space-y-2">
                    <div className="text-indigo-400 font-bold text-sm">
                      {pipeline.requirements_doc.title}
                    </div>
                    <div className="text-zinc-400 text-[11px]">
                      {pipeline.requirements_doc.problem_statement || pipeline.requirements_doc.overview}
                    </div>
                    <div className="pt-2 text-zinc-300 font-semibold text-[11px]">Functional Requirements:</div>
                    <ul className="list-disc list-inside space-y-1 pl-2 text-zinc-300">
                      {pipeline.requirements_doc.functional_requirements.map((fr, i) => (
                        <li key={i}><strong className="text-indigo-300">{fr.id}:</strong> {fr.description}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {pending.stage === 'Architecture' && pipeline.architecture_doc && (
                  <div className="space-y-2">
                    <div className="text-violet-400 font-bold text-sm">
                      System Overview
                    </div>
                    <div className="text-zinc-300">
                      {pipeline.architecture_doc.system_overview}
                    </div>
                    {pipeline.architecture_doc.design_patterns?.length > 0 && (
                      <div className="text-zinc-400 text-[11px]">
                        Patterns: {pipeline.architecture_doc.design_patterns.join(', ')}
                      </div>
                    )}
                    {pipeline.architecture_doc.folder_structure && (
                      <pre className="text-zinc-300 font-mono text-[11px] p-2 bg-zinc-900 rounded">
                        {pipeline.architecture_doc.folder_structure}
                      </pre>
                    )}
                  </div>
                )}

                {pending.stage === 'Code Review' && pipeline.review_doc && (
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-emerald-400 font-bold text-sm">
                        Score: {pipeline.review_doc.overall_score}/10
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${pipeline.review_doc.passed ? 'bg-emerald-900/60 text-emerald-300' : 'bg-rose-900/60 text-rose-300'}`}>
                        {pipeline.review_doc.passed ? 'PASSED' : 'NEEDS WORK'}
                      </span>
                    </div>
                    <p className="text-zinc-300">{pipeline.review_doc.summary}</p>
                    <div className="text-zinc-400 text-[11px]">
                      Identified {pipeline.review_doc.issues?.length || 0} issues / recommendations.
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Action Buttons Bar */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              id="hitl-approve-btn"
              type="button"
              onClick={handleApproveSubmit}
              disabled={isProcessing}
              className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
            >
              {isProcessing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <CheckCircle2 className="w-4 h-4" />
              )}
              <span>Approve & Continue</span>
            </button>

            <button
              id="hitl-request-changes-toggle-btn"
              type="button"
              onClick={() => {
                setShowFeedbackInput(!showFeedbackInput);
                setShowRejectInput(false);
              }}
              disabled={isProcessing}
              className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Request Changes</span>
            </button>

            <button
              id="hitl-reject-toggle-btn"
              type="button"
              onClick={() => {
                setShowRejectInput(!showRejectInput);
                setShowFeedbackInput(false);
              }}
              disabled={isProcessing}
              className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
            >
              <XCircle className="w-4 h-4" />
              <span>Reject & Stop</span>
            </button>
          </div>

          {/* Feedback Form for Request Changes */}
          {showFeedbackInput && (
            <form onSubmit={handleChangesSubmit} className="mt-4 pt-4 border-t border-amber-200 space-y-3">
              <div className="flex items-center space-x-2 text-xs font-semibold text-amber-900">
                <MessageSquare className="w-4 h-4" />
                <span>Specify Operator Feedback for {pending.stage} Agent:</span>
              </div>
              <textarea
                id="hitl-feedback-input"
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                disabled={isProcessing}
                rows={3}
                required
                placeholder={`Tell the ${pending.stage} Agent what to adjust, add, or fix (e.g. "Add validation for negative numbers", "Use repository pattern for storage", "Fix error boundary handling")...`}
                className="w-full text-xs bg-white border border-amber-300 rounded-lg p-3 text-zinc-900 placeholder-zinc-400 focus:outline-hidden focus:ring-2 focus:ring-amber-500"
              />
              <div className="flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowFeedbackInput(false)}
                  className="px-3 py-1.5 text-xs text-zinc-600 hover:text-zinc-900 font-medium"
                >
                  Cancel
                </button>
                <button
                  id="hitl-submit-feedback-btn"
                  type="submit"
                  disabled={isProcessing || !feedbackText.trim()}
                  className="inline-flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold shadow-xs disabled:opacity-50"
                >
                  {isProcessing ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Send className="w-3.5 h-3.5" />
                  )}
                  <span>Re-run {pending.stage} with Feedback</span>
                </button>
              </div>
            </form>
          )}

          {/* Reject Confirmation Form */}
          {showRejectInput && (
            <form onSubmit={handleRejectSubmit} className="mt-4 pt-4 border-t border-rose-200 space-y-3">
              <div className="flex items-center space-x-2 text-xs font-semibold text-rose-900">
                <AlertTriangle className="w-4 h-4 text-rose-600" />
                <span>Confirm Pipeline Abort:</span>
              </div>
              <input
                id="hitl-reject-reason-input"
                type="text"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                disabled={isProcessing}
                placeholder="Optional reason for rejecting (e.g., Requirement cancelled, out-of-scope)..."
                className="w-full text-xs bg-white border border-rose-300 rounded-lg p-2.5 text-zinc-900 placeholder-zinc-400 focus:outline-hidden focus:ring-2 focus:ring-rose-500"
              />
              <p className="text-[11px] text-zinc-500">
                Stopping the pipeline halts subsequent agents while preserving all commits, files, and artifacts generated up to this stage.
              </p>
              <div className="flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowRejectInput(false)}
                  className="px-3 py-1.5 text-xs text-zinc-600 hover:text-zinc-900 font-medium"
                >
                  Cancel
                </button>
                <button
                  id="hitl-confirm-reject-btn"
                  type="submit"
                  disabled={isProcessing}
                  className="inline-flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold shadow-xs disabled:opacity-50"
                >
                  {isProcessing ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <XCircle className="w-3.5 h-3.5" />
                  )}
                  <span>Halt Pipeline Permanently</span>
                </button>
              </div>
            </form>
          )}
        </div>
      )}

      {/* Stopped Banner if pipeline was rejected */}
      {isStopped && (
        <div className="rounded-xl border border-rose-200 bg-rose-50/60 p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <XCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <div>
              <span className="text-xs font-bold text-rose-900 block">
                Pipeline Execution Stopped by Human Operator
              </span>
              <span className="text-xs text-rose-700">
                All generated files and Git commits are preserved. You can inspect existing code, run sandbox tests, or export the repository.
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Historical Approval Timeline toggle */}
      {history.length > 0 && (
        <div className="rounded-lg border border-zinc-200 bg-white p-3.5 shadow-2xs">
          <button
            type="button"
            onClick={() => setShowHistory(!showHistory)}
            className="w-full flex items-center justify-between text-left text-xs font-semibold text-zinc-700 hover:text-zinc-900"
          >
            <div className="flex items-center space-x-2">
              <History className="w-4 h-4 text-indigo-600" />
              <span>Operator Approval Audit Trail ({history.length} events)</span>
            </div>
            <div className="flex items-center space-x-1 text-zinc-400">
              <span>{showHistory ? 'Hide history' : 'Show history'}</span>
              {showHistory ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </div>
          </button>

          {showHistory && (
            <div className="mt-3 pt-3 border-t border-zinc-100 space-y-2">
              {history.map((item) => {
                const isApprove = item.action === 'APPROVED';
                const isChanges = item.action === 'CHANGES_REQUESTED';
                const isReject = item.action === 'REJECTED';

                return (
                  <div
                    key={item.id}
                    className="p-2.5 rounded-lg border text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-zinc-50 border-zinc-200"
                  >
                    <div className="flex items-start sm:items-center space-x-2.5">
                      {isApprove && <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5 sm:mt-0" />}
                      {isChanges && <RotateCcw className="w-4 h-4 text-amber-600 shrink-0 mt-0.5 sm:mt-0" />}
                      {isReject && <XCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5 sm:mt-0" />}
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-zinc-900">{item.stage}</span>
                          <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                            isApprove ? 'bg-emerald-100 text-emerald-800' :
                            isChanges ? 'bg-amber-100 text-amber-800' :
                            'bg-rose-100 text-rose-800'
                          }`}>
                            {item.action.replace('_', ' ')}
                          </span>
                          <span className="text-zinc-500 text-[11px]">by {item.reviewer}</span>
                        </div>
                        {item.feedback && (
                          <p className="text-zinc-600 text-[11px] mt-0.5 italic">
                            "{item.feedback}"
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="text-[10px] text-zinc-400 font-mono flex items-center space-x-1 shrink-0">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
