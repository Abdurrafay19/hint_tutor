"""Thin wrapper around the Ollama Python client. Times every call."""
from __future__ import annotations

import time
from dataclasses import dataclass

from . import config


class LLMError(RuntimeError):
    pass


@dataclass
class LLMResult:
    text: str
    seconds: float
    model: str


def chat(system: str, user: str, *, temperature: float, max_tokens: int,
         schema: dict | None = None, model: str | None = None) -> LLMResult:
    model = model or config.MODEL
    options = {
        "temperature": temperature,
        "num_ctx": config.NUM_CTX,
        "num_predict": max_tokens,
        "seed": config.SEED,
    }
    start = time.perf_counter()
    try:
        import ollama  # lazy import so unit tests run without the package
        resp = ollama.chat(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            options=options,
            format=schema,
            keep_alive=config.KEEP_ALIVE,
        )
        text = resp["message"]["content"]
    except Exception as exc:  # connection refused, model missing, bad schema support
        raise LLMError(
            "Ollama call failed for model '%s': %s. Is 'ollama serve' running, and did you run "
            "'ollama pull %s'?" % (model, exc, model)
        ) from exc
    return LLMResult(text=text, seconds=time.perf_counter() - start, model=model)
