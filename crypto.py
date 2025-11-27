from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
import base64

SALT = b'some_salt_here'

def pad(text):
    pad_len = 16 - len(text) % 16
    return text + chr(pad_len) * pad_len

def unpad(text):
    return text[:-ord(text[-1])]

def derive_key(password):
    return PBKDF2(password, SALT, dkLen=32)

def encrypt_message(text, password):
    key = derive_key(password)
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(text).encode())
    return base64.b64encode(iv + encrypted).decode()

def decrypt_message(encrypted_b64, password):
    data = base64.b64decode(encrypted_b64)
    iv, encrypted = data[:16], data[16:]
    key = derive_key(password)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted).decode()
    return unpad(decrypted)
