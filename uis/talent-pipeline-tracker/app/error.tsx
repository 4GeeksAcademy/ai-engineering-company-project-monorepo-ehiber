"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 px-6">
      <div className="max-w-xl rounded-[2rem] border border-rose-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-[0.3em] text-rose-600">
          Error de aplicacion
        </p>
        <h1 className="mt-3 text-3xl font-semibold text-slate-900">
          No pudimos cargar el tracker de TrackFlow
        </h1>
        <p className="mt-3 text-sm leading-7 text-slate-600">{error.message}</p>
        <button
          className="mt-6 rounded-full bg-slate-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-700"
          onClick={reset}
          type="button"
        >
          Reintentar
        </button>
      </div>
    </main>
  );
}
