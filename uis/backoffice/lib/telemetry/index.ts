/**
 * Módulo de telemetría del backoffice.
 * Todo el tracking pasa por la función `track()`.
 *
 * @example
 *   import { track } from "@/lib/telemetry";
 *   track("dispatch_form_abandoned", { ... });
 */

export { track, TelemetryService } from "./telemetry-service";
export type {
  TelemetryEnvelope,
  EventName,
  WarehouseCode,
  ProcessingMode,
  AbandonReason,
  DispatchFormAbandonedPayload,
  InboundOrderSubmittedPayload,
  OutboundOrderSubmittedPayload,
} from "./types";
export { WAREHOUSE_MAP } from "./types";