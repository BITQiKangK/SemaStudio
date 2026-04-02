import os
from pathlib import Path

BASE_DIR   = Path(__file__).resolve().parent
DATA_DIR   = BASE_DIR / "upload"     
RESULT_DIR = BASE_DIR / "results"    
DB_PATH    = None 

MAX_ROWS_RETURN = 1000           

QUERY_TIMEOUT = 3600

LLM_MODEL   = os.environ.get("LLM_MODEL",   "google/gemma-3-12b-it")
OPTIMIZER_URL = os.environ.get("OPTIMIZER_URL", "https://openrouter.ai/api/v1/chat/completions")
OPTIMIZER_MODEL = os.environ.get("OPTIMIZER_MODEL", "qwen/qwen3-max")
LLM_URL     = os.environ.get("LLM_URL",     "https://openrouter.ai/api/v1/chat/completions")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")

ENABLE_LOGGING = os.environ.get("ENABLE_LOGGING", "true").lower() == "true"
LOGGING_LEVEL  = os.environ.get("LOGGING_LEVEL",  "trace")

SEMANTIC_BATCH_SIZE = int(os.environ.get("SEMANTIC_BATCH_SIZE", "4"))

ENABLE_SEMANTIC_FILTER_MULTIPLEXER  = os.environ.get("ENABLE_SEMANTIC_FILTER_MULTIPLEXER",  "true").lower()  == "true"
SEMANTIC_FILTER_ACCURACY_THRESHOLD  = float(os.environ.get("SEMANTIC_FILTER_ACCURACY_THRESHOLD", "0.9"))
SEMANTIC_FILTER_LATENCY_FIRST       = os.environ.get("SEMANTIC_FILTER_LATENCY_FIRST",       "true").lower()  == "true"
SEMANTIC_FILTER_BATCH_SIZE          = int(os.environ.get("SEMANTIC_FILTER_BATCH_SIZE",          "4"))
ENABLE_PARTIAL_DEDUCTION            = os.environ.get("ENABLE_PARTIAL_DEDUCTION",            "true").lower()  == "true"
ENABLE_NL_EXPRESSION_COMPRESSION    = os.environ.get("ENABLE_NL_EXPRESSION_COMPRESSION",    "true").lower()  == "true"


USE_SPLIT_PROFILING_FILES = os.environ.get("USE_SPLIT_PROFILING_FILES", "false").lower() == "true"
SPLIT_PROMPT_FILE_PATH    = RESULT_DIR / "deduction.json"
SPLIT_PROFILING_FILE_PATH = RESULT_DIR / "profiling.json"

for _p in (DATA_DIR, RESULT_DIR):
    _p.mkdir(parents=True, exist_ok=True)

