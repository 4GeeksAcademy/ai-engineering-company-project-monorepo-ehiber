import type {
  EstimatedMonthlyShipmentVolume,
  LeadRequest,
  LeadRequestFilters,
  LeadSortCriterion,
  SortDirection,
} from "../types/models.ts";

const shipmentVolumeRank: Record<EstimatedMonthlyShipmentVolume, number> = {
  "0-100": 1,
  "101-500": 2,
  "501-2000": 3,
  "2000+": 4,
  "No estoy seguro": 0,
};

const compareStrings = (left: string, right: string, direction: SortDirection): number => {
  const baseComparison = left.localeCompare(right, "es", { sensitivity: "base" });
  return direction === "asc" ? baseComparison : -baseComparison;
};

const compareShipmentVolumes = (
  left: EstimatedMonthlyShipmentVolume,
  right: EstimatedMonthlyShipmentVolume,
  direction: SortDirection,
): number => {
  const baseComparison = shipmentVolumeRank[left] - shipmentVolumeRank[right];
  return direction === "asc" ? baseComparison : -baseComparison;
};

export const filterLeadRequests = (
  leadRequests: LeadRequest[],
  filters: LeadRequestFilters,
): LeadRequest[] => {
  return leadRequests.filter((leadRequest) => {
    const matchesCountry =
      filters.mainOperatingCountry === undefined ||
      leadRequest.mainOperatingCountry === filters.mainOperatingCountry;

    const matchesProductType =
      filters.productType === undefined || leadRequest.productType === filters.productType;

    const matchesInterestedService =
      filters.interestedService === undefined ||
      leadRequest.interestedServices.includes(filters.interestedService);

    const matches3plStatus =
      filters.currentlyWorksWithAnother3pl === undefined ||
      leadRequest.currentlyWorksWithAnother3pl === filters.currentlyWorksWithAnother3pl;

    return (
      matchesCountry &&
      matchesProductType &&
      matchesInterestedService &&
      matches3plStatus
    );
  });
};

export const sortLeadRequestsByCompanyName = (
  leadRequests: LeadRequest[],
  direction: SortDirection = "asc",
): LeadRequest[] => {
  return [...leadRequests].sort((left, right) =>
    compareStrings(left.companyName, right.companyName, direction),
  );
};

export const sortLeadRequestsByShipmentVolume = (
  leadRequests: LeadRequest[],
  direction: SortDirection = "asc",
): LeadRequest[] => {
  return [...leadRequests].sort((left, right) =>
    compareShipmentVolumes(
      left.estimatedMonthlyShipmentVolume,
      right.estimatedMonthlyShipmentVolume,
      direction,
    ),
  );
};

export const sortLeadRequestsByCriteria = (
  leadRequests: LeadRequest[],
  criteria: LeadSortCriterion[],
): LeadRequest[] => {
  return [...leadRequests].sort((left, right) => {
    for (const criterion of criteria) {
      let comparison = 0;

      if (criterion.field === "estimatedMonthlyShipmentVolume") {
        comparison = compareShipmentVolumes(
          left.estimatedMonthlyShipmentVolume,
          right.estimatedMonthlyShipmentVolume,
          criterion.direction,
        );
      } else {
        comparison = compareStrings(
          String(left[criterion.field]),
          String(right[criterion.field]),
          criterion.direction,
        );
      }

      if (comparison !== 0) {
        return comparison;
      }
    }

    return 0;
  });
};
