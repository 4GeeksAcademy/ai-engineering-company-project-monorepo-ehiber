"use client";

import { useCallback, useEffect, useRef, useState } from "react";
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

const buildListFilters = ({
  statusFilter,
  originFilter,
  branchFilter,
  categoryFilter,
}: IncidentFilters) => ({
  status: statusFilter === "all" ? undefined : statusFilter,
  origin: originFilter === "all" ? undefined : originFilter,
  branch: branchFilter === "all" ? undefined : branchFilter,
  category: categoryFilter === "all" ? undefined : categoryFilter,
});

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
  const includeSummaryRef = useRef(true);

  const loadSummary = useCallback(async () => {
    const stats = await incidentsApi.summary();
    setSummary(stats);
    return stats;
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    setLoadError("");

    try {
      const [list, stats] = await Promise.all([
        incidentsApi.list(
          buildListFilters({
            statusFilter,
            originFilter,
            branchFilter,
            categoryFilter,
          }),
        ),
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
        const listPromise = incidentsApi.list(
          buildListFilters({
            statusFilter,
            originFilter,
            branchFilter,
            categoryFilter,
          }),
        );

        if (includeSummaryRef.current) {
          const [list, stats] = await Promise.all([listPromise, incidentsApi.summary()]);
          includeSummaryRef.current = false;

          if (!active) {
            return;
          }

          setIncidents(list);
          setSummary(stats);
          return;
        }

        const list = await listPromise;

        if (!active) {
          return;
        }

        setIncidents(list);
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
    loadSummary,
    parseFieldError,
  };
}
