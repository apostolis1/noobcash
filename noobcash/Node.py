from noobcash.Wallet import Wallet
from noobcash.Block import Block
from noobcash.Blockchain import Blockchain
from noobcash.Transaction import Transaction
from noobcash.TransactionOutput import TransactionOutput
from noobcash.utils import create_transaction, transaction_output_from_dict, transaction_from_dict
import requests
import time
from threading import Thread, Event

from noobcash.myEvent import SerializableEvent


class Node:
    def __init__(self, blockchain=None):
        self.blockchain = blockchain
        self.ring = {}
        self.wallet = Wallet()
        self.utxos_dict = {}
        self.mining = False
        self.transaction_pool = []
        # self.mining_thread = None
        self.event = None

    def broadcast_transaction(self, transaction: Transaction):
        # Transform the given transaction to a dict to be sent via the rest api
        # Send it to the corresponding api endpoint for each node in the ring
        transaction_dict = transaction.to_dict()
        for node in self.ring.values():
            for _ in range(5):
                try:
                    url = f"http://{node['url']}/transactions/create"
                    res = requests.post(url, json=transaction_dict)
                    break
                except Exception as e:
                    print("Got exception")
                    print(e)
                    time.sleep(2)
        return

    def broadcast_block(self, block: Block):
        # Transform the given transaction to a dict to be sent via the rest api
        # Send it to the corresponding api endpoint for each node in the ring
        block_dict = block.to_dict()
        print(f"I am about to start broadcasting block with hash {block.current_hash}")
        for node in self.ring.values():
            for _ in range(5):
                try:
                    url = f"http://{node['url']}/block/get"
                    requests.post(url, json=block_dict)
                    print(f"Successfully sent block with hash {block.current_hash} to {node['url']}")
                    break
                except Exception as e:
                    print(f"Exception at broadcast_block, {e}")
                    time.sleep(2)
        return
    
    def add_block_to_blockchain(self, block: Block):
        if block.previousHash != self.blockchain.getLastBlock().current_hash:
            return
        # if block.validate_block(self.blockchain.difficulty) and self.blockchain.getLastBlock().current_hash == block.previousHash:
        if block.validate_block(self.blockchain.difficulty):
            # self.event.set()
            print(f"Event object: {self.event}")
            print("Received a valid block, will check if I am mining already")
            if self.mining:
                self.mining = False
                print("I am mining, will stop...")
                # TODO: stop thread that mines since I received another already mined block
                self.event.set()
                if self.event.is_set():
                    print("Local event here is set")
                self.blockchain.current_block = None
            else:
                print("I am not mining, will add block")
            print(f"About to add block with hash {block.current_hash} at position {len(self.blockchain.chain)}")
            self.blockchain.addBlock(block)
        return
    
    def mine_block(self, ):
        self.mining = True
        self.event = SerializableEvent()
        print(f"Init event object at: {self.event}")
        # self.event = Event()
        self.event.clear()

        self.blockchain.current_block.get_nonce(self.blockchain.difficulty, self.event)
        print(f"Finished mining and about to broadcast, hash is {self.blockchain.current_block.current_hash}")
        # Not sure about this, but we need to somehow change the variables that indicate that we are mining
        self.mining = False
        self.event.set()
        self.broadcast_block(self.blockchain.current_block)
        return

    def add_transaction(self, t: Transaction):
        if self.blockchain.add_transaction(t):
            # transaction added filled the block, so I start mining
            mining_thread = Thread(target=self.mine_block)
            mining_thread.start()
        return
