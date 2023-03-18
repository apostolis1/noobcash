import blockchain
from time import time
from Crypto.Hash import SHA256
import random


class Block:
	def __init__(self):
		##set
		self.index = None
		self.previousHash = None
		self.timestamp = time()
		self.nonce = None
		self.current_hash = None
		self.list_of_transactions = []

	def add_transaction(self, transaction):
		#add a transaction to the block
		self.list_of_transactions.append(transaction)

	def is_full(self, capacity):
		#check if block has reached max capacity of transactions
		return len(self.list_of_transactions) == capacity

	def myHash(self, nonce):
		#calculate self.hash
		transaction_hash_list = [i.calculate_hash().hexdigest() for i in self.list_of_transactions]
		transaction_hash = ''.join(transaction_hash_list)
		value_to_hash = self.previousHash + transaction_hash + nonce 
		hash_object = SHA256.new(data=value_to_hash.encode())
		return hash_object.hexdigest()
	
	def get_nonce(self, difficulty):
		#try random values until block is valid
		nonce_attempt = 0
		while(not self.myHash(nonce_attempt).startswith('0'*difficulty)):
			nonce_attempt = random.random()
		self.nonce = nonce_attempt
		self.current_hash = self.myHash(self.nonce)
		return

	def validate_block(self,difficulty):
		#validate the block of transactions
		if (self.current_hash.startswith('0'*difficulty)):
			return True
		return False