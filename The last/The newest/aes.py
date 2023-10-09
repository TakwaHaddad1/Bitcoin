from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
import os
import hashlib
from Cryptodome.Protocol.KDF import PBKDF2


def verschlussel_privaten_schlüssel(privater_schluessel_als_hex, datei_pfad, aes_passwort):
    print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
    iv = os.urandom(16)
    salt = b'some_salt_value'  # Ein zufälliger Salt-Wert für die Schlüsselableitung
    iterationen = 100000  # Anzahl der Iterationen für die Schlüsselableitung
    schlüssel_länge = 32  # Die gewünschte Schlüssellänge in Bytes

    aes_pass_sha = PBKDF2(aes_passwort.encode(), salt, dkLen=schlüssel_länge, count=iterationen)

    AES_Objekt = AES.new(aes_pass_sha, AES.MODE_EAX, iv)
    ciphertext, tag = AES_Objekt.encrypt_and_digest(privater_schluessel_als_hex.encode())
    save_to_file(datei_pfad, iv, ciphertext, tag)
    
    return ciphertext, tag, iv

    
def save_to_file( filename, nonce, ciphertext, tag):
    with open(filename, "wb") as f:
        f.write(len(nonce).to_bytes(1, byteorder='big'))
        f.write(nonce)
        f.write(len(ciphertext).to_bytes(1, byteorder='big'))
        f.write(ciphertext)
        f.write(len(tag).to_bytes(1, byteorder='big'))
        f.write(tag)

def load_from_file( filename, aes_passwort):
    with open(filename, "rb") as f:
        nonce_length = int.from_bytes(f.read(1), byteorder='big')
        nonce = f.read(nonce_length)
        ciphertext_length = int.from_bytes(f.read(1), byteorder='big')
        ciphertext = f.read(ciphertext_length)
        tag_length = int.from_bytes(f.read(1), byteorder='big')
        tag = f.read(tag_length)
    return nonce, ciphertext, tag
  

def entschlüssel_privaten_schlüssel(key_file, aes_passwort):
    print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa ")
    nonce, ciphertext, tag = load_from_file(key_file, aes_passwort)
    print("bbbbb ", nonce, ciphertext, tag)
    salt = b'some_salt_value'  # Ein zufälliger Salt-Wert für die Schlüsselableitung
    iterationen = 100000  # Anzahl der Iterationen für die Schlüsselableitung
    schlüssel_länge = 32  # Die gewünschte Schlüssellänge in Bytes

    aes_pass_sha = PBKDF2(aes_passwort.encode(), salt, dkLen=schlüssel_länge, count=iterationen)

    AES_Objekt = AES.new(aes_pass_sha, AES.MODE_EAX, nonce)
    data = AES_Objekt.decrypt_and_verify(ciphertext, tag)
    print("ccccc ", data)
    return data.decode()
