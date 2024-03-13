import requests
import base64

BASEURL = "https://sandbox.bca.co.id"
API_KEY =" c3ba6229-c95a-4e99-8707-94632cc20ea0"
SECRET_KEY = "d012a91e-3421-41c8-9d18-d612884b692f"
OAUTH_SECRET = "cc1ca9c3-fead-40fd-89d2-078d12e41264"
OAUTH_KEY = "1599ff7d-8b17-44ae-ba5d-d653cd887fc5"

BASE64ENCODE = base64.b64encode(f'{OAUTH_SECRET}:{OAUTH_KEY}'.encode()).decode()
auth_token = requests.post(
    url=f"{BASEURL}/api/oauth/token", 
    headers={"Content-Type": "application/x-www-form-urlencoded", "Authorization": f"Basic {BASE64ENCODE}"}, 
    data={
        "grant_type": "client_credentials"
    })

auth_token = auth_token.json()['access_token']
print(auth_token)



import hashlib
import hmac
import base64
import json
import requests
from datetime import datetime

def generate_signature(client_secret, http_method, relative_url, access_token, request_body, timestamp):
    # Mengonversi body permintaan menjadi string JSON yang minimal
    minified_request_body = json.dumps(request_body, separators=(',', ':'))

    # Menghitung nilai hash SHA-256 dari body permintaan
    sha256_hash = hashlib.sha256(minified_request_body.encode()).hexdigest()

    # Membentuk StringToSign
    string_to_sign = f"{http_method.upper()}:{relative_url}:{access_token}:{sha256_hash.lower()}:{timestamp}"

    # Mengonversi Client Secret menjadi bytes
    client_secret_bytes = client_secret.encode()

    # Menghitung HMAC-SHA512 menggunakan Client Secret sebagai kunci
    signature = hmac.new(client_secret_bytes, string_to_sign.encode(), hashlib.sha512).digest()

    # Mengonversi tanda tangan ke dalam format Base64
    encoded_signature = base64.b64encode(signature).decode()

    return encoded_signature

# Contoh penggunaan fungsi
http_method = "GET"
relative_url = "/banking/v3/corporates/UATCORP001/accounts/0613005908/statements?StartDate=2023-03-07&EndDate=2024-03-07"
request_body = {}
timestamp = "2024-03-07T18:30:45.123+0700"

signature = generate_signature(SECRET_KEY, http_method, relative_url, auth_token, request_body, timestamp)
print("X-SIGNATURE:", signature)