import React, { useState } from 'react';
import { Play, Sparkles, Sliders, ChevronDown, ChevronUp, RotateCcw, Edit3 } from 'lucide-react';
import { PresetRequirement } from '../types';

interface RequirementInputProps {
  presets: PresetRequirement[];
  onRunPipeline: (requirement: string, maxIterations: number, requireApproval: boolean) => void;
  isRunning: boolean;
  requireApproval: boolean;
  onToggleRequireApproval: (enabled: boolean) => void;
}

export const RequirementInput: React.FC<RequirementInputProps> = ({
  presets,
  onRunPipeline,
  isRunning,
  requireApproval,
  onToggleRequireApproval
}) => {
  const [prompt, setPrompt] = useState<string>(
    presets[0]?.prompt || 'Build a production-grade Scientific and Financial CLI Calculator with memory registers, trigonometry, compound interest formulas, error handling for division-by-zero, and full unit test coverage.'
  );
  const [maxIterations, setMaxIterations] = useState<number>(3);
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(presets[0]?.id || null);

  // When a preset chip is clicked: auto-fill the text box with that template
  const handleSelectPreset = (preset: PresetRequirement) => {
    setSelectedPresetId(preset.id);
    setPrompt(preset.prompt);
  };

  // When text is typed or edited manually: update prompt and check if it matches a preset
  const handlePromptChange = (val: string) => {
    setPrompt(val);
    const matched = presets.find((p) => p.prompt.trim() === val.trim());
    setSelectedPresetId(matched ? matched.id : null);
  };

  // Clear text box to formulate a custom requirement from scratch
  const handleClearPrompt = () => {
    setPrompt('');
    setSelectedPresetId(null);
  };

  // Launch pipeline with whatever text is in the box right now
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const activeRequirement = prompt.trim();
    if (!activeRequirement || isRunning) return;
    onRunPipeline(activeRequirement, maxIterations, requireApproval);
  };

  const activePreset = presets.find((p) => p.id === selectedPresetId);

  return (
    <div className="bg-white border border-zinc-200 rounded-xl p-5 shadow-xs mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-indigo-600 shrink-0" />
          <h3 className="text-sm font-semibold text-zinc-900">
            Software Requirement & Mission Control
          </h3>
        </div>
        <span className="text-xs text-zinc-400">
          Type custom requirement directly OR choose a quick-start template
        </span>
      </div>

      {/* Quick-Start Templates Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[11px] font-medium text-zinc-500">
            Quick-Start Templates (click to auto-fill or replace below):
          </span>
          {prompt.length > 0 && !isRunning && (
            <button
              id="clear-prompt-btn"
              type="button"
              onClick={handleClearPrompt}
              className="text-[11px] text-zinc-500 hover:text-zinc-800 flex items-center space-x-1 underline decoration-zinc-300 hover:decoration-zinc-600 transition-colors"
            >
              <RotateCcw className="w-2.5 h-2.5" />
              <span>Clear / Blank Slate</span>
            </button>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {presets.map((p) => {
            const isSelected = selectedPresetId === p.id;
            return (
              <button
                key={p.id}
                id={`preset-${p.id}`}
                type="button"
                onClick={() => handleSelectPreset(p)}
                className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-all ${
                  isSelected
                    ? 'bg-indigo-50 border-indigo-300 text-indigo-800 ring-2 ring-indigo-500/10'
                    : 'bg-zinc-50 border-zinc-200 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900'
                }`}
              >
                <span className="text-indigo-600 mr-1.5 font-bold">[{p.badge}]</span>
                <span>{p.title}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1.5">
            <label
              htmlFor="requirement-prompt-input"
              className="text-xs font-semibold text-zinc-800 flex items-center space-x-2"
            >
              <span>Software Requirement Specification</span>
              {selectedPresetId ? (
                <span className="inline-flex items-center text-[10px] bg-indigo-50 border border-indigo-200 text-indigo-700 font-mono px-2 py-0.5 rounded-full font-medium">
                  Template: {activePreset?.badge || 'Selected'}
                </span>
              ) : prompt.trim() ? (
                <span className="inline-flex items-center text-[10px] bg-emerald-50 border border-emerald-200 text-emerald-700 font-mono px-2 py-0.5 rounded-full font-medium">
                  Custom / Manual Spec
                </span>
              ) : (
                <span className="inline-flex items-center text-[10px] bg-zinc-100 border border-zinc-200 text-zinc-500 font-mono px-2 py-0.5 rounded-full font-medium">
                  Awaiting Input
                </span>
              )}
            </label>

            <span className="text-[11px] text-zinc-500">
              Direct manual typing & template editing are both fully supported
            </span>
          </div>

          <textarea
            id="requirement-prompt-input"
            value={prompt}
            onChange={(e) => handlePromptChange(e.target.value)}
            disabled={isRunning}
            rows={3}
            className="w-full text-xs font-mono bg-zinc-50/50 border border-zinc-200 rounded-lg p-3 text-zinc-900 placeholder-zinc-400 focus:outline-hidden focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all resize-y"
            placeholder="Type any custom software requirement here (e.g., 'Build a rate-limited URL shortener with analytics and Redis caching'), or click any template chip above to auto-fill..."
          />
        </div>

        {/* Controls Row */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-1">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-xs text-zinc-500 hover:text-zinc-800 flex items-center space-x-1"
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Autonomous Pipeline Settings</span>
            {showAdvanced ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          <div className="flex items-center space-x-3">
            <button
              id="run-pipeline-submit-btn"
              type="submit"
              disabled={isRunning || !prompt.trim()}
              className="inline-flex items-center justify-center space-x-2 px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isRunning ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Orchestrating 7 Agents...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-white" />
                  <span>Launch Software Team Pipeline</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Advanced Settings Drawer */}
        {showAdvanced && (
          <div className="pt-3 border-t border-zinc-100 space-y-3 text-xs">
            {/* Human-in-the-loop Approval Gates Toggle */}
            <div className="p-3 bg-indigo-50/50 border border-indigo-100 rounded-lg flex items-center justify-between">
              <div>
                <label
                  htmlFor="hitl-require-approval-toggle"
                  className="font-bold text-zinc-900 flex items-center space-x-2 cursor-pointer"
                >
                  <span>Require approval before proceeding</span>
                  {requireApproval && (
                    <span className="text-[10px] bg-indigo-600 text-white font-mono px-1.5 py-0.2 rounded font-bold">
                      ACTIVE
                    </span>
                  )}
                </label>
                <p className="text-[11px] text-zinc-500 mt-0.5">
                  Pause execution after Requirements, Architecture, and Code Review stages for operator review, change requests, or approval.
                </p>
              </div>

              <label className="relative inline-flex items-center cursor-pointer shrink-0 ml-4">
                <input
                  type="checkbox"
                  id="hitl-require-approval-toggle"
                  checked={requireApproval}
                  onChange={(e) => onToggleRequireApproval(e.target.checked)}
                  disabled={isRunning}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-zinc-300 peer-focus:outline-hidden rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-zinc-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600"></div>
              </label>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="flex flex-col space-y-1">
                <label className="text-zinc-700 font-medium flex items-center justify-between">
                  <span>Max Bug-Fix Self-Healing Iterations:</span>
                  <span className="font-bold text-indigo-600 font-mono">{maxIterations} loops</span>
                </label>
                <input
                  type="range"
                  min={1}
                  max={5}
                  value={maxIterations}
                  onChange={(e) => setMaxIterations(Number(e.target.value))}
                  className="w-full accent-indigo-600 cursor-pointer"
                />
                <span className="text-[11px] text-zinc-400">
                  Number of autonomous diagnose-fix-retest cycles before returning.
                </span>
              </div>

              <div className="flex flex-col space-y-1">
                <span className="text-zinc-700 font-medium">Git Version Control Strategy:</span>
                <div className="text-zinc-600 text-[11px] bg-zinc-50 border border-zinc-200 rounded p-2">
                  Every stage commits under dedicated agent personas with atomic SHA-1 hashes and unified diff tracking.
                </div>
              </div>
            </div>
          </div>
        )}
      </form>
    </div>
  );
};
