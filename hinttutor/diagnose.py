"""Step 1: ask the model which line is buggy. JSON-schema constrained output."""
from __future__ import annotations

import json

from . import config, llm, prompts
from .models import CallLog, Diagnosis, DiagnoseResult

BUG_TYPES = ["off_by_one", "wrong_operator", "missing_base_case", "wrong_loop_bound", "mutation", "other"]

SCHEMA = {
    "type": "object",
    "properties": {
        "line": {"type": "integer"},
        "bug_type": {"type": "string", "enum": BUG_TYPES},
        "reason": {"type": "string"},
    },
    "required": ["line", "bug_type", "reason"],
}


def number_code(code: str) -> str:
    return "\n".join("%3d | %s" % (i, line) for i, line in enumerate(code.splitlines(), start=1))


def diagnose(problem: str, code: str, failure: str, model: str | None = None) -> DiagnoseResult:
    n_lines = len(code.splitlines())
    user = prompts.DIAGNOSE_USER.format(
        problem=problem, numbered_code=number_code(code), failure=failure,
        n_lines=n_lines, bug_types=", ".join(BUG_TYPES),
    )
    calls = []
    for attempt in range(2):
        res = llm.chat(
            prompts.DIAGNOSE_SYSTEM, user, temperature=config.DIAGNOSE_TEMPERATURE,
            max_tokens=config.DIAGNOSE_MAX_TOKENS, schema=SCHEMA, model=model,
        )
        try:
            data = json.loads(res.text)
            line_val = data["line"]
            valid = type(line_val) is int and 1 <= line_val <= n_lines
            line = line_val if valid else 0
        except (ValueError, KeyError, TypeError):
            valid = False
        calls.append(CallLog("diagnose", res.seconds, valid))
        if valid:
            bug_type = data.get("bug_type", "other")
            if bug_type not in BUG_TYPES:
                bug_type = "other"
            return DiagnoseResult(Diagnosis(line, bug_type, str(data.get("reason", "")), res.text), calls)
        if attempt == 0:
            user += prompts.DIAGNOSE_RETRY.format(n_lines=n_lines)
    return DiagnoseResult(None, calls)
