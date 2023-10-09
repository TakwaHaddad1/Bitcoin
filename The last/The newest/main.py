import requests
import trans
import time
import sys
import wallet
import os

global current_option
current_option = 0
global wallet_adresse
wallet_adresse = ''
global privater_schlüssel
privater_schlüssel = ''
global  öffentlicher_schlüssel
öffentlicher_schlüssel = ''


def display_menu():
    global current_option
    global wallet_adresse
    global privater_schlüssel
    global öffentlicher_schlüssel

    if current_option == 0:
        print("Option 1: Erstellen einer neuen Wallet auf dem Testnet")
        print("Option 2: Login mit der Wallet")
        print("Option 3: Beenden")
        print("Bitte option eintippen: ", end='')
        
        option = input()    

        current_option = int(option)

        print(option)
        os.system("cls")
        

    if current_option == 1:
        
        print("Bitte AES Passwort eintippen: ", end='')

        password = input()

        print("Bitte Namen der Wallet eintippen: ", end='')

        name_wallet = input()

        if(len(password) == 0):
            current_option = 0
            print("Konnte die Wallet nicht entschlüsseln")


        priv = wallet.generate_random_private_key()
        public = wallet.generate_public_key(priv)
        address = wallet.generate_address(priv)

        wallet.wallet_speichern(name_wallet, priv, public.hex(), address, password)

        current_option = 0
        os.system("cls")



    if current_option == 2:
        print("Bitte name der Wallet eintippen: ", end='')

        wallet_name = input()

        print("Bitte AES Passwort eintippen: ", end='')

        aes_passwort = input()

        if(len(aes_passwort) == 0):
            current_option = 0
            print("Konnte die Wallet nicht entschlüsseln")

        adressen = wallet.lade_wallets()

        is_found = False
        for adresse in adressen['adressen']:

            if(adresse['Name'] == wallet_name):

                AESDatei = adresse['AESDatei']
                print(AESDatei)
                öffentlicher_schlüssel = adresse['oeffentlicher_Key']
                print(aes_passwort)
                
                privater_schlüssel = wallet.entschlüssel_privaten_schlüssel(AESDatei, aes_passwort)
                        


                print("private Schlüssel :",privater_schlüssel)



                wallet_adresse = adresse['Adresse']

                is_found=True
                break

            pass
            

        if not is_found:
            raise Exception("Konnte wallet nicht finden")
        
        current_option = 50

    if current_option == 3:
        sys.exit()

    if current_option == 50:

        
        balance = wallet.get_balance(wallet_adresse)

        print(f"Aktuelle BTC Adresse: {wallet_adresse}")
        print(f"Aktueller BTC Guthaben: {balance}")

        print('')

        print("Option 1: Ausloggen")
        print("Option 2: Transaktion schicken")
        print("Bitte option eingeben: ", end='')

        new_option = int(input())
        current_option = new_option

        os.system("cls")

        if(new_option == 1):
           current_option = 0
           os.system("cls")

        if(new_option == 2):
            current_option = 70            


    if(current_option == 70):
        print("Bitte empfänger eintippen:", end='')
        receiver = input()

        print("Bitte menge angeben: ", end='')

        amount = int(input())

        current_option = 50
        fees=int(0.00000500* 100000000)
        transaction = trans.Transaction(wallet_adresse, privater_schlüssel, receiver, amount, fees)
        transaction.create_input_outputs()
        transaction = transaction.tx_Signieren()

        
        url = "https://api.blockcypher.com/v1/btc/test3/txs/push"
        response = requests.post(url, json={'tx': transaction})
        result= response.text
        print(f'Ergebnis: {result}')
        


if __name__ == '__main__':
    current_option = 0
    
    while(True):
        display_menu()