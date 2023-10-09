import struct 
import base58
import requests
import codecs
import hashlib
import ecdsa
import wallet

class Transaction:

    def __init__(self, send_addr, send_pkey, rec_addr, amount, fees):
        self.sender_addr = send_addr
        self.sender_hashed_pubkey = base58.b58decode_check(send_addr)[1:].hex()
        self.sender_private_key = send_pkey

        self.receiver_address = rec_addr
        self.receiver_hashed_pubkey = base58.b58decode_check(rec_addr)[1:].hex()
        
        self.sender_balance = wallet.get_balance(send_addr)
        self.sender_to_send_amount = amount
        self.tx_fee = fees

        self.prv_txids = self.auswahl_Utx(send_addr, amount + self.tx_fee)
        self.tx_in_count = struct.pack("<B", len(self.prv_txids))

        self.output_amount = self.sender_to_send_amount
        self.change_amount = 0

    def flip_byte_order(self,string):
        """Flips the byte order in a hex string"""
        flipped = "".join(reversed([string[i:i + 2] for i in range(0, len(string), 2)]))
        return flipped


    erste_Outouts = {}
    zweite_Outputs = {} 

    def create_input_outputs(self):
        self.tx_ins = []

        for txid in self.prv_txids:
            tx_in = {}
            tx_in["txouthash"] = codecs.decode(self.flip_byte_order(txid['txid']), 'hex')
            tx_in["tx_out_index"] = struct.pack("<L", txid['vout'])

            tx_in["script"] = b'\x76\xA9\x14' + bytes.fromhex(self.sender_hashed_pubkey) + b'\x88\xac'

            tx_in["script_bytes"] = struct.pack("<B", len(tx_in["script"]))

            tx_in["sequence"] = codecs.decode("ffffffff", 'hex')

            self.tx_ins.append(tx_in)
            self.change_amount += txid['value']

        self.change_amount = self.change_amount - self.output_amount - self.tx_fee
        self.erste_Outouts["value"] = struct.pack("<Q", self.output_amount)
        self.erste_Outouts["pk_script"] = b'\x76\xA9\x14' + bytes.fromhex(self.receiver_hashed_pubkey) + b'\x88\xac'
        self.erste_Outouts["pk_script_bytes"] = struct.pack("<B", len(self.erste_Outouts["pk_script"]))

        self.zweite_Outputs["value"] = struct.pack("<Q", self.change_amount)
        self.zweite_Outputs["pk_script"] = b'\x76\xA9\x14' + bytes.fromhex(self.sender_hashed_pubkey) + b'\x88\xac'
        self.zweite_Outputs["pk_script_bytes"] = struct.pack("<B", len(self.zweite_Outputs["pk_script"]))



    version = struct.pack("<L", 1)
    anzahl_Outputs = struct.pack("<B", 2)
    lock_time = struct.pack("<L", 0)


    def tx_Signieren(self) -> str:
        real_tx1 = (
            self.version
            + self.tx_in_count
        )

        for i in range(len(self.tx_ins)):
            real_tx1 += self.tx_ins[i]["txouthash"]
            real_tx1 += self.tx_ins[i]["tx_out_index"]

            tx_ins_copy = [x.copy() for x in self.tx_ins]

            for j in range(len(tx_ins_copy)):
                if j != i:
                    tx_ins_copy[j]['script'] = b''
                    tx_ins_copy[j]['script_bytes'] = struct.pack("<B", len(tx_ins_copy[j]["script"]))

            raw_tx_string = self._get_modified_raw_tx_(tx_ins_copy)

            hashed_tx_to_sign = hashlib.sha256(hashlib.sha256(raw_tx_string).digest()).digest()
            sk = ecdsa.SigningKey.from_string(codecs.decode(self.sender_private_key, 'hex'), curve=ecdsa.SECP256k1)
            vk = sk.verifying_key
            public_key = (b'\x04' + vk.to_string())
            signature = sk.sign_digest(hashed_tx_to_sign, sigencode=ecdsa.util.sigencode_der_canonize)

            signature += b'\x01'

            sigscript = (
                struct.pack("<B", len(signature))
                + signature
                + struct.pack("<B", len(public_key))
                + public_key
            )

            real_tx1 += struct.pack("<B", len(sigscript))
            real_tx1 += sigscript
            real_tx1 += self.tx_ins[i]["sequence"]

        real_tx2 = (
            self.anzahl_Outputs
            + self.erste_Outouts["value"]
            + self.erste_Outouts["pk_script_bytes"]
            + self.erste_Outouts["pk_script"]
            + self.zweite_Outputs["value"]
            + self.zweite_Outputs["pk_script_bytes"]
            + self.zweite_Outputs["pk_script"]
            + self.lock_time
        )

        real_tx = real_tx1 + real_tx2
        return real_tx.hex()

    def _get_modified_raw_tx_(self, modified_tx_ins) -> bytes:
        raw_tx_string1 = (
            self.version
            + self.tx_in_count
        )
        for i in range(len(modified_tx_ins)):
            raw_tx_string1 += modified_tx_ins[i]['txouthash']
            raw_tx_string1 += modified_tx_ins[i]['tx_out_index']
            raw_tx_string1 += modified_tx_ins[i]['script_bytes']
            raw_tx_string1 += modified_tx_ins[i]['script']
            raw_tx_string1 += modified_tx_ins[i]['sequence']

        raw_tx_string2 = (
            self.anzahl_Outputs
            + self.erste_Outouts["value"]
            + self.erste_Outouts["pk_script_bytes"]
            + self.erste_Outouts["pk_script"]
            + self.zweite_Outputs["value"]
            + self.zweite_Outputs["pk_script_bytes"]
            + self.zweite_Outputs["pk_script"]
            + self.lock_time
            + struct.pack("<L", 1)
        )
        return raw_tx_string1 + raw_tx_string2
    
    def get_Utx(self,address):
        testnet_prefixes = ["m", "n", "2", "tb1", "bcrt1"]
        tn = "/testnet" if any(address.startswith(prefix) for prefix in testnet_prefixes) else ""
        url = f"https://blockstream.info{tn}/api/address/{address}/utxo"
        if requests.get(url).text != "Invalid Bitcoin address":
            return requests.get(url).json()
        else: raise Exception("Invalid Bitcoin address")
    
    def auswahl_Utx(self,address:str, desired_amount:int):
        utxos = sorted(self.get_Utx(address), key=lambda utxo: utxo['value'], reverse=True)
        best_combination = self.ausgaben_Kombini(utxos, desired_amount)

        if best_combination is None:
            raise Exception("Insufficient funds")

        return best_combination
    
    def ausgaben_Kombini(self, utxos, gewuenschter_betrag, aktueller_betrag=0, index=0):
        if aktueller_betrag >= gewuenschter_betrag:
            return []

        if index >= len(utxos):
            return None

        utxo = utxos[index]

        mit_utxo = self.ausgaben_Kombini(utxos, gewuenschter_betrag, aktueller_betrag + utxo['value'], index + 1)
        if mit_utxo is not None:
            mit_utxo.append(utxo)

        ohne_utxo = self.ausgaben_Kombini(utxos, gewuenschter_betrag, aktueller_betrag, index + 1)

        if mit_utxo is None:
            return ohne_utxo
        if ohne_utxo is None:
            return mit_utxo

        return mit_utxo if len(mit_utxo) < len(ohne_utxo) else ohne_utxo
