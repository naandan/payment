import random
import secrets
import requests
from datetime import datetime, timedelta
import pytz

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

def generate_transaction_code():
    unique_numbers = random.sample(range(1, 9), 5)
    return "TR" + "".join(map(str, unique_numbers))


wib = pytz.timezone('Asia/Jakarta')
now = datetime.now(wib)

def get_expired_at(expire_period=30, time=now):
    return time + timedelta(minutes=expire_period)

def get_time_id(time):
    return time.astimezone(pytz.timezone('Asia/Jakarta'))

def get_datetime_now():
    wib = pytz.timezone('Asia/Jakarta')
    now = datetime.now(wib)
    return now

def get_transaction_url(request, transaction):
    return f"{request.scheme}://{request.get_host()}/api/v1/payment/pay/?code={transaction.code}"

def get_check_payment_url(request, transaction):
    return f"{request.scheme}://{request.get_host()}/api/v1/payment/check/?code={transaction.code}"

def check_expired(time_expired):
    print(get_datetime_now())
    print(get_time_id(time_expired))
    if get_datetime_now() > time_expired:
        return True
