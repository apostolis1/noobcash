from noobcash.Block import Block
import time
from noobcash.Transaction import Transaction

class Blockchain:
    def __init__(self, nodes) -> None:
        self.chain = []
        self.nodes = nodes

    def GenesisBlock(self, bootstrap_address):
        genesis = Block(index=0, previous_hash='1', nonce = 0)
        # TODO: Add transaction_inputs
        genesis_transaction = Transaction(sender_address = '0', recipient_address = bootstrap_address, value = 100*self.nodes, transaction_inputs=[])
        genesis.add_transaction(genesis_transaction)
        genesis.current_hash = genesis.my_hash(nonce = 0)
        self.chain.append(genesis)
        return

    def getLastBlock(self):
        return self.chain[len(self.chain) - 1]

    def addBlock(self, newBlock : Block):
        if (newBlock.is_full()):
            self.chain.append(newBlock)
        return
    
    def validate_chain(self):
        for idx, block in enumerate(self.chain[1:]):
            if (not (block.validate_block() and self.chain[idx-1].current_hash == block.previousHash)):
                return False
        return True
            