import datetime
import hashlib
import base64
import urllib
import hmac
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import lzstring
import requests,time, tempfile , json ,random,os
from os.path import join, dirname
from dotenv import load_dotenv
from typing import Optional

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# SECRETID            = os.environ.get("SECRETID")
SECRETID            = '0bESJB5DB1'
# SECRETID            = '0bESJB5DB1'
# CONSID              = os.environ.get("CONSID")
CONSID              = '3331'
# CONSID              = '3331'
# USERKEY             = os.environ.get("USERKEY")
# USERKEY             = 'cb27e963a381e479517d79add35ccb41'
USERKEY             = '7601626d0da3659eb22dd6235621cad0'
# USERKEY_VCLAIM      = os.environ.get("USERKEY_VCLAIM")
# USERKEY_VCLAIM      = 'cb27e963a381e479517d79add35ccb41'
USERKEY_VCLAIM      = '25c6e851f3a3d8b495a233f45d0d70e7'
# HOST                = os.environ.get("HOST")
HOST                = 'https://apijkn.bpjs-kesehatan.go.id/vclaim-rest'

def get(endpoint,host=None):
    try:
        stamp = str(
                round(
                    time.time()
                )
                )
        url = HOST+endpoint if not host else host+endpoint
        print(url)
        # print(generateHeader(stamp)[3])
        query = requests.get(url,headers = generateHeader(stamp)[3],verify=False)
        # print(query.text)
        response = returnDecrypt(query.json(),stamp)
        return response
    except requests.exceptions.RequestException as e:
        print("Error Guys : ")
        print(e)
        return None


def post(endpoint,data,host=None,jsonEncode=None):
    try:
        stamp = str(
                round(
                    time.time()
                )
                )
        url = HOST+endpoint if not host else host+endpoint
        jsonEncode = data if not jsonEncode else data.json() 
        query = requests.post(url,headers = generateHeader(stamp)[3],data = jsonEncode,verify=False)
        # print(query.json())
        print(url)
        response = returnDecrypt(query.json(),stamp)
        return response
    except requests.exceptions.RequestException as e:
        return None


def generateHeader(stamp):
    consID = CONSID
    secretKey = bytes(SECRETID, 'utf-8')
    # print(SECRETID)
    data = consID + '&' + stamp
    resultdata = data.encode("utf-8")
    signature = hmac.new(secretKey, resultdata, digestmod=hashlib.sha256).digest()
    encodesignature = base64.b64encode(signature).decode()
    headers = {
        "X-cons-id":consID,
        "X-timestamp":stamp,
        "X-signature":encodesignature,
        "user_key":USERKEY
    }
    print(headers)
    return consID,stamp,encodesignature,headers

def decrypt(key, txt_enc):

    x = lzstring.LZString()

    key_hash = hashlib.sha256(key.encode('utf-8')).digest()

    mode = AES.MODE_CBC

    # decrypt
    decryptor = AES.new(key_hash[0:32], mode, IV=key_hash[0:16])
    plain = decryptor.decrypt(base64.b64decode(txt_enc))
    decompress = x.decompressFromEncodedURIComponent(plain.decode('utf-8'))

    return decompress

def returnDecrypt(resultMentah,stamp):
    if resultMentah['metadata']['code'] == 1:

    # if hasil is not None:
        keyHash = CONSID + SECRETID + stamp
        result = decrypt(keyHash,resultMentah['response'])
        resultMentah.update({'response':json.loads(result)})
    if resultMentah['metadata']['code'] == 200:
        # if resultMentah['response']:
        if "response" in resultMentah:
            keyHash = CONSID + SECRETID + stamp
            result = decrypt(keyHash,resultMentah['response'])
            resultMentah.update({'response':json.loads(result)})
        else:
            return resultMentah

    return resultMentah
