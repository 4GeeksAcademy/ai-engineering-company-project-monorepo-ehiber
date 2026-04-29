import Link from "next/link";
import type { CandidateRecord } from "@/types/tracker";
import { CandidateStatusBadge } from "./candidate-status-badge";
import { formatDateTime, formatRelativeYears } from "@/lib/formatters";

export function CandidateTable({
  records,
}: {
  records: CandidateRecord[];
}) {
  return (
    <div className="overflow-hidden rounded-[2rem] border border-white/70 bg-white/90 shadow-sm">
      <div className="hidden grid-cols-[2.2fr_1.4fr_1fr_1.2fr_0.9fr_0.8fr] gap-4 border-b border-slate-200 px-6 py-4 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 lg:grid">
        <span>Candidatura</span>
        <span>Puesto</span>
        <span>Estado</span>
        <span>Etapa</span>
        <span>Experiencia</span>
        <span>Detalle</span>
      </div>

      <div className="divide-y divide-slate-100">
        {records.map((record) => (
          <article
            className="grid gap-4 px-6 py-5 lg:grid-cols-[2.2fr_1.4fr_1fr_1.2fr_0.9fr_0.8fr] lg:items-center"
            key={record.id}
          >
            <div>
              <h3 className="text-base font-semibold text-slate-900">{record.full_name}</h3>
              <p className="mt-1 text-sm text-slate-600">{record.email}</p>
              <p className="mt-1 text-xs text-slate-500">
                Aplico {formatDateTime(record.applied_at)}
              </p>
            </div>

            <div className="text-sm text-slate-700">{record.position}</div>
            <div>
              <CandidateStatusBadge kind="status" value={record.status} />
            </div>
            <div>
              <CandidateStatusBadge kind="stage" value={record.stage} />
            </div>
            <div className="text-sm text-slate-700">
              {formatRelativeYears(record.experience_years)}
            </div>
            <div>
              <Link
                className="inline-flex rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-800 transition hover:border-emerald-300 hover:bg-emerald-50"
                href={`/candidates/${record.id}`}
              >
                Abrir
              </Link>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
