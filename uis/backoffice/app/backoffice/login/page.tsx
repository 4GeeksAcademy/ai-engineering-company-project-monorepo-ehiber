import { Suspense } from "react";
import { BackofficeLoginForm } from "./backoffice-login-form";

export default function BackofficeLoginPage() {
  return (
    <Suspense
      fallback={
        <main className="center-shell">
          <section className="panel login-panel card-reveal">
            <p className="muted">Cargando login...</p>
          </section>
        </main>
      }
    >
      <BackofficeLoginForm />
    </Suspense>
  );
}
