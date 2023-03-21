from time import time
from Crypto.Hash import SHA256
import random


class Block:
	def __init__(self, index=0, previous_hash='', nonce=0, current_hash=None, list_of_transactions=[], timestamp=None):
		self.index = index
		self.previousHash = previous_hash
		if timestamp is not None:
			self.timestamp = timestamp
		else:
			self.timestamp = time()
		self.nonce = nonce
		self.current_hash = current_hash
		self.list_of_transactions = list_of_transactions
		# self.capacity = None ##pos mporo na paro tin parametro capacity apto config.py?

	def is_full(self, capacity):
		# check if block has reached max capacity of transactions
		return len(self.list_of_transactions) == capacity
	
	def add_transaction(self, transaction):
		# add a transaction to the block
		# if (not self.is_full(self.capacity)):
		self.list_of_transactions.append(transaction)

	def my_hash(self, nonce):
		# calculate self.hash
		transaction_hash_list = [i.calculate_hash().hexdigest() for i in self.list_of_transactions]
		transaction_hash = ''.join(transaction_hash_list)
		value_to_hash = self.previousHash + transaction_hash + str(nonce)
		hash_object = SHA256.new(data=value_to_hash.encode())
		return hash_object.hexdigest()
	
	def get_nonce(self, difficulty):
		# try random values until block is valid
		nonce_attempt = 0
		while not self.my_hash(nonce_attempt).startswith('0' * difficulty):
			nonce_attempt = random.random()
		self.nonce = nonce_attempt
		self.current_hash = self.my_hash(self.nonce)
		return

	def validate_block(self, difficulty):
		# validate the block of transactions
		return self.current_hash.startswith('0' * difficulty)

	def to_dict(self):
		res = {
			"index": self.index,
			"previousHash": self.previousHash,
			"timestamp": self.timestamp,
			"nonce": self.nonce,
			"current_hash": self.current_hash,
			"transactions": [i.to_dict() for i in self.list_of_transactions]
		}
		return res

	def __eq__(self, other):
		if not isinstance(other, Block):
			return False
		if not self.index == other.index and self.nonce == other.nonce and self.timestamp == other.timestamp and self.current_hash == other.current_hash and self.previousHash == other.previousHash:
			return False
		for i in self.list_of_transactions:
			if i not in other.list_of_transactions:
				return False
		return True
