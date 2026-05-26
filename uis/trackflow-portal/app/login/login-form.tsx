"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { authClient } from "@/lib/auth";

export default function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const resetSuccess = searchParams.get("reset") === "success";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      await authClient.login(email, password);
      const next = searchParams.get("next") || "/internal-app";
      router.replace(next);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "No se pudo iniciar sesion.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container" style={{ maxWidth: "520px", padding: "4rem 0" }}>
      <h1>Iniciar sesion</h1>
      <p style={{ color: "#64748b", marginBottom: "1.5rem" }}>
        Accede al workspace interno de TrackFlow.
      </p>
      {resetSuccess ? (
        <p style={{ color: "#146356", marginBottom: "1rem" }}>
          Tu contrasena fue actualizada. Ya puedes iniciar sesion.
        </p>
      ) : null}
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "1rem" }}>
        <label style={{ display: "grid", gap: "0.5rem" }}>
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <label style={{ display: "grid", gap: "0.5rem" }}>
          Contrasena
          <input
            type="password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        {error ? <p style={{ color: "#b54708" }}>{error}</p> : null}
        <button type="submit" disabled={loading}>
          {loading ? "Entrando..." : "Entrar"}
        </button>
      </form>
      <p style={{ marginTop: "1rem" }}>
        <Link href="/forgot-password">¿Olvidaste tu contrasena?</Link>
      </p>
      <p style={{ marginTop: "0.5rem" }}>
        ¿No tienes cuenta? <Link href="/register">Registrate</Link>
      </p>
    </main>
  );
}
