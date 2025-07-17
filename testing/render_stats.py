import requests

# 🔧 Replace this with your live Render URL
BASE_URL = "https://ranked-0xtx.onrender.com"

# 🔑 Replace this with the token you generated on Render
TOKEN = "07aad56c90c2faaee46ebec4d4cd7ab3e69bf7f5"

# ✅ Your API endpoint (make sure it exists in your urls.py)
url = f"{BASE_URL}/accounts/api/profile/"

# 🔑 Add your token in the Authorization header
headers = {
    "Authorization": f"Token {TOKEN}"
}

# 🚀 Send the GET request
response = requests.get(url, headers=headers)

# 📌 Print out results for debugging
print("Status:", response.status_code)
print("Raw text:", response.text)  # show raw response in case JSON fails
try:
    data = response.json()
    print("As JSON:", data)
except Exception as e:
    print("JSON decode error:", e)
