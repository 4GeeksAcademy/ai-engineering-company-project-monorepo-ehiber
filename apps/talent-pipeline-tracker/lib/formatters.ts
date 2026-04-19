import { STAGE_OPTIONS, STATUS_OPTIONS } from "./constants";

export const formatDateTime = (isoDate: string): string => {
  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(isoDate));
};

export const formatRelativeYears = (years: number): string => {
  if (years === 1) {
    return "1 ano";
  }

  return `${years} anos`;
};

export const getStatusLabel = (status: string): string => {
  return STATUS_OPTIONS.find((option) => option.value === status)?.label ?? status;
};

export const getStageLabel = (stage: string): string => {
  return STAGE_OPTIONS.find((option) => option.value === stage)?.label ?? stage;
};
