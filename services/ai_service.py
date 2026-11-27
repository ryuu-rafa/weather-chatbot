import json
import re
import time
from datetime import datetime, timedelta, timezone
from openai import OpenAI
from config.settings import AI_API_KEY, AI_BASE_URL, AI_MODEL


class AIServiceError(Exception):
    """Dilempar kalau AI API gagal merespons dengan benar."""
    pass


def _get_client() -> OpenAI:
    if not AI_API_KEY or not AI_BASE_URL:
        raise AIServiceError("Konfigurasi AI belum lengkap. Periksa AI_API_KEY dan AI_BASE_URL.")
    return OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)


def _sekarang_wib() -> datetime:
    """Waktu sekarang dalam WIB (UTC+7), supaya tanggal 'hari ini' benar walau server memakai UTC."""
    return datetime.now(timezone(timedelta(hours=7)))


def _strip_thinking_tags(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _get_content_safely(response) -> str:
    message = response.choices[0].message
    content = (message.content or "").strip()

    if content:
        cleaned = _strip_thinking_tags(content)
        if cleaned:
            return cleaned

    reasoning = (getattr(message, "reasoning_content", None) or "").strip()
    if reasoning:
        return _strip_thinking_tags(reasoning)

    finish_reason = response.choices[0].finish_reason
    raise AIServiceError(
        f"AI mengembalikan response kosong (finish_reason: {finish_reason}). "
        "Kemungkinan max_tokens masih terlalu kecil untuk proses berpikir model."
    )


def _call_ai(system_prompt: str, user_message: str, max_tokens: int, temperature: float) -> str:
    max_percobaan = 3
    jeda_detik = 3

    for percobaan in range(1, max_percobaan + 1):
        try:
            client = _get_client()
            response = client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return _get_content_safely(response)

        except AIServiceError:
            raise

        except Exception as e:
            error_text = str(e)
            error_bisa_diulang = any(
                kode in error_text for kode in ["429", "502", "503", "504", "timeout", "Timeout"]
            )

            if error_bisa_diulang and percobaan < max_percobaan:
                time.sleep(jeda_detik)
                continue

            raise AIServiceError(f"Gagal menghubungi AI API setelah {percobaan}x percobaan: {e}")


def _extract_json_block(text: str) -> dict:
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise AIServiceError(f"AI tidak mengembalikan format JSON yang bisa dibaca: {text[:200]}")
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        raise AIServiceError(f"AI membalas JSON yang rusak: {match.group()[:200]}")


def _ringkas_riwayat(riwayat_percakapan: list[dict] | None, maks_pesan: int = 6) -> str:
    """Ubah riwayat chat (termasuk kartu cuaca berisi HTML) jadi teks polos ringkas untuk konteks AI."""
    if not riwayat_percakapan:
        return "tidak ada riwayat"

    baris = []
    for pesan in riwayat_percakapan[-maks_pesan:]:
        peran = "User" if pesan["role"] == "user" else "Chatbot"
        teks = re.sub(r"<[^>]+>", " ", pesan["content"])
        teks = re.sub(r"\s+", " ", teks).strip()
        if teks:
            baris.append(f"{peran}: {teks[:200]}")

    return "\n".join(baris) if baris else "tidak ada riwayat"


def extract_intent(
    pesan_user: str,
    riwayat_lokasi: str | None = None,
    riwayat_percakapan: list[dict] | None = None,
) -> dict:
    """
    riwayat_lokasi: lokasi terakhir yang dibahas (fallback konteks, untuk kasus 1 lokasi).
    riwayat_percakapan: beberapa pesan chat terakhir di sesi ini.

    Return field "lokasi_list": daftar nama daerah yang diminta (1 lokasi atau lebih,
    user bisa menyebut beberapa kota sekaligus seperti "cuaca jaksel dan kalsel").
    """
    hari_ini = _sekarang_wib().strftime("%A, %d %B %Y")

    system_prompt = f"""Kamu adalah pengekstrak intent untuk chatbot cuaca Indonesia.
Tugasmu HANYA mengekstrak informasi, JANGAN menjawab pertanyaan cuaca itu sendiri.
JANGAN tampilkan proses berpikir dalam bentuk apapun, langsung balas JSON-nya saja tanpa teks lain.

Hari ini adalah: {hari_ini} (WIB). Gunakan ini sebagai acuan untuk menghitung tanggal relatif
yang disebut user (misalnya "besok", "lusa", "minggu depan", "4 hari lagi", "kemarin").

Pengguna sering memakai nama tidak resmi/singkatan untuk daerah, misalnya:
"jaksel" = Jakarta Selatan, "jakpus" = Jakarta Pusat, "jaktim" = Jakarta Timur,
"jakbar" = Jakarta Barat, "jakut" = Jakarta Utara, "jogja" = Yogyakarta,
"kalsel" = Kalimantan Selatan, "kaltim" = Kalimantan Timur, "sumut" = Sumatera Utara,
"sumbar" = Sumatera Barat, "jabar" = Jawa Barat, "jatim" = Jawa Timur, "jateng" = Jawa Tengah.
Tulis nama resmi/formal setiap daerah di "lokasi_list", walau user menulis singkatannya.

PENTING -- user bisa menanyakan LEBIH DARI SATU daerah sekaligus dalam satu kalimat,
misalnya "cuaca di jaksel dan kalsel hari ini" atau "bandingkan bandung, surabaya, depok".
Pisahkan setiap nama daerah sebagai elemen terpisah di "lokasi_list" (array string).
Kalau user tidak menyebut lokasi sama sekali, kosongkan array ini.
Kalau user menyebut lebih dari 3 daerah, tetap masukkan SEMUA yang disebut apa adanya
(pembatasan maksimal akan ditangani oleh sistem, bukan olehmu).

PENTING -- sumber data cuaca (BMKG) HANYA menyediakan data untuk HARI INI sampai
MAKSIMAL 3 HARI KE DEPAN. Tidak ada data cuaca masa lalu maupun lebih dari 3 hari
ke depan. Klasifikasikan "waktu_scope" (berlaku sama untuk semua lokasi di pertanyaan ini):

- "sekarang"       -> pertanyaan tentang kondisi saat ini / hari ini
- "besok"          -> pertanyaan spesifik tentang besok (hari ke-1 dari sekarang)
- "3hari"           -> pertanyaan tentang prakiraan beberapa hari ke depan dalam
                       rentang 2-3 hari (termasuk "lusa", "3 hari ke depan")
- "lampau"          -> pertanyaan tentang cuaca KEMARIN atau waktu sebelum hari ini
- "terlalu_jauh"    -> pertanyaan tentang cuaca LEBIH dari 3 hari ke depan (termasuk
                       "minggu depan", "bulan depan", tanggal spesifik lebih dari 3 hari)

Konteks lokasi terakhir yang dibahas (hanya dipakai kalau user tidak menyebut lokasi
baru sama sekali dan pertanyaan ini jelas pertanyaan lanjutan, misal "kalau besok?"): {riwayat_lokasi or "tidak ada"}

Riwayat percakapan terakhir di sesi ini:
{_ringkas_riwayat(riwayat_percakapan)}

Balas HANYA dalam format JSON, tanpa teks lain, tanpa markdown code block:
{{"is_weather_related": true/false, "lokasi_list": ["nama daerah 1", "nama daerah 2"], "waktu_scope": "sekarang" | "besok" | "3hari" | "lampau" | "terlalu_jauh"}}"""

    text = _call_ai(system_prompt, pesan_user, max_tokens=1500, temperature=0)
    return _extract_json_block(text)


def generate_response(data_cuaca: dict, pesan_user: str) -> str:
    """Hasilkan HANYA satu kalimat pembuka natural, bukan rekap data lengkap.
    Data lengkap ditampilkan terpisah lewat kartu cuaca di UI (lebih akurat)."""
    system_prompt = """Kamu asisten cuaca yang ramah dan santai, seperti teman yang paham cuaca.
Tulis HANYA SATU kalimat pembuka yang natural dan hangat, menyesuaikan dengan pertanyaan user.
Variasikan gaya bicaramu -- jangan selalu mulai dengan kata atau pola kalimat yang sama setiap kali.
Boleh pakai bahasa sehari-hari yang santai (tidak kaku/formal berlebihan), tapi tetap sopan.
JANGAN sebutkan angka suhu, kelembapan, atau angka lainnya -- itu akan ditampilkan terpisah.
JANGAN tampilkan proses berpikir. Langsung tulis satu kalimatnya saja, tanpa tanda kutip."""

    user_message = f"Pertanyaan user: {pesan_user}\n\nKondisi cuaca (JSON, untuk konteks saja, jangan disebut angkanya):\n{json.dumps(data_cuaca, ensure_ascii=False)}"

    return _call_ai(system_prompt, user_message, max_tokens=800, temperature=0.6)