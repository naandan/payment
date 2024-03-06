import random
import secrets
import requests
from datetime import datetime, timedelta
import pytz
import hashlib
from core.settings import BASEURL

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
    return f"{BASEURL}/api/v1/payment/pay/?code={transaction.code}"

def get_check_payment_url(request, transaction):
    return f"{BASEURL}/api/v1/payment/check/?code={transaction.code}"

def check_expired(time_expired):
    print(get_datetime_now())
    print(get_time_id(time_expired))
    if get_datetime_now() > time_expired:
        return True


def verify_signature(merchant_code, merchant_key, signature_to_verify, timestamp):
    timestamp = int(timestamp)
    expected_signature = hashlib.sha256(f"{merchant_code}{timestamp}{merchant_key}".encode()).hexdigest()
    if signature_to_verify == expected_signature:
        return True
    else:
        return False

def get_callback_url(transaction):
    return f"{transaction.callback_url}?transactionCode={transaction.code}&invoiceCode={transaction.invoice_code}&merchantCode={transaction.merchant.code}"