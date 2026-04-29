"use client";

import { useState } from "react";
import type { CandidateNote, FeedbackMessage } from "@/types/tracker";
import { FeedbackBanner } from "./feedback-banner";
import { EmptyState } from "./empty-state";
import { formatDateTime } from "@/lib/formatters";

export function NotesPanel({
  notes,
  isLoading,
  feedback,
  onCreateNote,
  onDeleteNote,
}: {
  notes: CandidateNote[];
  isLoading: boolean;
  feedback: FeedbackMessage | null;
  onCreateNote: (content: string) => Promise<void>;
  onDeleteNote: (noteId: string) => Promise<void>;
}) {
  const [draft, setDraft] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!draft.trim()) {
      return;
    }

    setIsSubmitting(true);

    try {
      await onCreateNote(draft.trim());
      setDraft("");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (noteId: string) => {
    setPendingDeleteId(noteId);

    try {
      await onDeleteNote(noteId);
    } finally {
      setPendingDeleteId(null);
    }
  };

  return (
    <section className="space-y-5 rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-sm">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Notas internas del equipo</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Usa este espacio para registrar observaciones de entrevistas, follow-ups y decisiones del pipeline.
        </p>
      </div>

      <FeedbackBanner message={feedback} />

      <form className="space-y-3" onSubmit={handleSubmit}>
        <label className="flex flex-col gap-2 text-sm font-medium text-slate-700">
          Nueva nota
          <textarea
            className="min-h-28 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Ej. Confirmar disponibilidad para entrevista tecnica esta semana."
            value={draft}
          />
        </label>
        <button
          className="rounded-full bg-slate-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-400"
          disabled={isSubmitting || !draft.trim()}
          type="submit"
        >
          {isSubmitting ? "Guardando nota..." : "Agregar nota"}
        </button>
      </form>

      {isLoading ? (
        <p className="text-sm text-slate-500">Cargando notas...</p>
      ) : notes.length === 0 ? (
        <EmptyState
          description="Todavia no hay notas registradas para esta candidatura."
          title="Sin notas internas"
        />
      ) : (
        <div className="space-y-3">
          {notes.map((note) => (
            <article
              className="rounded-3xl border border-slate-200 bg-slate-50 p-4"
              key={note.id}
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-sm leading-6 text-slate-800">{note.content}</p>
                  <p className="mt-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
                    {formatDateTime(note.created_at)}
                  </p>
                </div>
                <button
                  className="rounded-full border border-rose-200 px-4 py-2 text-sm font-medium text-rose-700 transition hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={pendingDeleteId === note.id}
                  onClick={() => void handleDelete(note.id)}
                  type="button"
                >
                  {pendingDeleteId === note.id ? "Eliminando..." : "Eliminar"}
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
