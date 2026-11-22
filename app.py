import html

import streamlit as st

from config.settings import validate_config
from services import history_service
from services.location_service import resolve_location
from services.weather_service import (
    get_current_weather,
    get_forecast,
    get_forecast_for_day,
    WeatherServiceError,
)
from services.ai_service import extract_intent, generate_response, AIServiceError
from utils.ui_components import inject_css, render_current_weather_card, render_forecast_card

st.set_page_config(page_title="Weather AI", page_icon="🌤️", layout="centered")
inject_css()

try:
    validate_config()
except EnvironmentError as e:
    st.error(f"⚠️ Konfigurasi belum lengkap: {e}")
    st.stop()

MAKS_LOKASI = 3

if "sesi_aktif" not in st.session_state:
    st.session_state.sesi_aktif = history_service.buat_sesi_baru()
st.session_state.setdefault("pending_question", None)
st.session_state.setdefault("pending_clarification", None)

sesi = st.session_state.sesi_aktif

CONTOH_PERTANYAAN = [
    "Cuaca hari ini di Jaksel",
    "Besok hujan nggak di Surabaya?",
    "Cuaca di Jaksel dan Kalsel hari ini",
    "Bandingkan cuaca Bandung, Surabaya, Depok",
]


def _mulai_sesi_baru() -> None:
    st.session_state.sesi_aktif = history_service.buat_sesi_baru()
    st.session_state.pending_clarification = None


def _buka_sesi(sesi_id: str) -> None:
    for s in history_service.list_sesi():
        if s["id"] == sesi_id:
            st.session_state.sesi_aktif = s
            st.session_state.pending_clarification = None
            return


def _simpan_sesi_aktif() -> None:
    history_service.simpan_sesi(st.session_state.sesi_aktif)


# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🌤️ Weather AI")
    st.caption("Informasi cuaca dengan data terpercaya dari BMKG.")
    st.divider()

    if st.button("➕ Chat Baru", use_container_width=True):
        _mulai_sesi_baru()
        st.rerun()

    st.caption("Riwayat percakapan:")
    daftar_sesi = history_service.list_sesi()
    if not daftar_sesi:
        st.caption("_Belum ada riwayat._")
    for s in daftar_sesi:
        kolom_judul, kolom_hapus = st.columns([5, 1])
        aktif = s["id"] == sesi["id"]
        with kolom_judul:
            label = ("📍 " if aktif else "") + s["judul"]
            if st.button(label, key=f"buka_{s['id']}", use_container_width=True):
                _buka_sesi(s["id"])
                st.rerun()
        with kolom_hapus:
            if st.button("🗑️", key=f"hapus_{s['id']}"):
                history_service.hapus_sesi(s["id"])
                if aktif:
                    _mulai_sesi_baru()
                st.rerun()

    st.divider()
    st.caption("Coba tanyakan:")
    for i, contoh in enumerate(CONTOH_PERTANYAAN):
        if st.button(contoh, key=f"contoh_{i}", use_container_width=True):
            st.session_state.pending_question = contoh
    st.divider()
    st.caption("Sumber data: Badan Meteorologi, Klimatologi, dan Geofisika (BMKG)")
    st.caption(f"Cakupan: hari ini s.d. 3 hari ke depan · maksimal {MAKS_LOKASI} kota sekaligus.")

# --- Header ---
st.markdown(
    '<div class="app-header">'
    '<div class="hero-orb"></div>'
    '<h1><span class="app-header-title">Weather AI</span></h1>'
    "<p>Informasi cuaca dengan data terpercaya dari BMKG</p></div>",
    unsafe_allow_html=True,
)

if not sesi["messages"]:
    st.markdown(
        '<div class="welcome"><div class="big">🌦️</div>'
        "<p>Tanyakan cuaca atau prakiraan untuk daerah di Indonesia.<br>"
        "Bisa untuk beberapa kota sekaligus, misalnya \"cuaca Jaksel dan Kalsel\".</p></div>",
        unsafe_allow_html=True,
    )

for msg in sesi["messages"]:
    with st.chat_message(msg["role"], avatar="🌤️" if msg["role"] == "assistant" else None):
        st.markdown(msg["content"], unsafe_allow_html=True)


def _intro_aman(data: dict, pesan_user: str) -> str | None:
    try:
        return generate_response(data, pesan_user)
    except AIServiceError:
        return None


