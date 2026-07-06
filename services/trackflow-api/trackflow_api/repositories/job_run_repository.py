"""Persistence helpers for nightly job runs and distributed locks."""

from __future__ import annotations

import threading
from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from ..models import JobLock, JobRun

NIGHTLY_TELEMETRY_JOB = "nightly-telemetry"

_PROCESS_LOCKS: dict[str, threading.Lock] = {}
_PROCESS_LOCK_GUARD = threading.Lock()


def _process_lock_for(job_name: str) -> threading.Lock:
    with _PROCESS_LOCK_GUARD:
        lock = _PROCESS_LOCKS.get(job_name)
        if lock is None:
            lock = threading.Lock()
            _PROCESS_LOCKS[job_name] = lock
        return lock


def has_completed_run(
    session: Session,
    *,
    job_name: str,
    target_date: date,
) -> bool:
    statement = (
        select(JobRun)
        .where(JobRun.job_name == job_name)
        .where(JobRun.target_date == target_date)
        .where(JobRun.status == "completed")
    )
    return session.exec(statement).first() is not None


def create_job_run(
    session: Session,
    *,
    job_name: str,
    target_date: date,
    run_id: str | None = None,
    status: str = "pending",
) -> JobRun:
    run = JobRun(
        run_id=run_id or str(uuid4()),
        job_name=job_name,
        target_date=target_date,
        status=status,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def mark_job_processing(session: Session, run: JobRun) -> JobRun:
    run.status = "processing"
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def mark_job_completed(
    session: Session,
    run: JobRun,
    *,
    csv_path: str | None = None,
) -> JobRun:
    run.status = "completed"
    run.finished_at = datetime.now(timezone.utc)
    if csv_path is not None:
        run.csv_path = csv_path
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def mark_job_failed(session: Session, run: JobRun, error_message: str) -> JobRun:
    run.status = "failed"
    run.finished_at = datetime.now(timezone.utc)
    run.error_message = error_message
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def ensure_lock_row(session: Session, job_name: str) -> None:
    if session.get(JobLock, job_name) is not None:
        return
    session.add(JobLock(job_name=job_name, is_locked=False))
    try:
        session.commit()
    except IntegrityError:
        session.rollback()


def try_acquire_lock(session: Session, job_name: str, run_id: str) -> bool:
    process_lock = _process_lock_for(job_name)
    if not process_lock.acquire(blocking=False):
        return False

    try:
        ensure_lock_row(session, job_name)
        lock = session.exec(
            select(JobLock).where(JobLock.job_name == job_name).with_for_update()
        ).first()
        if lock is None or lock.is_locked:
            session.rollback()
            process_lock.release()
            return False

        lock.is_locked = True
        lock.locked_at = datetime.now(timezone.utc)
        lock.holder_run_id = run_id
        session.add(lock)
        session.commit()
        return True
    except Exception:
        process_lock.release()
        raise


def release_lock(session: Session, job_name: str) -> None:
    lock = session.get(JobLock, job_name)
    if lock is not None:
        lock.is_locked = False
        lock.locked_at = None
        lock.holder_run_id = None
        session.add(lock)
        session.commit()

    process_lock = _PROCESS_LOCKS.get(job_name)
    if process_lock is not None and process_lock.locked():
        process_lock.release()


def get_job_run(session: Session, run_id: str) -> JobRun | None:
    return session.get(JobRun, run_id)
