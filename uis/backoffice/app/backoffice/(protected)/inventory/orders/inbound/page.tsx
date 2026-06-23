"use client";

import { FormEvent, useMemo, useState } from "react";
import { inventoryApi } from "@/lib/inventory-api";
import { useInventoryProducts } from "@/lib/hooks/use-inventory-products";
import type { InboundOrderCreate, WarehouseCode } from "@/lib/inventory-types";

const initialForm: InboundOrderCreate = {
  sku_id: 0,
  quantity: 1,
  reference: "",
  warehouse: "LA",
};

export default function InboundOrdersPage() {
  const [form, setForm] = useState<InboundOrderCreate>(initialForm);
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

  const handleSkuChange = (skuId: number) => {
    setForm((current) => ({
      ...current,
      sku_id: skuId,
      warehouse: getWarehouseForSku(skuId, current.warehouse),
    }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const payload: InboundOrderCreate = {
        ...form,
        sku_id: effectiveSkuId,
        warehouse: effectiveWarehouse,
      };

      await inventoryApi.createInboundOrder(payload);
      setSuccess("Entrada registrada correctamente.");
      setForm((current) => ({ ...current, quantity: 1, reference: "" }));
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "No se pudo registrar la entrada.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <main>
      <header className="page-head card-reveal">
        <p className="kicker">Inventory Orders</p>
        <h2>Inbound</h2>
        <p className="muted">Registra recepciones de inventario y actualiza stock por warehouse.</p>
      </header>

      <section className="panel card-reveal">
        {loading ? <p className="muted">Cargando datos...</p> : null}
        {!loading && products.length === 0 ? (
          <p className="notice notice-warning">Primero crea al menos un producto para registrar entradas.</p>
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
              Referencia
              <input
                className="input"
                value={form.reference}
                onChange={(event) => setForm((current) => ({ ...current, reference: event.target.value }))}
                required
              />
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

            <button className="button-primary" type="submit" disabled={saving}>
              {saving ? "Guardando..." : "Registrar inbound"}
            </button>
          </form>
        ) : null}

        {error || loadError ? <p className="notice notice-error">{error || loadError}</p> : null}
        {success ? <p className="notice notice-success">{success}</p> : null}
      </section>
    </main>
  );
}
