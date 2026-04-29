import Link from "next/link";
import { LeadForm } from "@/components/lead-form";

export default function ContactPage() {
  return (
    <main className="site-shell">
      <a href="#lead-form" className="sr-only-focusable">
        Saltar al formulario
      </a>
      <header>
        <div className="container public-nav">
          <Link href="/" style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <span className="brand-mark">TF</span>
            <span
              style={{
                color: "white",
                fontFamily: "var(--font-display)",
                fontWeight: 700,
                fontSize: "1.2rem",
              }}
            >
              TrackFlow
            </span>
          </Link>
          <Link className="pill-link" href="/" style={{ color: "rgba(255,255,255,0.84)" }}>
            Volver al sitio
          </Link>
        </div>
      </header>

      <section className="section">
        <div
          className="container"
          style={{
            display: "grid",
            gap: "2rem",
            alignItems: "start",
            gridTemplateColumns: "minmax(280px, 0.82fr) minmax(0, 1.18fr)",
          }}
        >
          <aside className="dark-panel" style={{ padding: "2rem", position: "sticky", top: "1.5rem" }}>
            <p className="eyebrow" style={{ color: "#99f6e4" }}>
              Solicitud comercial
            </p>
            <h1
              style={{
                marginTop: "1rem",
                color: "white",
                fontFamily: "var(--font-display)",
                fontSize: "clamp(2rem, 4vw, 3.3rem)",
                lineHeight: 1.05,
              }}
            >
              Cuentanos como opera tu marca
            </h1>
            <p style={{ marginTop: "1rem", color: "#cbd5e1", lineHeight: 1.8 }}>
              Este formulario esta pensado para empresas de e-commerce que buscan externalizar su
              logistica en Mexico, Espana o ambos mercados.
            </p>
            <div className="public-grid" style={{ marginTop: "1.4rem", color: "#cbd5e1" }}>
              <div className="stat-chip">
                Capturamos empresa, contacto, paises de operacion, categoria de producto, volumen
                mensual estimado y servicios de interes.
              </div>
              <div className="stat-chip">
                Nuestro equipo comercial revisa cada solicitud y responde en 24-48 horas.
              </div>
              <div className="stat-chip">
                Si tu caso es urgente, escribe a comercial@trackflow.com.
              </div>
            </div>
          </aside>

          <section id="lead-form" className="surface-card" style={{ padding: "2rem" }}>
            <h2
              style={{
                margin: 0,
                fontFamily: "var(--font-display)",
                fontSize: "clamp(1.8rem, 3vw, 2.6rem)",
                lineHeight: 1.08,
              }}
            >
              Formulario de solicitud de informacion
            </h2>
            <p style={{ marginTop: "0.75rem", color: "#64748b", lineHeight: 1.7 }}>
              Todos los campos marcados con * son obligatorios.
            </p>
            <LeadForm />
          </section>
        </div>
      </section>
    </main>
  );
}
