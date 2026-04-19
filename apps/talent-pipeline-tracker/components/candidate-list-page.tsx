"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { CandidateFilters } from "./candidate-filters";
import { CandidateTable } from "./candidate-table";
import { CandidateForm, getCandidateFormDefaults } from "./candidate-form";
import { EmptyState } from "./empty-state";
import { ErrorState } from "./error-state";
import { FeedbackBanner } from "./feedback-banner";
import { LoadingState } from "./loading-state";
import { TRACKFLOW_COPY } from "@/lib/constants";
import { trackerApi } from "@/lib/api";
import type {
  CandidateListResponse,
  CandidateRecord,
  CandidateRecordCreate,
  FeedbackMessage,
} from "@/types/tracker";

export function CandidateListPage() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [response, setResponse] = useState<CandidateListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackMessage | null>(null);

  const queryKey = searchParams.toString();

  const currentPage = Number(searchParams.get("page") ?? "1") || 1;

  const loadRecords = useCallback(async (activeQuery: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams(activeQuery);
      const nextResponse = await trackerApi.getRecords({
        status: params.get("status") ?? undefined,
        stage: params.get("stage") ?? undefined,
        search: params.get("search") ?? undefined,
        page: Number(params.get("page") ?? "1") || 1,
      });
      setResponse(nextResponse);
    } catch (loadError) {
      const message =
        loadError instanceof Error
          ? loadError.message
          : "No pudimos cargar las candidaturas de TrackFlow.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const run = async () => {
      await loadRecords(queryKey);
    };

    void run();
  }, [queryKey, loadRecords]);

  const handleCreateCandidate = async (payload: CandidateRecordCreate) => {
    setIsCreating(true);
    setFeedback(null);

    try {
      await trackerApi.createRecord(payload);
      setFeedback({
        type: "success",
        text: "La candidatura se registro correctamente en el pipeline de TrackFlow.",
      });
      setIsCreateOpen(false);
      await loadRecords(queryKey);
    } catch (createError) {
      setFeedback({
        type: "error",
        text:
          createError instanceof Error
            ? createError.message
            : "No pudimos registrar la candidatura.",
      });
    } finally {
      setIsCreating(false);
    }
  };

  const totalPages =
    response === null ? 1 : Math.max(1, Math.ceil(response.total / response.limit));

  const goToPage = (page: number) => {
    const params = new URLSearchParams(searchParams.toString());

    if (page <= 1) {
      params.delete("page");
    } else {
      params.set("page", String(page));
    }

    const nextUrl = params.toString() ? `${pathname}?${params}` : pathname;
    router.replace(nextUrl, { scroll: false });
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,#f4f8f5_0%,#edf4ef_48%,#e5ece7_100%)] px-6 py-14">
      <div className="mx-auto max-w-6xl space-y-6">
        <section className="rounded-[2.5rem] border border-white/70 bg-[linear-gradient(135deg,#173325_0%,#1f4531_48%,#24533c_100%)] p-8 text-white shadow-lg">
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-emerald-100/80">
            {TRACKFLOW_COPY.eyebrow}
          </p>
          <h1 className="mt-4 max-w-3xl text-4xl font-semibold tracking-tight md:text-5xl">
            {TRACKFLOW_COPY.title}
          </h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-emerald-50/85 md:text-base">
            {TRACKFLOW_COPY.description}
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button
              className="rounded-full bg-white px-5 py-3 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-50"
              onClick={() => setIsCreateOpen((currentValue) => !currentValue)}
              type="button"
            >
              {isCreateOpen ? "Cerrar formulario" : "Registrar candidatura"}
            </button>
          </div>
        </section>

        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
              Candidaturas visibles
            </p>
            <p className="mt-3 text-3xl font-semibold text-slate-900">
              {response?.total ?? "—"}
            </p>
          </div>
          <div className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
              Pagina actual
            </p>
            <p className="mt-3 text-3xl font-semibold text-slate-900">{currentPage}</p>
          </div>
          <div className="rounded-[2rem] border border-white/70 bg-white/85 p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
              Accion rapida
            </p>
            <p className="mt-3 text-sm leading-7 text-slate-700">
              Busca por email o mueve una candidatura al detalle para actualizar estado, etapa y notas internas.
            </p>
          </div>
        </div>

        <FeedbackBanner message={feedback} />

        {isCreateOpen ? (
          <CandidateForm
            description="Registra nuevos perfiles para que el equipo de People & Talent de TrackFlow pueda evaluarlos sin salir del tracker."
            feedback={feedback?.type === "error" ? feedback : null}
            initialValues={getCandidateFormDefaults()}
            isSubmitting={isCreating}
            onSubmit={handleCreateCandidate}
            submitLabel="Guardar candidatura"
            title="Nueva candidatura"
          />
        ) : null}

        <CandidateFilters />

        {isLoading ? (
          <LoadingState label="Cargando candidaturas del tracker..." />
        ) : error ? (
          <ErrorState
            message={error}
            onRetry={() => {
              void loadRecords(queryKey);
            }}
            title="No pudimos obtener el listado de candidaturas"
          />
        ) : response && response.data.length > 0 ? (
          <>
            <CandidateTable records={response.data as CandidateRecord[]} />

            <div className="flex flex-wrap items-center justify-between gap-4 rounded-[2rem] border border-white/70 bg-white/85 px-5 py-4 shadow-sm">
              <p className="text-sm text-slate-600">
                Mostrando pagina {response.page} de {totalPages}.
              </p>
              <div className="flex gap-3">
                <button
                  className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={currentPage <= 1}
                  onClick={() => goToPage(currentPage - 1)}
                  type="button"
                >
                  Anterior
                </button>
                <button
                  className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={currentPage >= totalPages}
                  onClick={() => goToPage(currentPage + 1)}
                  type="button"
                >
                  Siguiente
                </button>
              </div>
            </div>
          </>
        ) : (
          <EmptyState
            description="Prueba con otros filtros o registra una candidatura nueva para empezar a poblar el pipeline."
            title="No hay candidaturas para los filtros actuales"
          />
        )}

        <footer className="flex flex-wrap items-center justify-between gap-4 rounded-[2rem] border border-white/70 bg-white/70 px-5 py-4 text-sm text-slate-600">
          <p>
            Tracker conectado a la API publica de Playground para el flujo interno de TrackFlow.
          </p>
          <Link
            className="font-medium text-emerald-800 transition hover:text-emerald-600"
            href="https://playground.4geeks.com/tracker/api/v1/docs"
            rel="noreferrer"
            target="_blank"
          >
            Ver documentacion del API
          </Link>
        </footer>
      </div>
    </main>
  );
}
