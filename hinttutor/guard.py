"""Leak guard. Rejects hints that reveal the fix. Pure functions, no model calls.

The fix is computed by diffing the student's code against the reference solution
(both normalized with ast.unparse so formatting differences do not matter).

Rules:
  1. No triple-backtick code block.
  2. The hint must not contain a corrected line (whitespace ignored).
  3. The hint must not contain the changed tokens of the fix (for example "+1" or "n+1").
If the diff touches more than BROAD_LIMIT lines, the student probably took a different valid
approach, so only rule 1 and an exact-line match against any reference line apply.
"""
from __future__ import annotations

import ast
import difflib
import re
from dataclasses import dataclass, field

FENCE = "`" * 3
BROAD_LIMIT = 5
MIN_LINE_LEN = 5
_TOKEN_RE = re.compile(r"\w+|<=|>=|==|!=|//|\*\*|\+=|-=|\*=|/=|->|[^\w\s]")
_EXEC_STMT_RE = re.compile(
    r"\b(def\s+\w+\s*\(|return\s+[^.?!:\n]+|for\s+\w+\s+in\s+|while\s+[^.?!:\n]+:)"
)


@dataclass
class Fix:
    fix_lines: list = field(default_factory=list)
    reference_lines: list = field(default_factory=list)
    candidates: list = field(default_factory=list)
    changed: int = 0
    broad: bool = False


@dataclass
class Verdict:
    ok: bool
    reasons: list = field(default_factory=list)  # generic labels, safe to send to the model
    detail: list = field(default_factory=list)   # contains fix text, TA view only


def _normalize(code: str) -> str:
    try:
        return ast.unparse(ast.parse(code))
    except SyntaxError:
        return "\n".join(line.rstrip() for line in code.splitlines())


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _candidates(hunks: list) -> list:
    out = []
    for buggy, fixed in hunks:
        ta = _TOKEN_RE.findall(" ".join(buggy))
        tb = _TOKEN_RE.findall(" ".join(fixed))
        sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
        for tag, _i1, _i2, j1, j2 in sm.get_opcodes():
            if tag not in ("replace", "insert"):
                continue
            span = "".join(tb[j1:j2])
            left = tb[j1 - 1] if (j1 > 0 and tb[j1 - 1] not in "([,:") else ""
            cands = [span, left + span]
            for tok in tb[j1:j2]:
                if len(tok) >= 2 and not tok.isalpha():
                    cands.append(tok)
            # Catch variable assignment updates like count = 0 or count to 0
            if j1 > 1 and tb[j1 - 1] == "=" and tb[j1 - 2].isidentifier():
                cands.extend([tb[j1 - 2] + "=" + span, tb[j1 - 2] + span, tb[j1 - 2] + "to" + span])
            for cand in cands:
                if len(cand) >= 2 and not cand.isalpha() and cand not in out:
                    out.append(cand)
    return out


def compute_fix(student_code: str, reference_code: str) -> Fix:
    a = _normalize(student_code).splitlines()
    b = _normalize(reference_code).splitlines()
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    hunks, fix_lines, changed = [], [], 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        hunks.append((a[i1:i2], b[j1:j2]))
        fix_lines += b[j1:j2]
        changed += max(i2 - i1, j2 - j1)
    broad = changed > BROAD_LIMIT
    return Fix(
        fix_lines=fix_lines,
        reference_lines=b,
        candidates=[] if broad else _candidates(hunks),
        changed=changed,
        broad=broad,
    )


def check(hint: str, fix: Fix) -> Verdict:
    text = hint.strip()
    if not text:
        return Verdict(False, ["empty"])
    reasons, detail = [], []
    if FENCE in text or _EXEC_STMT_RE.search(text):
        reasons.append("code_block")
    squashed = _squash(text)

    lines = fix.reference_lines if fix.broad else fix.fix_lines
    for line in lines:
        clean = line.strip().rstrip(":")
        s = _squash(clean)
        if len(s) >= MIN_LINE_LEN and s in squashed:
            reasons.append("fix_line")
            detail.append(line.strip())
            break

    if not fix.broad:
        for cand in fix.candidates:
            if cand in squashed:
                reasons.append("fix_expression")
                detail.append(cand)
                break
    return Verdict(not reasons, reasons, detail)
