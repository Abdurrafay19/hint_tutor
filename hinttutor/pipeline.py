"""End to end flow: run tests, diagnose, hint. No UI code here."""
from __future__ import annotations

import time

from . import config, hint as hint_mod, runner
from .assignment import Assignment
from .diagnose import diagnose
from .llm import LLMError
from .models import PipelineResult


def run(asg: Assignment, code: str, model: str | None = None) -> PipelineResult:
    model = model or config.MODEL
    start = time.perf_counter()

    def done(**kw) -> PipelineResult:
        return PipelineResult(model=model, total_seconds=time.perf_counter() - start, **kw)

    if not code.strip():
        return done(status="empty", message="No code to run. Paste or write your function first.")

    if len(code.splitlines()) > config.MAX_CODE_LINES:
        return done(status="too_long", message="Code is longer than %d lines. Trim it and retry." % config.MAX_CODE_LINES)

    report = runner.run_tests(code, asg.function, asg.tests)

    if report.syntax_error:
        e = report.syntax_error
        where = "on line %d" % e.line if e.line else "in your file"
        msg = ("Python reports a syntax error %s: %s. Read that line and the one above it, then check "
               "brackets, colons, and indentation." % (where, e.message))
        return done(status="syntax_error", message=msg, report=report)

    if report.all_passed:
        return done(status="passed", message="All %d tests pass." % len(report.results), report=report)

    failure = runner.describe_failure(asg.function, report.first_failure)
    try:
        dres = diagnose(asg.problem, code, failure, model)
        hres, hcalls = hint_mod.generate_hint(asg.problem, code, failure, dres.diagnosis, asg.reference_code, model)
    except LLMError as exc:
        return done(status="llm_error", message=str(exc), report=report, error=str(exc))

    return done(
        status="hint", message=hres.text, report=report, diagnosis=dres.diagnosis,
        hint=hres, calls=dres.calls + hcalls,
    )
