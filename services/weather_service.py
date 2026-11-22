import requests
from config.settings import BMKG_BASE_URL
from utils.helpers import format_waktu_update, cek_indikasi_hujan


class WeatherServiceError(Exception):
    """Dilempar kalau data cuaca gagal diambil atau tidak ditemukan."""
    pass


def _fetch_raw(adm4_code: str) -> dict:
    try:
        response = requests.get(BMKG_BASE_URL, params={"adm4": adm4_code}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise WeatherServiceError("Permintaan ke BMKG timeout. Coba lagi sebentar.")
    except requests.exceptions.HTTPError:
        raise WeatherServiceError("BMKG tidak dapat memproses kode wilayah ini.")
    except requests.exceptions.RequestException:
        raise WeatherServiceError("Gagal terhubung ke server BMKG. Cek koneksi internet.")


def _extract_slots(raw: dict) -> list[list[dict]]:
    """Ambil array 'cuaca' (per hari, berisi slot 3-jaman)."""
    try:
        return raw["data"][0]["cuaca"]
    except (KeyError, IndexError):
        raise WeatherServiceError("Format data BMKG tidak sesuai dugaan.")


def get_current_weather(adm4_code: str, nama_lokasi: str) -> dict:
    """Cuaca 'sekarang' = slot pertama dari hari pertama."""
    raw = _fetch_raw(adm4_code)
    hari_pertama = _extract_slots(raw)[0]
    slot = hari_pertama[0]

    return {
        "lokasi": nama_lokasi,
        "suhu": slot["t"],
        "kondisi": slot["weather_desc"],
        "kelembapan": slot["hu"],
        "kecepatan_angin": slot["ws"],
        "arah_angin": slot["wd"],
        "akan_hujan": cek_indikasi_hujan(slot["weather_desc"], slot["tp"]),
        "waktu_data": slot["local_datetime"],
        "data_diperbarui": format_waktu_update(slot["analysis_date"]),
        "sumber": "BMKG",
        "sumber_url": "https://www.bmkg.go.id",
    }


def get_forecast(adm4_code: str, nama_lokasi: str, jumlah_hari: int = 3) -> dict:
    """Ringkasan prakiraan per hari (suhu min/maks, kemungkinan hujan)."""
    raw = _fetch_raw(adm4_code)
    hari_list = _extract_slots(raw)[:jumlah_hari]

    ringkasan = []
    for slot_per_hari in hari_list:
        if not slot_per_hari:
            continue
        suhu_list = [s["t"] for s in slot_per_hari]
        ada_hujan = any(cek_indikasi_hujan(s["weather_desc"], s["tp"]) for s in slot_per_hari)
        ringkasan.append({
            "tanggal": slot_per_hari[0]["local_datetime"][:10],
            "suhu_min": min(suhu_list),
            "suhu_maks": max(suhu_list),
            "kondisi_dominan": slot_per_hari[len(slot_per_hari) // 2]["weather_desc"],
            "kemungkinan_hujan": ada_hujan,
        })

    return {
        "lokasi": nama_lokasi,
        "prakiraan": ringkasan,
        "sumber": "BMKG",
        "sumber_url": "https://www.bmkg.go.id",
    }


def get_forecast_for_day(adm4_code: str, nama_lokasi: str, hari_ke: int) -> dict:
    """hari_ke: 0 = hari ini, 1 = besok, 2 = lusa."""
    hasil = get_forecast(adm4_code, nama_lokasi, jumlah_hari=hari_ke + 1)
    prakiraan = hasil["prakiraan"]

    if len(prakiraan) <= hari_ke:
        raise WeatherServiceError("Data prakiraan untuk hari tersebut belum tersedia dari BMKG.")

    return {
        "lokasi": nama_lokasi,
        "prakiraan_hari_ini": prakiraan[hari_ke],
        "sumber": "BMKG",
        "sumber_url": "https://www.bmkg.go.id",
    }