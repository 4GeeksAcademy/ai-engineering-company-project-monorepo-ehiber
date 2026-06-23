"use client";

import { useCallback, useEffect, useState } from "react";
import { suppliersApi } from "@/lib/suppliers-api";
import type { Supplier, SupplierCategory, SupplierCountry } from "@/lib/suppliers-types";

type SupplierFilters = {
  countryFilter: "all" | SupplierCountry;
  categoryFilter: "all" | SupplierCategory;
};

export function useSuppliersData({ countryFilter, categoryFilter }: SupplierFilters) {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setLoadError("");

    try {
      const result = await suppliersApi.list({
        country: countryFilter === "all" ? undefined : countryFilter,
        category: categoryFilter === "all" ? undefined : categoryFilter,
      });
      setSuppliers(result);
    } catch (error) {
      setLoadError(
        error instanceof Error ? error.message : "No se pudieron cargar suppliers.",
      );
    } finally {
      setLoading(false);
    }
  }, [categoryFilter, countryFilter]);

  useEffect(() => {
    let active = true;

    const sync = async () => {
      setLoading(true);
      setLoadError("");

      try {
        const result = await suppliersApi.list({
          country: countryFilter === "all" ? undefined : countryFilter,
          category: categoryFilter === "all" ? undefined : categoryFilter,
        });

        if (!active) {
          return;
        }

        setSuppliers(result);
      } catch (error) {
        if (!active) {
          return;
        }

        setLoadError(
          error instanceof Error ? error.message : "No se pudieron cargar suppliers.",
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
  }, [categoryFilter, countryFilter]);

  return {
    suppliers,
    setSuppliers,
    loading,
    loadError,
    refresh,
  };
}
