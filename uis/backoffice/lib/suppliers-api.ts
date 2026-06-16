import { authClient } from "@/lib/auth";
import type { Supplier, SupplierCategory, SupplierCountry, SupplierCreate, SupplierStatus } from "@/lib/suppliers-types";

type ListSuppliersFilters = {
  country?: SupplierCountry;
  category?: SupplierCategory;
};

export const suppliersApi = {
  list: async (filters: ListSuppliersFilters = {}): Promise<Supplier[]> => {
    const query = new URLSearchParams();
    if (filters.country) {
      query.set("country", filters.country);
    }
    if (filters.category) {
      query.set("category", filters.category);
    }

    const suffix = query.toString() ? `?${query.toString()}` : "";
    return authClient.authFetch<Supplier[]>(`/suppliers${suffix}`);
  },

  create: async (payload: SupplierCreate): Promise<Supplier> => {
    return authClient.authFetch<Supplier>("/suppliers", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateRate: async (supplierId: number, ratePerShipment: number): Promise<Supplier> => {
    return authClient.authFetch<Supplier>(`/suppliers/${supplierId}/rate`, {
      method: "PATCH",
      body: JSON.stringify({ rate_per_shipment: ratePerShipment }),
    });
  },

  updateStatus: async (supplierId: number, status: SupplierStatus): Promise<Supplier> => {
    return authClient.authFetch<Supplier>(`/suppliers/${supplierId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
  },
};
