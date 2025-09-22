import time
from typing import Dict

import jwt
from decouple import config


JWT_SECRET = config("secret")
JWT_ALGORITHM = config("algorithm")


def token_response(token: str):
    return {
        'response':{
            'token':token
        },
        'metadata':{
            'message':'Ok',
            'code':200
        }
    }

def signJWT(user_id: str) -> Dict[str, str]:
    payload = {
        "user_id": user_id,
        "expires": time.time() + 60000
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token_response(token)

# updated 08/06/2023
# perbaikan
# def decodeJWT(token: str,username):
#     try:
#         decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
#         return True if decoded_token["expires"] >= time.time() and decoded_token['user_id']==username else False
#     except:
#         return False
def decodeJWT(token: str, username):
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if decoded_token["expires"] < time.time():
            return{"message": "Token expired"}
        if decoded_token['user_id'] != username:
            return {"message": "Username / password salah"}
        else:
            return {"message":"OK"}
    except:
        return {'message':"Username / password salah"}
