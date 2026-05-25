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

    if (!email.trim()) {
      errors.push("El email es obligatorio.");
    }
    if (password.length < 8) {
      errors.push("La contrasena debe tener al menos 8 caracteres.");
    }
    if (password !== confirmPassword) {
      errors.push("Las contrasenas no coinciden.");
    }

    if (errors.length) {
      setFieldErrors(errors);
      return;
    }

    setLoading(true);
    setFieldErrors([]);

    try {
      await authClient.register(email, password);
      router.replace("/internal-app");
    } catch (submitError) {
      setFieldErrors([
        submitError instanceof Error ? submitError.message : "No se pudo completar el registro.",
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container" style={{ maxWidth: "520px", padding: "4rem 0" }}>
      <h1>Crear cuenta</h1>
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
        <label style={{ display: "grid", gap: "0.5rem" }}>
          Confirmar contrasena
          <input
            type="password"
            required
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
          />
        </label>
        {fieldErrors.map((message) => (
          <p key={message} style={{ color: "#b54708" }}>
            {message}
          </p>
        ))}
        <button type="submit" disabled={loading}>
          {loading ? "Creando cuenta..." : "Registrarme"}
        </button>
      </form>
      <p style={{ marginTop: "1rem" }}>
        ¿Ya tienes cuenta? <Link href="/login">Inicia sesion</Link>
      </p>
    </main>
  );
}
