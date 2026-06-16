import { redirect } from "next/navigation";

export default function ProtectedEntryPage() {
  redirect("/backoffice/inventory/products");
}
