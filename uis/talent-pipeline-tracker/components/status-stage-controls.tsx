"use client";

import { STAGE_OPTIONS, STATUS_OPTIONS } from "@/lib/constants";

export function StatusStageControls({
  status,
  stage,
  isUpdatingStatus,
  isUpdatingStage,
  onStatusChange,
  onStageChange,
}: {
  status: string;
  stage: string;
  isUpdatingStatus: boolean;
  isUpdatingStage: boolean;
  onStatusChange: (nextStatus: string) => Promise<void>;
  onStageChange: (nextStage: string) => Promise<void>;
}) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
        Estado de la candidatura
        <select
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          disabled={isUpdatingStatus}
          onChange={(event) => void onStatusChange(event.target.value)}
          value={status}
        >
          {STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
        Etapa actual
        <select
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          disabled={isUpdatingStage}
          onChange={(event) => void onStageChange(event.target.value)}
          value={stage}
        >
          {STAGE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
