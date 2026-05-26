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
      const responseMessage = await authClient.requestPasswordReset(email);
      setMessage(responseMessage);
      setSubmitted(true);
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "No se pudo procesar la solicitud.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container" style={{ maxWidth: "520px", padding: "4rem 0" }}>
      <h1>Recuperar contrasena</h1>
      <p style={{ color: "#64748b", marginBottom: "1.5rem" }}>
        Te enviaremos un enlace si la direccion esta registrada.
      </p>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "1rem" }}>
        <label style={{ display: "grid", gap: "0.5rem" }}>
          Email
          <input
            type="email"
            required
            disabled={submitted}
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        {message ? <p style={{ color: "#146356" }}>{message}</p> : null}
        {error ? <p style={{ color: "#b54708" }}>{error}</p> : null}
        <button type="submit" disabled={loading || submitted}>
          {loading ? "Enviando..." : submitted ? "Solicitud enviada" : "Enviar enlace"}
        </button>
      </form>
      <p style={{ marginTop: "1rem" }}>
        <Link href="/login">Volver a iniciar sesion</Link>
      </p>
    </main>
  );
}
