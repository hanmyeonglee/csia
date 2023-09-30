import base64
import json

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256


def RSA_decrypt(mes):
    message = json.loads(PKCS1_OAEP.new(RSA.importKey(open('/var/www/html/ssch/pem/prikey.pem').read()),
                         hashAlgo=SHA256).decrypt(base64.b64decode(mes)).decode("utf-8"))

    key = message['key']
    iv = message['iv']

    return key, iv
