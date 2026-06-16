"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { isAuthenticated } from "@repo/shared/auth";
import { authClient } from "@/lib/auth";

export function BackofficeLoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isAuthenticated()) {
      router.replace("/backoffice/inventory/products");
    }
  }, [router]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      await authClient.login(email, password);
      const nextPath = searchParams.get("next") || "/backoffice/inventory/products";
      router.push(nextPath);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "No se pudo iniciar sesion.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="center-shell">
      <section className="panel login-panel card-reveal">
        <p className="kicker">TrackFlow Internal</p>
        <h1>Backoffice Login</h1>
        <p className="muted">Accede para operar inventario, ordenes y modulos consolidados.</p>

        <form className="form-grid" onSubmit={handleSubmit}>
          <label>
            Email
            <input
              className="input"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>

          <label>
            Contrasena
            <input
              className="input"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>

          {error ? <p className="notice notice-error">{error}</p> : null}

          <button className="button-primary" type="submit" disabled={loading}>
            {loading ? "Ingresando..." : "Entrar"}
          </button>
        </form>
      </section>
    </main>
  );
}
