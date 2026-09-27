import React, { useState } from 'react';
import { ShieldCheck, CheckCircle2, Clock, AlertTriangle, XCircle, Search, Filter } from 'lucide-react';
import { AuditLog } from '../types';

interface AuditTrailViewProps {
  logs: AuditLog[];
}

export const AuditTrailView: React.FC<AuditTrailViewProps> = ({ logs }) => {
  const [filterStage, setFilterStage] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  if (!logs || logs.length === 0) {
    return (
      <div className="bg-white border border-zinc-200 rounded-xl p-8 text-center text-zinc-500">
        <Clock className="w-8 h-8 text-zinc-400 mx-auto mb-2" />
        <p className="text-sm">Audit log event journal is empty.</p>
        <p className="text-xs text-zinc-400 mt-1">Events will be logged as the multi-agent team progresses through the pipeline.</p>
      </div>
    );
  }

  const stages = ['ALL', ...Array.from(new Set(logs.map((l) => l.stage)))];

  const filteredLogs = logs.filter((log) => {
    if (filterStage !== 'ALL' && log.stage !== filterStage) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        log.action.toLowerCase().includes(q) ||
        log.agent.toLowerCase().includes(q) ||
        log.details.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="bg-white border border-zinc-200 rounded-xl p-5 sm:p-6 shadow-xs space-y-5">
      {/* Header & Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-100 pb-4">
        <div>
          <div className="flex items-center space-x-2 text-indigo-600 mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span className="text-xs font-semibold uppercase tracking-wider">
              Autonomous Governance & Observability
            </span>
          </div>
          <h3 className="text-lg font-bold text-zinc-900 tracking-tight">
            Pipeline Execution Audit Trail ({logs.length} events recorded)
          </h3>
          <p className="text-xs text-zinc-600 mt-0.5">
            Immutable log of every agent action, verification outcome, and git operation.
          </p>
        </div>

        {/* Filter controls */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search events..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="text-xs pl-8 pr-3 py-1.5 rounded-lg border border-zinc-200 bg-zinc-50 focus:outline-hidden focus:bg-white focus:border-indigo-500 w-36 sm:w-44"
            />
          </div>

          <select
            value={filterStage}
            onChange={(e) => setFilterStage(e.target.value)}
            className="text-xs py-1.5 px-2.5 rounded-lg border border-zinc-200 bg-zinc-50 text-zinc-700 focus:outline-hidden"
          >
            {stages.map((st) => (
              <option key={st} value={st}>
                {st === 'ALL' ? 'All Stages' : st}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Events Timeline */}
      <div className="space-y-2.5 max-h-[520px] overflow-y-auto pr-1">
        {filteredLogs.map((item, idx) => {
          const isSuccess = item.status === 'SUCCESS';
          const isInProgress = item.status === 'IN_PROGRESS';
          const isWarning = item.status === 'WARNING';
          const isFailed = item.status === 'FAILED';

          let statusBadge = 'bg-zinc-100 text-zinc-700 border-zinc-200';
          let StatusIcon = Clock;

          if (isSuccess) {
            statusBadge = 'bg-emerald-50 text-emerald-800 border-emerald-200';
            StatusIcon = CheckCircle2;
          } else if (isInProgress) {
            statusBadge = 'bg-amber-50 text-amber-800 border-amber-200';
            StatusIcon = Clock;
          } else if (isWarning) {
            statusBadge = 'bg-orange-50 text-orange-800 border-orange-200';
            StatusIcon = AlertTriangle;
          } else if (isFailed) {
            statusBadge = 'bg-rose-50 text-rose-800 border-rose-200';
            StatusIcon = XCircle;
          }

          return (
            <div
              key={idx}
              className="p-3 rounded-lg border border-zinc-200/80 bg-zinc-50/40 hover:bg-zinc-50 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-2"
            >
              <div className="flex items-start space-x-3">
                <div className={`mt-0.5 p-1 rounded-md border ${statusBadge} shrink-0`}>
                  <StatusIcon className="w-3.5 h-3.5" />
                </div>

                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-zinc-900">
                      {item.action}
                    </span>
                    <span className="text-[10px] font-medium px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700 border border-indigo-100">
                      {item.stage}
                    </span>
                  </div>

                  <p className="text-xs text-zinc-600 mt-0.5">
                    {item.details}
                  </p>

                  <span className="text-[11px] text-zinc-400 font-medium">
                    Agent: <span className="text-zinc-600">{item.agent}</span>
                  </span>
                </div>
              </div>

              <div className="text-right sm:shrink-0 text-[10px] font-mono text-zinc-400 pl-8 sm:pl-0">
                {item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : ''}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
