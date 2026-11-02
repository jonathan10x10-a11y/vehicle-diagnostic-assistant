"""
Configuration file for Vehicle Diagnostic Assistant
Edit these settings based on your setup
"""

import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()  # read keys from the .env file

# Project Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
FAISS_INDEX_PATH = PROCESSED_DATA_DIR / "faiss_index.bin"
DOCUMENTS_PATH = PROCESSED_DATA_DIR / "documents.json"

# OBD-II Settings
OBD_PORT = None  # None for auto-detection, or specify like "/dev/ttyUSB0" or "COM3"
OBD_BAUDRATE = 38400
USE_MOCK_DATA = True  # Set to False when connected to real vehicle

# Embedding Model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast and efficient for college projects
EMBEDDING_DIMENSION = 384

# RAG Settings
TOP_K_DOCUMENTS = 3  # Number of relevant documents to retrieve
MAX_CONTEXT_LENGTH = 2000  # Maximum characters in context

# LLM Settings
# Provider options: "groq" (free tier), "openai", "anthropic"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your-api-key-here")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-api-key-here")

_DEFAULT_MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "openai": "gpt-3.5-turbo",
    "anthropic": "claude-3-haiku-20240307",
}
_env_model = (os.getenv("LLM_MODEL") or "").strip()
# Ignore a model name that belongs to a different provider (e.g. gpt-* with Groq)
if LLM_PROVIDER == "groq" and _env_model.startswith(("gpt", "claude")):
    _env_model = ""
if LLM_PROVIDER == "openai" and _env_model.startswith("claude"):
    _env_model = ""
if LLM_PROVIDER == "anthropic" and _env_model.startswith("gpt"):
    _env_model = ""
LLM_MODEL = _env_model or _DEFAULT_MODELS.get(LLM_PROVIDER, "llama-3.3-70b-versatile")

LLM_TEMPERATURE = 0.3  # Lower = more focused responses
LLM_MAX_TOKENS = 800   # Enough room for the full JSON answer

# Safety Check Thresholds
COOLANT_TEMP_WARNING = 100  # Celsius
COOLANT_TEMP_CRITICAL = 120  # Celsius
RPM_MAX_SAFE = 6000
SPEED_MAX_WARNING = 160  # km/h

# Flask Settings
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True

# Create necessary directories
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
