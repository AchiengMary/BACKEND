from datetime import datetime, timedelta

# Temporary in-memory store: email -> {code, expiry}
verification_store = {}

def generate_verification_code(length=4):
    from random import randint
    return str(randint(10**(length-1), 10**length - 1))

def store_code(email: str, code: str, expiry_minutes=2):
    verification_store[email] = {
        "code": code,
        "expires_at": datetime.utcnow() + timedelta(minutes=expiry_minutes)
    }

def is_code_valid(email: str, code: str) -> bool:
    entry = verification_store.get(email)
    if not entry:
        return False
    return entry["code"] == code and datetime.utcnow() < entry["expires_at"]
