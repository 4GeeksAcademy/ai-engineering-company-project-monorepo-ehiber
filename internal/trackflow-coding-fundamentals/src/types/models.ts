export type MainOperatingCountry = "Mexico" | "Espana" | "Ambos" | "Otro";

export type ProductType =
  | "Moda"
  | "Electronica"
  | "Cosmetica"
  | "Alimentacion"
  | "Otro";

export type EstimatedMonthlyShipmentVolume =
  | "0-100"
  | "101-500"
  | "501-2000"
  | "2000+"
  | "No estoy seguro";

export type InterestedService =
  | "Almacenaje"
  | "Ultima milla"
  | "Logistica inversa";

export type Current3plStatus = "Si" | "No" | "Estoy evaluando opciones";

export type SortDirection = "asc" | "desc";

export interface TrackFlowService {
  name: InterestedService;
  description: string;
  availableCountries: ("Mexico" | "Espana")[];
}

export interface WarehouseHub {
  country: "Mexico" | "Espana";
  city: string;
  coverage: string;
  carriers: string[];
}

export interface LeadRequest {
  companyName: string;
  contactPerson: string;
  corporateEmail: string;
  phone: string;
  companyWebsite?: string;
  mainOperatingCountry: MainOperatingCountry;
  productType: ProductType;
  estimatedMonthlyShipmentVolume: EstimatedMonthlyShipmentVolume;
  interestedServices: InterestedService[];
  currentlyWorksWithAnother3pl: Current3plStatus;
  commentsOrSpecificNeeds?: string;
  acceptedPrivacyPolicy: boolean;
}

export type LeadRequestField =
  | "companyName"
  | "contactPerson"
  | "corporateEmail"
  | "phone"
  | "companyWebsite"
  | "mainOperatingCountry"
  | "productType"
  | "estimatedMonthlyShipmentVolume"
  | "interestedServices"
  | "currentlyWorksWithAnother3pl"
  | "commentsOrSpecificNeeds"
  | "acceptedPrivacyPolicy";

export type LeadRequestErrors = Partial<Record<LeadRequestField, string>>;

export interface LeadRequestValidationResult {
  isValid: boolean;
  errors: LeadRequestErrors;
  warnings: string[];
}

export interface LeadRequestFilters {
  mainOperatingCountry?: MainOperatingCountry;
  productType?: ProductType;
  interestedService?: InterestedService;
  currentlyWorksWithAnother3pl?: Current3plStatus;
}

export interface LeadSortCriterion {
  field:
    | "companyName"
    | "contactPerson"
    | "mainOperatingCountry"
    | "productType"
    | "estimatedMonthlyShipmentVolume";
  direction: SortDirection;
}

export interface ShipmentVolumeSummary {
  averageVolumeScore: number;
  minimumVolume: EstimatedMonthlyShipmentVolume | null;
  maximumVolume: EstimatedMonthlyShipmentVolume | null;
}
