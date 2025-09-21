import time
from typing import Dict

import jwt

def sign_jwt(user_id: int, secret: str):
    payload = {
        "user_id": user_id,
    }

    token = jwt.encode(payload, secret, algorithm="HS256")

    return token

def decode_jwt(token: str, secret: str):
    try:
        decoded_token = jwt.decode(token, secret, algorithms="HS256")
        return decoded_token
    except:
        return {}
