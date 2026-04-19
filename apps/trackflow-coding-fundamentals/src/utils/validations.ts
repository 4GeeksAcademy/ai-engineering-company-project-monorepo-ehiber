import type {
  Current3plStatus,
  EstimatedMonthlyShipmentVolume,
  LeadRequest,
  LeadRequestErrors,
  LeadRequestValidationResult,
  MainOperatingCountry,
  ProductType,
} from "../types/models.ts";

const validCountries: MainOperatingCountry[] = ["Mexico", "Espana", "Ambos", "Otro"];
const validProductTypes: ProductType[] = [
  "Moda",
  "Electronica",
  "Cosmetica",
  "Alimentacion",
  "Otro",
];
const validShipmentVolumes: EstimatedMonthlyShipmentVolume[] = [
  "0-100",
  "101-500",
  "501-2000",
  "2000+",
  "No estoy seguro",
];
const valid3plStatuses: Current3plStatus[] = ["Si", "No", "Estoy evaluando opciones"];

const corporateEmailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const phonePattern = /^\+\d+/;

export const validateCompanyName = (companyName: string): string | null => {
  return companyName.trim().length >= 2
    ? null
    : "El nombre de la empresa debe tener al menos 2 caracteres";
};

export const validateContactPerson = (contactPerson: string): string | null => {
  const words = contactPerson.trim().split(/\s+/).filter(Boolean);
  return words.length >= 2 ? null : "Ingresa nombre y apellido del contacto";
};

export const validateCorporateEmail = (corporateEmail: string): string | null => {
  return corporateEmailPattern.test(corporateEmail.trim())
    ? null
    : "Ingresa un email corporativo valido (ejemplo: nombre@empresa.com)";
};

export const validatePhone = (phone: string): string | null => {
  return phonePattern.test(phone.trim())
    ? null
    : "El telefono debe incluir codigo de pais (ejemplo: +52 81 1234 5678)";
};

export const validateCompanyWebsite = (companyWebsite?: string): string | null => {
  if (companyWebsite === undefined || companyWebsite.trim() === "") {
    return null;
  }

  const trimmedWebsite = companyWebsite.trim();

  if (
    !trimmedWebsite.startsWith("http://") &&
    !trimmedWebsite.startsWith("https://")
  ) {
    return "Si incluyes sitio web, debe ser una URL valida";
  }

  try {
    new URL(trimmedWebsite);
    return null;
  } catch {
    return "Si incluyes sitio web, debe ser una URL valida";
  }
};

export const validateMainOperatingCountry = (
  mainOperatingCountry: MainOperatingCountry,
): string | null => {
  return validCountries.includes(mainOperatingCountry)
    ? null
    : "Selecciona el pais de operacion principal";
};

export const validateProductType = (productType: ProductType): string | null => {
  return validProductTypes.includes(productType)
    ? null
    : "Selecciona el tipo de producto que manejas";
};

export const validateEstimatedMonthlyShipmentVolume = (
  estimatedMonthlyShipmentVolume: EstimatedMonthlyShipmentVolume,
): string | null => {
  return validShipmentVolumes.includes(estimatedMonthlyShipmentVolume)
    ? null
    : "Selecciona el volumen mensual estimado";
};

export const validateInterestedServices = (interestedServices: string[]): string | null => {
  return interestedServices.length > 0
    ? null
    : "Selecciona al menos un servicio de interes";
};

export const validateCurrent3plStatus = (
  current3plStatus: Current3plStatus,
): string | null => {
  return valid3plStatuses.includes(current3plStatus)
    ? null
    : "Indica si actualmente trabajas con otro proveedor logistico";
};

export const validateCommentsOrSpecificNeeds = (
  commentsOrSpecificNeeds?: string,
): string | null => {
  if (commentsOrSpecificNeeds === undefined) {
    return null;
  }

  const remainingCharacters = 500 - commentsOrSpecificNeeds.length;

  return commentsOrSpecificNeeds.length <= 500
    ? null
    : `Los comentarios no pueden exceder 500 caracteres (quedan ${remainingCharacters})`;
};

export const validateAcceptedPrivacyPolicy = (
  acceptedPrivacyPolicy: boolean,
): string | null => {
  return acceptedPrivacyPolicy
    ? null
    : "Debes aceptar la politica de privacidad para continuar";
};

export const validateLeadRequest = (
  leadRequest: LeadRequest,
): LeadRequestValidationResult => {
  const errors: LeadRequestErrors = {};

  const companyNameError = validateCompanyName(leadRequest.companyName);
  const contactPersonError = validateContactPerson(leadRequest.contactPerson);
  const corporateEmailError = validateCorporateEmail(leadRequest.corporateEmail);
  const phoneError = validatePhone(leadRequest.phone);
  const companyWebsiteError = validateCompanyWebsite(leadRequest.companyWebsite);
  const mainOperatingCountryError = validateMainOperatingCountry(
    leadRequest.mainOperatingCountry,
  );
  const productTypeError = validateProductType(leadRequest.productType);
  const estimatedMonthlyShipmentVolumeError = validateEstimatedMonthlyShipmentVolume(
    leadRequest.estimatedMonthlyShipmentVolume,
  );
  const interestedServicesError = validateInterestedServices(
    leadRequest.interestedServices,
  );
  const current3plStatusError = validateCurrent3plStatus(
    leadRequest.currentlyWorksWithAnother3pl,
  );
  const commentsError = validateCommentsOrSpecificNeeds(
    leadRequest.commentsOrSpecificNeeds,
  );
  const acceptedPrivacyPolicyError = validateAcceptedPrivacyPolicy(
    leadRequest.acceptedPrivacyPolicy,
  );

  if (companyNameError !== null) {
    errors.companyName = companyNameError;
  }
  if (contactPersonError !== null) {
    errors.contactPerson = contactPersonError;
  }
  if (corporateEmailError !== null) {
    errors.corporateEmail = corporateEmailError;
  }
  if (phoneError !== null) {
    errors.phone = phoneError;
  }
  if (companyWebsiteError !== null) {
    errors.companyWebsite = companyWebsiteError;
  }
  if (mainOperatingCountryError !== null) {
    errors.mainOperatingCountry = mainOperatingCountryError;
  }
  if (productTypeError !== null) {
    errors.productType = productTypeError;
  }
  if (estimatedMonthlyShipmentVolumeError !== null) {
    errors.estimatedMonthlyShipmentVolume = estimatedMonthlyShipmentVolumeError;
  }
  if (interestedServicesError !== null) {
    errors.interestedServices = interestedServicesError;
  }
  if (current3plStatusError !== null) {
    errors.currentlyWorksWithAnother3pl = current3plStatusError;
  }
  if (commentsError !== null) {
    errors.commentsOrSpecificNeeds = commentsError;
  }
  if (acceptedPrivacyPolicyError !== null) {
    errors.acceptedPrivacyPolicy = acceptedPrivacyPolicyError;
  }

  const warnings =
    leadRequest.estimatedMonthlyShipmentVolume === "0-100"
      ? [
          "Para volumenes menores a 100 envios mensuales, nuestros servicios podrian no ser la solucion mas eficiente. Seguro que quieres continuar?",
        ]
      : [];

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
    warnings,
  };
};
