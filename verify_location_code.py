import sys
from services.weather_service import _fetch_raw

if len(sys.argv) != 2:
    print("Cara pakai: python verify_location_code.py <kode_adm4>")
    print("Contoh    : python verify_location_code.py 32.73.01.1002")
    sys.exit(1)

kode = sys.argv[1]
raw = _fetch_raw(kode)
lokasi = raw.get("lokasi", {})

print("=== Info lokasi dari BMKG ===")
print(f"Provinsi   : {lokasi.get('provinsi')}")
print(f"Kota/Kab   : {lokasi.get('kotkab')}")
print(f"Kecamatan  : {lokasi.get('kecamatan')}")
print(f"Desa       : {lokasi.get('desa')}")
print(f"Kode adm4  : {lokasi.get('adm4')}")
print("\nKalau ini sesuai daerah yang kamu maksud, kode ini aman ditambahkan ke LOKASI_TERDAFTAR.")