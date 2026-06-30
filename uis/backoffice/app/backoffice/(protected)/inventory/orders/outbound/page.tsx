"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { inventoryApi } from "@/lib/inventory-api";
import { useInventoryProducts } from "@/lib/hooks/use-inventory-products";
import { track, WAREHOUSE_MAP } from "@/lib/telemetry";
import type { ExitType, OutboundOrderCreate, WarehouseCode } from "@/lib/inventory-types";

const initialForm: OutboundOrderCreate = {
  sku_id: 0,
  quantity: 1,
  exit_type: "dispatch",
  tracking_number: "",
  warehouse: "LA",
};

export default function OutboundOrdersPage() {
  const [form, setForm] = useState<OutboundOrderCreate>(initialForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const { products, loading, loadError, getWarehouseForSku } = useInventoryProducts();

  const effectiveSkuId = useMemo(() => {
    if (products.length === 0) {
      return 0;
    }

    if (form.sku_id !== 0) {
      return form.sku_id;
    }

    return products[0].id;
  }, [form.sku_id, products]);

  const effectiveWarehouse = useMemo(() => {
    if (products.length === 0) {
      return form.warehouse;
    }

    if (form.sku_id === 0) {
      return products[0].warehouse;
    }

    return getWarehouseForSku(form.sku_id, form.warehouse);
  }, [form.sku_id, form.warehouse, getWarehouseForSku, products]);

  const formSessionId = useRef<string>(
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : Date.now().toString(36),
  );
  const formStartTime = useRef<number>(Date.now());
  const formSubmitted = useRef(false);

  // Detectar abandono del formulario
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (!formSubmitted.current) {
        const secondsOnForm = Math.floor((Date.now() - formStartTime.current) / 1000);
        track("dispatch_form_abandoned", {
          warehouse: WAREHOUSE_MAP[form.warehouse],
          sku_id: effectiveSkuId || null,
          form_session_id: formSessionId.current,
          seconds_on_form: secondsOnForm,
          abandon_reason: "navigation_away",
        });
      }
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState === "hidden" && !formSubmitted.current) {
        const secondsOnForm = Math.floor((Date.now() - formStartTime.current) / 1000);
        track("dispatch_form_abandoned", {
          warehouse: WAREHOUSE_MAP[form.warehouse],
          sku_id: effectiveSkuId || null,
          form_session_id: formSessionId.current,
          seconds_on_form: secondsOnForm,
          abandon_reason: "tab_closed",
        });
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [form.warehouse, effectiveSkuId]);

  const handleSkuChange = (skuId: number) => {
    setForm((current) => ({
      ...current,
      sku_id: skuId,
      warehouse: getWarehouseForSku(skuId, current.warehouse),
    }));
  };

  const handleExitTypeChange = (exitType: ExitType) => {
    setForm((current) => ({
      ...current,
      exit_type: exitType,
      tracking_number: exitType === "loss" ? null : current.tracking_number || "",
    }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const payload: OutboundOrderCreate = {
        ...form,
        sku_id: effectiveSkuId,
        warehouse: effectiveWarehouse,
        tracking_number:
          form.exit_type === "dispatch"
            ? (form.tracking_number || "").trim() || null
            : null,
      };

      await inventoryApi.createOutboundOrder(payload);
      formSubmitted.current = true;
      track("outbound_order_submitted", {
        sku_id: payload.sku_id,
        quantity: payload.quantity,
        warehouse: WAREHOUSE_MAP[payload.warehouse],
        exit_type: payload.exit_type,
        tracking_number: payload.tracking_number,
      });
      setSuccess("Salida registrada correctamente.");
      setForm((current) => ({
        ...current,
        quantity: 1,
        tracking_number: current.exit_type === "dispatch" ? "" : null,
      }));
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "No se pudo registrar la salida.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <main>
      <header className="page-head card-reveal">
        <p className="kicker">Inventory Orders</p>
        <h2>Outbound</h2>
        <p className="muted">Registra despachos o perdidas y valida tracking segun tipo de salida.</p>
      </header>

      <section className="panel card-reveal">
        {loading ? <p className="muted">Cargando datos...</p> : null}
        {!loading && products.length === 0 ? (
          <p className="notice notice-warning">Primero crea al menos un producto para registrar salidas.</p>
        ) : null}

        {!loading && products.length > 0 ? (
          <form className="form-grid" onSubmit={handleSubmit}>
            <label>
              Producto SKU
              <select
                className="input"
                value={effectiveSkuId}
                onChange={(event) => handleSkuChange(Number(event.target.value))}
                required
              >
                {products.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.sku} - {product.name}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Cantidad
              <input
                className="input"
                type="number"
                min={1}
                value={form.quantity}
                onChange={(event) =>
                  setForm((current) => ({ ...current, quantity: Number(event.target.value) }))
                }
                required
              />
            </label>

            <label>
              Tipo de salida
              <select
                className="input"
                value={form.exit_type}
                onChange={(event) => handleExitTypeChange(event.target.value as ExitType)}
                required
              >
                <option value="dispatch">dispatch</option>
                <option value="loss">loss</option>
              </select>
            </label>

            <label>
              Warehouse
              <select
                className="input"
                value={effectiveWarehouse}
                onChange={(event) =>
                  setForm((current) => ({ ...current, warehouse: event.target.value as WarehouseCode }))
                }
                required
              >
                <option value="LA">LA</option>
                <option value="ZGZ">ZGZ</option>
              </select>
            </label>

            <label>
              Tracking number
              <input
                className="input"
                value={form.tracking_number ?? ""}
                disabled={form.exit_type === "loss"}
                onChange={(event) =>
                  setForm((current) => ({ ...current, tracking_number: event.target.value }))
                }
                placeholder={form.exit_type === "loss" ? "No aplica para loss" : "TRACK-123"}
              />
            </label>

            <button className="button-primary" type="submit" disabled={saving}>
              {saving ? "Guardando..." : "Registrar outbound"}
            </button>
          </form>
        ) : null}

        {error || loadError ? <p className="notice notice-error">{error || loadError}</p> : null}
        {success ? <p className="notice notice-success">{success}</p> : null}
      </section>
    </main>
  );
}
