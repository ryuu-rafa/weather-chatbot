import os
from dotenv import load_dotenv
from openai import OpenAI

# Load variabel dari file .env
load_dotenv()

api_key = os.getenv("AI_API_KEY")
base_url = os.getenv("AI_BASE_URL")
model = os.getenv("AI_MODEL")

# Cek dulu apakah semua variabel berhasil terbaca
print("=== Cek Konfigurasi ===")
print(f"Base URL : {base_url}")
print(f"Model    : {model}")
print(f"API Key  : {'*' * len(api_key) if api_key else 'TIDAK DITEMUKAN'}")
print("========================\n")

if not api_key or not base_url or not model:
    print("❌ Ada variabel yang kosong. Cek kembali file .env kamu.")
    exit()

# Buat client, kompatibel dengan format OpenAI
client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

print("Mengirim pesan test ke Qwen API...\n")

try:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "Halo, siapa kamu? Jawab singkat dalam 1 kalimat."}
        ],
        max_tokens=100
    )

    reply = response.choices[0].message.content
    print("✅ BERHASIL! Response dari AI:")
    print(reply)

except Exception as e:
    print("❌ GAGAL. Terjadi error:")
    print(e)