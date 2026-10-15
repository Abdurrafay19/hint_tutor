"""Runs student code against test cases, one subprocess per case."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from . import config
from .models import CaseResult, SyntaxInfo, TestReport

WORKER = Path(__file__).with_name("_worker.py")


def run_tests(code: str, function: str, tests: list, timeout: float | None = None) -> TestReport:
    timeout = timeout or config.TEST_TIMEOUT_SECONDS
    try:
        compile(code, "student.py", "exec")
    except SyntaxError as exc:
        return TestReport(function, [], SyntaxInfo(exc.lineno, exc.msg))
    results = []
    for i, t in enumerate(tests):
        res = _run_case(code, function, i, t, timeout)
        results.append(res)
        if res.kind == "timeout":
            for j in range(i + 1, len(tests)):
                results.append(CaseResult(
                    index=j, args=tests[j]["args"], expected=tests[j]["expected"],
                    kind="timeout", error="timed out (aborted after earlier timeout)",
                ))
            break
    return TestReport(function, results)


def _run_case(code: str, function: str, index: int, test: dict, timeout: float) -> CaseResult:
    res = CaseResult(index=index, args=test["args"], expected=test["expected"])
    payload = json.dumps({"code": code, "function": function, "args": test["args"]})
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, "-I", str(WORKER)],
            input=payload, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        res.kind, res.error = "timeout", "timed out after %gs (infinite loop?)" % timeout
        res.seconds = time.perf_counter() - start
        return res
    res.seconds = time.perf_counter() - start

    lines = proc.stdout.strip().splitlines()
    try:
        data = json.loads(lines[-1])
    except (IndexError, json.JSONDecodeError):
        err = proc.stderr.strip().splitlines()
        res.kind, res.error = "crash", (err[-1] if err else "worker process crashed")
        return res

    if data["ok"]:
        val = data["value"]
        if data.get("val_type") == "tuple" and isinstance(val, list):
            val = tuple(val)
        res.actual = val
        res.passed = val == test["expected"]
        res.kind = "ok" if res.passed else "wrong"
    else:
        res.kind, res.error, res.error_line = "exception", data["error"], data.get("line")
    return res


def call_repr(function: str, args: list) -> str:
    return "%s(%s)" % (function, ", ".join(repr(a) for a in args))


def describe_failure(function: str, r: CaseResult | None) -> str:
    if r is None:
        return "No test failure details available."
    lines = ["call: " + call_repr(function, r.args), "expected: %r" % (r.expected,)]
    if r.kind == "wrong":
        lines.append("actual: %r" % (r.actual,))
    else:
        where = " (raised at line %d)" % r.error_line if r.error_line else ""
        lines.append("error: %s%s" % (r.error, where))
    return "\n".join(lines)
