import requests

# 🔧 Your local dev server or production URL
# For local testing:
BASE_URL = "http://127.0.0.1:8000"
# For production:
# BASE_URL = "https://ranked-0xtx.onrender.com"

# ✅ Endpoint for getting profile stats
url = f"{BASE_URL}/accounts/api/profile/"

# 🔑 Token you generated with `python manage.py drf_create_token poppy`
token = "07aad56c90c2faaee46ebec4d4cd7ab3e69bf7f5"

# ✅ Headers with token auth
headers = {
    "Authorization": f"Token {token}"
}

# 🚀 Make GET request
response = requests.get(url, headers=headers)

# 📦 Print output
print("Status:", response.status_code)
print("Raw text:", response.text)

# Try to parse JSON
try:
    data = response.json()
    print("As JSON:", data)

    # Optional: pretty print some fields
    print("\n🎉 Profile Stats:")
    print(f"Username: {data.get('username')}")
    print(f"Display Name: {data.get('display_name')}")
    print(f"XP: {data.get('xp')}")
    print(f"Rank: {data.get('rank')}")

except Exception as e:
    print("⚠️ JSON decode error:", e)
