import { leadRequests } from "./data/sample-data.ts";
import {
  filterLeadRequests,
  findLeadRequestByCompanyNameBinary,
  findLeadRequestByCompanyNameLinear,
  sortLeadRequestsByCompanyName,
  summarizeShipmentVolumes,
  validateLeadRequest,
  countLeadRequestsByCountry,
  countInterestedServices,
} from "./index.ts";

const sortedLeadRequests = sortLeadRequestsByCompanyName(leadRequests);
const mexicoFashionLeads = filterLeadRequests(leadRequests, {
  mainOperatingCountry: "Mexico",
  productType: "Moda",
});

const linearSearchIndex = findLeadRequestByCompanyNameLinear(leadRequests, "ElectroHub");
const binarySearchIndex = findLeadRequestByCompanyNameBinary(
  sortedLeadRequests,
  "ElectroHub",
);

console.log("TrackFlow coding fundamentals demo");
console.log("----------------------------------");
console.log("Mexico + Moda leads:", mexicoFashionLeads.map((lead) => lead.companyName));
console.log("Linear search index for ElectroHub:", linearSearchIndex);
console.log("Binary search index for ElectroHub:", binarySearchIndex);
console.log("Lead requests by country:", countLeadRequestsByCountry(leadRequests));
console.log("Requested services totals:", countInterestedServices(leadRequests));
console.log("Shipment volume summary:", summarizeShipmentVolumes(leadRequests));
console.log("Validation result for FreshBox:", validateLeadRequest(leadRequests[3]));
