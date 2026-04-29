import type {
  EstimatedMonthlyShipmentVolume,
  InterestedService,
  LeadRequest,
  MainOperatingCountry,
  ProductType,
  ShipmentVolumeSummary,
} from "../types/models.ts";

const shipmentVolumeScore: Record<EstimatedMonthlyShipmentVolume, number> = {
  "0-100": 50,
  "101-500": 300,
  "501-2000": 1250,
  "2000+": 2000,
  "No estoy seguro": 0,
};

const shipmentVolumeRank: Record<EstimatedMonthlyShipmentVolume, number> = {
  "No estoy seguro": 0,
  "0-100": 1,
  "101-500": 2,
  "501-2000": 3,
  "2000+": 4,
};

const buildCounterRecord = <K extends string>(keys: readonly K[]): Record<K, number> => {
  return keys.reduce(
    (counterRecord, key) => {
      counterRecord[key] = 0;
      return counterRecord;
    },
    {} as Record<K, number>,
  );
};

const operationCountries = ["Mexico", "Espana", "Ambos", "Otro"] as const;
const productTypes = ["Moda", "Electronica", "Cosmetica", "Alimentacion", "Otro"] as const;
const interestedServices = ["Almacenaje", "Ultima milla", "Logistica inversa"] as const;

export const countLeadRequestsByCountry = (
  leadRequests: LeadRequest[],
): Record<MainOperatingCountry, number> => {
  const totals = buildCounterRecord(operationCountries);

  return leadRequests.reduce((countryTotals, leadRequest) => {
    countryTotals[leadRequest.mainOperatingCountry] += 1;
    return countryTotals;
  }, totals);
};

export const countLeadRequestsByProductType = (
  leadRequests: LeadRequest[],
): Record<ProductType, number> => {
  const totals = buildCounterRecord(productTypes);

  return leadRequests.reduce((productTotals, leadRequest) => {
    productTotals[leadRequest.productType] += 1;
    return productTotals;
  }, totals);
};

export const countInterestedServices = (
  leadRequests: LeadRequest[],
): Record<InterestedService, number> => {
  const totals = buildCounterRecord(interestedServices);

  return leadRequests.reduce((serviceTotals, leadRequest) => {
    leadRequest.interestedServices.forEach((interestedService) => {
      serviceTotals[interestedService] += 1;
    });
    return serviceTotals;
  }, totals);
};

export const totalSelectedServices = (leadRequests: LeadRequest[]): number => {
  return leadRequests.reduce(
    (selectedServicesTotal, leadRequest) =>
      selectedServicesTotal + leadRequest.interestedServices.length,
    0,
  );
};

export const summarizeShipmentVolumes = (
  leadRequests: LeadRequest[],
): ShipmentVolumeSummary => {
  if (leadRequests.length === 0) {
    return {
      averageVolumeScore: 0,
      minimumVolume: null,
      maximumVolume: null,
    };
  }

  const totalScore = leadRequests.reduce(
    (scoreTotal, leadRequest) =>
      scoreTotal + shipmentVolumeScore[leadRequest.estimatedMonthlyShipmentVolume],
    0,
  );

  const sortedVolumes = [...leadRequests]
    .map((leadRequest) => leadRequest.estimatedMonthlyShipmentVolume)
    .sort((left, right) => shipmentVolumeRank[left] - shipmentVolumeRank[right]);

  return {
    averageVolumeScore: totalScore / leadRequests.length,
    minimumVolume: sortedVolumes[0],
    maximumVolume: sortedVolumes[sortedVolumes.length - 1],
  };
};
