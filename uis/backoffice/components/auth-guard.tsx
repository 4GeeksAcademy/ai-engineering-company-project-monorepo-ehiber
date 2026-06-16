"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { isAuthenticated } from "@repo/shared/auth";
import { authClient } from "@/lib/auth";

type AuthGuardProps = {
  children: React.ReactNode;
};

export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const verifySession = async () => {
      if (!isAuthenticated()) {
        const next = encodeURIComponent(pathname || "/backoffice/inventory/products");
        router.replace(`/backoffice/login?next=${next}`);
        return;
      }

      try {
        await authClient.getCurrentUser();
        setReady(true);
      } catch {
        const next = encodeURIComponent(pathname || "/backoffice/inventory/products");
        router.replace(`/backoffice/login?next=${next}`);
      }
    };

    void verifySession();
  }, [pathname, router]);

  if (!ready) {
    return (
      <main className="center-shell">
        <div className="panel card-reveal">
          <p>Verificando sesion...</p>
        </div>
      </main>
    );
  }

  return <>{children}</>;
}
