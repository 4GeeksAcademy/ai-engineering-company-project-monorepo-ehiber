"use client";

import dynamic from "next/dynamic";

const CandidatesPageContent = dynamic(() => import("./candidates-page-content"), {
  loading: () => <p className="muted">Cargando modulo candidates...</p>,
});

export default function CandidatesPage() {
  return <CandidatesPageContent />;
}
