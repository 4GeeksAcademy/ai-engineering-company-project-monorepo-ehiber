"use client";

import { Suspense } from "react";
import LoginForm from "./login-form";

export default function LoginPage() {
  return (
    <Suspense fallback={<main className="container" style={{ padding: "4rem 0" }}>Cargando...</main>}>
      <LoginForm />
    </Suspense>
  );
}
