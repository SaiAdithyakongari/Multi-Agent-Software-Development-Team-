import React, { useState, useEffect } from 'react';
import {
  Code2,
  FileText,
  Layers,
  CheckCircle2,
  FlaskConical,
  GitCommit as GitCommitIcon,
  BookOpen,
  ShieldCheck,
  AlertCircle,
  Sparkles,
  RefreshCw,
  ShieldAlert,
  Settings
} from 'lucide-react';
import { PipelineState, PresetRequirement, FeatureFlags } from './types';
import { Header } from './components/Header';
import { StagePipeline } from './components/StagePipeline';
import { RequirementInput } from './components/RequirementInput';
import { CodeExplorer } from './components/CodeExplorer';
import { RequirementsView } from './components/RequirementsView';
import { ArchitectureView } from './components/ArchitectureView';
import { CodeReviewView } from './components/CodeReviewView';
import { TestSandboxView } from './components/TestSandboxView';
import { GitHistoryView } from './components/GitHistoryView';
import { DocumentationView } from './components/DocumentationView';
import { AuditTrailView } from './components/AuditTrailView';
import { ApprovalGatePanel } from './components/ApprovalGatePanel';
import { GitHubPushModal } from './components/GitHubPushModal';
import { SettingsPanel } from './components/SettingsPanel';

