import sys

from noobcash.Wallet import Wallet
from noobcash.Block import Block
from noobcash.Blockchain import Blockchain
from noobcash.Transaction import Transaction
from noobcash.TransactionOutput import TransactionOutput
from noobcash.utils import create_transaction, transaction_output_from_dict, transaction_from_dict, block_from_dict
import requests
import time
import os
import signal
from copy import deepcopy
from threading import Thread, Event


class Node:
    def __init__(self, blockchain=None):
        self.blockchain: Blockchain = blockchain
        self.ring = {}
        self.wallet = Wallet()
        # Local copy of utxos only for the given node, we use it to create intermediate transactions
        # We only care about our own utxos here because these are the ones we can modify
        # Be careful to update this list accordingly eg on transaction creation and block addition
        self.my_utxos: list = []
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
            self.resolve_conflicts()
            # TODO: We probably need to resolve_conflicts here, careful with locks and events
            return
        # if block.validate_block(self.blockchain.difficulty) and self.blockchain.getLastBlock().current_hash == block.previousHash:
        if block.validate_block(self.blockchain.difficulty) and self.blockchain.can_block_be_added(block):
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
                self.my_utxos = deepcopy(self.blockchain.utxos_dict[self.wallet.address])
            except KeyError:
                self.my_utxos = []
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
        #TODO: check if we need a chain lock
        if self.blockchain.add_transaction(t):
            # transaction added filled the block, so I start mining
            child_process = Thread(target=self.mine_block)
            child_process.start()
        return

    def resolve_conflicts(self):
        # Get blockchain_length from all other nodes
        # Find the biggest chain
        #
        print("Resolving conflicts ...")
        lengths = {}
        for k, n in self.ring.items():
            if n['public_key'] == self.wallet.public_key:
                continue
            for _ in range(5):
                try:
                    url = f"http://{n['url']}/blockchain_length"
                    res = requests.get(url)
                    lengths[int(k.replace("id", ""))] = res.json()['length']
                    break
                except Exception as e:
                    print("Got exception")
                    print(e)
                    time.sleep(1)
        print(f"Got lengths: {lengths}")
        # Find biggest chain
        biggest_length = 1
        biggest_node_id = sys.maxsize
        for k,v in lengths.items():
            if v > biggest_length or (v == biggest_length and k < biggest_node_id):
                biggest_length = v
                biggest_node_id = k
        print(f"I will ask node id {biggest_node_id} with length {biggest_length} for the chain")
        # We don't need the whole chain, only the part where our chains differ
        # Send only hashes of block to the node with the biggest chain
        hashes_to_send = {"hashes": [i.current_hash for i in self.blockchain.chain]}
        url_base = self.ring[f"id{biggest_node_id}"]['url']
        url = f"http://{url_base}/blockchain_differences/"
        res = requests.post(url, json=hashes_to_send)
        if res.status_code != 200:
            print(f"Error when requesting {url}, status_code: {res.status_code}")
            print(res.content)
        res_json = res.json()

        new_chain = self.blockchain.chain[:res_json["conflict_idx"]]
        # Convert dict to block object
        second_part = [block_from_dict(b_dict) for b_dict in res_json["blocks"]]
        new_chain.extend(second_part)
        self.blockchain.chain = new_chain
        # TODO: need to check how to call pool and utxo locks
        self.transaction_pool = [transaction_from_dict(i) for i in res_json["transaction_pool"]]
        self.blockchain.utxos_dict = {k: [transaction_output_from_dict(i) for i in v] for k,v in res_json["blockchain_utxos"].items()}
        self.blockchain.current_block_utxos = {k: [transaction_output_from_dict(i) for i in v] for k,v in res_json["current_block_utxos"].items()}

        # print(self.blockchain.current_block_utxos)
        # self.blockchain.current_block_utxos = [transaction_output_from_dict(i) for i in res_json["current_block_utxos"]]
        # print(res_json)
        print(f"Last block current_hash after asking is {self.blockchain.getLastBlock().current_hash}")
        print("Resolve conflicts finished")
        return
