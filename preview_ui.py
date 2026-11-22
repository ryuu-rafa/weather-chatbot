import streamlit as st

from services.location_service import resolve_location
from services.weather_service import (
    get_current_weather,
    get_forecast,
    get_forecast_for_day,
    WeatherServiceError,
)
from utils.ui_components import inject_css, render_current_weather_card, render_forecast_card

st.set_page_config(page_title="Preview UI", page_icon="🌤️")
inject_css()

st.title("Preview UI (tanpa AI)")
st.caption("Data cuaca asli dari BMKG. Kalimat pembuka di bawah hanya teks contoh.")

nama = st.text_input("Nama daerah", "Jakarta Selatan")
hasil = resolve_location(nama)

if hasil["status"] == "ambiguous":
    st.warning("Nama terlalu umum. Pilihan: " + ", ".join(hasil["opsi"]))
    st.stop()
if hasil["status"] == "not_found":
    st.error("Wilayah tidak ditemukan.")
    st.stop()

try:
    contoh = "(Contoh kalimat pembuka dari AI)"
    st.markdown("**Cuaca sekarang**")
    st.markdown(render_current_weather_card(get_current_weather(hasil["adm4"], hasil["nama_tampil"]), contoh), unsafe_allow_html=True)

    st.markdown("**Besok**")
    st.markdown(render_forecast_card(get_forecast_for_day(hasil["adm4"], hasil["nama_tampil"], 1), contoh, single_day=True), unsafe_allow_html=True)

    st.markdown("**3 hari**")
    st.markdown(render_forecast_card(get_forecast(hasil["adm4"], hasil["nama_tampil"], 3), contoh), unsafe_allow_html=True)
except WeatherServiceError as e:
    st.error(str(e))