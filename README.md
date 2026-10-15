# Hint Tutor

Test-grounded hints for Python assignments. A TA or student runs code against the assignment's tests. If a test fails, a local 3B model explains where to look, without giving the fix. A leak guard checks every hint against the real fix before the student sees it.

**Target user:** TAs and students in intro programming courses.
**Problem:** A TA with 200 submissions cannot write 200 hints. Generic LLM tutors either hallucinate a bug or paste the solution.
**Solution:** Tests decide pass or fail. The model only explains a failure the tests already proved. A diff-based guard blocks answers.

## AI component

| Item | Value |
|---|---|
| Model | `qwen2.5-coder:3b` |
| Parameters | 3B (limit is 8B) |
| Runtime | Ollama, local, offline |
| Role | Step 1: pick the buggy line (JSON-schema output). Step 2: write a hint from that diagnosis. |

Without the model there is no hint. Tests only say pass or fail.

## How it works

1. `runner.py` runs the student file against each test in a separate process (5 s timeout).
2. All pass: success, no model call. Syntax error: line number from the compiler, no model call.
3. Otherwise the first failing test and the numbered code go to the model for a diagnosis.
4. A second call writes a 2 to 3 sentence hint that ends in a question.
5. `guard.py` diffs the student code against `reference.py` and rejects any hint containing a code block, a corrected line, or the changed tokens (for example `n + 1`).
6. Up to 3 attempts. After 3 rejections the app prints a fixed template: "Look at line N. Trace the failing input by hand and compare each step to what you expect."

The model never sees `reference.py`. Diagrams are in [docs/architecture.md](docs/architecture.md).

## Setup

```
ollama pull qwen2.5-coder:3b
python -m venv .venv
.venv\Scripts\activate          # Windows. On Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Needs Python 3.11+ and a recent Ollama (structured output needs 0.5 or newer). No API keys. Optional env vars: `HINTTUTOR_MODEL`, `HINTTUTOR_NUM_CTX` (default 4096), `HINTTUTOR_SEED`, `HINTTUTOR_KEEP_ALIVE`.

## Usage

```
streamlit run app.py                         # web UI at http://localhost:8501
python cli.py --list                         # list assignments
python cli.py sum_to_n assignments/sum_to_n/buggy.py --debug
```

Add an assignment: create `assignments/<name>/assignment.json` (title, problem, function, tests with `args` and `expected`) and `reference.py`. An optional `buggy.py` becomes the demo default.

## Testing and findings

Unit tests (no Ollama needed, the model is mocked):

```
python -m unittest discover -s tests -t .
```

Model evaluation (needs Ollama):

```
python -m eval.mutate --per-assignment 6    # generate buggy variants by AST mutation
python -m eval.run_eval                     # writes eval/results.csv and eval/summary.json
```

Cases: AST mutants that fail the tests (comparison swaps, operator swaps, constants plus or minus 1) plus hand-written bugs (missing base case, list mutation, missing `.lower()`, bad initial value). Ground truth for mutants is the mutated line.

### Results

> TODO: replace with real numbers from `eval/summary.json` after running the eval. Do not publish estimates.

| Metric | Result |
|---|---|
| Cases | TBD |
| Diagnosis line exact | TBD |
| Diagnosis line within 1 line | TBD |
| Hints hand-labeled good (n = 20) | TBD |
| First-attempt guard rejection rate | TBD |
| Fallback template used | TBD |
| Median / p95 latency per model call | TBD |

Hardware used: TBD.

### Known limitations

- Mutants are synthetic and easier than real student bugs.
- The guard catches literal and near-literal leaks. A paraphrase such as "add one to the bound" can pass. Final hints were audited by hand for this.
- A 3B model sometimes blames the wrong line. The tests are still correct, so the failure shown to the student is always real.
- Scope: Python only, one file, pure functions, no `input()`, 150 lines max, one bug at a time.
- The runner is isolated process execution with a timeout. It is not a security sandbox. Do not run untrusted code on a machine you care about.
- The "under the hood" panel shows the guard's matched text, which reveals the fix. Turn it off for students.

## Team and licensing

Team: TBD (names and contributions).

License: MIT, see [LICENSE](LICENSE).

Acknowledgements: Ollama, Streamlit, and the Qwen2.5-Coder 3B model. TODO: check the model card on Ollama or Hugging Face for the model's license terms and state them here before submitting.
