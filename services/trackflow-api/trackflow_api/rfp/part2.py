"""Parte 2: generator–evaluator cycle with per-department parallelism."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable

from .agents.evaluators import EvaluationBundle, run_evaluators_parallel
from .agents.generators import generate_department_section
from .constants import MAX_GENERATOR_ITERATIONS


ProgressCallback = Callable[[str, dict[str, Any]], None]


@dataclass
class SectionLoopResult:
    department_id: str
    draft_content: str
    evaluation_results: dict[str, Any]
    iteration_count: int
    approval_status: str
    passed: bool
    attempts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "department_id": self.department_id,
            "draft_content": self.draft_content,
            "evaluation_results": self.evaluation_results,
            "iteration_count": self.iteration_count,
            "approval_status": self.approval_status,
            "passed": self.passed,
            "attempts": self.attempts,
        }


def run_generator_evaluator_loop(
    department_id: str,
    *,
    metadata: dict,
    key_aspects: list[str],
    markdown: str = "",
    max_iterations: int = MAX_GENERATOR_ITERATIONS,
    on_progress: ProgressCallback | None = None,
) -> SectionLoopResult:
    """Generate → evaluate in parallel → retry with feedback until pass or max iterations."""
    feedback: list[str] = []
    attempts: list[dict[str, Any]] = []
    draft = ""
    bundle: EvaluationBundle | None = None

    for iteration in range(1, max_iterations + 1):
        if on_progress:
            on_progress(
                department_id,
                {"stage": "generating", "iteration": iteration, "ticket_status": "generando_borrador"},
            )

        generated = generate_department_section(
            department_id,
            metadata=metadata,
            key_aspects=key_aspects,
            markdown=markdown,
            feedback=feedback or None,
        )
        draft = generated.draft_content

        if on_progress:
            on_progress(
                department_id,
                {
                    "stage": "evaluating",
                    "iteration": iteration,
                    "ticket_status": "en_evaluación",
                    "draft_content": draft,
                },
            )

        bundle = run_evaluators_parallel(
            draft,
            metadata=metadata,
            key_aspects=key_aspects,
            department_id=department_id,
        )
        attempt = {
            "iteration": iteration,
            "passed": bundle.passed,
            "evaluation": bundle.to_dict(),
            "feedback": bundle.feedback_for_generator(),
        }
        attempts.append(attempt)

        if bundle.passed:
            evaluation_results = {
                **bundle.to_dict(),
                "stage": "complete",
                "attempts": attempts,
            }
            if on_progress:
                on_progress(
                    department_id,
                    {
                        "stage": "complete",
                        "iteration": iteration,
                        "draft_content": draft,
                        "evaluation_results": evaluation_results,
                        "approval_status": "pending",
                        "passed": True,
                    },
                )
            return SectionLoopResult(
                department_id=department_id,
                draft_content=draft,
                evaluation_results=evaluation_results,
                iteration_count=iteration,
                approval_status="pending",
                passed=True,
                attempts=attempts,
            )

        feedback = bundle.feedback_for_generator()

    assert bundle is not None
    evaluation_results = {
        **bundle.to_dict(),
        "stage": "needs_human_review",
        "attempts": attempts,
        "max_iterations_reached": True,
    }
    if on_progress:
        on_progress(
            department_id,
            {
                "stage": "needs_human_review",
                "iteration": max_iterations,
                "draft_content": draft,
                "evaluation_results": evaluation_results,
                "approval_status": "needs_human_review",
                "passed": False,
            },
        )
    return SectionLoopResult(
        department_id=department_id,
        draft_content=draft,
        evaluation_results=evaluation_results,
        iteration_count=max_iterations,
        approval_status="needs_human_review",
        passed=False,
        attempts=attempts,
    )


def run_part2_for_departments(
    department_ids: list[str],
    *,
    metadata: dict,
    sections_by_dept: dict[str, list[str]],
    markdown: str = "",
    max_iterations: int = MAX_GENERATOR_ITERATIONS,
    on_progress: ProgressCallback | None = None,
) -> list[SectionLoopResult]:
    """Fan-out department generator–evaluator loops in parallel (departments do not block each other)."""
    if not department_ids:
        return []

    results_by_id: dict[str, SectionLoopResult] = {}
    with ThreadPoolExecutor(max_workers=max(1, len(department_ids))) as pool:
        futures = {
            pool.submit(
                run_generator_evaluator_loop,
                dept_id,
                metadata=metadata,
                key_aspects=list(sections_by_dept.get(dept_id) or []),
                markdown=markdown,
                max_iterations=max_iterations,
                on_progress=on_progress,
            ): dept_id
            for dept_id in department_ids
        }
        for fut in as_completed(futures):
            result = fut.result()
            results_by_id[result.department_id] = result

    return [results_by_id[d] for d in department_ids if d in results_by_id]
