"use client";

import { Suspense } from "react";
import ResetPasswordForm from "./reset-password-form";

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<main className="container" style={{ padding: "4rem 0" }}>Cargando...</main>}>
      <ResetPasswordForm />
    </Suspense>
  );
}
