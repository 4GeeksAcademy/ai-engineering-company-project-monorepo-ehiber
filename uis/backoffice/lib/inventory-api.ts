import { authClient } from "@/lib/auth";
import type {
  InboundOrderCreate,
  InventoryMovement,
  OutboundOrderCreate,
  Product,
  ProductCreate,
} from "@/lib/inventory-types";

export const inventoryApi = {
  listProducts: async (): Promise<Product[]> => {
    return authClient.authFetch<Product[]>("/inventory/products");
  },

  createProduct: async (payload: ProductCreate): Promise<Product> => {
    return authClient.authFetch<Product>("/inventory/products", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  createInboundOrder: async (payload: InboundOrderCreate) => {
    return authClient.authFetch("/inventory/orders/inbound", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  createOutboundOrder: async (payload: OutboundOrderCreate) => {
    return authClient.authFetch("/inventory/orders/outbound", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  listOrders: async (): Promise<InventoryMovement[]> => {
    return authClient.authFetch<InventoryMovement[]>("/inventory/orders");
  },
};
