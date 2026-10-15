"""All prompt text in one place."""

DIAGNOSE_SYSTEM = (
    "You are a debugging assistant for beginner Python assignments. You receive a problem "
    "statement, a student's code with line numbers, and one failing test. Find the single line "
    "most responsible for the failure. Reply with JSON only."
)

DIAGNOSE_USER = """Problem:
{problem}

Student code (line number, then code):
{numbered_code}

Failing test:
{failure}

Return JSON with these keys:
line: the line number of the buggy line (integer, between 1 and {n_lines})
bug_type: one of {bug_types}
reason: one sentence explaining what is wrong on that line"""

DIAGNOSE_RETRY = "\n\nYour previous answer had an invalid line number. Use an integer between 1 and {n_lines}."

HINT_SYSTEM = (
    "You are a patient programming tutor. You guide students toward the bug with questions. "
    "You never write code and never state the corrected line."
)

HINT_USER = """Problem:
{problem}

Student code (line number, then code):
{numbered_code}

Failing test:
{failure}

Diagnosis: line {line}, {bug_type}: {reason}

Write 2 to 3 sentences that point the student toward line {line}. End with one question that makes
them check the problem themselves. Do not write code. Do not say what the fixed line should be.
Do not use code blocks."""

HINT_RETRY = "\n\nYour previous hint was rejected ({reasons}). Rewrite it so it only points at the location and asks a question."
