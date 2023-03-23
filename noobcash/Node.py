from noobcash.Wallet import Wallet
from noobcash.Block import Block
from noobcash.Blockchain import Blockchain
from noobcash.Transaction import Transaction
from noobcash.TransactionOutput import TransactionOutput
from noobcash.utils import create_transaction, transaction_output_from_dict, transaction_from_dict
import requests
import time


class Node:
    def __init__(self, blockchain=None):
        self.blockchain = blockchain
        self.ring = {}
        self.wallet = Wallet()
        self.utxos_dict = {}

    def broadcast_transaction(self, transaction: Transaction):
        # Transform the given transaction to a dict to be sent via the rest api
        # Send it to the corresponding api endpoint for each node in the ring
        transaction_dict = transaction.to_dict()
        for node in self.ring.values():
            for _ in range(5):
                try:
                    url = f"http://{node['url']}/transactions/create"
                    requests.post(url, json=transaction_dict)
                    break
                except Exception as e:
                    time.sleep(2)
        return
