"""Plain dataclasses shared across modules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CaseResult:
    index: int
    args: list
    expected: Any
    actual: Any = None
    passed: bool = False
    kind: str = "wrong"  # ok | wrong | exception | timeout | crash
    error: str = ""
    error_line: Optional[int] = None
    seconds: float = 0.0


@dataclass
class SyntaxInfo:
    line: Optional[int]
    message: str


@dataclass
class TestReport:
    __test__ = False  # stop test runners from collecting this class
    function: str
    results: list = field(default_factory=list)
    syntax_error: Optional[SyntaxInfo] = None

    @property
    def all_passed(self) -> bool:
        return self.syntax_error is None and bool(self.results) and all(r.passed for r in self.results)

    @property
    def first_failure(self) -> Optional[CaseResult]:
        return next((r for r in self.results if not r.passed), None)

    @property
    def n_passed(self) -> int:
        return sum(1 for r in self.results if r.passed)


@dataclass
class Diagnosis:
    line: int
    bug_type: str
    reason: str
    raw: str = ""


@dataclass
class CallLog:
    name: str  # diagnose | hint
    seconds: float
    ok: bool = True


@dataclass
class DiagnoseResult:
    diagnosis: Optional[Diagnosis]
    calls: list = field(default_factory=list)


@dataclass
class Attempt:
    text: str
    ok: bool
    reasons: list = field(default_factory=list)  # generic labels, safe to send back to the model
    detail: list = field(default_factory=list)   # contains fix text, TA view only
    seconds: float = 0.0


@dataclass
class HintResult:
    text: str
    attempts: list = field(default_factory=list)
    used_fallback: bool = False


@dataclass
class PipelineResult:
    status: str  # passed | syntax_error | too_long | hint | llm_error
    message: str
    model: str
    report: Optional[TestReport] = None
    diagnosis: Optional[Diagnosis] = None
    hint: Optional[HintResult] = None
    calls: list = field(default_factory=list)
    error: str = ""
    total_seconds: float = 0.0
