from dataclasses import dataclass
from decimal import Decimal
from json.decoder import JSONDecodeError
import logging
from pathlib import Path
import requests  # type: ignore
from typing import Optional, TYPE_CHECKING
from web3 import Web3
from web3.middleware import geth_poa_middleware

from eth_account.signers.local import LocalAccount


ERC20_ABI_FILE = Path(__file__).parent / "erc20abi.json"

logger = logging.getLogger(__name__)


def wei_to_ether(value) -> Decimal:
    return Decimal(Web3.fromWei(value, "ether"))


def ether_to_wei(value: Decimal) -> int:
    return Web3.toWei(value, "ether")


@dataclass
class PaymentNetworkConfig:
    """Set of configuration values related to a single Ethereum network."""

    network_name: str
    node_address: str
    glm_contract_address: str
    geth_poa_middleware: bool = False


class PaymentClient():
    def __init__(self, config: "PaymentNetworkConfig"):
        self._config = config

    @property
    def network_name(self) -> str:
        return self._config.network_name

    def use_private_key(self, key: str, key_password: str):
        self.account = self.w3.eth.account.from_key(self.w3.eth.account.decrypt(key, key_password))


# class Erc20(PaymentClient):
#     def __init__(self, config: "PaymentNetworkConfig", gas_price_gwei: Optional[str] = None):
#         super().__init__(config)
#         self.w3 = Web3(Web3.HTTPProvider(self._config.geth_address))
#         self.gas_price_wei = Web3.toWei(Decimal(gas_price_gwei), "gwei") if gas_price_gwei else None
#
#         # optionally inject a middleware needed for the client to work correctly with a POA chain
#         if self._config.geth_poa_middleware:
#             self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
#
#         assert self.w3.isConnected()
#
#         self.account: Optional[LocalAccount] = None
#
#         with open(ERC20_ABI_FILE, "r") as f:
#             self.glm_contract = self.w3.eth.contract(  # type: ignore
#                 self._config.glm_contract_address, abi=f.read()
#             )
#
#
#     @property
#     def glm(self):
#         """Interface for the functions exposed by the GLM contract."""
#         return self.glm_contract.functions
#
#     @property
#     def address(self) -> str:
#         assert self.account
#         return self.account.address
#
#     @property
#     def eth_required_for_transfer_ether(self):
#         gas_limit = 47563
#         gas_price = self.gas_price_wei or self.w3.eth.gas_price
#         return Decimal(Web3.fromWei(gas_limit * gas_price, "ether"))
#
#     def send_glm(self, address: str, amount_wei: int):
#         assert self.account
#         nonce = self.w3.eth.get_transaction_count(self.address)
#         txdata = {"from": self.address, "nonce": nonce}
#         if self.gas_price_wei:
#             txdata["gasPrice"] = self.gas_price_wei
#         tx = self.glm.transfer(address, amount_wei).buildTransaction(txdata)
#         logger.debug("ERC-20 transfer: %s", tx)
#         signed_tx = self.account.sign_transaction(tx)
#         tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
#         logger.debug("Transaction hash: %s", tx_hash)
#         return tx_hash
#
#     def wait_for_receipt(self, tx_hash, timeout=120):
#         return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
