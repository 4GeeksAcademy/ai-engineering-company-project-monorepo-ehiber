"use client";

import { startTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { STAGE_OPTIONS, STATUS_OPTIONS } from "@/lib/constants";

export function CandidateFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const replaceParams = (entries: Record<string, string | null>) => {
    const params = new URLSearchParams(searchParams.toString());

    Object.entries(entries).forEach(([key, value]) => {
      if (value) {
        params.set(key, value);
      } else {
        params.delete(key);
      }
    });

    if ("status" in entries || "stage" in entries || "search" in entries) {
      params.delete("page");
    }

    const nextUrl = params.toString() ? `${pathname}?${params}` : pathname;
    startTransition(() => {
      router.replace(nextUrl, { scroll: false });
    });
  };

  return (
    <div className="grid gap-4 rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm lg:grid-cols-[1.3fr_0.8fr_0.8fr]">
      <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
        Buscar por nombre o email
        <input
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          onChange={(event) => replaceParams({ search: event.target.value || null })}
          placeholder="Ej. maria@trackflow.com"
          value={searchParams.get("search") ?? ""}
        />
      </label>

      <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
        Estado
        <select
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          onChange={(event) => replaceParams({ status: event.target.value || null })}
          value={searchParams.get("status") ?? ""}
        >
          <option value="">Todos</option>
          {STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
        Etapa
        <select
          className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          onChange={(event) => replaceParams({ stage: event.target.value || null })}
          value={searchParams.get("stage") ?? ""}
        >
          <option value="">Todas</option>
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
