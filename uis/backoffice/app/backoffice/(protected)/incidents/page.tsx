"use client";

import dynamic from "next/dynamic";

const IncidentsPageContent = dynamic(() => import("./incidents-page-content"), {
  loading: () => <p className="muted">Cargando modulo incidents...</p>,
});

export default function IncidentsPage() {
  return <IncidentsPageContent />;
}
