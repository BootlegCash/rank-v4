import requests

# 🔧 Base URL for local dev
BASE_URL = "http://127.0.0.1:8000"

# ✅ Endpoint for logging drinks
url = f"{BASE_URL}/accounts/api/log_drink/"

# 🔑 Token from `drf_create_token`
token = "07aad56c90c2faaee46ebec4d4cd7ab3e69bf7f5"

headers = {
    "Authorization": f"Token {token}",
    "Content-Type": "application/json"
}

# 📦 Example payload – adjust as needed
payload = {
    "beer": 3,
    "floco": 0,
    "rum": 2,
    "whiskey": 1,
    "vodka": 0,
    "tequila": 0,
    "shotguns": 1,
    "snorkels": 0,
    "thrown_up": 0
}

# 🚀 Send POST
response = requests.post(url, json=payload, headers=headers)

# 📦 Print response
print("Status:", response.status_code)
print("Raw text:", response.text)
try:
    data = response.json()
    print("As JSON:", data)
except Exception as e:
    print("⚠️ JSON decode error:", e)
