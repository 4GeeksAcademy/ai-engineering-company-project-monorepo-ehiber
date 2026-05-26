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
      setError(
        submitError instanceof Error
          ? submitError.message
          : "No se pudo restablecer la contrasena.",
      );
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <main className="container" style={{ maxWidth: "520px", padding: "4rem 0" }}>
        <h1>Enlace invalido</h1>
        <p style={{ color: "#b54708" }}>
          Este enlace de recuperacion no es valido o ya expiro.
        </p>
        <p style={{ marginTop: "1rem" }}>
          <Link href="/forgot-password">Solicitar un nuevo enlace</Link>
        </p>
      </main>
    );
  }

  return (
    <main className="container" style={{ maxWidth: "520px", padding: "4rem 0" }}>
      <h1>Nueva contrasena</h1>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "1rem", marginTop: "1.5rem" }}>
        <label style={{ display: "grid", gap: "0.5rem" }}>
          Nueva contrasena
          <input
            type="password"
            required
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
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
        {error ? <p style={{ color: "#b54708" }}>{error}</p> : null}
        <button type="submit" disabled={loading}>
          {loading ? "Guardando..." : "Restablecer contrasena"}
        </button>
      </form>
      <p style={{ marginTop: "1rem" }}>
        <Link href="/forgot-password">Solicitar un nuevo enlace</Link>
      </p>
    </main>
  );
}