def _ambil_data_dan_render(lokasi_hasil: dict, waktu_scope: str, pesan_user: str, pakai_intro: bool) -> str:
    """Ambil data BMKG untuk satu lokasi yang sudah 'found', lalu render jadi kartu."""
    adm4 = lokasi_hasil["adm4"]
    nama = lokasi_hasil["nama_tampil"]
    intro_fn = (lambda data: _intro_aman(data, pesan_user)) if pakai_intro else (lambda data: None)

    if waktu_scope == "sekarang":
        data = get_current_weather(adm4, nama)
        return render_current_weather_card(data, intro_fn(data))
    if waktu_scope == "besok":
        data = get_forecast_for_day(adm4, nama, hari_ke=1)
        return render_forecast_card(data, intro_fn(data), single_day=True)
    data = get_forecast(adm4, nama, jumlah_hari=3)
    return render_forecast_card(data, intro_fn(data), single_day=False)


def _resolve_banyak_lokasi(nama_list: list[str]) -> list[dict]:
    """Resolve tiap nama lokasi jadi item dengan status found/ambiguous/not_found."""
    items = []
    for nama_asli in nama_list:
        hasil = resolve_location(nama_asli)
        item = {"nama_asli": nama_asli, "status": hasil["status"]}
        if hasil["status"] == "found":
            item["adm4"] = hasil["adm4"]
            item["nama_tampil"] = hasil["nama_tampil"]
        elif hasil["status"] == "ambiguous":
            item["opsi"] = hasil["opsi"]
        items.append(item)
    return items


def _render_hasil_banyak_lokasi(items: list[dict], waktu_scope: str, pesan_user: str) -> str:
    """Setelah semua item final (found/not_found, tidak ada ambiguous tersisa),
    ambil data cuaca untuk tiap item 'found' dan gabungkan jadi satu balasan."""
    item_found = [it for it in items if it["status"] == "found"]
    item_gagal = [it for it in items if it["status"] != "found"]

    if item_found:
        sesi["last_location"] = item_found[-1]["nama_tampil"]

    bagian = []
    if len(item_found) > 1:
        bagian.append(f"Berikut cuaca untuk {len(item_found)} daerah yang kamu tanyakan:\n")

    pakai_intro = len(item_found) == 1  # kalimat pembuka AI cuma untuk 1 lokasi, biar ringkas kalau banyak
    for it in item_found:
        lokasi_hasil = {"adm4": it["adm4"], "nama_tampil": it["nama_tampil"]}
        try:
            bagian.append(_ambil_data_dan_render(lokasi_hasil, waktu_scope, pesan_user, pakai_intro))
        except WeatherServiceError as e:
            bagian.append(f"⚠️ **{html.escape(it['nama_tampil'])}**: gagal mengambil data cuaca ({html.escape(str(e))})")

    for it in item_gagal:
        bagian.append(f"⚠️ Wilayah **{html.escape(it['nama_asli'])}** tidak ditemukan dalam database.")

    return "\n\n---\n\n".join(bagian)


