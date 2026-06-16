"use client";

import { authClient } from "@/lib/auth";

export function LogoutButton() {
  return (
    <button type="button" className="nav-link" onClick={() => authClient.logout()}>
      Cerrar sesion
    </button>
  );
}
