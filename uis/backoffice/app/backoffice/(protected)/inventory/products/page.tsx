"use client";

import { FormEvent, useEffect, useState } from "react";
import { inventoryApi } from "@/lib/inventory-api";
import type { Product, ProductCreate, SKUCategory, WarehouseCode } from "@/lib/inventory-types";

const initialForm: ProductCreate = {
  name: "",
  sku: "",
  client_name: "",
  category: "fashion",
  warehouse: "LA",
};

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState<ProductCreate>(initialForm);

  const refreshProducts = async () => {
    setLoading(true);
    setError("");
    try {
      setProducts(await inventoryApi.listProducts());
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "No se pudieron cargar los productos.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;

    const loadInitialProducts = async () => {
      try {
        const result = await inventoryApi.listProducts();
        if (!active) {
          return;
        }
        setProducts(result);
      } catch (loadError) {
        if (!active) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "No se pudieron cargar los productos.");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void loadInitialProducts();

    return () => {
      active = false;
    };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      await inventoryApi.createProduct(form);
      setForm(initialForm);
      await refreshProducts();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "No se pudo crear el producto.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <main>
      <header className="page-head card-reveal">
        <p className="kicker">Inventory</p>
        <h2>Products</h2>
        <p className="muted">Gestion de catalogo SKU por warehouse con stock actual en tiempo real.</p>
      </header>

      <section className="panel card-reveal">
        <h3>Nuevo producto</h3>
        <form className="form-grid two-col" onSubmit={handleSubmit}>
          <label>
            Nombre
            <input
              className="input"
              value={form.name}
              onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              required
            />
          </label>
          <label>
            SKU
            <input
              className="input"
              value={form.sku}
              onChange={(event) => setForm((current) => ({ ...current, sku: event.target.value }))}
              required
            />
          </label>
          <label>
            Cliente
            <input
              className="input"
              value={form.client_name}
              onChange={(event) =>
                setForm((current) => ({ ...current, client_name: event.target.value }))
              }
              required
            />
          </label>
          <label>
            Categoria
            <select
              className="input"
              value={form.category}
              onChange={(event) =>
                setForm((current) => ({ ...current, category: event.target.value as SKUCategory }))
              }
            >
              <option value="fashion">fashion</option>
              <option value="electronics">electronics</option>
              <option value="cosmetics">cosmetics</option>
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
            >
              <option value="LA">LA</option>
              <option value="ZGZ">ZGZ</option>
            </select>
          </label>

          <div className="actions-inline">
            <button className="button-primary" type="submit" disabled={saving}>
              {saving ? "Guardando..." : "Crear producto"}
            </button>
          </div>
        </form>

        {error ? <p className="notice notice-error">{error}</p> : null}
      </section>

      <section className="panel card-reveal">
        <h3>Catalogo</h3>
        {loading ? <p className="muted">Cargando productos...</p> : null}
        {!loading && products.length === 0 ? (
          <p className="muted">No hay productos cargados todavia.</p>
        ) : null}

        {!loading && products.length > 0 ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Nombre</th>
                  <th>SKU</th>
                  <th>Cliente</th>
                  <th>Categoria</th>
                  <th>Warehouse</th>
                  <th>Stock</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product) => (
                  <tr key={product.id}>
                    <td>{product.id}</td>
                    <td>{product.name}</td>
                    <td>{product.sku}</td>
                    <td>{product.client_name}</td>
                    <td>{product.category}</td>
                    <td>{product.warehouse}</td>
                    <td>{product.current_stock}</td>
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