def proses_pertanyaan(pesan_user: str) -> str:
    # 1) User sedang menjawab klarifikasi lokasi yang masih ambigu
    pending = st.session_state.pending_clarification
    if pending:
        items = pending["items"]
        idx = pending["index_menunggu"]
        hasil = resolve_location(pesan_user.strip())

        if hasil["status"] == "found":
            items[idx] = {
                "nama_asli": items[idx]["nama_asli"],
                "status": "found",
                "adm4": hasil["adm4"],
                "nama_tampil": hasil["nama_tampil"],
            }
        elif hasil["status"] == "ambiguous":
            items[idx]["opsi"] = hasil["opsi"]
            st.session_state.pending_clarification = pending  # tetap menunggu di index yang sama
            daftar = "\n".join(f"- {o}" for o in hasil["opsi"])
            return f"Masih ada beberapa pilihan untuk **{html.escape(items[idx]['nama_asli'])}**. Maksud kamu yang mana?\n\n{daftar}"
        else:
            items[idx]["status"] = "not_found"

        # cari lokasi berikutnya yang masih ambigu
        idx_berikut = next((i for i, it in enumerate(items) if it["status"] == "ambiguous"), None)
        if idx_berikut is not None:
            st.session_state.pending_clarification = {
                "items": items,
                "waktu_scope": pending["waktu_scope"],
                "pertanyaan_awal": pending["pertanyaan_awal"],
                "index_menunggu": idx_berikut,
            }
            opsi = "\n".join(f"- {o}" for o in items[idx_berikut]["opsi"])
            return f"Oke, lanjut. Untuk **{html.escape(items[idx_berikut]['nama_asli'])}**, maksud kamu yang mana?\n\n{opsi}"

        # semua lokasi sudah final -> tampilkan hasilnya
        st.session_state.pending_clarification = None
        return _render_hasil_banyak_lokasi(items, pending["waktu_scope"], pending["pertanyaan_awal"])

    # 2) Pertanyaan baru
    intent = extract_intent(
        pesan_user,
        riwayat_lokasi=sesi.get("last_location"),
        riwayat_percakapan=sesi["messages"],
    )

    if not intent.get("is_weather_related"):
        return "Saya adalah chatbot khusus informasi cuaca. Silakan tanyakan kondisi atau prakiraan cuaca suatu daerah. 🌤️"

    lokasi_list = [l.strip() for l in intent.get("lokasi_list", []) if l and l.strip()]
    if not lokasi_list:
        return "Daerah mana yang ingin kamu tanyakan cuacanya?"

    waktu_scope = intent.get("waktu_scope", "sekarang")

    # 2a) Batasan cakupan waktu -- diputuskan oleh KODE, bukan oleh AI
    if waktu_scope == "lampau":
        return (
            "Maaf, saya hanya bisa memberikan informasi cuaca untuk **hari ini sampai 3 hari ke depan**. "
            "Data cuaca yang sudah berlalu (kemarin atau sebelumnya) tidak tersedia dari sumber data BMKG yang saya gunakan."
        )
    if waktu_scope == "terlalu_jauh":
        return (
            "Maaf, prakiraan cuaca dari BMKG hanya tersedia untuk **hari ini sampai maksimal 3 hari ke depan**. "
            "Saya belum bisa memberikan prakiraan untuk rentang waktu yang lebih jauh dari itu. "
            "Coba tanyakan cuaca untuk hari ini, besok, atau dalam 3 hari ke depan."
        )

    # 2b) Batasan jumlah lokasi -- juga diputuskan KODE, bukan AI
    catatan_pembatasan = ""
    if len(lokasi_list) > MAKS_LOKASI:
        sisa = ", ".join(lokasi_list[MAKS_LOKASI:])
        catatan_pembatasan = (
            f"_Catatan: saya cuma bisa menampilkan maksimal {MAKS_LOKASI} kota sekaligus, "
            f"jadi {sisa} belum saya tampilkan. Tanyakan terpisah ya._\n\n"
        )
        lokasi_list = lokasi_list[:MAKS_LOKASI]

    # 3) Resolusi semua lokasi
    items = _resolve_banyak_lokasi(lokasi_list)
    idx_ambigu = next((i for i, it in enumerate(items) if it["status"] == "ambiguous"), None)

    if idx_ambigu is not None:
        st.session_state.pending_clarification = {
            "items": items,
            "waktu_scope": waktu_scope,
            "pertanyaan_awal": pesan_user,
            "index_menunggu": idx_ambigu,
        }
        opsi = "\n".join(f"- {o}" for o in items[idx_ambigu]["opsi"])
        awalan = f"Ada beberapa daerah yang cocok dengan **{html.escape(items[idx_ambigu]['nama_asli'])}**. Maksud kamu yang mana?\n\n{opsi}"
        return catatan_pembatasan + awalan

    if all(it["status"] == "not_found" for it in items):
        daftar = ", ".join(it["nama_asli"] for it in items)
        return catatan_pembatasan + f"Maaf, saya tidak menemukan wilayah untuk: **{html.escape(daftar)}**."

    return catatan_pembatasan + _render_hasil_banyak_lokasi(items, waktu_scope, pesan_user)


pertanyaan = st.chat_input("Ask Anything...")
if not pertanyaan and st.session_state.pending_question:
    pertanyaan = st.session_state.pending_question
st.session_state.pending_question = None

if pertanyaan:
    if not sesi["messages"]:
        sesi["judul"] = history_service.judul_dari_pesan(pertanyaan)

    sesi["messages"].append({"role": "user", "content": html.escape(pertanyaan)})
    with st.chat_message("user"):
        st.markdown(html.escape(pertanyaan))

    with st.chat_message("assistant", avatar="🌤️"):
        with st.spinner("Mengambil data cuaca terbaru..."):
            try:
                jawaban = proses_pertanyaan(pertanyaan)
            except WeatherServiceError as e:
                jawaban = f"⚠️ Gagal mengambil data cuaca: {html.escape(str(e))}"
            except AIServiceError as e:
                jawaban = f"⚠️ AI sedang bermasalah: {html.escape(str(e))}"
            except Exception as e:
                jawaban = f"⚠️ Terjadi kesalahan tak terduga: {html.escape(str(e))}"

        st.markdown(jawaban, unsafe_allow_html=True)

    sesi["messages"].append({"role": "assistant", "content": jawaban})
    _simpan_sesi_aktif()