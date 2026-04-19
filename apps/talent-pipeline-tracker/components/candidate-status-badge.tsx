import { getStageLabel, getStatusLabel } from "@/lib/formatters";

export function CandidateStatusBadge({
  kind,
  value,
}: {
  kind: "status" | "stage";
  value: string;
}) {
  const label = kind === "status" ? getStatusLabel(value) : getStageLabel(value);
  const palette =
    kind === "status"
      ? {
          received: "bg-slate-100 text-slate-700",
          in_progress: "bg-amber-100 text-amber-800",
          selected: "bg-emerald-100 text-emerald-800",
          discarded: "bg-rose-100 text-rose-800",
        }
      : {
          pending: "bg-slate-100 text-slate-700",
          review: "bg-cyan-100 text-cyan-800",
          personal_interview: "bg-indigo-100 text-indigo-800",
          technical_interview: "bg-fuchsia-100 text-fuchsia-800",
          offer_presented: "bg-emerald-100 text-emerald-800",
        };

  const colorClass =
    palette[value as keyof typeof palette] ?? "bg-slate-100 text-slate-700";

  return (
    <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${colorClass}`}>
      {label}
    </span>
  );
}
