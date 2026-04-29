"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { trackerApi } from "@/lib/api";
import { formatDateTime, formatRelativeYears } from "@/lib/formatters";
import type {
  CandidateRecord,
  CandidateRecordCreate,
  CandidateNote,
  FeedbackMessage,
} from "@/types/tracker";
import { CandidateStatusBadge } from "./candidate-status-badge";
import { CandidateForm, getCandidateFormDefaults } from "./candidate-form";
import { EmptyState } from "./empty-state";
import { ErrorState } from "./error-state";
import { FeedbackBanner } from "./feedback-banner";
import { LoadingState } from "./loading-state";
import { NotesPanel } from "./notes-panel";
import { StatusStageControls } from "./status-stage-controls";

export function CandidateDetailPage({
  candidateId,
}: {
  candidateId: string;
}) {
  const [candidate, setCandidate] = useState<CandidateRecord | null>(null);
  const [notes, setNotes] = useState<CandidateNote[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [notesLoading, setNotesLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [candidateFeedback, setCandidateFeedback] = useState<FeedbackMessage | null>(null);
  const [notesFeedback, setNotesFeedback] = useState<FeedbackMessage | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isSavingCandidate, setIsSavingCandidate] = useState(false);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [isUpdatingStage, setIsUpdatingStage] = useState(false);

  const loadCandidate = useCallback(async () => {
    const [candidateResponse, notesResponse] = await Promise.all([
      trackerApi.getRecordById(candidateId),
      trackerApi.getNotes(candidateId),
    ]);

    setCandidate(candidateResponse);
    setNotes(notesResponse.data);
  }, [candidateId]);

  useEffect(() => {
    const run = async () => {
      setIsLoading(true);
      setNotesLoading(true);
      setError(null);

      try {
        await loadCandidate();
      } catch (loadError) {
        setError(
          loadError instanceof Error
            ? loadError.message
            : "No pudimos cargar la candidatura seleccionada.",
        );
      } finally {
        setIsLoading(false);
        setNotesLoading(false);
      }
    };

    void run();
  }, [candidateId, loadCandidate]);

  const refreshNotes = async () => {
    setNotesLoading(true);

    try {
      const notesResponse = await trackerApi.getNotes(candidateId);
      setNotes(notesResponse.data);
      setCandidate((currentCandidate) =>
        currentCandidate
          ? {
              ...currentCandidate,
              notes_count: notesResponse.meta.total,
            }
          : currentCandidate,
      );
    } finally {
      setNotesLoading(false);
    }
  };

  const handleStatusChange = async (nextStatus: string) => {
    if (!candidate || nextStatus === candidate.status) {
      return;
    }

    setIsUpdatingStatus(true);
    setCandidateFeedback(null);

    try {
      const updatedRecord = await trackerApi.patchRecord(candidate.id, { status: nextStatus });
      setCandidate(updatedRecord);
      setCandidateFeedback({
        type: "success",
        text: "Estado actualizado correctamente.",
      });
    } catch (updateError) {
      setCandidateFeedback({
        type: "error",
        text:
          updateError instanceof Error
            ? updateError.message
            : "No pudimos actualizar el estado.",
      });
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const handleStageChange = async (nextStage: string) => {
    if (!candidate || nextStage === candidate.stage) {
      return;
    }

    setIsUpdatingStage(true);
    setCandidateFeedback(null);

    try {
      const updatedRecord = await trackerApi.patchRecord(candidate.id, { stage: nextStage });
      setCandidate(updatedRecord);
      setCandidateFeedback({
        type: "success",
        text: "Etapa actualizada correctamente.",
      });
    } catch (updateError) {
      setCandidateFeedback({
        type: "error",
        text:
          updateError instanceof Error
            ? updateError.message
            : "No pudimos actualizar la etapa.",
      });
    } finally {
      setIsUpdatingStage(false);
    }
  };

  const handleCandidateEdit = async (payload: CandidateRecordCreate) => {
    if (!candidate) {
      return;
    }

    setIsSavingCandidate(true);
    setCandidateFeedback(null);

    try {
      const updatedRecord = await trackerApi.updateRecord(candidate.id, payload);
      setCandidate(updatedRecord);
      setCandidateFeedback({
        type: "success",
        text: "La candidatura se actualizo correctamente.",
      });
      setIsEditing(false);
    } catch (updateError) {
      setCandidateFeedback({
        type: "error",
        text:
          updateError instanceof Error
            ? updateError.message
            : "No pudimos actualizar la candidatura.",
      });
    } finally {
      setIsSavingCandidate(false);
    }
  };

  const handleCreateNote = async (content: string) => {
    setNotesFeedback(null);

    try {
      await trackerApi.createNote(candidateId, content);
      await refreshNotes();
      setNotesFeedback({
        type: "success",
        text: "La nota interna se guardo correctamente.",
      });
    } catch (noteError) {
      setNotesFeedback({
        type: "error",
        text:
          noteError instanceof Error
            ? noteError.message
            : "No pudimos guardar la nota.",
      });
    }
  };

  const handleDeleteNote = async (noteId: string) => {
    setNotesFeedback(null);

    try {
      await trackerApi.deleteNote(candidateId, noteId);
      await refreshNotes();
      setNotesFeedback({
        type: "success",
        text: "La nota se elimino correctamente.",
      });
    } catch (noteError) {
      setNotesFeedback({
        type: "error",
        text:
          noteError instanceof Error
            ? noteError.message
            : "No pudimos eliminar la nota.",
      });
    }
  };

  if (isLoading) {
    return (
      <main className="min-h-screen bg-[radial-gradient(circle_at_top,#f4f8f5_0%,#edf4ef_48%,#e5ece7_100%)] px-6 py-14">
        <div className="mx-auto max-w-6xl">
          <LoadingState label="Cargando candidatura..." />
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-[radial-gradient(circle_at_top,#f4f8f5_0%,#edf4ef_48%,#e5ece7_100%)] px-6 py-14">
        <div className="mx-auto max-w-6xl">
          <ErrorState
            message={error}
            onRetry={() => {
              void loadCandidate();
            }}
            title="No pudimos cargar el detalle de la candidatura"
          />
        </div>
      </main>
    );
  }

  if (!candidate) {
    return (
      <main className="min-h-screen bg-[radial-gradient(circle_at_top,#f4f8f5_0%,#edf4ef_48%,#e5ece7_100%)] px-6 py-14">
        <div className="mx-auto max-w-6xl">
          <EmptyState
            description="Comprueba el identificador o vuelve al listado para abrir otra candidatura."
            title="No encontramos esta candidatura"
          />
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,#f4f8f5_0%,#edf4ef_48%,#e5ece7_100%)] px-6 py-14">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="rounded-[2.5rem] border border-white/70 bg-[linear-gradient(135deg,#173325_0%,#1f4531_48%,#24533c_100%)] p-8 text-white shadow-lg">
          <Link
            className="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-100/80 transition hover:text-white"
            href="/"
          >
            Volver al pipeline
          </Link>
          <div className="mt-5 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-4xl font-semibold tracking-tight">{candidate.full_name}</h1>
              <p className="mt-3 text-sm leading-7 text-emerald-50/85 md:text-base">
                Candidatura para {candidate.position} en el flujo interno de People & Talent de TrackFlow.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <CandidateStatusBadge kind="status" value={candidate.status} />
              <CandidateStatusBadge kind="stage" value={candidate.stage} />
            </div>
          </div>
        </header>

        <FeedbackBanner message={candidateFeedback} />

        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-6">
            <div className="rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold text-slate-900">
                    Resumen de candidatura
                  </h2>
                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    Informacion principal para coordinar entrevistas, actualizar estado y preparar feedback interno.
                  </p>
                </div>
                <button
                  className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                  onClick={() => setIsEditing((currentValue) => !currentValue)}
                  type="button"
                >
                  {isEditing ? "Cerrar edicion" : "Editar candidatura"}
                </button>
              </div>

              <dl className="mt-6 grid gap-5 sm:grid-cols-2">
                {[
                  ["Email", candidate.email],
                  ["Telefono", candidate.phone],
                  ["Puesto", candidate.position],
                  ["LinkedIn", candidate.linkedin_url ?? "No disponible"],
                  ["CV", candidate.cv_url ?? "No disponible"],
                  ["Experiencia", formatRelativeYears(candidate.experience_years)],
                  ["Aplico", formatDateTime(candidate.applied_at)],
                  ["Ultima actualizacion", formatDateTime(candidate.updated_at)],
                ].map(([label, value]) => (
                  <div key={label}>
                    <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                      {label}
                    </dt>
                    <dd className="mt-2 text-sm leading-6 text-slate-800 break-words">
                      {String(value)}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>

            <div className="rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-sm">
              <h2 className="text-xl font-semibold text-slate-900">Estado del pipeline</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Actualiza el estado o la etapa con una sola interaccion. Los cambios se reflejan de inmediato sin recargar la pagina.
              </p>
              <div className="mt-5">
                <StatusStageControls
                  isUpdatingStage={isUpdatingStage}
                  isUpdatingStatus={isUpdatingStatus}
                  onStageChange={handleStageChange}
                  onStatusChange={handleStatusChange}
                  stage={candidate.stage}
                  status={candidate.status}
                />
              </div>
            </div>

            {isEditing ? (
              <CandidateForm
                description="Corrige datos del perfil sin alterar el estado ni la etapa actual de la candidatura."
                feedback={candidateFeedback?.type === "error" ? candidateFeedback : null}
                initialValues={getCandidateFormDefaults(candidate)}
                isSubmitting={isSavingCandidate}
                onCancel={() => setIsEditing(false)}
                onSubmit={handleCandidateEdit}
                submitLabel="Guardar cambios"
                title="Editar candidatura"
              />
            ) : null}
          </div>

          <div className="space-y-6">
            <div className="rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                Notas registradas
              </p>
              <p className="mt-3 text-3xl font-semibold text-slate-900">
                {candidate.notes_count}
              </p>
            </div>

            <NotesPanel
              feedback={notesFeedback}
              isLoading={notesLoading}
              notes={notes}
              onCreateNote={handleCreateNote}
              onDeleteNote={handleDeleteNote}
            />
          </div>
        </section>
      </div>
    </main>
  );
}
