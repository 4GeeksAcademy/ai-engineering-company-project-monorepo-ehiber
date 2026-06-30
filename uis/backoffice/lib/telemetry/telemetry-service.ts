/**
 * TelemetryService — sistema de captura de eventos del backoffice.
 *
 * Acumula eventos en una cola local y los envía al backend en lotes,
 * nunca uno a uno. La URL del endpoint se configura vía variable de entorno
 * `NEXT_PUBLIC_TELEMETRY_ENDPOINT`.
 *
 * Características:
 * - Batch + debounce: cada 10s o 20 eventos se envía un lote
 * - Flush con `sendBeacon` para maximizar entrega incluso en navegación
 * - Retry con backoff (hasta 3 reintentos) si falla el envío
 * - `sessionId` y `timestamp` autogenerados — el componente solo pasa payload
 * - Única función pública: `track()`
 *
 * Uso:
 *   import { track } from "@/lib/telemetry";
 *   track("dispatch_form_abandoned", { ... });
 */

import type { EventName, TelemetryEnvelope, TelemetrySource } from "./types";

const DEFAULT_FLUSH_INTERVAL_MS = 10_000;
const DEFAULT_BATCH_SIZE = 20;
const MAX_RETRIES = 3;
const SOURCE: TelemetrySource = "backoffice-web";
const EVENT_VERSION = "1.0";

function getEndpointUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_TELEMETRY_ENDPOINT;
  if (envUrl) {
    // Si ya es URL completa, usarla directamente
    if (envUrl.includes("://")) {
      return envUrl;
    }
    // Si es solo base URL, añadir path del endpoint
    return `${envUrl.replace(/\/$/, "")}/telemetry/events`;
  }
  // Fallback a la API base
  const fallback =
    process.env.NEXT_PUBLIC_TRACKFLOW_API_URL ?? "http://localhost:8000";
  return `${fallback.replace(/\/$/, "")}/telemetry/events`;
}

function generateId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

class TelemetryService {
  private queue: TelemetryEnvelope[] = [];
  private flushTimer: ReturnType<typeof setInterval> | null = null;
  private readonly flushIntervalMs: number;
  private readonly batchSize: number;
  private readonly endpointUrl: string;
  private readonly sessionId: string;

  constructor(
    flushIntervalMs: number = DEFAULT_FLUSH_INTERVAL_MS,
    batchSize: number = DEFAULT_BATCH_SIZE,
  ) {
    this.flushIntervalMs = flushIntervalMs;
    this.batchSize = batchSize;
    this.endpointUrl = getEndpointUrl();
    this.sessionId = generateId();
  }

  /**
   * Registra un evento en la cola local.
   * Esta es la ÚNICA función pública para emitir eventos.
   * El componente solo pasa eventName + payload — sessionId y timestamp
   * se generan automáticamente aquí.
   */
  track(
    eventName: EventName,
    payload: Record<string, unknown>,
    options?: {
      warehouse?: string | null;
      correlationId?: string | null;
      processingMode?: "stream" | "batch";
    },
  ): void {
    const envelope: TelemetryEnvelope = {
      event_id: generateId(),
      event_name: eventName,
      event_version: EVENT_VERSION,
      occurred_at: new Date().toISOString(),
      source: SOURCE,
      warehouse: options?.warehouse ?? null,
      correlation_id: options?.correlationId ?? this.sessionId,
      processing_mode: options?.processingMode ?? "batch",
      payload,
    };

    this.queue.push(envelope);
    this.ensureTimer();

    if (this.queue.length >= this.batchSize) {
      void this.flush();
    }
  }

  /** Envía todos los eventos acumulados al backend con retry y backoff */
  async flush(): Promise<void> {
    if (this.queue.length === 0) return;

    const batch = this.queue.splice(0);
    this.stopTimerIfEmpty();

    await this.sendWithRetry(batch, 0);
  }

  /**
   * Envía el batch con sendBeacon. Si sendBeacon no puede encolar la
   * petición (returns false), reintenta con fetch con backoff exponencial
   * (2^attempt * 200ms, hasta MAX_RETRIES=3).
   */
  private async sendWithRetry(
    batch: TelemetryEnvelope[],
    attempt: number,
  ): Promise<void> {
    const blob = new Blob(
      [JSON.stringify({ events: batch })],
      { type: "application/json" },
    );

    // sendBeacon es el mecanismo principal — no bloquea la página
    const queued = navigator.sendBeacon(this.endpointUrl, blob);

    if (queued) return;

    // sendBeacon rechazó el envío — reintentar con fetch + backoff
    try {
      const response = await fetch(this.endpointUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: blob,
      });

      if (!response.ok && attempt < MAX_RETRIES) {
        const delay = Math.pow(2, attempt) * 200;
        await new Promise((resolve) => setTimeout(resolve, delay));
        await this.sendWithRetry(batch, attempt + 1);
      }
    } catch {
      if (attempt < MAX_RETRIES) {
        const delay = Math.pow(2, attempt) * 200;
        await new Promise((resolve) => setTimeout(resolve, delay));
        await this.sendWithRetry(batch, attempt + 1);
      }
    }
  }

  /** Fuerza el envío inmediato y limpia el timer (útil en navegación) */
  async flushAndStop(): Promise<void> {
    this.stopTimer();
    await this.flush();
  }

  private ensureTimer(): void {
    if (this.flushTimer !== null) return;
    this.flushTimer = setInterval(() => {
      void this.flush();
    }, this.flushIntervalMs);

    if (typeof window !== "undefined") {
      window.addEventListener("beforeunload", () => {
        this.sendOnUnload();
      });
    }
  }

  /** En beforeunload usamos sendBeacon síncrono (no async) */
  private sendOnUnload(): void {
    if (this.queue.length === 0) return;
    const batch = this.queue.splice(0);
    const blob = new Blob(
      [JSON.stringify({ events: batch })],
      { type: "application/json" },
    );
    navigator.sendBeacon(this.endpointUrl, blob);
  }

  private stopTimerIfEmpty(): void {
    if (this.queue.length === 0 && this.flushTimer !== null) {
      this.stopTimer();
    }
  }

  private stopTimer(): void {
    if (this.flushTimer !== null) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
  }
}

/** Instancia singleton del servicio */
const telemetryService = new TelemetryService();

/**
 * Única función pública para emitir eventos de telemetría.
 * Todo el tracking del backoffice pasa por aquí.
 */
export function track(
  eventName: EventName,
  payload: Record<string, unknown>,
  options?: {
    warehouse?: string | null;
    correlationId?: string | null;
    processingMode?: "stream" | "batch";
  },
): void {
  telemetryService.track(eventName, payload, options);
}

export { TelemetryService };