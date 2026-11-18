"""Configuración centralizada del proyecto"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

# Directorios
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"
OUTPUT_DIR = PROJECT_ROOT / Path(os.getenv("OUTPUT_DIR", "output"))

# API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# MCP Server
MCP_HOST = os.getenv("MCP_HOST", "localhost")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_DEBUG = os.getenv("MCP_DEBUG", "false").lower() == "true"

# Guardrails y límites
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))
TOKEN_BUDGET = int(os.getenv("TOKEN_BUDGET", "100000"))
REVIEWER_TIMEOUT_SECONDS = float(os.getenv("REVIEWER_TIMEOUT_SECONDS", "30"))
COVERAGE_THRESHOLD = float(os.getenv("COVERAGE_THRESHOLD", "0.80"))

# Paths de datos
GOLDEN_SET_PATH = PROJECT_ROOT / os.getenv(
    "GOLDEN_SET_PATH",
    "ideacion/02-entregables/golden_set.json",
)


def get_config_dict():
    """Retorna diccionario de configuración"""
    return {
        "project_root": str(PROJECT_ROOT),
        "output_dir": str(OUTPUT_DIR),
        "max_iterations": MAX_ITERATIONS,
        "token_budget": TOKEN_BUDGET,
        "reviewer_timeout": REVIEWER_TIMEOUT_SECONDS,
        "coverage_threshold": COVERAGE_THRESHOLD,
        "golden_set_path": str(GOLDEN_SET_PATH),
    }
