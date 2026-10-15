"""Loads assignments from assignments/<name>/{assignment.json, reference.py}."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import config


@dataclass
class Assignment:
    name: str
    title: str
    problem: str
    function: str
    tests: list
    reference_code: str
    directory: Path

    @property
    def buggy_example(self) -> str | None:
        path = self.directory / "buggy.py"
        return path.read_text(encoding="utf-8") if path.exists() else None


def list_assignments(root: Path | None = None) -> list:
    root = root or config.ASSIGNMENTS_DIR
    return sorted(p.name for p in root.iterdir() if (p / "assignment.json").exists())


def load(name: str, root: Path | None = None) -> Assignment:
    root = root or config.ASSIGNMENTS_DIR
    d = root / name
    if not (d / "assignment.json").exists():
        raise FileNotFoundError("No assignment '%s'. Available: %s" % (name, ", ".join(list_assignments(root))))
    ref_path = d / "reference.py"
    if not ref_path.exists():
        raise FileNotFoundError("Assignment '%s' is missing reference.py" % name)
    meta = json.loads((d / "assignment.json").read_text(encoding="utf-8"))
    return Assignment(
        name=name, title=meta["title"], problem=meta["problem"], function=meta["function"],
        tests=meta["tests"], reference_code=ref_path.read_text(encoding="utf-8"), directory=d,
    )
