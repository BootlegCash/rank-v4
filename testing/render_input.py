import requests

# 🔧 API endpoint
url = "https://ranked-0xtx.onrender.com/accounts/api/log_drink/"

# 🔑 Your token from Render
token = "a7f3551f606dd5ca0ff0903ac0579fdddeb9d1a9"

# ✅ Headers with Token Authentication
headers = {
    "Authorization": f"Token {token}",
    "Content-Type": "application/json"
}

# 📦 Payload to log drinks
payload = {
    "beer": 2,
    "floco": 1,
    "rum": 0,
    "whiskey": 0,
    "vodka": 0,
    "tequila": 0,
    "shotguns": 1,
    "snorkels": 0,
    "thrown_up": 0
}

# 🚀 Send POST request
response = requests.post(url, json=payload, headers=headers)

# 🔎 Inspect response
print("Status:", response.status_code)
print("Raw text:", response.text)
try:
    print("As JSON:", response.json())
except Exception as e:
    print("JSON decode error:", e)
