"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogoutButton } from "@/components/logout-button";

type BackofficeShellProps = {
  children: React.ReactNode;
};

const navItems = [
  { href: "/backoffice/inventory/products", label: "Inventory Products" },
  { href: "/backoffice/inventory/orders/inbound", label: "Inbound Order" },
  { href: "/backoffice/inventory/orders/outbound", label: "Outbound Order" },
  { href: "/backoffice/inventory/orders", label: "Orders History" },
  { href: "/backoffice/suppliers", label: "Suppliers" },
  { href: "/backoffice/incidents", label: "Incidents" },
  { href: "/backoffice/candidates", label: "Candidates" },
  { href: "/backoffice/knowledge", label: "Knowledge Assistant" },
  { href: "/backoffice/rfps", label: "RFP Intake" },
];

export function BackofficeShell({ children }: BackofficeShellProps) {
  const pathname = usePathname();

  return (
    <div className="backoffice-shell">
      <aside className="backoffice-side card-reveal">
        <p className="kicker">TrackFlow</p>
        <h1>Backoffice</h1>
        <nav className="side-nav">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-link ${
                pathname === item.href || pathname.startsWith(`${item.href}/`)
                  ? "nav-link-active"
                  : ""
              }`}
            >
              {item.label}
            </Link>
          ))}
          <LogoutButton />
        </nav>
      </aside>
      <section className="backoffice-main">{children}</section>
    </div>
  );
}
