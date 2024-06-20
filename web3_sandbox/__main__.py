import click
from web3 import Web3, HTTPProvider


@click.group()
def _cli():
    pass


@_cli.command(help="test the connection, using a given address")
@click.option(
    "--node-address",
    type=str,
    default="https://rpc.ankr.com/eth_holesky",
)
@click.argument(
    "wallet_address",
    default="0xb929ac45b74e182b287d9ce1142e5bda76d1a3d0"
)
def test(node_address: str, wallet_address: str):
    wallet_address = Web3.to_checksum_address(wallet_address)
    w3 = Web3(HTTPProvider(node_address))
    print(Web3.from_wei(w3.eth.get_balance(wallet_address), "ether"))
