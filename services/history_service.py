import json
import uuid
from datetime import datetime
from pathlib import Path

_HISTORY_DIR = Path(__file__).parent.parent / "history"
_HISTORY_FILE = _HISTORY_DIR / "chat_sessions.json"


def _pastikan_folder() -> None:
    _HISTORY_DIR.mkdir(exist_ok=True)
    if not _HISTORY_FILE.exists():
        _HISTORY_FILE.write_text("[]", encoding="utf-8")


def _load_semua() -> list[dict]:
    _pastikan_folder()
    try:
        with open(_HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _simpan_semua(sessions: list[dict]) -> None:
    _pastikan_folder()
    with open(_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


def buat_sesi_baru() -> dict:
    return {
        "id": str(uuid.uuid4()),
        "judul": "Percakapan Baru",
        "dibuat_pada": datetime.now().isoformat(timespec="seconds"),
        "last_location": None,
        "messages": [],
    }


def list_sesi() -> list[dict]:
    """Daftar semua sesi, terbaru lebih dulu."""
    sessions = _load_semua()
    sessions.sort(key=lambda s: s.get("dibuat_pada", ""), reverse=True)
    return sessions


def simpan_sesi(sesi: dict) -> None:
    """Simpan/timpa satu sesi berdasarkan id-nya."""
    sessions = _load_semua()
    sessions = [s for s in sessions if s["id"] != sesi["id"]]
    sessions.append(sesi)
    _simpan_semua(sessions)


def hapus_sesi(sesi_id: str) -> None:
    sessions = _load_semua()
    sessions = [s for s in sessions if s["id"] != sesi_id]
    _simpan_semua(sessions)


def judul_dari_pesan(pesan: str, maks_karakter: int = 40) -> str:
    teks = pesan.strip()
    if len(teks) > maks_karakter:
        teks = teks[:maks_karakter].rstrip() + "..."
    return teks or "Percakapan Baru"