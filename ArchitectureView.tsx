import React from 'react';
import { Layers, GitFork, Box, FolderTree, Cpu } from 'lucide-react';
import { ArchitectureDoc } from '../types';
import { AgentReasoningSection } from './AgentReasoningSection';

interface ArchitectureViewProps {
  doc: ArchitectureDoc | null;
}

export const ArchitectureView: React.FC<ArchitectureViewProps> = ({ doc }) => {
  if (!doc) {
    return (
      <div className="bg-white border border-zinc-200 rounded-xl p-8 text-center text-zinc-500">
        <Layers className="w-8 h-8 text-zinc-400 mx-auto mb-2" />
        <p className="text-sm">Architecture design document has not been formulated yet.</p>
        <p className="text-xs text-zinc-400 mt-1">Run the pipeline to activate the Architecture Agent.</p>
      </div>
    );
  }

  const moduleList = (doc.module_specifications || doc.modules || []).map((m: any) => ({
    name: m.name || m.file_path || 'Module',
    responsibility: m.responsibility || m.purpose || 'Domain business logic and operations',
    public_interfaces: m.public_interfaces || m.exports || [],
    dependencies: m.dependencies || []
  }));

  return (
    <div className="bg-white border border-zinc-200 rounded-xl p-5 sm:p-6 shadow-xs space-y-6">
      {/* Overview & Design Patterns */}
      <div className="border-b border-zinc-100 pb-4">
        <div className="flex items-center space-x-2 text-indigo-600 mb-1">
          <Layers className="w-4 h-4" />
          <span className="text-xs font-semibold uppercase tracking-wider">
            Architecture Agent Blueprint
          </span>
        </div>
        <h3 className="text-lg font-bold text-zinc-900 tracking-tight">
          System Architecture & Domain Modularity
        </h3>
        <p className="text-xs text-zinc-600 mt-1 leading-relaxed">
          {doc.system_overview}
        </p>

        {/* Patterns Tags */}
        <div className="mt-3 flex flex-wrap gap-2">
          {doc.design_patterns?.map((pattern, idx) => (
            <span
              key={idx}
              className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-100"
            >
              <Cpu className="w-3 h-3 mr-1 text-indigo-500" />
              {pattern}
            </span>
          ))}
        </div>
      </div>

      {/* Agent Reasoning Section */}
      <AgentReasoningSection
        agentName="Architecture Agent"
        stageName="Architecture"
        reasoning={doc.reasoning}
      />

      {/* Data Flow Diagram Card */}
      <div className="p-4 rounded-lg bg-zinc-900 text-zinc-200 font-mono text-xs border border-zinc-800">
        <div className="flex items-center space-x-2 text-zinc-400 mb-2 font-sans font-semibold text-xs uppercase tracking-wider">
          <GitFork className="w-4 h-4 text-emerald-400" />
          <span>Execution & Data Flow Lifecycle</span>
        </div>
        <div className="p-3 bg-zinc-950 rounded border border-zinc-800 text-emerald-400 leading-relaxed whitespace-pre-wrap">
          {doc.data_flow}
        </div>
      </div>

      {/* Module Specifications */}
      <div>
        <h4 className="text-xs font-bold text-zinc-900 uppercase tracking-wider mb-3 flex items-center gap-1.5">
          <Box className="w-4 h-4 text-indigo-600" />
          <span>Module Specifications & Contracts ({moduleList.length})</span>
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {moduleList.map((mod, i) => (
            <div
              key={i}
              className="border border-zinc-200 rounded-lg p-3.5 bg-zinc-50/40 hover:bg-zinc-50 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold font-mono text-zinc-900 bg-white border border-zinc-200 px-2 py-0.5 rounded shadow-2xs">
                    {mod.name}
                  </span>
                </div>
                <p className="text-xs text-zinc-600 mb-2.5">
                  {mod.responsibility}
                </p>
              </div>

              <div className="space-y-2 border-t border-zinc-200/60 pt-2 text-[11px]">
                {mod.public_interfaces?.length > 0 && (
                  <div>
                    <span className="text-zinc-400 font-semibold uppercase tracking-wider block mb-0.5">
                      Public APIs:
                    </span>
                    <div className="flex flex-wrap gap-1 font-mono text-zinc-700">
                      {mod.public_interfaces.map((iface, j) => (
                        <span key={j} className="bg-zinc-200/60 px-1.5 py-0.5 rounded">
                          {iface}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {mod.dependencies?.length > 0 && (
                  <div>
                    <span className="text-zinc-400 font-semibold uppercase tracking-wider block mb-0.5">
                      Dependencies:
                    </span>
                    <div className="flex flex-wrap gap-1 font-mono text-zinc-500">
                      {mod.dependencies.map((dep, k) => (
                        <span key={k} className="bg-zinc-100 px-1 py-0.5 rounded">
                          {dep}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* File Structure Breakdown or Folder Structure */}
      {doc.folder_structure && (
        <div className="border border-zinc-200 rounded-lg p-4 bg-zinc-50/30">
          <h4 className="text-xs font-bold text-zinc-900 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <FolderTree className="w-4 h-4 text-violet-600" />
            <span>Target Package Hierarchy</span>
          </h4>
          <pre className="font-mono text-xs text-zinc-800 bg-zinc-100/70 p-3 rounded border border-zinc-200 whitespace-pre-wrap">
            {doc.folder_structure}
          </pre>
        </div>
      )}

      {!doc.folder_structure && doc.file_structure && doc.file_structure.length > 0 && (
        <div className="border border-zinc-200 rounded-lg p-4 bg-zinc-50/30">
          <h4 className="text-xs font-bold text-zinc-900 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <FolderTree className="w-4 h-4 text-violet-600" />
            <span>Target Package Hierarchy</span>
          </h4>
          <div className="space-y-1.5 font-mono text-xs">
            {doc.file_structure.map((f, idx) => (
              <div key={idx} className="flex items-center space-x-2">
                <span className="text-indigo-600 font-semibold">{f.path}</span>
                <span className="text-zinc-400">—</span>
                <span className="text-zinc-600 font-sans text-xs">{f.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

