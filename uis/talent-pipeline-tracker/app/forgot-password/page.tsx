"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { authClient } from "@/lib/auth";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      setMessage(await authClient.requestPasswordReset(email));
      setSubmitted(true);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "No se pudo procesar la solicitud.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-full max-w-md flex-col justify-center px-4 py-16">
      <h1 className="text-3xl font-bold text-slate-900">Recuperar contrasena</h1>
      <p className="mt-2 text-slate-600">Te enviaremos un enlace si la direccion esta registrada.</p>
      <form onSubmit={handleSubmit} className="mt-8 grid gap-4">
        <label className="grid gap-2 text-sm font-medium">
          Email
          <input className="rounded-xl border border-slate-300 px-3 py-2" type="email" required disabled={submitted} value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="text-sm text-amber-700">{error}</p> : null}
        <button type="submit" disabled={loading || submitted} className="rounded-full bg-slate-900 px-4 py-2 font-semibold text-white disabled:opacity-60">
          {loading ? "Enviando..." : submitted ? "Solicitud enviada" : "Enviar enlace"}
        </button>
      </form>
      <p className="mt-4 text-sm text-slate-600"><Link href="/login">Volver a iniciar sesion</Link></p>
    </main>
  );
}
