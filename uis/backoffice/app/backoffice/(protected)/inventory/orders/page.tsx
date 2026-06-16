"use client";

import { useEffect, useMemo, useState } from "react";
import { inventoryApi } from "@/lib/inventory-api";
import type { InventoryMovement, WarehouseCode } from "@/lib/inventory-types";

type MovementTypeFilter = "all" | "inbound" | "outbound";

const toDateInputValue = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

export default function OrdersHistoryPage() {
  const [orders, setOrders] = useState<InventoryMovement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState(toDateInputValue(new Date()));
  const [movementType, setMovementType] = useState<MovementTypeFilter>("all");
  const [skuQuery, setSkuQuery] = useState("");
  const [warehouse, setWarehouse] = useState<"all" | WarehouseCode>("all");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        setOrders(await inventoryApi.listOrders());
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "No se pudo cargar el historial.");
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const filteredOrders = useMemo(() => {
    return orders.filter((order) => {
      if (movementType !== "all" && order.movement_type !== movementType) {
        return false;
      }

      if (warehouse !== "all" && order.warehouse !== warehouse) {
        return false;
      }

      if (skuQuery.trim()) {
        const query = skuQuery.toLowerCase();
        if (!order.sku.toLowerCase().includes(query) && !order.sku_name.toLowerCase().includes(query)) {
          return false;
        }
      }

      if (fromDate) {
        const from = new Date(`${fromDate}T00:00:00`);
        const createdAt = new Date(order.created_at);
        if (createdAt < from) {
          return false;
        }
      }

      if (toDate) {
        const to = new Date(`${toDate}T23:59:59`);
        const createdAt = new Date(order.created_at);
        if (createdAt > to) {
          return false;
        }
      }

      return true;
    });
  }, [fromDate, movementType, orders, skuQuery, toDate, warehouse]);

  return (
    <main>
      <header className="page-head card-reveal">
        <p className="kicker">Inventory Orders</p>
        <h2>History</h2>
        <p className="muted">Historial consolidado con filtros locales por fecha, tipo, SKU y warehouse.</p>
      </header>

      <section className="panel card-reveal">
        <h3>Filtros</h3>
        <div className="filters-grid">
          <label>
            Desde
            <input className="input" type="date" value={fromDate} onChange={(event) => setFromDate(event.target.value)} />
          </label>

          <label>
            Hasta
            <input className="input" type="date" value={toDate} onChange={(event) => setToDate(event.target.value)} />
          </label>

          <label>
            Tipo
            <select
              className="input"
              value={movementType}
              onChange={(event) => setMovementType(event.target.value as MovementTypeFilter)}
            >
              <option value="all">all</option>
              <option value="inbound">inbound</option>
              <option value="outbound">outbound</option>
            </select>
          </label>

          <label>
            Warehouse
            <select
              className="input"
              value={warehouse}
              onChange={(event) => setWarehouse(event.target.value as "all" | WarehouseCode)}
            >
              <option value="all">all</option>
              <option value="LA">LA</option>
              <option value="ZGZ">ZGZ</option>
            </select>
          </label>

          <label>
            SKU / Producto
            <input
              className="input"
              value={skuQuery}
              onChange={(event) => setSkuQuery(event.target.value)}
              placeholder="Ej: SKU-001 o nombre"
            />
          </label>
        </div>
      </section>

      <section className="panel card-reveal">
        <h3>Resultados ({filteredOrders.length})</h3>

        {loading ? <p className="muted">Cargando ordenes...</p> : null}
        {error ? <p className="notice notice-error">{error}</p> : null}

        {!loading && !error && filteredOrders.length === 0 ? (
          <p className="muted">No hay movimientos para los filtros seleccionados.</p>
        ) : null}

        {!loading && !error && filteredOrders.length > 0 ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Tipo</th>
                  <th>SKU</th>
                  <th>Producto</th>
                  <th>Cantidad</th>
                  <th>Warehouse</th>
                  <th>Detalle</th>
                </tr>
              </thead>
              <tbody>
                {filteredOrders.map((order) => (
                  <tr key={`${order.movement_type}-${order.id}`}>
                    <td>{new Date(order.created_at).toLocaleString()}</td>
                    <td>{order.movement_type}</td>
                    <td>{order.sku}</td>
                    <td>{order.sku_name}</td>
                    <td>{order.quantity}</td>
                    <td>{order.warehouse}</td>
                    <td>
                      {order.movement_type === "inbound"
                        ? `reference: ${order.reference || "-"}`
                        : `exit_type: ${order.exit_type || "-"} | tracking: ${order.tracking_number || "-"}`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </main>
  );
}
