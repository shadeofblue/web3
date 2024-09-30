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


logger = logging.getLogger(__name__)


def wei_to_ether(value) -> Decimal:
    return Decimal(Web3.from_wei(value, "ether"))


def ether_to_wei(value: Decimal) -> int:
    return Web3.to_wei(value, "ether")


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

