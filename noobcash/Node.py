from noobcash.Wallet import Wallet
from noobcash.Block import Block
from noobcash.Blockchain import Blockchain
from noobcash.Transaction import Transaction
from noobcash.TransactionOutput import TransactionOutput
from noobcash.utils import create_transaction, transaction_output_from_dict, transaction_from_dict


class Node:
    def __init__(self, blockchain=None):
        self.blockchain = blockchain
        self.ring = []
        self.wallet = Wallet()
        self.utxos_dict = {}

    def broadcast_transaction(self):
        ...
