export type SKUCategory = "fashion" | "electronics" | "cosmetics";
export type WarehouseCode = "LA" | "ZGZ";
export type ExitType = "dispatch" | "loss";

export type Product = {
  id: number;
  name: string;
  sku: string;
  client_name: string;
  category: SKUCategory;
  warehouse: WarehouseCode;
  current_stock: number;
};

export type ProductCreate = {
  name: string;
  sku: string;
  client_name: string;
  category: SKUCategory;
  warehouse: WarehouseCode;
};

export type InboundOrderCreate = {
  sku_id: number;
  quantity: number;
  reference: string;
  warehouse: WarehouseCode;
};

export type OutboundOrderCreate = {
  sku_id: number;
  quantity: number;
  exit_type: ExitType;
  tracking_number: string | null;
  warehouse: WarehouseCode;
};

export type InventoryMovement = {
  id: number;
  movement_type: "inbound" | "outbound";
  sku_id: number;
  sku: string;
  sku_name: string;
  client_name: string;
  category: SKUCategory;
  quantity: number;
  warehouse: WarehouseCode;
  created_at: string;
  user_uuid: string;
  reference?: string | null;
  exit_type?: ExitType | null;
  tracking_number?: string | null;
};
