import Link from "next/link";

const organizationSchema = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "TrackFlow",
  description: "Gestion de almacenes y entregas de ultima milla para e-commerce",
  url: "https://trackflow.com",
  foundingDate: "2009",
  address: [
    {
      "@type": "PostalAddress",
      addressCountry: "MX",
      addressLocality: "Monterrey",
    },
    {
      "@type": "PostalAddress",
      addressCountry: "ES",
      addressLocality: "Zaragoza",
    },
  ],
  contactPoint: {
    "@type": "ContactPoint",
    telephone: "+52-81-1234-5678",
    contactType: "sales",
    availableLanguage: ["Spanish", "English"],
  },
  sameAs: ["https://linkedin.com/company/trackflow"],
  areaServed: [
    { "@type": "Country", name: "Mexico" },
    { "@type": "Country", name: "Spain" },
  ],
};

const services = [
  {
    id: "01",
    title: "Gestion de Almacenes",
    bullets: [
      "Almacenamiento, picking y packing.",
      "Inventario en tiempo real para decisiones mas rapidas.",
      "Operamos almacenes en Monterrey y Zaragoza.",
    ],
  },
  {
    id: "02",
    title: "Entregas de Ultima Milla",
    bullets: [
      "Red de carriers certificados en ambos paises.",
      "Seguimiento unificado de envios y trazabilidad.",
      "Gestion de incidencias y devoluciones con menos friccion.",
    ],
  },
  {
    id: "03",
    title: "Logistica Inversa",
    bullets: [
      "Gestion completa de devoluciones.",
      "Inspeccion y reacondicionamiento de productos.",
      "Integracion con tu plataforma de ventas.",
    ],
  },
];

const benefits = [
  {
    title: "Operacion binacional",
    copy: "Infraestructura propia en Mexico y Espana para servir operaciones exigentes.",
  },
  {
    title: "130 profesionales",
    copy: "Equipos dedicados a almacenaje, ultima milla, incidencias y devoluciones.",
  },
  {
    title: "Tecnologia propia",
    copy: "Visibilidad de inventario y mejor coordinacion para marcas con volumen.",
  },
  {
    title: "Especializacion e-commerce",
    copy: "Moda, electronica y cosmetica como categorias centrales de la operacion.",
  },
];

const coverage = [
  {
    country: "Mexico",
    title: "Monterrey como nodo principal",
    bullets: ["Almacen en Monterrey.", "Cobertura nacional.", "Carriers: Estafeta, FedEx, DHL."],
  },
  {
    country: "Espana",
    title: "Zaragoza como hub operativo",
    bullets: [
      "Almacen en Zaragoza.",
      "Cobertura peninsular e islas.",
      "Carriers: MRW, SEUR, DHL.",
    ],
  },
];

