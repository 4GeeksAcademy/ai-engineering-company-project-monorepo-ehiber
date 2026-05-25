import { AuthGuard } from "@/components/auth-guard";
import { AuthNav } from "@/components/auth-nav";
import Link from "next/link";

export default function InternalAppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <AuthGuard>
      <div className="internal-shell">
        <header className="internal-topbar">
          <div
            className="container"
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "1rem",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "1rem 0",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <span className="brand-mark">TF</span>
              <div>
                <div style={{ color: "white", fontWeight: 800 }}>TrackFlow Internal App</div>
                <div style={{ color: "#94a3b8", fontSize: "0.92rem" }}>
                  Workspace inicial para futuras operaciones internas
                </div>
              </div>
            </div>
            <nav style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap", alignItems: "center" }}>
              <Link className="pill-link" href="/">
                Sitio publico
              </Link>
              <Link className="pill-link" href="/contacto">
                Contacto
              </Link>
              <AuthNav />
            </nav>
          </div>
        </header>
        {children}
      </div>
    </AuthGuard>
  );
}
