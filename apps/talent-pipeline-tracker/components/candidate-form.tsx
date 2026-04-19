"use client";

import { useState } from "react";
import type {
  CandidateFormErrors,
  CandidateFormValues,
  CandidateRecord,
  CandidateRecordCreate,
  FeedbackMessage,
} from "@/types/tracker";
import { FeedbackBanner } from "./feedback-banner";

export const getCandidateFormDefaults = (
  candidate?: CandidateRecord,
): CandidateFormValues => ({
  full_name: candidate?.full_name ?? "",
  email: candidate?.email ?? "",
  phone: candidate?.phone ?? "",
  position: candidate?.position ?? "",
  linkedin_url: candidate?.linkedin_url ?? "",
  cv_url: candidate?.cv_url ?? "",
  experience_years:
    candidate?.experience_years !== undefined ? String(candidate.experience_years) : "",
});

const validateCandidateForm = (
  values: CandidateFormValues,
): CandidateFormErrors => {
  const errors: CandidateFormErrors = {};

  if (!values.full_name.trim()) {
    errors.full_name = "El nombre completo es obligatorio.";
  }

  if (!values.email.trim()) {
    errors.email = "El email es obligatorio.";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email.trim())) {
    errors.email = "Ingresa un email valido.";
  }

  if (!values.phone.trim()) {
    errors.phone = "El telefono es obligatorio.";
  }

  if (!values.position.trim()) {
    errors.position = "El puesto es obligatorio.";
  }

  if (!values.experience_years.trim()) {
    errors.experience_years = "Los anos de experiencia son obligatorios.";
  } else if (Number.isNaN(Number(values.experience_years))) {
    errors.experience_years = "Ingresa un numero valido.";
  }

  return errors;
};

const normalizePayload = (
  values: CandidateFormValues,
): CandidateRecordCreate => ({
  full_name: values.full_name.trim(),
  email: values.email.trim(),
  phone: values.phone.trim(),
  position: values.position.trim(),
  linkedin_url: values.linkedin_url.trim() || undefined,
  cv_url: values.cv_url.trim() || undefined,
  experience_years: Number(values.experience_years),
});

export function CandidateForm({
  initialValues,
  title,
  description,
  submitLabel,
  isSubmitting,
  feedback,
  onSubmit,
  onCancel,
}: {
  initialValues: CandidateFormValues;
  title: string;
  description: string;
  submitLabel: string;
  isSubmitting: boolean;
  feedback: FeedbackMessage | null;
  onSubmit: (payload: CandidateRecordCreate) => Promise<void>;
  onCancel?: () => void;
}) {
  const [values, setValues] = useState<CandidateFormValues>(initialValues);
  const [errors, setErrors] = useState<CandidateFormErrors>({});

  const updateField = (field: keyof CandidateFormValues, value: string) => {
    setValues((currentValues) => ({
      ...currentValues,
      [field]: value,
    }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextErrors = validateCandidateForm(values);
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    await onSubmit(normalizePayload(values));
  };

  const fields: Array<{
    name: keyof CandidateFormValues;
    label: string;
    type?: string;
    placeholder?: string;
  }> = [
    { name: "full_name", label: "Nombre completo" },
    { name: "email", label: "Email", type: "email" },
    { name: "phone", label: "Telefono", type: "tel" },
    { name: "position", label: "Puesto" },
    {
      name: "linkedin_url",
      label: "LinkedIn",
      type: "url",
      placeholder: "https://linkedin.com/in/...",
    },
    {
      name: "cv_url",
      label: "CV",
      type: "url",
      placeholder: "https://...",
    },
    {
      name: "experience_years",
      label: "Anos de experiencia",
      type: "number",
    },
  ];

  return (
    <form
      className="space-y-5 rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-sm"
      onSubmit={handleSubmit}
    >
      <div>
        <h3 className="text-xl font-semibold text-slate-900">{title}</h3>
        <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
      </div>

      <FeedbackBanner message={feedback} />

      <div className="grid gap-4 md:grid-cols-2">
        {fields.map((field) => (
          <label className="flex flex-col gap-2 text-sm font-medium text-slate-700" key={field.name}>
            {field.label}
            <input
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
              min={field.name === "experience_years" ? "0" : undefined}
              onChange={(event) => updateField(field.name, event.target.value)}
              placeholder={field.placeholder}
              type={field.type ?? "text"}
              value={values[field.name]}
            />
            {errors[field.name] ? (
              <span className="text-xs font-medium text-rose-600">{errors[field.name]}</span>
            ) : null}
          </label>
        ))}
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          className="rounded-full bg-slate-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-400"
          disabled={isSubmitting}
          type="submit"
        >
          {isSubmitting ? "Guardando..." : submitLabel}
        </button>
        {onCancel ? (
          <button
            className="rounded-full border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            onClick={onCancel}
            type="button"
          >
            Cancelar
          </button>
        ) : null}
      </div>
    </form>
  );
}
