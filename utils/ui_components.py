import html
from datetime import datetime

import streamlit as st

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

CSS = """
<style>
/* ---------- Latar utama: gradasi ungu gelap ---------- */
.stApp {
  background:
    radial-gradient(ellipse 900px 500px at 50% 0%, rgba(168,85,247,0.18), transparent 60%),
    radial-gradient(ellipse 700px 400px at 85% 15%, rgba(236,72,153,0.12), transparent 55%),
    linear-gradient(180deg, #120B22 0%, #0D0817 55%, #0A0615 100%);
  background-attachment: fixed;
}
[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 760px; padding-top: 2.5rem; }
.stDeployButton { display: none; }
footer { visibility: hidden; }

/* ---------- Sidebar gelap ---------- */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0A0615 0%, #0E0920 100%);
  border-right: 1px solid rgba(168,85,247,0.15);
}
[data-testid="stSidebar"] .stButton > button {
  background: rgba(168,85,247,0.08);
  border: 1px solid rgba(168,85,247,0.22);
  color: #DCCBFA;
  border-radius: 14px;
  text-align: left;
  font-weight: 500;
  transition: all 0.15s ease;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: linear-gradient(90deg, rgba(168,85,247,0.30), rgba(236,72,153,0.20));
  border-color: #C084FC;
  color: #FFFFFF;
}
[data-testid="stSidebar"] hr { border-color: rgba(168,85,247,0.15); }
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small {
  color: #8B7BA8 !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.72rem !important;
}

/* ---------- Hero / bola bercahaya di tengah ---------- */
.hero-orb {
  width: 84px; height: 84px; border-radius: 50%; margin: 0 auto 1.25rem;
  background: radial-gradient(circle at 35% 30%, #E9D5FF, #A855F7 45%, #6B21A8 80%);
  box-shadow: 0 0 50px 10px rgba(168,85,247,0.45), inset 0 0 20px rgba(255,255,255,0.25);
  display: flex; align-items: center; justify-content: center;
  font-size: 2.4rem;
}
.app-header { text-align: center; }
.app-header h1 {
  margin: 0; font-size: 2rem; font-weight: 800; letter-spacing: -0.02em;
  justify-content: center;
  background: linear-gradient(90deg, #E9D5FF 0%, #C084FC 40%, #F0ABFC 70%, #FDA4AF 100%);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.app-header-emoji { display: none; } /* emoji dipindah ke hero-orb */
.app-header p { margin: 0.4rem 0 1.5rem; color: #A697C4; font-size: 0.95rem; text-align: center; }

/* ---------- Bubble chat ---------- */
[data-testid="stChatMessage"] {
  background: rgba(168,85,247,0.06);
  border: 1px solid rgba(168,85,247,0.16);
  border-radius: 18px;
  padding: 0.9rem 1.1rem;
  backdrop-filter: blur(8px);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background: rgba(236,72,153,0.10);
  border-color: rgba(236,72,153,0.28);
}

/* ---------- Kotak input seperti "Ask Anything..." ---------- */
[data-testid="stChatInput"] {
  background: rgba(10,6,21,0.85);
  border: 1px solid rgba(168,85,247,0.35);
  border-radius: 20px;
  box-shadow: 0 0 30px rgba(168,85,247,0.08);
}
[data-testid="stChatInput"]:focus-within {
  border-color: #C084FC;
  box-shadow: 0 0 0 3px rgba(168,85,247,0.25), 0 0 30px rgba(168,85,247,0.25);
}
[data-testid="stChatInput"] textarea::placeholder { color: #7C6B9A; }
[data-testid="stBottom"] > div { background: transparent; }
[data-testid="stChatInputSubmitButton"] {
  background: linear-gradient(135deg, #A855F7, #EC4899) !important;
  border-radius: 50% !important;
}

/* ---------- Kartu cuaca ---------- */
.wx-intro { margin: 0 0 0.75rem; line-height: 1.5; color: #E3D8F7; }
.wx-card {
  border: 1px solid rgba(192,132,252,0.22); border-radius: 20px; overflow: hidden;
  background: rgba(20,12,36,0.55);
  box-shadow: 0 10px 30px rgba(0,0,0,0.35);
}
.wx-hero { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: 1.25rem 1.5rem; }
.wx-sunny   { background: linear-gradient(135deg, rgba(251,191,36,0.40), rgba(236,72,153,0.18)); }
.wx-cloudy  { background: linear-gradient(135deg, rgba(168,85,247,0.35), rgba(100,85,160,0.20)); }
.wx-rain    { background: linear-gradient(135deg, rgba(99,102,241,0.45), rgba(168,85,247,0.22)); }
.wx-default { background: linear-gradient(135deg, rgba(168,85,247,0.38), rgba(236,72,153,0.18)); }
.wx-loc  { font-size: 0.9rem; color: #D8C8F5; }
.wx-cond { font-size: 1.35rem; font-weight: 700; margin-top: 0.15rem; color: #FFFFFF; }
.wx-temp { font-size: 2.6rem; font-weight: 800; white-space: nowrap; color: #FFFFFF; }

.wx-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.75rem; padding: 1rem 1.5rem; }
.wx-metric { padding: 0.7rem 0.9rem; border-radius: 14px; background: rgba(255,255,255,0.05); border-left: 4px solid #A855F7; }
.wx-m-hum  { border-left-color: #C084FC; }
.wx-m-wind { border-left-color: #F0ABFC; }
.wx-m-rain { border-left-color: #818CF8; }
.wx-metric-label { font-size: 0.75rem; color: #A697C4; }
.wx-metric-value { font-size: 1rem; font-weight: 700; margin-top: 0.1rem; color: #F3EBFF; }

.wx-foot {
  display: flex; flex-wrap: wrap; justify-content: space-between; gap: 0.5rem;
  padding: 0.75rem 1.5rem; border-top: 1px solid rgba(168,85,247,0.18); font-size: 0.78rem;
  background: rgba(0,0,0,0.22);
}
.wx-foot span { color: #A697C4; }
.wx-foot a { text-decoration: none; font-weight: 700; color: #E9D5FF; }
.wx-foot a:hover { color: #FDA4AF; }

.wx-days { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.75rem; padding: 1rem 1.5rem; }
.wx-day { border-radius: 16px; padding: 0.9rem; text-align: center; border: 1px solid rgba(255,255,255,0.10); }
.wx-day-name { font-size: 0.8rem; color: #D8C8F5; }
.wx-day-emoji { font-size: 2rem; margin: 0.3rem 0; }
.wx-day-cond { font-weight: 700; color: #FFFFFF; }
.wx-day-temp { font-size: 1.15rem; font-weight: 800; margin-top: 0.2rem; color: #FFFFFF; }
.wx-day-rain { font-size: 0.78rem; color: #E3D8F7; margin-top: 0.3rem; }

.welcome { text-align: center; padding: 1rem 1rem 2rem; color: #BBA9DD; }
.welcome .big { font-size: 3.2rem; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def _esc(value) -> str:
    return html.escape(str(value))


def _tema(kondisi: str) -> str:
    k = (kondisi or "").lower()
    if "hujan" in k or "petir" in k:
        return "rain"
    if any(x in k for x in ["berawan", "mendung", "kabut", "kabur", "asap"]):
        return "cloudy"
    if "cerah" in k:
        return "sunny"
    return "default"


def emoji_cuaca(kondisi: str) -> str:
    k = (kondisi or "").lower()
    if "petir" in k:
        return "⛈️"
    if "hujan" in k:
        return "🌧️"
    if any(x in k for x in ["kabut", "kabur", "asap"]):
        return "🌫️"
    if "berawan tebal" in k or "mendung" in k:
        return "☁️"
    if "berawan" in k:
        return "⛅"
    if "cerah" in k:
        return "☀️"
    return "🌤️"


def format_tanggal(tanggal: str) -> str:
    """'2026-09-22' -> 'Selasa, 22 Sep'"""
    try:
        d = datetime.strptime(tanggal, "%Y-%m-%d")
        return f"{HARI[d.weekday()]}, {d.day} {BULAN[d.month - 1]}"
    except ValueError:
        return tanggal


def format_waktu(waktu: str) -> str:
    """'2026-09-22 11:00:00' -> '22 Sep 2026, 11:00 WIB'"""
    try:
        d = datetime.strptime(waktu, "%Y-%m-%d %H:%M:%S")
        return f"{d.day} {BULAN[d.month - 1]} {d.year}, {d.strftime('%H:%M')} WIB"
    except ValueError:
        return waktu


def _metric(ikon: str, label: str, nilai: str, kelas: str = "") -> str:
    return (
        f'<div class="wx-metric {kelas}">'
        f'<div class="wx-metric-label">{ikon} {_esc(label)}</div>'
        f'<div class="wx-metric-value">{_esc(nilai)}</div>'
        "</div>"
    )


def _footer(waktu_data: str | None, diperbarui: str | None, sumber: str, url: str) -> str:
    kiri = f"<span>🕐 {_esc(waktu_data)}</span>" if waktu_data else ""
    tengah = f"<span>Diperbarui: {_esc(diperbarui)}</span>" if diperbarui else ""
    return (
        '<div class="wx-foot">'
        f"{kiri}{tengah}"
        f'<a href="{_esc(url)}" target="_blank">🔗 Sumber: {_esc(sumber)}</a>'
        "</div>"
    )


def render_current_weather_card(data: dict, intro: str | None = None) -> str:
    """Kartu cuaca 'sekarang'. Semua angka langsung dari data BMKG, bukan tulisan AI."""
    tema = _tema(data["kondisi"])
    hujan = "Ada kemungkinan hujan" if data["akan_hujan"] else "Tidak ada indikasi hujan"

    bagian = []
    if intro:
        bagian.append(f'<p class="wx-intro">{_esc(intro)}</p>')

    bagian.append(
        '<div class="wx-card">'
        f'<div class="wx-hero wx-{tema}">'
        f'<div><div class="wx-loc">📍 {_esc(data["lokasi"])}</div>'
        f'<div class="wx-cond">{_esc(data["kondisi"])}</div></div>'
        f'<div class="wx-temp">{emoji_cuaca(data["kondisi"])} {_esc(data["suhu"])}°C</div>'
        "</div>"
        '<div class="wx-grid">'
        + _metric("💧", "Kelembapan", f'{data["kelembapan"]}%', "wx-m-hum")
        + _metric("💨", "Kecepatan angin", f'{data["kecepatan_angin"]} km/jam · {data["arah_angin"]}', "wx-m-wind")
        + _metric("🌦️", "Prediksi cuaca", hujan, "wx-m-rain")
        + "</div>"
        + _footer(format_waktu(data["waktu_data"]), data["data_diperbarui"], data["sumber"], data["sumber_url"])
        + "</div>"
    )
    return "".join(bagian)


def render_forecast_card(data: dict, intro: str | None = None, single_day: bool = False) -> str:
    """Kartu prakiraan: satu hari (besok) atau beberapa hari."""
    hari_list = [data["prakiraan_hari_ini"]] if single_day else data["prakiraan"]

    tiles = ""
    for h in hari_list:
        tema = _tema(h["kondisi_dominan"])
        hujan = "🌧️ Ada kemungkinan hujan" if h["kemungkinan_hujan"] else "Cenderung tidak hujan"
        tiles += (
            f'<div class="wx-day wx-{tema}">'
            f'<div class="wx-day-name">{_esc(format_tanggal(h["tanggal"]))}</div>'
            f'<div class="wx-day-emoji">{emoji_cuaca(h["kondisi_dominan"])}</div>'
            f'<div class="wx-day-cond">{_esc(h["kondisi_dominan"])}</div>'
            f'<div class="wx-day-temp">{_esc(h["suhu_min"])}° – {_esc(h["suhu_maks"])}°</div>'
            f'<div class="wx-day-rain">{hujan}</div>'
            "</div>"
        )

    bagian = []
    if intro:
        bagian.append(f'<p class="wx-intro">{_esc(intro)}</p>')

    bagian.append(
        '<div class="wx-card">'
        f'<div class="wx-hero wx-default"><div><div class="wx-loc">📍 {_esc(data["lokasi"])}</div>'
        f'<div class="wx-cond">Prakiraan Cuaca</div></div></div>'
        f'<div class="wx-days">{tiles}</div>'
        + _footer(None, None, data["sumber"], data["sumber_url"])
        + "</div>"
    )
    return "".join(bagian)