"""Generate buggy variants of each reference solution by AST mutation.

    python -m eval.mutate --per-assignment 6

Only mutants that FAIL the assignment's tests are kept. The ground-truth line is the mutated
node's line. Both original and mutant go through ast.unparse so line numbers align with what the
model sees. Mutants are synthetic and easier than real student bugs: say so in the README.
"""
from __future__ import annotations

import argparse
import ast
import copy
import json
import random
from pathlib import Path

from hinttutor import assignment, config, runner

OUT_DIR = config.ROOT / "eval" / "cases"

CMP_SWAPS = {
    ast.Lt: [ast.LtE, ast.Gt], ast.LtE: [ast.Lt, ast.GtE],
    ast.Gt: [ast.GtE, ast.Lt], ast.GtE: [ast.Gt, ast.LtE],
    ast.Eq: [ast.NotEq], ast.NotEq: [ast.Eq],
}
OFF_BY_ONE = {frozenset({ast.Lt, ast.LtE}), frozenset({ast.Gt, ast.GtE})}
BIN_SWAPS = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Add}
AUG_SWAPS = {ast.Add: ast.Sub, ast.Sub: ast.Add}


def _candidates(tree: ast.AST) -> list:
    nodes = list(ast.walk(tree))
    in_range = set()
    for n in nodes:
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "range":
            for sub in ast.walk(n):
                if isinstance(sub, ast.Constant) and type(sub.value) is int:
                    in_range.add(id(sub))
    out = []
    for idx, n in enumerate(nodes):
        if isinstance(n, ast.Compare) and len(n.ops) == 1:
            old = type(n.ops[0])
            for new in CMP_SWAPS.get(old, []):
                bug = "off_by_one" if frozenset({old, new}) in OFF_BY_ONE else "wrong_operator"
                out.append((idx, ("cmp", new), "%s -> %s" % (old.__name__, new.__name__), bug))
        elif isinstance(n, ast.BinOp) and type(n.op) in BIN_SWAPS:
            new = BIN_SWAPS[type(n.op)]
            out.append((idx, ("binop", new), "%s -> %s" % (type(n.op).__name__, new.__name__), "wrong_operator"))
        elif isinstance(n, ast.AugAssign) and type(n.op) in AUG_SWAPS:
            new = AUG_SWAPS[type(n.op)]
            out.append((idx, ("aug", new), "%s -> %s" % (type(n.op).__name__, new.__name__), "wrong_operator"))
        elif isinstance(n, ast.Constant) and type(n.value) is int:
            bug = "wrong_loop_bound" if id(n) in in_range else "off_by_one"
            for delta in (1, -1):
                out.append((idx, ("const", delta), "const %+d" % delta, bug))
    return out


def _apply(node: ast.AST, variant: tuple) -> None:
    kind, arg = variant
    if kind == "cmp":
        node.ops[0] = arg()
    elif kind in ("binop", "aug"):
        node.op = arg()
    elif kind == "const":
        node.value += arg


def generate(asg, timeout: float = 2.0) -> list:
    base = ast.unparse(ast.parse(asg.reference_code))
    tree0 = ast.parse(base)
    out, seen = [], {base}
    for idx, variant, desc, bug in _candidates(tree0):
        tree = copy.deepcopy(tree0)
        node = list(ast.walk(tree))[idx]
        line = node.lineno
        _apply(node, variant)
        code = ast.unparse(tree)
        if code in seen or code.count("\n") != base.count("\n"):
            continue
        seen.add(code)
        report = runner.run_tests(code, asg.function, asg.tests, timeout)
        if report.syntax_error or report.all_passed:
            continue
        out.append({"code": code, "line": line, "bug_type": bug, "mutation": desc})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-assignment", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*"):
        if old.is_file():
            old.unlink()
    rng = random.Random(args.seed)
    manifest = []
    for name in assignment.list_assignments():
        asg = assignment.load(name)
        mutants = generate(asg)
        picked = rng.sample(mutants, min(args.per_assignment, len(mutants)))
        for k, m in enumerate(picked, start=1):
            case_id = "%s__%02d" % (name, k)
            rel = "eval/cases/%s.py" % case_id
            (config.ROOT / rel).write_text(m["code"] + "\n", encoding="utf-8")
            manifest.append({"id": case_id, "kind": "mutant", "assignment": name, "file": rel,
                             "line": m["line"], "bug_type": m["bug_type"], "mutation": m["mutation"]})
        print("%-18s %2d failing mutants found, %d kept" % (name, len(mutants), len(picked)))
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("wrote %d cases to %s" % (len(manifest), OUT_DIR))


if __name__ == "__main__":
    main()
