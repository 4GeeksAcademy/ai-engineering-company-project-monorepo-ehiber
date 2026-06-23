"use client";

import { useCallback, useEffect, useState } from "react";
import { inventoryApi } from "@/lib/inventory-api";
import type { Product, WarehouseCode } from "@/lib/inventory-types";

export function useInventoryProducts() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setLoadError("");

    try {
      const result = await inventoryApi.listProducts();
      setProducts(result);
      return result;
    } catch (error) {
      setLoadError(
        error instanceof Error ? error.message : "No se pudieron cargar los productos.",
      );
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;

    const load = async () => {
      setLoading(true);
      setLoadError("");

      try {
        const result = await inventoryApi.listProducts();

        if (!active) {
          return;
        }

        setProducts(result);
      } catch (error) {
        if (!active) {
          return;
        }

        setLoadError(
          error instanceof Error ? error.message : "No se pudieron cargar los productos.",
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void load();

    return () => {
      active = false;
    };
  }, []);

  const getWarehouseForSku = useCallback(
    (skuId: number, fallback: WarehouseCode): WarehouseCode => {
      const selected = products.find((item) => item.id === skuId);
      return selected?.warehouse ?? fallback;
    },
    [products],
  );

  return {
    products,
    loading,
    loadError,
    refresh,
    getWarehouseForSku,
  };
}