export function PublicSite() {
  return (
    <div className="site-shell">
      <a href="#main-content" className="sr-only-focusable">
        Saltar al contenido
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
          <nav className="nav-links" aria-label="Navegacion principal">
            <a className="pill-link" href="#inicio">
              Inicio
            </a>
            <a className="pill-link" href="#servicios">
              Servicios
            </a>
            <a className="pill-link" href="#cobertura">
              Cobertura
            </a>
            <a className="pill-link" href="#contacto">
              Contacto
            </a>
            <Link className="button-primary" href="/contacto">
              Solicitar informacion
            </Link>
          </nav>
        </div>
      </header>

      <main id="main-content">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationSchema) }}
        />

        <section id="inicio" className="section">
          <div
            className="container"
            style={{
              display: "grid",
              gap: "2rem",
              alignItems: "center",
              gridTemplateColumns: "minmax(0, 1.15fr) minmax(280px, 0.85fr)",
            }}
          >
            <div>
              <p
                style={{
                  display: "inline-flex",
                  padding: "0.65rem 1rem",
                  borderRadius: "999px",
                  background: "rgba(255,255,255,0.08)",
                  border: "1px solid rgba(255,255,255,0.16)",
                  color: "#99f6e4",
                  fontWeight: 700,
                }}
              >
                Operador logistico binacional para e-commerce
              </p>
              <h1
                style={{
                  margin: "1.25rem 0 0",
                  color: "white",
                  fontFamily: "var(--font-display)",
                  fontSize: "clamp(2.5rem, 6vw, 4.6rem)",
                  lineHeight: 1,
                }}
              >
                Logistica que escala con tu e-commerce
              </h1>
              <p
                style={{
                  marginTop: "1.5rem",
                  maxWidth: "46rem",
                  fontSize: "1.12rem",
                  lineHeight: 1.8,
                  color: "#cbd5e1",
                }}
              >
                Gestion de almacenes, entregas de ultima milla y logistica inversa en Mexico y
                Espana. Mas de 15 anos ayudando a marcas de moda, electronica y cosmetica a crecer
                sin preocuparse por la operacion.
              </p>
              <div className="hero-actions" style={{ marginTop: "2rem" }}>
                <Link className="button-primary" href="/contacto">
                  Solicitar informacion
                </Link>
                <a className="button-secondary" href="#servicios">
                  Ver servicios
                </a>
              </div>
              <div className="metrics-grid" style={{ marginTop: "2rem" }}>
                {[
                  ["Operacion", "Mexico + Espana"],
                  ["Equipo", "130 profesionales"],
                  ["Experiencia", "15+ anos"],
                ].map(([label, value]) => (
                  <div key={label} className="dark-panel" style={{ padding: "1.2rem 1.25rem" }}>
                    <div style={{ color: "#cbd5e1", fontSize: "0.92rem" }}>{label}</div>
                    <div
                      style={{
                        marginTop: "0.55rem",
                        color: "white",
                        fontWeight: 800,
                        fontSize: "1.55rem",
                      }}
                    >
                      {value}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <aside className="dark-panel" style={{ padding: "1.5rem" }} aria-label="Resumen">
              <div className="surface-card" style={{ padding: "1.5rem" }}>
                <p className="eyebrow" style={{ color: "var(--brand-teal)" }}>
                  Vista operativa
                </p>
                <h2
                  style={{
                    marginTop: "0.75rem",
                    fontFamily: "var(--font-display)",
                    fontSize: "2rem",
                    lineHeight: 1.1,
                  }}
                >
                  Infraestructura propia para una operacion mas visible
                </h2>
                <div className="public-grid" style={{ marginTop: "1.5rem" }}>
                  {[
                    "Almacenes en Monterrey y Zaragoza con procesos de picking, packing y control de inventario.",
                    "Red de carriers certificados para seguimiento unificado, incidencias y devoluciones.",
                    "Integracion operativa pensada para marcas de moda, electronica y cosmetica.",
                  ].map((item) => (
                    <div
                      key={item}
                      style={{
                        padding: "1rem",
                        borderRadius: "1.2rem",
                        background: "#f1f5f9",
                        color: "#334155",
                        lineHeight: 1.7,
                      }}
                    >
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </aside>
          </div>
        </section>

        <section id="servicios" className="section" style={{ background: "#f8fafc" }}>
          <div className="container">
            <p className="eyebrow" style={{ color: "var(--brand-teal)" }}>
              Servicios
            </p>
            <h2
              style={{
                marginTop: "0.9rem",
                fontFamily: "var(--font-display)",
                fontSize: "clamp(2rem, 4vw, 3rem)",
                lineHeight: 1.05,
              }}
            >
              Tres capas de logistica para crecer sin friccion
            </h2>
            <p style={{ marginTop: "1rem", maxWidth: "42rem", color: "#475569", lineHeight: 1.8 }}>
              TrackFlow unifica la operacion completa de e-commerce para que tu equipo venda mas y
              coordine menos.
            </p>
            <div className="services-grid" style={{ marginTop: "2rem" }}>
              {services.map((service) => (
                <article key={service.id} className="surface-card" style={{ padding: "1.7rem" }}>
                  <p style={{ color: "#d97706", fontWeight: 800 }}>{service.id}</p>
                  <h3
                    style={{
                      marginTop: "0.8rem",
                      fontFamily: "var(--font-display)",
                      fontSize: "1.7rem",
                    }}
                  >
                    {service.title}
                  </h3>
                  <ul style={{ marginTop: "1rem", paddingLeft: "1rem", color: "#475569", lineHeight: 1.85 }}>
                    {service.bullets.map((bullet) => (
                      <li key={bullet}>{bullet}</li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="section" style={{ background: "white" }}>
          <div className="container" style={{ display: "grid", gap: "2rem", gridTemplateColumns: "0.9fr 1.1fr" }}>
            <div>
              <p className="eyebrow" style={{ color: "var(--brand-teal)" }}>
                Por que TrackFlow
              </p>
              <h2
                style={{
                  marginTop: "0.9rem",
                  fontFamily: "var(--font-display)",
                  fontSize: "clamp(2rem, 4vw, 3rem)",
                  lineHeight: 1.05,
                }}
              >
                Una primera capa digital para una empresa con experiencia real
              </h2>
              <p style={{ marginTop: "1rem", color: "#475569", lineHeight: 1.8 }}>
                La propuesta se apoya en experiencia operativa, infraestructura propia y una
                especializacion clara en e-commerce transfronterizo.
              </p>
            </div>
            <div className="benefits-grid">
              {benefits.map((benefit) => (
                <article key={benefit.title} className="soft-panel" style={{ padding: "1.4rem" }}>
                  <h3
                    style={{
                      margin: 0,
                      fontFamily: "var(--font-display)",
                      fontSize: "1.35rem",
                    }}
                  >
                    {benefit.title}
                  </h3>
                  <p style={{ marginTop: "0.8rem", color: "#475569", lineHeight: 1.75 }}>
                    {benefit.copy}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="cobertura" className="section" style={{ background: "#0f172a", color: "white" }}>
          <div className="container">
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                alignItems: "end",
                justifyContent: "space-between",
                gap: "1rem",
              }}
            >
              <div>
                <p className="eyebrow" style={{ color: "#99f6e4" }}>
                  Cobertura
                </p>
                <h2
                  style={{
                    marginTop: "0.9rem",
                    fontFamily: "var(--font-display)",
                    fontSize: "clamp(2rem, 4vw, 3rem)",
                    lineHeight: 1.05,
                  }}
                >
                  Operacion activa en dos mercados clave
                </h2>
              </div>
              <Link className="button-secondary" href="/contacto">
                Hablar con el equipo comercial
              </Link>
            </div>
            <div className="coverage-grid" style={{ marginTop: "2rem" }}>
              {coverage.map((entry) => (
                <article key={entry.country} className="dark-panel" style={{ padding: "1.7rem" }}>
                  <p className="eyebrow" style={{ color: "#99f6e4" }}>
                    {entry.country}
                  </p>
                  <h3
                    style={{
                      marginTop: "0.7rem",
                      fontFamily: "var(--font-display)",
                      fontSize: "1.8rem",
                    }}
                  >
                    {entry.title}
                  </h3>
                  <ul style={{ marginTop: "1rem", paddingLeft: "1rem", color: "#cbd5e1", lineHeight: 1.85 }}>
                    {entry.bullets.map((bullet) => (
                      <li key={bullet}>{bullet}</li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="contacto" className="section" style={{ background: "#f8fafc" }}>
          <div className="container" style={{ display: "grid", gap: "2rem", gridTemplateColumns: "1.1fr 0.9fr" }}>
            <div>
              <p className="eyebrow" style={{ color: "var(--brand-teal)" }}>
                Contacto
              </p>
              <h2
                style={{
                  marginTop: "0.9rem",
                  fontFamily: "var(--font-display)",
                  fontSize: "clamp(2rem, 4vw, 3rem)",
                  lineHeight: 1.05,
                }}
              >
                Tu proxima conversacion puede empezar hoy
              </h2>
              <p style={{ marginTop: "1rem", maxWidth: "42rem", color: "#475569", lineHeight: 1.8 }}>
                Cuantificamos mejor cada oportunidad cuando recibimos informacion clara sobre el
                tipo de producto, paises de operacion y volumen mensual de envios.
              </p>
              <div className="contact-actions" style={{ marginTop: "1.6rem" }}>
                <a
                  className="button-primary"
                  href="mailto:comercial@trackflow.com"
                  style={{ background: "#0f172a", color: "white" }}
                >
                  comercial@trackflow.com
                </a>
                <Link
                  className="button-secondary"
                  href="/contacto"
                  style={{ color: "#334155", borderColor: "#cbd5e1" }}
                >
                  Completar formulario
                </Link>
              </div>
            </div>

            <div className="surface-card" style={{ padding: "1.6rem" }}>
              <h3
                style={{
                  margin: 0,
                  fontFamily: "var(--font-display)",
                  fontSize: "1.7rem",
                }}
              >
                Datos comerciales
              </h3>
              <div className="public-grid" style={{ marginTop: "1.3rem", color: "#475569", lineHeight: 1.75 }}>
                <div>
                  <strong style={{ color: "#0f172a" }}>Email</strong>
                  <div>comercial@trackflow.com</div>
                </div>
                <div>
                  <strong style={{ color: "#0f172a" }}>Monterrey</strong>
                  <div>+52 81 1234 5678</div>
                </div>
                <div>
                  <strong style={{ color: "#0f172a" }}>Zaragoza</strong>
                  <div>+34 976 123 456</div>
                </div>
                <div>
                  <strong style={{ color: "#0f172a" }}>LinkedIn</strong>
                  <div>
                    <a href="https://linkedin.com/company/trackflow" style={{ color: "var(--brand-teal)" }}>
                      linkedin.com/company/trackflow
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer style={{ background: "white", borderTop: "1px solid #e2e8f0", padding: "1.8rem 0" }}>
        <div
          className="container"
          style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: "1rem", color: "#475569" }}
        >
          <p style={{ margin: 0 }}>&copy; 2025 TrackFlow. Todos los derechos reservados.</p>
          <a href="https://linkedin.com/company/trackflow" style={{ color: "var(--brand-teal)", fontWeight: 700 }}>
            LinkedIn
          </a>
        </div>
      </footer>
    </div>
  );
}
