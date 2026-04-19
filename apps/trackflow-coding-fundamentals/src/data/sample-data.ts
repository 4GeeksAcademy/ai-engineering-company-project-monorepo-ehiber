import type { LeadRequest, TrackFlowService, WarehouseHub } from "../types/models.ts";

export const trackFlowServices: TrackFlowService[] = [
  {
    name: "Almacenaje",
    description: "Almacenamiento, picking y packing con inventario en tiempo real.",
    availableCountries: ["Mexico", "Espana"],
  },
  {
    name: "Ultima milla",
    description: "Red de carriers certificados y seguimiento unificado de envios.",
    availableCountries: ["Mexico", "Espana"],
  },
  {
    name: "Logistica inversa",
    description: "Devoluciones, inspeccion y reacondicionamiento de productos.",
    availableCountries: ["Mexico", "Espana"],
  },
];

export const warehouseHubs: WarehouseHub[] = [
  {
    country: "Mexico",
    city: "Monterrey",
    coverage: "Cobertura nacional",
    carriers: ["Estafeta", "FedEx", "DHL"],
  },
  {
    country: "Espana",
    city: "Zaragoza",
    coverage: "Cobertura peninsular e islas",
    carriers: ["MRW", "SEUR", "DHL"],
  },
];

export const leadRequests: LeadRequest[] = [
  {
    companyName: "Moda Norte",
    contactPerson: "Laura Gomez",
    corporateEmail: "laura@modanorte.com",
    phone: "+52 81 4455 7788",
    companyWebsite: "https://modanorte.com",
    mainOperatingCountry: "Mexico",
    productType: "Moda",
    estimatedMonthlyShipmentVolume: "501-2000",
    interestedServices: ["Almacenaje", "Ultima milla"],
    currentlyWorksWithAnother3pl: "Si",
    commentsOrSpecificNeeds: "Buscamos consolidar almacenamiento y entregas en un mismo proveedor.",
    acceptedPrivacyPolicy: true,
  },
  {
    companyName: "Belleza Viva",
    contactPerson: "Marta Ruiz",
    corporateEmail: "marta@bellezaviva.es",
    phone: "+34 611 223 344",
    companyWebsite: "https://bellezaviva.es",
    mainOperatingCountry: "Espana",
    productType: "Cosmetica",
    estimatedMonthlyShipmentVolume: "101-500",
    interestedServices: ["Logistica inversa"],
    currentlyWorksWithAnother3pl: "Estoy evaluando opciones",
    commentsOrSpecificNeeds: "Necesitamos reacondicionamiento y control de devoluciones.",
    acceptedPrivacyPolicy: true,
  },
  {
    companyName: "ElectroHub",
    contactPerson: "Carlos Mendez",
    corporateEmail: "carlos@electrohub.com",
    phone: "+52 55 9988 1122",
    companyWebsite: "https://electrohub.com",
    mainOperatingCountry: "Ambos",
    productType: "Electronica",
    estimatedMonthlyShipmentVolume: "2000+",
    interestedServices: ["Almacenaje", "Ultima milla", "Logistica inversa"],
    currentlyWorksWithAnother3pl: "Si",
    commentsOrSpecificNeeds: "Queremos cobertura coordinada en Mexico y Espana.",
    acceptedPrivacyPolicy: true,
  },
  {
    companyName: "FreshBox",
    contactPerson: "Ana Perez",
    corporateEmail: "ana@freshbox.mx",
    phone: "+52 33 2211 9900",
    mainOperatingCountry: "Mexico",
    productType: "Alimentacion",
    estimatedMonthlyShipmentVolume: "0-100",
    interestedServices: ["Ultima milla"],
    currentlyWorksWithAnother3pl: "No",
    commentsOrSpecificNeeds: "Estamos empezando y queremos validar costos operativos.",
    acceptedPrivacyPolicy: true,
  },
];
