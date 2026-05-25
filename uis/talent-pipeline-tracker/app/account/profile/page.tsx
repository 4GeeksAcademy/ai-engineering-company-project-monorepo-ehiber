"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { authClient } from "@/lib/auth";
import { getStoredUser, type UserPublic } from "@repo/shared/auth";

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
    authClient.getCurrentUser().then((currentUser) => {
      setUser(currentUser);
      setEmail(currentUser.email);
    }).catch((loadError) => {
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
    <main className="mx-auto max-w-xl px-4 py-10">
      <Link href="/" className="text-sm text-slate-600">← Volver al tracker</Link>
      <h1 className="mt-4 text-3xl font-bold">Perfil de cuenta</h1>
      <form onSubmit={handleSubmit} className="mt-6 grid gap-4">
        <label className="grid gap-2 text-sm font-medium">
          Email
          <input className="rounded-xl border border-slate-300 px-3 py-2" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="text-sm text-amber-700">{error}</p> : null}
        <button type="submit" disabled={loading || !user} className="rounded-full bg-slate-900 px-4 py-2 font-semibold text-white disabled:opacity-60">
          {loading ? "Guardando..." : "Guardar cambios"}
        </button>
      </form>
    </main>
  );
}
