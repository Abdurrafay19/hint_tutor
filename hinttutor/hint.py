"""Step 2: write a hint from the diagnosis, check it with the guard, retry, then fall back."""
from __future__ import annotations

from . import config, guard, llm, prompts
from .diagnose import number_code
from .models import Attempt, CallLog, Diagnosis, HintResult


def fallback_text(diagnosis: Diagnosis | None, failure: str) -> str:
    if diagnosis is not None:
        return ("Look at line %d. Trace the failing input by hand and compare each step "
                "to what you expect." % diagnosis.line)
    return "Trace the failing input by hand, one step at a time, and compare each step to the expected output."


def generate_hint(problem: str, code: str, failure: str, diagnosis: Diagnosis | None,
                  reference_code: str, model: str | None = None):
    """Returns (HintResult, list[CallLog])."""
    if diagnosis is None:
        return HintResult(fallback_text(None, failure), [], True), []

    fix = guard.compute_fix(code, reference_code)
    base_user = prompts.HINT_USER.format(
        problem=problem, numbered_code=number_code(code), failure=failure,
        line=diagnosis.line, bug_type=diagnosis.bug_type, reason=diagnosis.reason,
    )
    user, attempts, calls = base_user, [], []
    for _ in range(config.MAX_HINT_ATTEMPTS):
        res = llm.chat(
            prompts.HINT_SYSTEM, user, temperature=config.HINT_TEMPERATURE,
            max_tokens=config.HINT_MAX_TOKENS, model=model,
        )
        verdict = guard.check(res.text, fix)
        attempts.append(Attempt(res.text.strip(), verdict.ok, verdict.reasons, verdict.detail, res.seconds))
        calls.append(CallLog("hint", res.seconds, verdict.ok))
        if verdict.ok:
            return HintResult(res.text.strip(), attempts, False), calls
        user = base_user + prompts.HINT_RETRY.format(reasons=", ".join(verdict.reasons))
    return HintResult(fallback_text(diagnosis, failure), attempts, True), calls
