"use client";

import { FormEvent, useEffect, useState } from "react";
import { inventoryApi } from "@/lib/inventory-api";
import type { ExitType, OutboundOrderCreate, Product, WarehouseCode } from "@/lib/inventory-types";

const initialForm: OutboundOrderCreate = {
  sku_id: 0,
  quantity: 1,
  exit_type: "dispatch",
  tracking_number: "",
  warehouse: "LA",
};

export default function OutboundOrdersPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [form, setForm] = useState<OutboundOrderCreate>(initialForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const result = await inventoryApi.listProducts();
        setProducts(result);
        if (result.length > 0) {
          setForm((current) => ({
            ...current,
            sku_id: result[0].id,
            warehouse: result[0].warehouse,
          }));
        }
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "No se pudieron cargar los productos.");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const handleSkuChange = (skuId: number) => {
    const selected = products.find((item) => item.id === skuId);
    setForm((current) => ({
      ...current,
      sku_id: skuId,
      warehouse: selected?.warehouse ?? current.warehouse,
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
        tracking_number:
          form.exit_type === "dispatch"
            ? (form.tracking_number || "").trim() || null
            : null,
      };

      await inventoryApi.createOutboundOrder(payload);
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
                value={form.sku_id}
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
                value={form.warehouse}
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

        {error ? <p className="notice notice-error">{error}</p> : null}
        {success ? <p className="notice notice-success">{success}</p> : null}
      </section>
    </main>
  );
}
