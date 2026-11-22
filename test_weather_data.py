import requests
import json

BMKG_BASE_URL = "https://api.bmkg.go.id/publik/prakiraan-cuaca"

# Kode wilayah tingkat IV (kelurahan) untuk testing awal
# Contoh: Kelurahan Kemayoran, Jakarta Pusat
kode_wilayah_test = "31.71.03.1001"

params = {"adm4": kode_wilayah_test}

print(f"Mengambil data cuaca untuk kode wilayah: {kode_wilayah_test}\n")

try:
    response = requests.get(BMKG_BASE_URL, params=params, timeout=10)
    response.raise_for_status()  # error jika status code bukan 200

    data = response.json()

    print("✅ BERHASIL mengambil data!\n")
    print("=== RAW RESPONSE (untuk debugging) ===")
    print(json.dumps(data, indent=2, ensure_ascii=False))

except requests.exceptions.Timeout:
    print("❌ GAGAL: Request timeout. Cek koneksi internet kamu.")
except requests.exceptions.HTTPError as e:
    print(f"❌ GAGAL: HTTP Error - {e}")
except requests.exceptions.RequestException as e:
    print(f"❌ GAGAL: Terjadi masalah koneksi - {e}")
except json.JSONDecodeError:
    print("❌ GAGAL: Response bukan format JSON yang valid.")