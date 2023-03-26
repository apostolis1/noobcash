from noobcash.Wallet import Wallet
from noobcash.Block import Block
from noobcash.Blockchain import Blockchain
from noobcash.Transaction import Transaction
from noobcash.TransactionOutput import TransactionOutput
from noobcash.utils import create_transaction, transaction_output_from_dict, transaction_from_dict
import requests
import time
import os
import signal
from threading import Thread, Event


class Node:
    def __init__(self, blockchain=None):
        self.blockchain = blockchain
        self.ring = {}
        self.wallet = Wallet()
        # Local copy of utxos only for the given node, we use it to create intermediate transactions
        # We only care about our own utxos here because these are the ones we can modify
        # Be careful to update this list accordingly eg on transaction creation and block addition
        self.utxos_list: list = []
        self.mining = False
        self.transaction_pool = []
        self.event = Event()
        self.event.clear()
        self.child_process_id = None

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
                    time.sleep(1)
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
            print("Block can't be placed at the end of blockchain")
            # TODO: We probably need to resolve_conflicts here, careful with locks and events
            return
        # if block.validate_block(self.blockchain.difficulty) and self.blockchain.getLastBlock().current_hash == block.previousHash:
        if block.validate_block(self.blockchain.difficulty):
            print("Received a valid block, will check if I am mining already")
            if self.mining:
                print("SET MINING TO FALSE")
                self.mining = False
                print("I am mining, will stop...")
                # TODO: stop thread that mines since I received another already mined block
                self.event.set()
                print("Set event to true")
                self.blockchain.current_block = None
            else:
                print("I am not mining, will add block")
            print(f"About to add block with hash {block.current_hash} at position {len(self.blockchain.chain)}")
            self.blockchain.addBlock(block)
            # Update our utxos list accordingly
            try:
                self.utxos_list = self.blockchain.utxos_dict[self.wallet.address]
            except KeyError:
                self.utxos_list = []
        return
    
    def mine_block(self):
        self.mining = True
        print("SET MINING TO TRUE")
        try:
            self.blockchain.current_block.get_nonce(self.blockchain.difficulty, self.event)
        except Exception as e:
            self.mining = False
            print("Stopped mining because someone stopped me, setting mining to false and exiting without broadcasting")
            return
        # Not sure about this, but we need to somehow change the variables that indicate that we are mining
        self.mining = False
        print("SET MINING TO FALSE")
        print(f"Finished mining and about to broadcast, hash is {self.blockchain.current_block.current_hash}")
        self.broadcast_block(self.blockchain.current_block)
        return

    def add_transaction(self, t: Transaction):
        if self.blockchain.add_transaction(t):
            # transaction added filled the block, so I start mining
            child_process = Thread(target=self.mine_block)
            child_process.start()
        return
