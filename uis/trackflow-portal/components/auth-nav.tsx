"use client";

import Link from "next/link";
import { authClient } from "@/lib/auth";

export function AuthNav() {
  return (
    <nav style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
      <Link className="pill-link" href="/account/profile">
        Perfil
      </Link>
      <Link className="pill-link" href="/account/change-password">
        Cambiar clave
      </Link>
      <button
        type="button"
        className="pill-link"
        style={{ cursor: "pointer", border: "none" }}
        onClick={() => authClient.logout()}
      >
        Cerrar sesion
      </button>
    </nav>
  );
}