export default function App() {
  const [pipeline, setPipeline] = useState<PipelineState | null>(null);
  const [presets, setPresets] = useState<PresetRequirement[]>([]);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [provider, setProvider] = useState<string>('deterministic');
  const [selectedTab, setSelectedTab] = useState<string>('code');
  const [selectedStageId, setSelectedStageId] = useState<string>('codegen');
  const [activeStageIndex, setActiveStageIndex] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [requireApproval, setRequireApproval] = useState<boolean>(false);
  const [isProcessingApproval, setIsProcessingApproval] = useState<boolean>(false);
  const [isGitHubModalOpen, setIsGitHubModalOpen] = useState<boolean>(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [featureFlags, setFeatureFlags] = useState<FeatureFlags>({
    clarification_loop: true,    // Always ON
    security_review: true,
    static_analysis: true,
    bugfix_escalation: true,
    regression_testing: true,
    coverage_reporting: true,
    trace_dashboard: true,
    hitl_checkpoints: false,
    live_stream: false,
    cicd_scaffolding: false,
  });

  // Load presets and run initial preset on first load so user immediately sees real generated project
  useEffect(() => {
    fetch('/api/pipeline/presets')
      .then((res) => res.json())
      .then((data) => {
        if (data.presets) {
          setPresets(data.presets);
        }
      })
      .catch((err) => console.error('Failed to fetch presets:', err));

    // Run initial deterministic pipeline so the dashboard is immediately populated with real code, tests, reviews, and commits!
    runPipeline(
      'Build a production-grade Scientific and Financial CLI Calculator with memory registers, trigonometry, compound interest formulas, error handling for division-by-zero, and full unit test coverage.',
      3,
      false
    );
  }, []);

  const runPipeline = async (
    requirement: string,
    maxIterations: number,
    approvalEnabled: boolean = requireApproval
  ) => {
    setIsRunning(true);
    setErrorMessage(null);
    setActiveStageIndex(0);

    // Simulate stepping through stages for visual feedback during execution
    const interval = setInterval(() => {
      setActiveStageIndex((prev) => (prev < 6 ? prev + 1 : prev));
    }, 450);

    try {
      const res = await fetch('/api/pipeline/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          requirement,
          provider,
          maxIterations,
          requireApproval: approvalEnabled,
          featureFlags
        })
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.details || data.error || 'Pipeline execution failed');
      }

      setPipeline(data.pipeline);

      if (data.pipeline?.pipeline_status === 'PAUSED_FOR_APPROVAL' && data.pipeline.pending_approval) {
        const stage = data.pipeline.pending_approval.stage.toLowerCase();
        if (stage.includes('require')) {
          setSelectedTab('requirements');
          setSelectedStageId('requirements');
          setActiveStageIndex(0);
        } else if (stage.includes('arch')) {
          setSelectedTab('architecture');
          setSelectedStageId('architecture');
          setActiveStageIndex(1);
        } else if (stage.includes('review')) {
          setSelectedTab('review');
          setSelectedStageId('review');
          setActiveStageIndex(3);
        }
      } else {
        setActiveStageIndex(7);
        setSelectedTab('code');
      }
    } catch (err: any) {
      console.error('Pipeline error:', err);
      setErrorMessage(err.message || 'An error occurred while running the pipeline.');
    } finally {
      clearInterval(interval);
      setIsRunning(false);
    }
  };

  // Human-in-the-loop Gate Action 1: Approve & Continue
  const handleApprove = async (notes?: string) => {
    if (!pipeline?.project_dir) return;
    setIsProcessingApproval(true);
    setErrorMessage(null);
    try {
      const res = await fetch('/api/pipeline/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          projectDir: pipeline.project_dir,
          notes: notes || 'Approved by operator',
          reviewer: 'Human Lead Architect'
        })
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.details || data.error || 'Approval failed');
      }

      setPipeline(data.pipeline);

      if (data.pipeline?.pipeline_status === 'PAUSED_FOR_APPROVAL' && data.pipeline.pending_approval) {
        const stage = data.pipeline.pending_approval.stage.toLowerCase();
        if (stage.includes('arch')) {
          setSelectedTab('architecture');
          setSelectedStageId('architecture');
        } else if (stage.includes('review')) {
          setSelectedTab('review');
          setSelectedStageId('review');
        }
      } else if (data.pipeline?.current_stage === 'Completed') {
        setSelectedTab('code');
        setSelectedStageId('codegen');
        setActiveStageIndex(7);
      }
    } catch (err: any) {
      console.error('Approval continuation error:', err);
      setErrorMessage(err.message || 'Failed to approve and resume pipeline.');
    } finally {
      setIsProcessingApproval(false);
    }
  };

  // Human-in-the-loop Gate Action 2: Request Changes & Re-run Stage
  const handleRequestChanges = async (feedback: string) => {
    if (!pipeline?.project_dir) return;
    setIsProcessingApproval(true);
    setErrorMessage(null);
    try {
      const res = await fetch('/api/pipeline/request-changes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          projectDir: pipeline.project_dir,
          feedback,
          reviewer: 'Human Lead Architect'
        })
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.details || data.error || 'Request changes failed');
      }

      setPipeline(data.pipeline);
    } catch (err: any) {
      console.error('Request changes error:', err);
      setErrorMessage(err.message || 'Failed to request changes and re-run agent stage.');
    } finally {
      setIsProcessingApproval(false);
    }
  };

  // Human-in-the-loop Gate Action 3: Reject & Terminate Pipeline
  const handleReject = async (reason: string) => {
    if (!pipeline?.project_dir) return;
    setIsProcessingApproval(true);
    setErrorMessage(null);
    try {
      const res = await fetch('/api/pipeline/reject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          projectDir: pipeline.project_dir,
          reason,
          reviewer: 'Human Lead Architect'
        })
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.details || data.error || 'Rejection failed');
      }

      setPipeline(data.pipeline);
    } catch (err: any) {
      console.error('Rejection error:', err);
      setErrorMessage(err.message || 'Failed to reject and terminate pipeline.');
    } finally {
      setIsProcessingApproval(false);
    }
  };

  // Run Pytest in isolated sandbox directly
  const handleRunPytestSandbox = async () => {
    if (!pipeline) return;
    setIsTesting(true);
    try {
      const res = await fetch('/api/sandbox/run-tests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          codeFiles: pipeline.code_files,
          testFiles: pipeline.test_files
        })
      });
      const data = await res.json();
      if (data.success && data.test_result) {
        setPipeline((prev) =>
          prev ? { ...prev, test_result: data.test_result } : null
        );
        setSelectedTab('testing');
      }
    } catch (err) {
      console.error('Failed to re-run pytest:', err);
    } finally {
      setIsTesting(false);
    }
  };

  // Export full git repository as .zip
  const handleExportZip = () => {
    if (!pipeline?.project_dir) return;
    window.location.href = `/api/git/download?projectDir=${encodeURIComponent(pipeline.project_dir)}`;
  };

  // Map stage click to corresponding tab
  const handleStageSelect = (stageId: string) => {
    setSelectedStageId(stageId);
    if (stageId === 'requirements') setSelectedTab('requirements');
    else if (stageId === 'architecture') setSelectedTab('architecture');
    else if (stageId === 'codegen') setSelectedTab('code');
    else if (stageId === 'review') setSelectedTab('review');
    else if (stageId === 'testing') setSelectedTab('testing');
    else if (stageId === 'bugfix') setSelectedTab('testing');
    else if (stageId === 'documentation') setSelectedTab('documentation');
  };

  const tabs = [
    { id: 'code', label: 'Source Code & Tests', icon: Code2, badge: Object.keys(pipeline?.code_files || {}).length },
    { id: 'requirements', label: 'Requirements Spec', icon: FileText },
    { id: 'architecture', label: 'Architecture Blueprint', icon: Layers },
    { id: 'review', label: 'Code Review Audit', icon: CheckCircle2, badge: pipeline?.review_doc?.overall_score ? `${pipeline.review_doc.overall_score}/10` : null },
    { id: 'testing', label: 'Pytest Sandbox', icon: FlaskConical, badge: pipeline?.test_result?.success ? 'Passed' : null },
    { id: 'git', label: 'Git Commits & Diffs', icon: GitCommitIcon, badge: pipeline?.git_commits?.length || null },
    { id: 'documentation', label: 'Docs & README', icon: BookOpen },
    { id: 'audit', label: 'Audit Trail', icon: ShieldCheck, badge: pipeline?.audit_logs?.length || null }
  ];

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 flex flex-col font-sans antialiased selection:bg-indigo-500 selection:text-white">
      {/* Top Application Header */}
      <Header
        pipeline={pipeline}
        isRunning={isRunning}
        provider={provider}
        onProviderChange={setProvider}
        onExportZip={handleExportZip}
        onOpenGitHubModal={() => setIsGitHubModalOpen(true)}
        onRunPytest={handleRunPytestSandbox}
        isTesting={isTesting}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Settings Panel (Slide-out) */}
      <SettingsPanel
        featureFlags={featureFlags}
        onFeatureFlagsChange={setFeatureFlags}
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Error Alert if any */}
        {errorMessage && (
          <div className="mb-6 p-4 rounded-xl border border-rose-200 bg-rose-50 text-rose-800 flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="text-xs">
              <span className="font-bold block">Pipeline Execution Notice:</span>
              <span>{errorMessage}</span>
            </div>
          </div>
        )}

        {/* Requirements Formulation & Prompt Control */}
        <RequirementInput
          presets={presets}
          onRunPipeline={runPipeline}
          isRunning={isRunning}
          requireApproval={requireApproval}
          onToggleRequireApproval={setRequireApproval}
        />

        {/* LangGraph 7-Agent Stage Pipeline Stepper */}
        <StagePipeline
          pipeline={pipeline}
          isRunning={isRunning}
          activeStageIndex={activeStageIndex}
          selectedStageId={selectedStageId}
          onSelectStage={handleStageSelect}
        />

        {/* Human-in-the-Loop Approval Gate Panel (Visible when pipeline paused for approval) */}
        {pipeline?.pipeline_status === 'PAUSED_FOR_APPROVAL' && pipeline.pending_approval && (
          <div className="mb-6">
            <ApprovalGatePanel
              pending={pipeline.pending_approval}
              approvalHistory={pipeline.approval_history || []}
              onApprove={handleApprove}
              onRequestChanges={handleRequestChanges}
              onReject={handleReject}
              isProcessing={isProcessingApproval}
            />
          </div>
        )}

        {/* Tab Navigation for Artifacts Inspection */}
        <div className="border-b border-zinc-200 mb-6 flex items-center justify-between overflow-x-auto">
          <div className="flex space-x-1 sm:space-x-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isSelected = selectedTab === tab.id;
              return (
                <button
                  key={tab.id}
                  id={`tab-${tab.id}`}
                  onClick={() => setSelectedTab(tab.id)}
                  className={`flex items-center space-x-2 py-3 px-3.5 border-b-2 text-xs font-semibold whitespace-nowrap transition-all ${
                    isSelected
                      ? 'border-indigo-600 text-indigo-600'
                      : 'border-transparent text-zinc-500 hover:text-zinc-800 hover:border-zinc-300'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isSelected ? 'text-indigo-600' : 'text-zinc-400'}`} />
                  <span>{tab.label}</span>
                  {tab.badge && (
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded-full font-mono ${
                        isSelected
                          ? 'bg-indigo-100 text-indigo-700 font-bold'
                          : 'bg-zinc-100 text-zinc-600'
                      }`}
                    >
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Active Tab View */}
        <div className="pb-12">
          {selectedTab === 'code' && (
            <CodeExplorer
              codeFiles={pipeline?.code_files || {}}
              testFiles={pipeline?.test_files || {}}
              onRunSandbox={handleRunPytestSandbox}
              isTesting={isTesting}
              reasoning={pipeline?.codegen_reasoning}
            />
          )}

          {selectedTab === 'requirements' && (
            <RequirementsView doc={pipeline?.requirements_doc || null} />
          )}

          {selectedTab === 'architecture' && (
            <ArchitectureView doc={pipeline?.architecture_doc || null} />
          )}

          {selectedTab === 'review' && (
            <CodeReviewView doc={pipeline?.review_doc || null} />
          )}

          {selectedTab === 'testing' && (
            <TestSandboxView
              testResult={pipeline?.test_result || null}
              onRunPytest={handleRunPytestSandbox}
              isTesting={isTesting}
              bugfixHistory={pipeline?.bugfix_history || []}
            />
          )}

          {selectedTab === 'git' && (
            <GitHistoryView
              commits={pipeline?.git_commits || []}
              projectDir={pipeline?.project_dir || ''}
              onExportZip={handleExportZip}
              onOpenGitHubModal={() => setIsGitHubModalOpen(true)}
            />
          )}

          {selectedTab === 'documentation' && (
            <DocumentationView docs={pipeline?.documentation || null} />
          )}

          {selectedTab === 'audit' && (
            <AuditTrailView logs={pipeline?.audit_logs || []} />
          )}
        </div>
      </main>

      {/* GitHub Push Modal */}
      <GitHubPushModal
        isOpen={isGitHubModalOpen}
        onClose={() => setIsGitHubModalOpen(false)}
        projectDir={pipeline?.project_dir || ''}
        commitsCount={pipeline?.git_commits?.length || 0}
      />
    </div>
  );
}
