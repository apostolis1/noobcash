from noobcash.Wallet import Wallet
from noobcash.Block import Block
from noobcash.Blockchain import Blockchain
from noobcash.Transaction import Transaction
from noobcash.TransactionOutput import TransactionOutput
from noobcash.utils import create_transaction, transaction_output_from_dict, transaction_from_dict
import requests
import time
from threading import Thread, Event


class Node:
    def __init__(self, blockchain=None):
        self.blockchain = blockchain
        self.ring = {}
        self.wallet = Wallet()
        self.utxos_dict = {}
        self.mining = False
        self.transaction_pool = []
        self.mining_thread = None
        self.event = None

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

    def broadcast_block(self, block: Block):
        # Transform the given transaction to a dict to be sent via the rest api
        # Send it to the corresponding api endpoint for each node in the ring
        block_dict = block.to_dict()
        for node in self.ring.values():
            for _ in range(5):
                try:
                    url = f"http://{node['url']}/block/get"
                    requests.post(url, json=block_dict)
                    break
                except Exception as e:
                    time.sleep(2)
        return
    
    
    def add_block_to_blockchain(self, block: Block):
        if block.validate_block() and self.blockchain.getLastBlock.current_hash == block.previousHash:
            if self.mining == True:           
                self.mining = False
                # TODO: stop thread that mines since I received another already mined block
                self.event.set()
            self.blockchain.addBlock(block)
        return
    
    def mine_block(self):
        self.mining = True
        self.event = Event()
        self.mining_thread = Thread(target=self.blockchain.getLastBlock().get_nonce, args=[self.blockchain.difficulty, self.event])
        self.mining_thread.start()
        return

    def add_transaction (self, t : Transaction):
        if self.blockchain.add_transaction(t):
            #transaction added filled the block, so I start mining
            self.mine_block()
            self.broadcast_block(self.blockchain.getLastBlock())
        return  