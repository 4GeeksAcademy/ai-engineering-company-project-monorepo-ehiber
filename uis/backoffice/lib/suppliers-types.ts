export type SupplierCountry = "USA" | "Spain";
export type SupplierStatus = "active" | "suspended";

export type SupplierCategory =
  | "carrier_last_mile"
  | "carrier_international"
  | "warehouse_supplies"
  | "packaging_materials"
  | "reverse_logistics"
  | "fleet_maintenance"
  | "it_and_wms_software"
  | "cleaning_and_facilities";

export type Supplier = {
  id: number;
  name: string;
  country: SupplierCountry;
  categories: SupplierCategory[];
  rate_per_shipment: number;
  currency: string;
  rate_updated_at: string;
  status: SupplierStatus;
  service_zone: string | null;
  contact_email: string | null;
  notes: string | null;
};

export type SupplierCreate = {
  name: string;
  country: SupplierCountry;
  categories: SupplierCategory[];
  rate_per_shipment: number;
  status: SupplierStatus;
  service_zone: string | null;
  contact_email: string | null;
  notes: string | null;
};
