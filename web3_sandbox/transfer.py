import json
from getpass import getpass
from pathlib import Path
from web3 import Web3
from eth_account.signers.local import LocalAccount


def transfer(node_address: str, keyfile: Path, key_password: str, to_address: str, value: float):
    w3 = Web3(Web3.HTTPProvider(node_address))
    with keyfile.open("r"):
        key = keyfile.read_text()

    account: LocalAccount = w3.eth.account.from_key(w3.eth.account.decrypt(key, key_password))
    to_address = address = Web3.to_checksum_address(to_address)
    transaction = {
        "from": account.address,
        "to": to_address,
        "value": w3.to_wei(value, "ether"),
        "gas": 21000,
        "gasPrice": w3.to_wei("50", "gwei"),
        "nonce": w3.eth.get_transaction_count(account.address),
        "chainId": 1, #17000,
    }

    signed_tx = account.sign_transaction(transaction)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(tx_hash)


def encrypt(keyfile: Path, key_password: str):
    w3 = Web3(Web3.HTTPProvider())
    with keyfile.open("r"):
        key = keyfile.read_text()

    account: LocalAccount = w3.eth.account.from_key(w3.eth.account.decrypt(key, key_password))
    password = getpass("password:")
    password2 = getpass("repeat password:")
    if password != password2:
        raise Exception("repeated password different from the original one")

    encrypted_account = account.encrypt(password)
    print(json.dumps(encrypted_account, indent=2))
