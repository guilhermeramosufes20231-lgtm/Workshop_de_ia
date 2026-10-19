"""Configuração lida de variáveis de ambiente (nunca do frontend)."""
import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv é opcional
    pass

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5").strip()
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(2 * 1024 * 1024)))
MAX_TRANSACTIONS = int(os.getenv("MAX_TRANSACTIONS", "20000"))
AI_RATE_LIMIT_PER_MIN = int(os.getenv("AI_RATE_LIMIT_PER_MIN", "20"))

AI_ENABLED = bool(ANTHROPIC_API_KEY)
