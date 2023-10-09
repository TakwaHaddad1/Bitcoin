
import hashlib
import secrets
import ecdsa
import json
import os
import requests
import aes
import base58
import string
import random
import codecs

from ecdsa import SECP256k1

def get_balance(address):
    url = f"https://api.blockcypher.com/v1/btc/test3/addrs/{address}/balance"
    response = requests.get(url)
    balance = response.json()['final_balance']
    return balance

def generate_public_key(private_key):
    private_key_bytes = bytes.fromhex(private_key)
    signing_key = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1)
    verifying_key = signing_key.get_verifying_key()
    return bytes.fromhex("04") + verifying_key.to_string()

def generate_address(private_key):
    public_key_bytes = generate_public_key(private_key)
    sha256_hash = hashlib.sha256(public_key_bytes).digest()
    ripemd160_hash = hashlib.new('ripemd160', sha256_hash).digest()
    version = b"\x6f"
    payload = version + ripemd160_hash
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    address = base58.b58encode(payload + checksum).decode('utf-8')
    return address

def generate_random_private_key():
    length = 64  # Länge des privaten Schlüssels in Hexadezimalzeichen
    characters = string.hexdigits  # Nur Hexadezimalzeichen ohne Buchstaben a-f
    return ''.join(random.choice(characters) for _ in range(length))

def wallet_speichern(name, private_key, oeffentlicher_key, address, aes_password):
    
    datei_inhalt = {
        'Name' : name,
        'AESDatei': name + '.aes',
        'oeffentlicher_Key': oeffentlicher_key,
        'Adresse': address
    }

    # Encrypt the private key
    aes.verschlussel_privaten_schlüssel(private_key, name + '.aes', aes_password)

    # Create new file if it does not exists
    if not os.path.isfile('adressen.json'):
        f = open("adressen.json", "a")
        f.write("{\"adressen\":[]}")
        f.close()

    with open('adressen.json','r+') as file:
        file_data = json.load(file)
        file_data["adressen"].append(datei_inhalt)
        file.seek(0)
        json.dump(file_data, file, indent = 4)



def lade_wallets():

    if os.path.isfile('adressen.json') == False:
        datei = open("adressen.json", "a")
        datei.write("{\"adressen\":[]}")
        datei.close()


    datei = open('adressen.json','r+')
    datei_inhalt = json.load(datei)
    datei.close()
    return datei_inhalt
    

def entschlüssel_privaten_schlüssel(key_file, password):
    return aes.entschlüssel_privaten_schlüssel(key_file, password)



