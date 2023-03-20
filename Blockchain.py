from Block import Block
import time
from Transaction import Transaction

class Blockchain:
    
    def __init__(self, nodes) -> None:
        self.chain = []
        self.nodes = nodes

    def GenesisBlock(self, bootstrap_address):
        genesis = Block(index=0, previousHash = 1, nonce = 0)  
        genesis_transaction = Transaction(sender_address = '0', recipient_address = bootstrap_address, value = 100*self.nodes)
        genesis.add_transaction(genesis_transaction)
        self.chain.append(genesis)
        return

    def getLastBlock(self):
        return self.chain[len(self.chain) - 1]

    def addBlock(self, newBlock : Block):
        if (newBlock.is_full()):
            self.chain.append(newBlock)
        return