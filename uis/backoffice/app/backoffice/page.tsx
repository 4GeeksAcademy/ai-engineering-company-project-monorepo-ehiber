import { redirect } from "next/navigation";

export default function BackofficeEntryPage() {
  redirect("/backoffice/inventory/products");
}
