export function LoadingState({
  label,
}: {
  label: string;
}) {
  return (
    <div className="rounded-[1.75rem] border border-dashed border-slate-300 bg-white/80 px-6 py-10 text-center text-sm text-slate-600">
      {label}
    </div>
  );
}
