"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { authClient } from "@/lib/auth";
import { getStoredUser } from "@repo/shared/auth";
import type { UserPublic } from "@repo/shared/auth";

export default function ProfilePage() {
  const [user, setUser] = useState<UserPublic | null>(null);
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const stored = getStoredUser();
    if (stored) {
      setUser(stored);
      setEmail(stored.email);
      return;
    }

    authClient
      .getCurrentUser()
      .then((currentUser) => {
        setUser(currentUser);
        setEmail(currentUser.email);
      })
      .catch((loadError) => {
        setError(loadError instanceof Error ? loadError.message : "No se pudo cargar el perfil.");
      });
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!user) return;

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const updated = await authClient.updateProfile(user.id, email);
      setUser(updated);
      setMessage("Perfil actualizado correctamente.");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "No se pudo actualizar el perfil.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container" style={{ maxWidth: "620px", padding: "3rem 0" }}>
      <Link href="/internal-app">← Volver al workspace</Link>
      <h1 style={{ marginTop: "1rem" }}>Perfil de cuenta</h1>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "1rem", marginTop: "1.5rem" }}>
        <label style={{ display: "grid", gap: "0.5rem" }}>
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        {message ? <p style={{ color: "#146356" }}>{message}</p> : null}
        {error ? <p style={{ color: "#b54708" }}>{error}</p> : null}
        <button type="submit" disabled={loading || !user}>
          {loading ? "Guardando..." : "Guardar cambios"}
        </button>
      </form>
    </main>
  );
}
