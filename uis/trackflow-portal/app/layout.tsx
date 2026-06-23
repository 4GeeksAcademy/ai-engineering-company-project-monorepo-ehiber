import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://trackflow.com"),
  title: "TrackFlow | Logistica que escala con tu e-commerce",
  description:
    "Gestion de almacenes, entregas de ultima milla y logistica inversa en Mexico y Espana para marcas de e-commerce.",
  keywords: [
    "logistica e-commerce",
    "gestion de almacenes",
    "ultima milla",
    "logistica inversa",
    "Mexico",
    "Espana",
    "TrackFlow",
  ],
  alternates: {
    canonical: "/",
  },
  openGraph: {
    type: "website",
    locale: "es_ES",
    url: "https://trackflow.com",
    siteName: "TrackFlow",
    title: "TrackFlow | Logistica que escala con tu e-commerce",
    description:
      "Gestion de almacenes, entregas de ultima milla y logistica inversa en Mexico y Espana para marcas de e-commerce.",
  },
  twitter: {
    card: "summary_large_image",
    title: "TrackFlow | Logistica que escala con tu e-commerce",
    description:
      "Gestion de almacenes, entregas de ultima milla y logistica inversa en Mexico y Espana para marcas de e-commerce.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
