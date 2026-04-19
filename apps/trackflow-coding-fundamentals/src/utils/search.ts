import type { LeadRequest } from "../types/models.ts";

export const linearSearchIndex = <T>(
  items: T[],
  matchesTarget: (item: T) => boolean,
): number => {
  for (let index = 0; index < items.length; index += 1) {
    if (matchesTarget(items[index])) {
      return index;
    }
  }

  return -1;
};

export const binarySearchIndexByString = <T>(
  items: T[],
  target: string,
  getValue: (item: T) => string,
): number => {
  let start = 0;
  let end = items.length - 1;
  const normalizedTarget = target.toLocaleLowerCase("es");

  while (start <= end) {
    const middle = Math.floor((start + end) / 2);
    const currentValue = getValue(items[middle]).toLocaleLowerCase("es");

    if (currentValue === normalizedTarget) {
      return middle;
    }

    if (currentValue < normalizedTarget) {
      start = middle + 1;
    } else {
      end = middle - 1;
    }
  }

  return -1;
};

export const findLeadRequestByCompanyNameLinear = (
  leadRequests: LeadRequest[],
  companyName: string,
): number => {
  const normalizedCompanyName = companyName.trim().toLocaleLowerCase("es");

  return linearSearchIndex(
    leadRequests,
    (leadRequest) => leadRequest.companyName.toLocaleLowerCase("es") === normalizedCompanyName,
  );
};

export const findLeadRequestByCompanyNameBinary = (
  sortedLeadRequests: LeadRequest[],
  companyName: string,
): number => {
  return binarySearchIndexByString(
    sortedLeadRequests,
    companyName.trim(),
    (leadRequest) => leadRequest.companyName,
  );
};
