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

    if (newPassword.length < 8) {
      validationErrors.push("La nueva contrasena debe tener al menos 8 caracteres.");
    }
    if (newPassword !== confirmPassword) {
      validationErrors.push("La confirmacion no coincide con la nueva contrasena.");
    }

    if (validationErrors.length) {
      setErrors(validationErrors);
      setMessage("");
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
      setErrors([
        submitError instanceof Error ? submitError.message : "No se pudo cambiar la contrasena.",
      ]);
      setMessage("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container" style={{ maxWidth: "620px", padding: "3rem 0" }}>
      <Link href="/account/profile">← Volver al perfil</Link>
      <h1 style={{ marginTop: "1rem" }}>Cambiar contrasena</h1>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "1rem", marginTop: "1.5rem" }}>
        <label style={{ display: "grid", gap: "0.5rem" }}>
          Contrasena actual
          <input
            type="password"
            required
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
          />
        </label>
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
          Confirmar nueva contrasena
          <input
            type="password"
            required
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
          />
        </label>
        {message ? <p style={{ color: "#146356" }}>{message}</p> : null}
        {errors.map((item) => (
          <p key={item} style={{ color: "#b54708" }}>
            {item}
          </p>
        ))}
        <button type="submit" disabled={loading}>
          {loading ? "Actualizando..." : "Actualizar contrasena"}
        </button>
      </form>
    </main>
  );
}
