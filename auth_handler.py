import time
from typing import Dict

import jwt

def sign_jwt(user_id: int, secret: str):
    payload = {
        "user_id": user_id,
        "expires": time.time() + 600
    }

    token = jwt.encode(payload, secret, algorithm=HS256)

    return token

def decode(token: str, secret: str):
    try:
        decoded_token = jwt.decode(token, secret, algorithms=HS256)
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except:
        return {}
