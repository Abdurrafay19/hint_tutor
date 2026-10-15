"""Command line front end.

    python cli.py --list
    python cli.py sum_to_n my_code.py
    python cli.py sum_to_n my_code.py --debug
"""
import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from hinttutor import assignment, config, pipeline, runner


def main() -> int:
    p = argparse.ArgumentParser(description="Test-grounded hints for Python assignments.")
    p.add_argument("assignment", nargs="?", help="assignment name (see --list)")
    p.add_argument("file", nargs="?", help="path to the student's .py file")
    p.add_argument("--model", default=config.MODEL, help="Ollama model (default: %(default)s)")
    p.add_argument("--debug", action="store_true", help="show diagnosis, guard attempts, latency (TA view)")
    p.add_argument("--json", action="store_true", help="print the full result as JSON")
    p.add_argument("--list", action="store_true", help="list assignments and exit")
    args = p.parse_args()

    if args.list:
        for name in assignment.list_assignments():
            print("%-18s %s" % (name, assignment.load(name).title))
        return 0
    if not args.assignment or not args.file:
        p.error("assignment and file are required (or use --list)")

    asg = assignment.load(args.assignment)
    code = Path(args.file).read_text(encoding="utf-8")
    res = pipeline.run(asg, code, model=args.model)

    if args.json:
        print(json.dumps(asdict(res), indent=2, default=str))
        return 0 if res.status == "passed" else 1

    if res.report and res.report.results:
        for r in res.report.results:
            status = "PASS" if r.passed else "FAIL"
            detail = "" if r.passed else "  -> %s" % (repr(r.actual) if r.kind == "wrong" else r.error)
            print("[%s] %s == %r%s" % (status, runner.call_repr(asg.function, r.args), r.expected, detail))
        print("%d/%d tests pass\n" % (res.report.n_passed, len(res.report.results)))

    label = {"hint": "Hint", "passed": "Result", "syntax_error": "Syntax error",
             "too_long": "Error", "empty": "Error", "empty_tests": "Error",
             "llm_error": "Model error"}.get(res.status, "Error")
    print("%s: %s" % (label, res.message))

    if args.debug and res.status == "hint":
        print("\n--- under the hood (TA view, contains fix details) ---")
        print("model: %s  total: %.1fs" % (res.model, res.total_seconds))
        if res.diagnosis:
            d = res.diagnosis
            print("diagnosis: line %d, %s, %s" % (d.line, d.bug_type, d.reason))
        for i, a in enumerate(res.hint.attempts, start=1):
            print("attempt %d: %s %s %s (%.1fs)" % (i, "accepted" if a.ok else "REJECTED",
                                                    a.reasons or "", a.detail or "", a.seconds))
        if res.hint.used_fallback:
            print("fallback template used")
    return 0 if res.status == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
