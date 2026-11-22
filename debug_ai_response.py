from openai import OpenAI
from config.settings import AI_API_KEY, AI_BASE_URL, AI_MODEL

client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)

response = client.chat.completions.create(
    model=AI_MODEL,
    messages=[
        {"role": "system", "content": "Balas HANYA dengan JSON: {\"status\": \"ok\"}"},
        {"role": "user", "content": "Halo"},
    ],
    max_tokens=200,
    temperature=0,
)

print("=== FULL RESPONSE OBJECT ===")
print(response.model_dump_json(indent=2))