import click
from web3 import Web3, HTTPProvider


@click.group()
def _cli():
    pass


@_cli.command(help="test the connection, using a given address")
@click.option(
    "--node-address",
    type=str,
    default="https://geth.golem.network:55555",
    # default="https://rpc.ankr.com/eth_holesky",
)
@click.argument(
    "wallet_address",
    default="0xb929ac45b74e182b287d9ce1142e5bda76d1a3d0"
)
def test(node_address: str, wallet_address: str):
    wallet_address = Web3.to_checksum_address(wallet_address)
    w3 = Web3(HTTPProvider(node_address))
    print(Web3.from_wei(w3.eth.get_balance(wallet_address), "ether"))
    #print(w3.eth.get_logs({"fromBlock": "0x10369d2", "toBlock": "0x10369d2","address": "0x7DD9c5Cba05E151C895FDe1CF355C9A1D5DA6429","topics": ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"]}))


if __name__ == "__main__":
    _cli()
