from abc import ABC, abstractmethod
from decimal import Decimal
from json.decoder import JSONDecodeError
import logging
from pathlib import Path
import requests  # type: ignore
from typing import Optional, TYPE_CHECKING
from web3 import Web3
from web3.middleware import geth_poa_middleware

from eth_account.signers.local import LocalAccount

if TYPE_CHECKING:
    from airdropper.config import PaymentNetworkConfig


ERC20_ABI_FILE = Path(__file__).parent / "erc20abi.json"

logger = logging.getLogger(__name__)


def wei_to_ether(value) -> Decimal:
    return Decimal(Web3.fromWei(value, "ether"))


def ether_to_wei(value: Decimal) -> int:
    return Web3.toWei(value, "ether")


class PaymentClient(ABC):
    def __init__(self, config: "PaymentNetworkConfig"):
        self._config = config

    @property
    def network_name(self) -> str:
        return self._config.network_name

    @property
    @abstractmethod
    def address_property(self) -> str:
        pass


class ZkSync(PaymentClient):
    def get_balance_wei(self, address: str, num_tries: int = 3) -> Optional[int]:
        """The current GLM balance on zkSync for the given address, denominated in wei."""
        r = None
        uri = f"{self.api_url}/accounts/{address}/committed"
        for t in range(num_tries):
            try:
                r = requests.get(uri, timeout=10)
                break
            except Exception as e:
                retrying = t + 1 < num_tries
                logger.warning(
                    "Error retrieving zkSync balance %s, %s.",
                    address,
                    "retrying" if retrying else "this was the final try",
                )
                logger.debug("uri: %s, exception %s(%s)", uri, type(e), e)

        if not r:
            return None

        try:
            return int(r.json().get("result").get("balances").get(self.glm_symbol))
        except (AttributeError, TypeError, JSONDecodeError):
            logger.debug(
                "Unable to retrieve zkSync balance from the API response. "
                "uri: %s, status code: %s, response body: %s",
                uri,
                r.status_code,
                r.text,
            )
            return None

    @property
    def api_url(self):
        return self._config.zksync_api_url

    @property
    def glm_symbol(self):
        return self._config.zksync_glm_symbol

    @property
    def address_property(self) -> str:
        return self._config.zksync_address_property


class Erc20(PaymentClient):
    def __init__(self, config: "PaymentNetworkConfig", gas_price_gwei: Optional[str] = None):
        super().__init__(config)
        self.w3 = Web3(Web3.HTTPProvider(self._config.geth_address))
        self.gas_price_wei = Web3.toWei(Decimal(gas_price_gwei), "gwei") if gas_price_gwei else None

        # optionally inject a middleware needed for the client to work correctly with a POA chain
        if self._config.geth_poa_middleware:
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        assert self.w3.isConnected()

        self.account: Optional[LocalAccount] = None

        with open(ERC20_ABI_FILE, "r") as f:
            self.glm_contract = self.w3.eth.contract(  # type: ignore
                self._config.glm_contract_address, abi=f.read()
            )

    def use_private_key(self, key: str, key_password: str):
        self.account = self.w3.eth.account.from_key(self.w3.eth.account.decrypt(key, key_password))

    @property
    def address_property(self) -> str:
        return self._config.erc20_address_property

    @property
    def glm(self):
        """Interface for the functions exposed by the GLM contract."""
        return self.glm_contract.functions

    @property
    def address(self) -> str:
        assert self.account
        return self.account.address

    @property
    def eth_required_for_transfer_ether(self):
        gas_limit = 47563
        gas_price = self.gas_price_wei or self.w3.eth.gas_price
        return Decimal(Web3.fromWei(gas_limit * gas_price, "ether"))

    def send_glm(self, address: str, amount_wei: int):
        assert self.account
        nonce = self.w3.eth.get_transaction_count(self.address)
        txdata = {"from": self.address, "nonce": nonce}
        if self.gas_price_wei:
            txdata["gasPrice"] = self.gas_price_wei
        tx = self.glm.transfer(address, amount_wei).buildTransaction(txdata)
        logger.debug("ERC-20 transfer: %s", tx)
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        logger.debug("Transaction hash: %s", tx_hash)
        return tx_hash

    def wait_for_receipt(self, tx_hash, timeout=120):
        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
