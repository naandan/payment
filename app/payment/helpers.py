import random
import secrets
import requests

def generate_merchant_code():
    unique_numbers = random.sample(range(1, 9), 5)
    return "SP" + "".join(map(str, unique_numbers))


def generate_api_key():
    return secrets.token_hex(20)

def cek_web_status(url):
    response = requests.get(url)
    if response.status_code == 200:
        return True
    return False
