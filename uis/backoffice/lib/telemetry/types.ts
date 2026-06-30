/**
 * Tipos para el sistema de telemetría del backoffice.
 * Basados en el plan de telemetría Fase 1 (docs/telemetry/).
 */

export type TelemetrySource = "backoffice-web";

export type WarehouseCode = "LA" | "ZGZ";

/** Mapeo de códigos internos a nombres canónicos del plan */
export const WAREHOUSE_MAP: Record<WarehouseCode, string> = {
  LA: "los_angeles",
  ZGZ: "zaragoza",
};

export type ProcessingMode = "stream" | "batch";

export type EventName =
  | "dispatch_form_abandoned"
  | "inbound_order_submitted"
  | "outbound_order_submitted";

export type AbandonReason = "navigation_away" | "session_timeout" | "tab_closed";

/** Envelope común de todo evento de telemetría */
export interface TelemetryEnvelope {
  event_id: string;
  event_name: EventName;
  event_version: string;
  occurred_at: string;
  source: TelemetrySource;
  warehouse: string | null;
  correlation_id: string | null;
  processing_mode: ProcessingMode;
  payload: Record<string, unknown>;
}

/** Payload para dispatch_form_abandoned */
export interface DispatchFormAbandonedPayload {
  warehouse: string;
  sku_id: number | null;
  form_session_id: string;
  seconds_on_form: number;
  abandon_reason: AbandonReason;
}

/** Payload para inbound_order_submitted (evento auxiliar frontend) */
export interface InboundOrderSubmittedPayload {
  sku_id: number;
  quantity: number;
  warehouse: string;
  reference: string;
}

/** Payload para outbound_order_submitted (evento auxiliar frontend) */
export interface OutboundOrderSubmittedPayload {
  sku_id: number;
  quantity: number;
  warehouse: string;
  exit_type: string;
  tracking_number: string | null;
}