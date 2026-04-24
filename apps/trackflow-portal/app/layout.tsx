import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TrackFlow | Logistica que escala con tu e-commerce",
  description:
    "Gestion de almacenes, entregas de ultima milla y logistica inversa en Mexico y Espana para marcas de e-commerce.",
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
