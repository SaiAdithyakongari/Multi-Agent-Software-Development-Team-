import React from 'react';
import { 
  Settings, 
  Shield, 
  FlaskConical, 
  GitGraph, 
  Radio, 
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileCode,
  Zap,
  Layers,
  BookOpen,
  RefreshCw,
  MessageSquare
} from 'lucide-react';
import { FeatureFlags } from '../types';

interface SettingsPanelProps {
  featureFlags: FeatureFlags;
  onFeatureFlagsChange: (flags: FeatureFlags) => void;
  isOpen: boolean;
  onClose: () => void;
}

const FEATURE_CONFIG: Array<{
  key: keyof FeatureFlags;
  label: string;
  description: string;
  icon: React.ReactNode;
  defaultOn: boolean;
}> = [
  {
    key: 'security_review',
    label: 'Security Review',
    description: 'Scan for hardcoded secrets, SQL injection, unsafe eval/exec, insecure deserialization',
    icon: <Shield className="w-4 h-4" />,
    defaultOn: true,
  },
  {
    key: 'static_analysis',
    label: 'Static Analysis Gate',
    description: 'Run ruff/flake8 + mypy before tests. Errors block, warnings log.',
    icon: <FileCode className="w-4 h-4" />,
    defaultOn: true,
  },
  {
    key: 'regression_testing',
    label: 'Regression Testing',
    description: 'Re-run full test suite after each bug fix to catch regressions',
    icon: <RefreshCw className="w-4 h-4" />,
    defaultOn: true,
  },
  {
    key: 'coverage_reporting',
    label: 'Code Coverage Reporting',
    description: 'Report per-module coverage % with 80% threshold flagging',
    icon: <FlaskConical className="w-4 h-4" />,
    defaultOn: true,
  },
  {
    key: 'trace_dashboard',
    label: 'Pipeline Trace & Cost',
    description: 'Track per-stage token usage, duration, cost, and artifacts',
    icon: <GitGraph className="w-4 h-4" />,
    defaultOn: true,
  },
  {
    key: 'clarification_loop',
    label: 'Requirements Clarification',
    description: 'Detect ambiguous requirements and ask clarifying questions before proceeding',
    icon: <MessageSquare className="w-4 h-4" />,
    defaultOn: true,
  },
  {
    key: 'hitl_checkpoints',
    label: 'Human-in-the-Loop Checkpoints',
    description: 'Pause after Architecture and CodeGen stages for approval',
    icon: <CheckCircle2 className="w-4 h-4" />,
    defaultOn: false,
  },
  {
    key: 'live_stream',
    label: 'Live Agent Reasoning',
    description: 'Stream each agent\'s reasoning in real-time as it works',
    icon: <Radio className="w-4 h-4" />,
    defaultOn: false,
  },
  {
    key: 'cicd_scaffolding',
    label: 'CI/CD Pipeline Scaffolding',
    description: 'Generate GitHub Actions workflow, requirements.txt, Dockerfile',
    icon: <Zap className="w-4 h-4" />,
    defaultOn: false,
  },
  {
    key: 'bugfix_escalation',
    label: 'Bug-Fix Retry with Escalation',
    description: 'Cap retry at 3 per test, escalate to user if limit exceeded',
    icon: <AlertTriangle className="w-4 h-4" />,
    defaultOn: true,
  },
];

export function SettingsPanel({ featureFlags, onFeatureFlagsChange, isOpen, onClose }: SettingsPanelProps) {
  const handleToggle = (key: keyof FeatureFlags) => {
    // clarification_loop is always required - cannot be turned off
    if (key === 'clarification_loop') return;
    
    onFeatureFlagsChange({
      ...featureFlags,
      [key]: !featureFlags[key],
    });
  };

  const resetToDefaults = () => {
    const defaults: FeatureFlags = {
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
    };
    onFeatureFlagsChange(defaults);
  };

  const enabledCount = Object.values(featureFlags).filter(Boolean).length;
  const totalCount = Object.keys(featureFlags).length;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-2xl border-l border-zinc-200 z-50 flex flex-col transform transition-transform duration-300">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-200 bg-zinc-50">
        <div className="flex items-center space-x-3">
          <Settings className="w-5 h-5 text-zinc-700" />
          <h2 className="text-lg font-semibold text-zinc-900">Pipeline Settings</h2>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-zinc-200 transition-colors"
        >
          <XCircle className="w-5 h-5 text-zinc-500" />
        </button>
      </div>

      {/* Summary Bar */}
      <div className="px-6 py-3 bg-indigo-50 border-b border-indigo-100">
        <div className="flex items-center justify-between text-sm">
          <span className="text-indigo-700 font-medium">Features Enabled</span>
          <span className="text-indigo-900 font-bold">{enabledCount}/{totalCount}</span>
        </div>
        <div className="mt-2 h-2 bg-indigo-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-indigo-600 rounded-full transition-all duration-300"
            style={{ width: `${(enabledCount / totalCount) * 100}%` }}
          />
        </div>
      </div>

      {/* Feature List */}
      <div className="flex-1 overflow-y-auto py-2">
        {FEATURE_CONFIG.map((feature) => {
          const isEnabled = featureFlags[feature.key];
          const isLocked = feature.key === 'clarification_loop';

          return (
            <div
              key={feature.key}
              className={`px-6 py-4 border-b border-zinc-100 hover:bg-zinc-50 transition-colors ${
                isLocked ? 'opacity-60' : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <div className={`mt-0.5 ${isEnabled ? 'text-indigo-600' : 'text-zinc-400'}`}>
                    {feature.icon}
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-medium text-zinc-900 text-sm">{feature.label}</span>
                      {feature.defaultOn && !isEnabled && (
                        <span className="text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded font-medium">
                          OFF
                        </span>
                      )}
                      {!feature.defaultOn && isEnabled && (
                        <span className="text-[10px] px-1.5 py-0.5 bg-emerald-100 text-emerald-700 rounded font-medium">
                          ON
                        </span>
                      )}
                      {isLocked && (
                        <span className="text-[10px] px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded font-medium">
                          ALWAYS ON
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-zinc-500 mt-1 leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </div>

                {isLocked ? (
                  <div className="text-emerald-500">
                    <CheckCircle2 className="w-5 h-5" />
                  </div>
                ) : (
                  <button
                    onClick={() => handleToggle(feature.key)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      isEnabled ? 'bg-indigo-600' : 'bg-zinc-300'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform ${
                        isEnabled ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer Actions */}
      <div className="px-6 py-4 border-t border-zinc-200 bg-zinc-50">
        <button
          onClick={resetToDefaults}
          className="w-full py-2.5 px-4 bg-white border border-zinc-300 rounded-lg text-sm font-medium text-zinc-700 hover:bg-zinc-100 hover:border-zinc-400 transition-colors flex items-center justify-center space-x-2"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Reset to Defaults</span>
        </button>
      </div>
    </div>
  );
}

export default SettingsPanel;