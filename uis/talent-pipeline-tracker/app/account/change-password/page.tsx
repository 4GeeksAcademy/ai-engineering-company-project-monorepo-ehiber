"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { authClient } from "@/lib/auth";

export default function ChangePasswordPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const validationErrors: string[] = [];
    if (newPassword.length < 8) validationErrors.push("La nueva contrasena debe tener al menos 8 caracteres.");
    if (newPassword !== confirmPassword) validationErrors.push("La confirmacion no coincide.");
    if (validationErrors.length) {
      setErrors(validationErrors);
      return;
    }

    setLoading(true);
    setErrors([]);
    try {
      await authClient.changePassword(currentPassword, newPassword);
      setMessage("Contrasena actualizada correctamente.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (submitError) {
      setErrors([submitError instanceof Error ? submitError.message : "No se pudo cambiar la contrasena."]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto max-w-xl px-4 py-10">
      <Link href="/account/profile" className="text-sm text-slate-600">← Volver al perfil</Link>
      <h1 className="mt-4 text-3xl font-bold">Cambiar contrasena</h1>
      <form onSubmit={handleSubmit} className="mt-6 grid gap-4">
        <label className="grid gap-2 text-sm font-medium">
          Contrasena actual
          <input className="rounded-xl border border-slate-300 px-3 py-2" type="password" required value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Nueva contrasena
          <input className="rounded-xl border border-slate-300 px-3 py-2" type="password" required value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Confirmar nueva contrasena
          <input className="rounded-xl border border-slate-300 px-3 py-2" type="password" required value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
        </label>
        {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
        {errors.map((item) => <p key={item} className="text-sm text-amber-700">{item}</p>)}
        <button type="submit" disabled={loading} className="rounded-full bg-slate-900 px-4 py-2 font-semibold text-white disabled:opacity-60">
          {loading ? "Actualizando..." : "Actualizar contrasena"}
        </button>
      </form>
    </main>
  );
}
