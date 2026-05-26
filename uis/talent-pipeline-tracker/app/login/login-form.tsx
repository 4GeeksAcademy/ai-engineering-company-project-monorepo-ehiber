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
      router.replace(searchParams.get("next") || "/");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "No se pudo iniciar sesion.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-full max-w-md flex-col justify-center px-4 py-16">
      <h1 className="text-3xl font-bold text-slate-900">Iniciar sesion</h1>
      <p className="mt-2 text-slate-600">Accede al Talent Pipeline Tracker.</p>
      {resetSuccess ? (
        <p className="mt-3 text-sm text-emerald-700">
          Tu contrasena fue actualizada. Ya puedes iniciar sesion.
        </p>
      ) : null}
      <form onSubmit={handleSubmit} className="mt-8 grid gap-4">
        <label className="grid gap-2 text-sm font-medium">
          Email
          <input
            className="rounded-xl border border-slate-300 px-3 py-2"
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Contrasena
          <input
            className="rounded-xl border border-slate-300 px-3 py-2"
            type="password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        {error ? <p className="text-sm text-amber-700">{error}</p> : null}
        <button
          type="submit"
          disabled={loading}
          className="rounded-full bg-slate-900 px-4 py-2 font-semibold text-white disabled:opacity-60"
        >
          {loading ? "Entrando..." : "Entrar"}
        </button>
      </form>
      <p className="mt-4 text-sm text-slate-600">
        <Link href="/forgot-password">¿Olvidaste tu contrasena?</Link>
      </p>
      <p className="mt-2 text-sm text-slate-600">
        ¿No tienes cuenta? <Link href="/register">Registrate</Link>
      </p>
    </main>
  );
}
