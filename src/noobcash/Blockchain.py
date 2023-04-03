import threading

from noobcash.Block import Block
import time
from noobcash.Transaction import Transaction
from noobcash.TransactionOutput import TransactionOutput
from copy import deepcopy
from typing import List


class Blockchain:
    def __init__(self, nodes, chain=None, capacity=None, difficulty=None, utxos_dict=None) -> None:
        if chain is None:
            chain = []
        self.chain: List[Block] = chain
        self.nodes = nodes
        self.capacity = capacity
        self.difficulty = difficulty
        # Keep track of new block, has to be mined and verified before being added to the blockchain
        self.current_block = None
        # Keep track of the valid utxos for each node, this could also be derived from traversing the whole chain
        # However this is slow and should only be done when absolutely necessary, so update them each time a block is
        # added
        self.current_block_utxos = {}
        if utxos_dict is None:
            self.utxos_dict = {}
        else:
            self.utxos_dict = utxos_dict

    def GenesisBlock(self, bootstrap_address):
        genesis = Block(index=0, previous_hash='1', nonce=0, capacity=self.capacity)
        # TODO: Add transaction_inputs
        genesis_transaction = Transaction(sender_address = '0', recipient_address = bootstrap_address, value = 100*self.nodes, transaction_inputs=[])
        genesis_transaction.transaction_outputs = [TransactionOutput(genesis_transaction.transaction_id, genesis_transaction.receiver_address, genesis_transaction.amount)]
        genesis.add_transaction(genesis_transaction)
        genesis.current_hash = genesis.my_hash(nonce = 0)
        self.chain.append(genesis)
        # Update the utxos_dict
        self.utxos_dict[bootstrap_address] = deepcopy(genesis_transaction.transaction_outputs)
        return

    def getLastBlock(self) -> Block:
        return self.chain[len(self.chain) - 1]

    def addBlock(self, newBlock: Block):
        # When adding a block to the chain we also want to update the utxos of the blockchain
        # This assumes that we already checked that the transactions of the block we are adding
        # are valid, meaning checking the utxos of the blockchain
        # Update transactions
        for transaction in newBlock.list_of_transactions:
            for t_input in transaction.transaction_inputs:
                try:
                    self.utxos_dict[t_input.recipient].remove(t_input)
                except Exception as e:
                    print("Cant find it")
                    print(e)
                    raise e
            for t_output in transaction.transaction_outputs:
                print(f"Adding output {t_output.unique_id} to recipient {t_output.recipient[-4:]}")
                try:
                    self.utxos_dict[t_output.recipient].append(t_output)
                except KeyError:
                    self.utxos_dict[t_output.recipient] = [t_output]
        # Finally add the block to the chain
        self.chain.append(newBlock)
        return

    def can_block_be_added(self, b: Block):
        previous_utxos = deepcopy(self.utxos_dict)
        # for k, v in previous_utxos.items():
        #     print(k)
        #     for i in v:
        #         print(i)

        for t in b.list_of_transactions:
            for t_input in t.transaction_inputs:
                try:
                    previous_utxos[t_input.recipient].remove(t_input)
                except Exception as e:
                    print("BLOCK CANT BE ADDED")
                    print(e)
                    print(t_input)
                    return False
            for t_output in t.transaction_outputs:
                try:
                    previous_utxos[t_output.recipient].append(t_output)
                except KeyError:
                    previous_utxos[t_output.recipient] = [t_output]
        return True

    def can_transaction_be_added(self, t: Transaction) -> bool:
        # Check to see if the transaction can be added to the current_block by making sure that the
        # inputs are indeed unspent
        for t_input in t.transaction_inputs:
            try:
                if t_input not in self.current_block_utxos[t_input.recipient]:
                    return False
            except KeyError:
                return False
        return True

    def add_transaction(self, t: Transaction) -> bool:
        # Returns True if we need to start mining
        # TODO: Check if this condition is correct, maybe checks are required in additional places
        if self.current_block is None or self.getLastBlock() == self.current_block:
            print("Creating a new current_block and adding transaction there")
            last_block = self.getLastBlock()
            new_block = Block(index=last_block.index + 1, previous_hash=last_block.current_hash, capacity=self.capacity)
            self.current_block_utxos = deepcopy(self.utxos_dict)
            # If the transaction is not valid for the given current_block state, return False without adding it
            if not self.can_transaction_be_added(t):
                print(f"Discarded transaction with amount {t.amount}")
                return False
            new_block.add_transaction(t)
            print(f"Added transaction with amount {t.amount}")
            
            # Update the current_block_utxos
            for t_input in t.transaction_inputs:
                self.current_block_utxos[t_input.recipient].remove(t_input)
            for t_output in t.transaction_outputs:
                try:
                    self.current_block_utxos[t_output.recipient].append(t_output)
                except KeyError:
                    self.current_block_utxos[t_output.recipient] = [t_output]
            self.current_block = new_block
        else:

            print("Appending to current block...")
            if self.current_block is not None:
                print("... Because current block is not None")
            # If the transaction is not valid for the given current_block state, return False without adding it
            if not self.can_transaction_be_added(t):
                print(f"Discarded transaction with amount {t.amount}")
                return False
            self.current_block.add_transaction(t)
            # print(f"Added transaction with amount {t.amount}")
            # Update the current_block_utxos
            for t_input in t.transaction_inputs:
                self.current_block_utxos[t_input.recipient].remove(t_input)
            for t_output in t.transaction_outputs:
                try:
                    self.current_block_utxos[t_output.recipient].append(t_output)
                except KeyError:
                    self.current_block_utxos[t_output.recipient] = [t_output]
        if self.current_block.is_full():
            #last_block.get_nonce(difficulty=self.difficulty)
            return True
            # TODO: We want a new thread to do that, but we need to be careful of new transactions arriving
            # threading.Thread(target=last_block.get_nonce, args=[self.difficulty]).start()
        return False

    def validate_chain(self):
        """

        :return:
        """
        # Check hashes
        for idx, block in enumerate(self.chain[1:]):
            if not (block.validate_block(difficulty=self.difficulty) and self.chain[idx].current_hash == block.previousHash):
                return False
        # Check that utxos are indeed unspent throughout the blockchain
        _utxos = {
        }
        genesis_transaction = self.chain[0].list_of_transactions[0]
        _utxos[genesis_transaction.receiver_address] = [genesis_transaction.transaction_outputs[0]]
        for b in self.chain[1:]:
            for t in b.list_of_transactions:
                for t_input in t.transaction_inputs:
                    try:
                        _utxos[t_input.recipient].remove(t_input)
                    except Exception as e:
                        print("BLOCK IS NOT VALID")
                        print(e)
                        print(t_input)
                        return False
                for t_output in t.transaction_outputs:
                    try:
                        _utxos[t_output.recipient].append(t_output)
                    except KeyError:
                        _utxos[t_output.recipient] = [t_output]

        return True

    def to_dict(self):
        chain_list = [i.to_dict() for i in self.chain]
        # print(chain_list)
        res = {
            "chain": chain_list,
            "nodes": self.nodes,
            "capacity": self.capacity,
            "difficulty": self.difficulty,
            "utxos_dict": {
                k: [i.to_dict() for i in v] for k, v in self.utxos_dict.items()
            }
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
