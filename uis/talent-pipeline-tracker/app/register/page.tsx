"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { authClient } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const errors: string[] = [];
    if (!email.trim()) errors.push("El email es obligatorio.");
    if (password.length < 8) errors.push("La contrasena debe tener al menos 8 caracteres.");
    if (password !== confirmPassword) errors.push("Las contrasenas no coinciden.");
    if (errors.length) {
      setFieldErrors(errors);
      return;
    }

    setLoading(true);
    setFieldErrors([]);
    try {
      await authClient.register(email, password);
      router.replace("/");
    } catch (submitError) {
      setFieldErrors([
        submitError instanceof Error ? submitError.message : "No se pudo completar el registro.",
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-full max-w-md flex-col justify-center px-4 py-16">
      <h1 className="text-3xl font-bold text-slate-900">Crear cuenta</h1>
      <form onSubmit={handleSubmit} className="mt-8 grid gap-4">
        <label className="grid gap-2 text-sm font-medium">
          Email
          <input className="rounded-xl border border-slate-300 px-3 py-2" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Contrasena
          <input className="rounded-xl border border-slate-300 px-3 py-2" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Confirmar contrasena
          <input className="rounded-xl border border-slate-300 px-3 py-2" type="password" required value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
        </label>
        {fieldErrors.map((message) => (
          <p key={message} className="text-sm text-amber-700">{message}</p>
        ))}
        <button type="submit" disabled={loading} className="rounded-full bg-slate-900 px-4 py-2 font-semibold text-white disabled:opacity-60">
          {loading ? "Creando cuenta..." : "Registrarme"}
        </button>
      </form>
      <p className="mt-4 text-sm text-slate-600">
        ¿Ya tienes cuenta? <Link href="/login">Inicia sesion</Link>
      </p>
    </main>
  );
}
