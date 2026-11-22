from services.location_service import resolve_location
from services.weather_service import get_current_weather, WeatherServiceError
from services.ai_service import extract_intent, generate_response

pesan_user = "Cuaca hari ini di Jakarta Selatan?"

print(f"User: {pesan_user}\n")

intent = extract_intent(pesan_user)
print(f"Intent terdeteksi: {intent}\n")

if not intent["is_weather_related"]:
    print("Bukan pertanyaan cuaca.")
else:
    lokasi_hasil = resolve_location(intent["lokasi"])
    print(f"Resolusi lokasi: {lokasi_hasil}\n")

    if lokasi_hasil["status"] == "found":
        try:
            data = get_current_weather(lokasi_hasil["adm4"], lokasi_hasil["nama_tampil"])
            print(f"Data BMKG: {data}\n")

            jawaban = generate_response(data, pesan_user)
            print("=== Jawaban Chatbot ===")
            print(jawaban)
        except WeatherServiceError as e:
            print(f"❌ Error ambil cuaca: {e}")
    elif lokasi_hasil["status"] == "ambiguous":
        print(f"Perlu klarifikasi, opsi: {lokasi_hasil['opsi']}")
    else:
        print("Lokasi tidak ditemukan dalam daftar.")