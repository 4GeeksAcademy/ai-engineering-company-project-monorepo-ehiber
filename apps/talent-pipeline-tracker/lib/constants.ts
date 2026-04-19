export const STATUS_OPTIONS = [
  { value: "received", label: "Recibida" },
  { value: "in_progress", label: "En proceso" },
  { value: "selected", label: "Seleccionada" },
  { value: "discarded", label: "Descartada" },
] as const;

export const STAGE_OPTIONS = [
  { value: "pending", label: "Pendiente" },
  { value: "review", label: "Revision" },
  { value: "personal_interview", label: "Entrevista personal" },
  { value: "technical_interview", label: "Entrevista tecnica" },
  { value: "offer_presented", label: "Oferta enviada" },
] as const;

export const PAGE_SIZE = 12;

export const TRACKFLOW_COPY = {
  productName: "TrackFlow Talent Pipeline Tracker",
  eyebrow: "TrackFlow People & Talent",
  title: "Pipeline de candidaturas de TrackFlow",
  description:
    "Seguimiento interno de postulaciones para los equipos que hacen crecer la operacion binacional de TrackFlow.",
};
