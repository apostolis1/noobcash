import blockchain



class Block:
	def __init__(self):
		##set
		self.index = None
		self.previousHash = None
		self.timestamp = None
		self.nonce = get_nonce()
		self.current_hash = self.myHash()
		self.nonce = None
		self.list_of_transactions = None
	
	def myHash:
		#calculate self.hash


	def add_transaction(transaction transaction, blockchain blockchain):
		#add a transaction to the block