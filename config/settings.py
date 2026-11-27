import os
from dotenv import load_dotenv

load_dotenv()


def _get(nama: str) -> str | None:
    """Ambil konfigurasi dari .env/environment, lalu dari Streamlit Secrets saat deploy."""
    nilai = os.getenv(nama)
    if nilai:
        return nilai
    try:
        import streamlit as st
        return st.secrets.get(nama)
    except Exception:
        return None


# AI
AI_API_KEY = _get("AI_API_KEY")
AI_BASE_URL = _get("AI_BASE_URL")
AI_MODEL = _get("AI_MODEL")

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
            f"Konfigurasi belum diisi ({', '.join(missing)}). "
            "Isi di file .env saat pengembangan, atau di Secrets saat deploy."
        )