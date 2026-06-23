"use client";

import { FormEvent, useMemo, useState } from "react";
import { suppliersApi } from "@/lib/suppliers-api";
import { useSuppliersData } from "@/lib/hooks/use-suppliers-data";
import type { SupplierCategory, SupplierCountry, SupplierCreate, SupplierStatus } from "@/lib/suppliers-types";

const CATEGORIES: SupplierCategory[] = [
  "carrier_last_mile",
  "carrier_international",
  "warehouse_supplies",
  "packaging_materials",
  "reverse_logistics",
  "fleet_maintenance",
  "it_and_wms_software",
  "cleaning_and_facilities",
];

const initialForm: SupplierCreate = {
  name: "",
  country: "USA",
  categories: ["carrier_last_mile"],
  rate_per_shipment: 0,
  status: "active",
  service_zone: null,
  contact_email: null,
  notes: null,
};

export default function SuppliersPage() {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [form, setForm] = useState<SupplierCreate>(initialForm);

  const [countryFilter, setCountryFilter] = useState<"all" | SupplierCountry>("all");
  const [categoryFilter, setCategoryFilter] = useState<"all" | SupplierCategory>("all");
  const [statusFilter, setStatusFilter] = useState<"all" | SupplierStatus>("all");
  const { suppliers, setSuppliers, loading, loadError, refresh } = useSuppliersData({
    countryFilter,
    categoryFilter,
  });

  const filteredSuppliers = useMemo(() => {
    return suppliers.filter((supplier) => {
      if (statusFilter !== "all" && supplier.status !== statusFilter) {
        return false;
      }
      return true;
    });
  }, [statusFilter, suppliers]);

  const updateRate = async (supplierId: number, rateValue: string) => {
    const parsed = Number(rateValue);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      return;
    }

    setError("");
    try {
      const updated = await suppliersApi.updateRate(supplierId, parsed);
      setSuppliers((current) =>
        current.map((supplier) => (supplier.id === supplierId ? updated : supplier)),
      );
    } catch (rateError) {
      setError(rateError instanceof Error ? rateError.message : "No se pudo actualizar la tarifa.");
    }
  };

  const toggleStatus = async (supplierId: number, currentStatus: SupplierStatus) => {
    const nextStatus: SupplierStatus = currentStatus === "active" ? "suspended" : "active";

    setError("");
    try {
      const updated = await suppliersApi.updateStatus(supplierId, nextStatus);
      setSuppliers((current) =>
        current.map((supplier) => (supplier.id === supplierId ? updated : supplier)),
      );
    } catch (statusError) {
      setError(statusError instanceof Error ? statusError.message : "No se pudo actualizar el estado.");
    }
  };

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      await suppliersApi.create(form);
      setForm(initialForm);
      setSuccess("Supplier creado correctamente.");
      await refresh();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "No se pudo crear el supplier.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <main>
      <header className="page-head card-reveal">
        <p className="kicker">Consolidated Module</p>
        <h2>Suppliers</h2>
        <p className="muted">
          Modulo conectado a API real para listar, crear y actualizar suppliers.
        </p>
      </header>

      <section className="panel card-reveal">
        <h3>Nuevo supplier</h3>

        <form className="form-grid two-col" onSubmit={handleCreate}>
          <label>
            Name
            <input
              className="input"
              value={form.name}
              onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              required
            />
          </label>

          <label>
            Country
            <select
              className="input"
              value={form.country}
              onChange={(event) =>
                setForm((current) => ({ ...current, country: event.target.value as SupplierCountry }))
              }
            >
              <option value="USA">USA</option>
              <option value="Spain">Spain</option>
            </select>
          </label>

          <label>
            Category
            <select
              className="input"
              value={form.categories[0]}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  categories: [event.target.value as SupplierCategory],
                }))
              }
            >
              {CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>

          <label>
            Rate per shipment
            <input
              className="input"
              type="number"
              min={0.1}
              step={0.1}
              value={form.rate_per_shipment || ""}
              onChange={(event) =>
                setForm((current) => ({ ...current, rate_per_shipment: Number(event.target.value) }))
              }
              required
            />
          </label>

          <label>
            Service zone
            <input
              className="input"
              value={form.service_zone ?? ""}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  service_zone: event.target.value.trim() ? event.target.value : null,
                }))
              }
            />
          </label>

          <label>
            Contact email
            <input
              className="input"
              type="email"
              value={form.contact_email ?? ""}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  contact_email: event.target.value.trim() ? event.target.value : null,
                }))
              }
            />
          </label>

          <label style={{ gridColumn: "1 / -1" }}>
            Notes
            <textarea
              className="input"
              rows={3}
              value={form.notes ?? ""}
              onChange={(event) =>
                setForm((current) => ({ ...current, notes: event.target.value.trim() ? event.target.value : null }))
              }
            />
          </label>

          <button className="button-primary" type="submit" disabled={saving}>
            {saving ? "Guardando..." : "Crear supplier"}
          </button>
        </form>

        {error ? <p className="notice notice-error">{error}</p> : null}
        {success ? <p className="notice notice-success">{success}</p> : null}
      </section>

      <section className="panel card-reveal">
        <h3>Supplier Directory</h3>

        <div className="filters-grid">
          <label>
            Country
            <select
              className="input"
              value={countryFilter}
              onChange={(event) => setCountryFilter(event.target.value as "all" | SupplierCountry)}
            >
              <option value="all">all</option>
              <option value="USA">USA</option>
              <option value="Spain">Spain</option>
            </select>
          </label>

          <label>
            Category
            <select
              className="input"
              value={categoryFilter}
              onChange={(event) =>
                setCategoryFilter(event.target.value as "all" | SupplierCategory)
              }
            >
              <option value="all">all</option>
              {CATEGORIES.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </label>

          <label>
            Status
            <select
              className="input"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as "all" | SupplierStatus)}
            >
              <option value="all">all</option>
              <option value="active">active</option>
              <option value="suspended">suspended</option>
            </select>
          </label>
        </div>

        {loading ? <p className="muted">Cargando suppliers...</p> : null}
        {!loading && (error || loadError) ? (
          <p className="notice notice-error">{error || loadError}</p>
        ) : null}
        {filteredSuppliers.length === 0 ? <p className="muted">No suppliers match current filters.</p> : null}

        {!loading && filteredSuppliers.length > 0 ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Country</th>
                  <th>Categories</th>
                  <th>Rate</th>
                  <th>Currency</th>
                  <th>Status</th>
                  <th>Zone</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredSuppliers.map((supplier) => (
                  <tr key={supplier.id}>
                    <td>{supplier.name}</td>
                    <td>{supplier.country}</td>
                    <td>{supplier.categories.join(", ")}</td>
                    <td>
                      <input
                        className="input"
                        type="number"
                        min={0.1}
                        step={0.1}
                        defaultValue={supplier.rate_per_shipment}
                        onBlur={(event) => updateRate(supplier.id, event.target.value)}
                      />
                    </td>
                    <td>{supplier.currency}</td>
                    <td>
                      <span className={`pill ${supplier.status === "active" ? "pill-ok" : "pill-muted"}`}>
                        {supplier.status}
                      </span>
                    </td>
                    <td>{supplier.service_zone ?? "-"}</td>
                    <td>
                      <button
                        className="button-ghost"
                        type="button"
                        onClick={() => toggleStatus(supplier.id, supplier.status)}
                      >
                        {supplier.status === "active" ? "Suspend" : "Activate"}
                      </button>
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
