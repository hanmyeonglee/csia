import base64
from datetime import datetime

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class Client:
    def __init__(self):
        self.key = None
        self.iv = None

    def set_ki(self, key, iv):
        self.key = key
        self.iv = iv.encode('utf-8')

    def encrypt(self, data):
        if self.key == None or self.iv == None:
            raise NoKeyOrIVError()
        data = pad(data.encode('utf-8'), 16)
        cipher = AES.new(self.key.encode('utf-8'), AES.MODE_CBC, self.iv)
        return base64.b64encode(cipher.encrypt(data)).decode("utf-8")

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        cipher = AES.new(self.key.encode('utf-8'), AES.MODE_CBC, self.iv)
        return unpad(cipher.decrypt(enc), 16).decode("utf-8")


class WsClient(Client):
    def __init__(self, websocket):
        super().__init__()
        self.client = websocket
        self.time = datetime.now().timestamp()

    def time_remain(self):
        ago = datetime.now().timestamp() - self.time
        if 10 <= ago // 60 <= 30:
            self.client.close()
            return True
        return False

    def time_recon(self):
        self.time = datetime.now().timestamp()

    async def send(self, mes=""):
        await self.client.send(mes)


class NoKeyOrIVError(Exception):
    def __init__(self):
        super().__init__('No Key or IV')
