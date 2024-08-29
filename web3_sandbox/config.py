from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


_CONFIG = Path(__file__).parent / "config.json"


class Config:
    __config = None

    @classmethod
    def get(cls, component: str) -> dict:
        """Get the dictionary of settings for the specific component."""
        if not cls.__config:
            with open(_CONFIG, "r") as f:
                cls.__config = json.load(f)

        assert cls.__config, f"Could not load config from {_CONFIG}"
        try:
            return cls.__config[component]
        except KeyError as e:
            raise KeyError(f"Configuration for `{component}` not found in `{_CONFIG}`") from e

    @classmethod
    def path(cls):
        """Get the config file path."""
        return _CONFIG


@dataclass
class PaymentNetworkConfig:
    """Set of configuration values related to a single Ethereum network."""

    network_name: str
    node_address: str
    glm_contract_address: str
    geth_poa_middleware: bool = False


class PaymentConfig:
    __CONFIG_KEY = "payment_networks"

    @classmethod
    def _get_config(cls) -> dict:
        """Get the dictionary of all Ethereum network configurations."""
        return Config.get(cls.__CONFIG_KEY)

    @classmethod
    def for_network(cls, network_name: str) -> PaymentNetworkConfig:
        """Get the configuration for a given Ethereum network."""
        try:
            config_kwargs = cls._get_config()[network_name]
        except KeyError:
            raise KeyError(
                f"`{network_name}` not defined in {cls.__CONFIG_KEY} of {Config.path()}`"
            )

        logger.debug("Payment network config [%s]: %s", network_name, config_kwargs)
        return PaymentNetworkConfig(network_name=network_name, **config_kwargs)

    @classmethod
    def network_names(cls) -> List[str]:
        return list(cls._get_config().keys())
