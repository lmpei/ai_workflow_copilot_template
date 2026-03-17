def build_eval_run_summary(
    *,
    scenario_summary_fields: dict[str, object],
    total_cases: int,
    completed_cases: int,
    failed_cases: int,
    passed_cases: int,
    score_total: float,
) -> dict[str, object]:
    return {
        **scenario_summary_fields,
        "total_cases": total_cases,
        "completed_cases": completed_cases,
        "failed_cases": failed_cases,
        "passed_cases": passed_cases,
        "avg_score": round(score_total / completed_cases, 4) if completed_cases > 0 else 0.0,
        "pass_rate": round(passed_cases / total_cases, 4) if total_cases > 0 else 0.0,
    }
