"use client";

import { useCallback, useEffect, useState } from "react";
import { incidentsApi } from "@/lib/incidents-api";
import type {
  Incident,
  IncidentBranch,
  IncidentCategory,
  IncidentOrigin,
  IncidentStatus,
  IncidentSummary,
} from "@/lib/incidents-types";

type IncidentFilters = {
  statusFilter: "all" | IncidentStatus;
  originFilter: "all" | IncidentOrigin;
  branchFilter: "all" | IncidentBranch;
  categoryFilter: "all" | IncidentCategory;
};

const parseFieldError = (message: string): string => {
  try {
    const parsed = JSON.parse(message) as { field?: string; message?: string };
    return parsed.message ?? message;
  } catch {
    return message;
  }
};

export function useIncidentsData({
  statusFilter,
  originFilter,
  branchFilter,
  categoryFilter,
}: IncidentFilters) {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [summary, setSummary] = useState<IncidentSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setLoadError("");

    try {
      const [list, stats] = await Promise.all([
        incidentsApi.list({
          status: statusFilter === "all" ? undefined : statusFilter,
          origin: originFilter === "all" ? undefined : originFilter,
          branch: branchFilter === "all" ? undefined : branchFilter,
          category: categoryFilter === "all" ? undefined : categoryFilter,
        }),
        incidentsApi.summary(),
      ]);

      setIncidents(list);
      setSummary(stats);
    } catch (error) {
      setLoadError(
        error instanceof Error
          ? parseFieldError(error.message)
          : "No se pudieron cargar incidentes.",
      );
    } finally {
      setLoading(false);
    }
  }, [branchFilter, categoryFilter, originFilter, statusFilter]);

  useEffect(() => {
    let active = true;

    const sync = async () => {
      setLoading(true);
      setLoadError("");

      try {
        const [list, stats] = await Promise.all([
          incidentsApi.list({
            status: statusFilter === "all" ? undefined : statusFilter,
            origin: originFilter === "all" ? undefined : originFilter,
            branch: branchFilter === "all" ? undefined : branchFilter,
            category: categoryFilter === "all" ? undefined : categoryFilter,
          }),
          incidentsApi.summary(),
        ]);

        if (!active) {
          return;
        }

        setIncidents(list);
        setSummary(stats);
      } catch (error) {
        if (!active) {
          return;
        }

        setLoadError(
          error instanceof Error
            ? parseFieldError(error.message)
            : "No se pudieron cargar incidentes.",
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void sync();

    return () => {
      active = false;
    };
  }, [branchFilter, categoryFilter, originFilter, statusFilter]);

  return {
    incidents,
    setIncidents,
    summary,
    setSummary,
    loading,
    loadError,
    refresh,
    parseFieldError,
  };
}
