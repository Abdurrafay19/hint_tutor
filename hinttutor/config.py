"""Central settings. Override the model and context with environment variables."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSIGNMENTS_DIR = ROOT / "assignments"

MODEL = os.getenv("HINTTUTOR_MODEL", "qwen2.5-coder:3b")
NUM_CTX = int(os.getenv("HINTTUTOR_NUM_CTX", "4096"))  # set explicitly, old Ollama defaults to 2048
SEED = int(os.getenv("HINTTUTOR_SEED", "0"))
KEEP_ALIVE = os.getenv("HINTTUTOR_KEEP_ALIVE", "30m")

DIAGNOSE_TEMPERATURE = 0.0
HINT_TEMPERATURE = 0.3
DIAGNOSE_MAX_TOKENS = 256
HINT_MAX_TOKENS = 200

MAX_HINT_ATTEMPTS = 3
TEST_TIMEOUT_SECONDS = 5.0
MAX_CODE_LINES = 150
