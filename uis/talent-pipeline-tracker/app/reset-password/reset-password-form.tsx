"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { authClient } from "@/lib/auth";

export default function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token) {
      setError("El enlace de recuperacion no es valido.");
      return;
    }
    if (newPassword.length < 8) {
      setError("La nueva contrasena debe tener al menos 8 caracteres.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Las contrasenas no coinciden.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      await authClient.resetPassword(token, newPassword);
      router.replace("/login?reset=success");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "No se pudo restablecer la contrasena.");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <main className="mx-auto max-w-md px-4 py-16">
        <h1 className="text-3xl font-bold text-slate-900">Enlace invalido</h1>
        <p className="mt-2 text-amber-700">Este enlace de recuperacion no es valido o ya expiro.</p>
        <p className="mt-4 text-sm"><Link href="/forgot-password">Solicitar un nuevo enlace</Link></p>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-full max-w-md flex-col justify-center px-4 py-16">
      <h1 className="text-3xl font-bold text-slate-900">Nueva contrasena</h1>
      <form onSubmit={handleSubmit} className="mt-8 grid gap-4">
        <label className="grid gap-2 text-sm font-medium">
          Nueva contrasena
          <input className="rounded-xl border border-slate-300 px-3 py-2" type="password" required value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Confirmar contrasena
          <input className="rounded-xl border border-slate-300 px-3 py-2" type="password" required value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
        </label>
        {error ? <p className="text-sm text-amber-700">{error}</p> : null}
        <button type="submit" disabled={loading} className="rounded-full bg-slate-900 px-4 py-2 font-semibold text-white disabled:opacity-60">
          {loading ? "Guardando..." : "Restablecer contrasena"}
        </button>
      </form>
      <p className="mt-4 text-sm"><Link href="/forgot-password">Solicitar un nuevo enlace</Link></p>
    </main>
  );
}
