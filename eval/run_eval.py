"""Run the full pipeline on every eval case and write results.

    python -m eval.run_eval                 # all cases
    python -m eval.run_eval --limit 5       # smoke test
    python -m eval.run_eval --model llama3.2:3b

Outputs eval/results.csv (one row per case, with an empty hand_label column) and eval/summary.json.
Needs Ollama running. Generate mutants first: python -m eval.mutate
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys

from hinttutor import assignment, config, pipeline

EVAL_DIR = config.ROOT / "eval"
FIELDS = ["id", "kind", "assignment", "truth_bug_type", "truth_line", "status", "diag_line", "diag_bug_type",
          "line_exact", "line_within1", "bug_type_match", "hint_attempts", "first_attempt_rejected",
          "used_fallback", "total_seconds", "final_hint", "hand_label"]


def load_cases() -> list:
    cases = []
    for path in (EVAL_DIR / "cases" / "manifest.json", EVAL_DIR / "handwritten" / "manifest.json"):
        if path.exists():
            cases += json.loads(path.read_text(encoding="utf-8"))
    return cases


def p95(values: list) -> float:
    s = sorted(values)
    return s[max(0, math.ceil(0.95 * len(s)) - 1)] if s else 0.0


def summarize(rows: list, call_times: dict) -> dict:
    hinted = [r for r in rows if r["status"] == "hint"]
    with_diag = [r for r in hinted if r["diag_line"] != ""]
    out = {
        "cases": len(rows),
        "cases_with_hint": len(hinted),
        "diagnosis_returned": len(with_diag),
        "line_exact_pct": round(100 * sum(r["line_exact"] for r in with_diag) / max(1, len(hinted)), 1),
        "line_within1_pct": round(100 * sum(r["line_within1"] for r in with_diag) / max(1, len(hinted)), 1),
        "bug_type_match_pct": round(100 * sum(r["bug_type_match"] for r in with_diag) / max(1, len(hinted)), 1),
        "first_attempt_guard_rejection_pct": round(
            100 * sum(r["first_attempt_rejected"] for r in with_diag) / max(1, len(with_diag)), 1),
        "fallback_pct": round(100 * sum(r["used_fallback"] for r in hinted) / max(1, len(hinted)), 1),
        "latency_seconds": {},
    }
    for name, times in call_times.items():
        if times:
            out["latency_seconds"][name] = {"calls": len(times), "median": round(statistics.median(times), 2),
                                            "p95": round(p95(times), 2)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=config.MODEL)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    cases = load_cases()
    if not cases:
        print("No cases found. Run: python -m eval.mutate")
        return 1
    if args.limit:
        cases = cases[: args.limit]

    cache, rows, call_times = {}, [], {"diagnose": [], "hint": []}
    with open(EVAL_DIR / "results.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for n, c in enumerate(cases, start=1):
            asg = cache.setdefault(c["assignment"], assignment.load(c["assignment"]))
            code = (config.ROOT / c["file"]).read_text(encoding="utf-8")
            res = pipeline.run(asg, code, model=args.model)
            if res.status == "llm_error":
                print(res.message)
                return 1
            d, h = res.diagnosis, res.hint
            row = {
                "id": c["id"], "kind": c["kind"], "assignment": c["assignment"],
                "truth_bug_type": c["bug_type"], "truth_line": c["line"], "status": res.status,
                "diag_line": d.line if d else "", "diag_bug_type": d.bug_type if d else "",
                "line_exact": int(bool(d and d.line == c["line"])),
                "line_within1": int(bool(d and abs(d.line - c["line"]) <= 1)),
                "bug_type_match": int(bool(d and d.bug_type == c["bug_type"])),
                "hint_attempts": len(h.attempts) if h else 0,
                "first_attempt_rejected": int(bool(h and h.attempts and not h.attempts[0].ok)),
                "used_fallback": int(bool(h and h.used_fallback)),
                "total_seconds": round(res.total_seconds, 2),
                "final_hint": (h.text if h else res.message).replace("\n", " "),
                "hand_label": "",
            }
            for call in res.calls:
                call_times[call.name].append(call.seconds)
            rows.append(row)
            writer.writerow(row)
            fh.flush()
            print("[%d/%d] %-26s line %s (truth %s)  attempts=%s  %.1fs" % (
                n, len(cases), c["id"], row["diag_line"], c["line"], row["hint_attempts"], res.total_seconds))

    summary = summarize(rows, call_times)
    summary["model"] = args.model
    (EVAL_DIR / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n" + json.dumps(summary, indent=2))
    print("\nNext: open eval/results.csv, fill hand_label (good / leaks / wrong_bug) for ~20 rows.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
