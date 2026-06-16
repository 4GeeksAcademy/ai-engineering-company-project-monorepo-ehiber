import { AuthGuard } from "@/components/auth-guard";
import { BackofficeShell } from "@/components/backoffice-shell";

export default function ProtectedBackofficeLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <AuthGuard>
      <BackofficeShell>{children}</BackofficeShell>
    </AuthGuard>
  );
}
