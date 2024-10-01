import logging
from decimal import Decimal
from pathlib import Path
from typing import Optional
from web3 import Web3
from eth_account.signers.local import LocalAccount

from .eth import wei_to_ether

logger = logging.getLogger(__name__)


ERC2O_ABI = (Path(__file__).parent / "erc20_abi.json").open("r").read()


def erc20_balance(w3: Web3, contract_address: str, address: str):
    contract_address = w3.to_checksum_address(contract_address)
    erc20 = w3.eth.contract(address=contract_address, abi=ERC2O_ABI)
    return wei_to_ether(erc20.functions.balanceOf(address).call())


class Erc20:
    def __init__(self, w3: Web3, contract_address: str, gas_price_gwei: Optional[str] = None):
        self.w3 = w3
        self.gas_price_wei = Web3.to_wei(Decimal(gas_price_gwei), "gwei") if gas_price_gwei else None

        assert self.w3.is_connected()

        self.account: Optional[LocalAccount] = None

        contract_address = w3.to_checksum_address(contract_address)
        self.contract = w3.eth.contract(address=contract_address, abi=ERC2O_ABI)

    def use_private_key(self, key: str, key_password: str):
        self.account = self.w3.eth.account.from_key(self.w3.eth.account.decrypt(key, key_password))

    @property
    def fn(self):
        """Interface for the functions exposed by the GLM contract."""
        return self.contract.functions

    @property
    def address(self) -> str:
        assert self.account
        return self.account.address

    @property
    def eth_required_for_transfer_ether(self):
        gas_limit = 47563
        gas_price = self.gas_price_wei or self.w3.eth.gas_price
        return Decimal(Web3.from_wei(gas_limit * gas_price, "ether"))

    def send_glm(self, address: str, amount_wei: int):
        assert self.account
        sender_address = self.w3.to_checksum_address(self.address)
        nonce = self.w3.eth.get_transaction_count(sender_address)
        txdata = {"from": self.address, "nonce": nonce}
        if self.gas_price_wei:
            txdata["gasPrice"] = self.gas_price_wei
        tx = self.fn.transfer(address, amount_wei).buildTransaction(txdata)
        logger.debug("ERC-20 transfer: %s", tx)
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        logger.debug("Transaction hash: %s", tx_hash)
        return tx_hash

    def wait_for_receipt(self, tx_hash, timeout=120):
        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)

