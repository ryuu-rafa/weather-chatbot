from datetime import datetime

def format_waktu_update(analysis_date: str) -> str:
    """Ubah '2026-09-21T00:00:00' jadi '21 September 2026, 00:00 UTC'."""
    try:
        dt = datetime.fromisoformat(analysis_date)
        bulan = [
            "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember"
        ]
        return f"{dt.day} {bulan[dt.month]} {dt.year}, {dt.strftime('%H:%M')} UTC"
    except (ValueError, TypeError):
        return analysis_date  # fallback kalau format tak terduga

def cek_indikasi_hujan(weather_desc: str, tp: float) -> bool:
    """True jika slot cuaca ini mengindikasikan hujan."""
    kata_hujan = ["hujan", "petir"]
    desc_lower = (weather_desc or "").lower()
    return any(k in desc_lower for k in kata_hujan) or (tp or 0) > 0