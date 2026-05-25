"use client";

import Link from "next/link";
import { authClient } from "@/lib/auth";

export function AuthNav() {
  return (
    <div className="flex flex-wrap items-center gap-3 text-sm">
      <Link href="/account/profile" className="rounded-full border border-slate-300 px-3 py-1.5">
        Perfil
      </Link>
      <Link href="/account/change-password" className="rounded-full border border-slate-300 px-3 py-1.5">
        Cambiar clave
      </Link>
      <button
        type="button"
        className="rounded-full border border-slate-300 px-3 py-1.5"
        onClick={() => authClient.logout()}
      >
        Cerrar sesion
      </button>
    </div>
  );
}
