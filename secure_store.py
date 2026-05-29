from cryptography.fernet import Fernet
import json
import os

KEY_FILE = "secret.key"
STORE_FILE = "devices.enc"


def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key


def load_key():
    if not os.path.exists(KEY_FILE):
        return generate_key()
    return open(KEY_FILE, "rb").read()


def get_cipher():
    return Fernet(load_key())


def save_devices(devices: list):
    cipher = get_cipher()
    data = json.dumps(devices).encode()
    encrypted = cipher.encrypt(data)

    with open(STORE_FILE, "wb") as f:
        f.write(encrypted)


def load_devices():
    if not os.path.exists(STORE_FILE):
        return []

    cipher = get_cipher()
    data = open(STORE_FILE, "rb").read()
    decrypted = cipher.decrypt(data)

    return json.loads(decrypted.decode())