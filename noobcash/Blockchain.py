from noobcash.Block import Block
import time
from noobcash.Transaction import Transaction
from noobcash.TransactionOutput import TransactionOutput


class Blockchain:
    def __init__(self, nodes, chain=None, capacity=None, difficulty=None) -> None:
        if chain is None:
            chain = []
        self.chain: list = chain
        self.nodes = nodes
        self.capacity = capacity
        self.difficulty = difficulty

    def GenesisBlock(self, bootstrap_address):
        genesis = Block(index=0, previous_hash='1', nonce=0, capacity=self.capacity)
        # TODO: Add transaction_inputs
        genesis_transaction = Transaction(sender_address = '0', recipient_address = bootstrap_address, value = 100*self.nodes, transaction_inputs=[])
        genesis_transaction.transaction_outputs = [TransactionOutput(genesis_transaction.transaction_id, genesis_transaction.receiver_address, genesis_transaction.amount)]
        genesis.add_transaction(genesis_transaction)
        genesis.current_hash = genesis.my_hash(nonce = 0)
        self.chain.append(genesis)
        return

    def getLastBlock(self) -> Block:
        return self.chain[len(self.chain) - 1]

    def addBlock(self, newBlock : Block):
        self.chain.append(newBlock)
        return

    def add_transaction(self, t: Transaction) -> None:
        last_block = self.getLastBlock()
        # Check if last block is the genesis block
        if last_block.previousHash == '1' or last_block.is_full():
            new_block = Block(index=last_block.index+1, previous_hash=last_block.current_hash, capacity=self.capacity)
            self.addBlock(new_block)
            new_block.add_transaction(t)
        else:
            last_block.add_transaction(t)
        last_block = self.getLastBlock()
        if last_block.is_full():
            last_block.get_nonce(difficulty=self.difficulty)
        return

    def validate_chain(self):
        for idx, block in enumerate(self.chain[1:]):
            if not (block.validate_block(difficulty=self.difficulty) and self.chain[idx].current_hash == block.previousHash):
                return False
        return True

    def to_dict(self):
        chain_list = [i.to_dict() for i in self.chain]
        print(chain_list)
        res = {
            "chain": chain_list,
            "nodes": self.nodes,
            "capacity": self.capacity,
            "difficulty": self.difficulty
        }
        return res

    def __eq__(self, other):
        if not isinstance(other, Blockchain):
            return False
        for i, _ in enumerate(self.chain):
            if self.chain[i] != other.chain[i]:
                return False
        for i, _ in enumerate(other.chain):
            if self.chain[i] != other.chain[i]:
                return False
        return self.nodes == other.nodes

    def get_all_transactions(self):
        all_transactions = [i for j in self.chain for i in j.list_of_transactions]
        return all_transactions

    def get_all_transaction_outputs(self):
        all_transactions = self.get_all_transactions()
        res = []
        for transaction in all_transactions:
            for i in transaction.transaction_outputs:
                res.append(i)
        return res

    def get_used_transaction_outputs(self):
        # Return all outputs used as inputs to other transactions
        # TODO Make this faster with list collapse
        all_transactions = self.get_all_transactions()
        used_transaction_outputs = []
        for transaction in all_transactions:
            for i in transaction.transaction_inputs:
                used_transaction_outputs.append(i)
        return used_transaction_outputs

    def get_unspent_transaction_outputs(self):
        # TODO Make this faster with sets maybe
        all_transaction_outputs = self.get_all_transaction_outputs()
        used_transaction_outputs = self.get_used_transaction_outputs()
        unused_transaction_outputs = [i for i in all_transaction_outputs if i not in used_transaction_outputs]
        return unused_transaction_outputs
