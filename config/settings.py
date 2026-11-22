import os
from dotenv import load_dotenv

load_dotenv()

# AI (Qwen)
AI_API_KEY = os.getenv("AI_API_KEY")
AI_BASE_URL = os.getenv("AI_BASE_URL")
AI_MODEL = os.getenv("AI_MODEL")

# BMKG
BMKG_BASE_URL = "https://api.bmkg.go.id/publik/prakiraan-cuaca"

def validate_config():
    """Cek konfigurasi wajib sebelum aplikasi jalan."""
    missing = []
    if not AI_API_KEY:
        missing.append("AI_API_KEY")
    if not AI_BASE_URL:
        missing.append("AI_BASE_URL")
    if not AI_MODEL:
        missing.append("AI_MODEL")

    if missing:
        raise EnvironmentError(
            f"Environment variable belum diisi: {', '.join(missing)}. Cek file .env kamu."
        )