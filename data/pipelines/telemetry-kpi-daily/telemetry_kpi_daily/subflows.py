"""Reusable Prefect subflows — one per ETL phase."""

from __future__ import annotations

from datetime import date
from typing import Any

from prefect import flow

from telemetry_kpi_daily.config import PipelineConfig
from telemetry_kpi_daily.phases import coalesce_validation
from telemetry_kpi_daily.tasks import extract_task, load_task, transform_task, validate_task


def _retry_kwargs(config: PipelineConfig, stage: str) -> dict[str, int]:
    # 3 retries × 30s: Supabase transient blips clear within ~90s; beyond that is likely config.
    if stage == "extract":
        return {
            "retries": config.extract_retries,
            "retry_delay_seconds": config.extract_retry_delay_seconds,
        }
    if stage == "load":
        return {
            "retries": config.load_retries,
            "retry_delay_seconds": config.load_retry_delay_seconds,
        }
    return {"retries": 0, "retry_delay_seconds": 0}


@flow(name="extract-subflow", log_prints=True)
def extract_subflow(processing_date: date, config: PipelineConfig) -> dict[str, Any]:
    return extract_task.with_options(**_retry_kwargs(config, "extract"))(
        processing_date, config
    )


@flow(name="validate-subflow", log_prints=True)
def validate_subflow(extracted: dict[str, Any]) -> dict[str, Any]:
    state = validate_task.with_options(allow_failure=True)(extracted, return_state=True)
    return coalesce_validation(extracted, state)


@flow(name="transform-subflow", log_prints=True)
def transform_subflow(processing_date: date) -> dict[str, Any]:
    return transform_task(processing_date)


@flow(name="load-subflow", log_prints=True)
def load_subflow(
    transformed: dict[str, Any],
    *,
    run_id: str,
    config: PipelineConfig,
) -> dict[str, Any]:
    return load_task.with_options(**_retry_kwargs(config, "load"))(
        transformed,
        run_id=run_id,
        config=config,
    )
