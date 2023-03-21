from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
# from Crypto.Cipher import PKCS1_v1_5
from noobcash.TransactionOutput import TransactionOutput


class Transaction:

    def __init__(self, sender_address: str, recipient_address: str, value: int, transaction_inputs: list,transaction_id="1", signature=None, transaction_outputs=[]):
        # Transaction()
        self.sender_address = sender_address
        self.receiver_address = recipient_address
        self.amount = value
        self.signature = signature
        self.transaction_id = transaction_id
        self.transaction_inputs = transaction_inputs
        self.transaction_outputs = transaction_outputs
        # self.sender_address: To public key του wallet από το οποίο προέρχονται τα χρήματα
        # self.receiver_address: To public key του wallet στο οποίο θα καταλήξουν τα χρήματα
        # self.amount: το ποσό που θα μεταφερθεί
        # self.transaction_id: το hash του transaction
        # self.transaction_inputs: λίστα από Transaction Input
        # self.transaction_outputs: λίστα από Transaction Output
        # Transaction Output = (unique id, id transaction, recipient, amount)
        # unique_id = node_id +
        # selfSignature

    def to_dict(self):
        res = {
            "sender_address": self.sender_address,
            "receiver_address": self.receiver_address,
            "amount": self.amount,
            "signature": self.signature,
            "transaction_id":  self.transaction_id,
            "transaction_inputs":  self.transaction_inputs,
            "transaction_outputs": [i.to_dict() for i in self.transaction_outputs]
        }
        return res

    def calculate_hash(self):
        value_to_hash = self.sender_address + self.receiver_address + str(self.amount)
        hash_object = SHA256.new(data=value_to_hash.encode())
        return hash_object

    def sign_transaction(self, private_key):
        #
        # Sign transaction with private key
        #
        transaction_hash = self.calculate_hash()
        # Encrypt hash using the private key
        rsa_key = RSA.importKey(private_key)
        signature = pkcs1_15.new(rsa_key).sign(transaction_hash)
        self.signature = signature
        print("Changed signature...")
        return

    def verify(self):
        public_key = RSA.importKey(self.sender_address)
        transaction_hash = self.calculate_hash()
        try:
            pkcs1_15.new(public_key).verify(transaction_hash, self.signature)
            print("The signature is valid.")
        except (ValueError, TypeError):
            print("The signature is NOT valid.")
        return

    @staticmethod
    def find_transaction_inputs_for_amount(list_of_utxos, amount):
        # Find a list of transaction outputs to create the amount we want to send
        # Greedy algorithm
        found = 0
        i = 0
        utxos_used = []
        while found < amount and i < len(list_of_utxos):
            found += list_of_utxos[i].amount
            utxos_used.append(list_of_utxos[i])
            i += 1
        if found < amount:
            print(f"Not enough money, found {found} but needed {amount}")
            return []
        return utxos_used

    def create_transaction_outputs(self, sender_amount_before):
        recipient_output = TransactionOutput(self.transaction_id, self.receiver_address, self.amount)
        sender_output = TransactionOutput(self.transaction_id, self.sender_address, sender_amount_before - self.amount)
        return [recipient_output, sender_output]

    def __eq__(self, other):
        if not isinstance(other, Transaction):
            return False
        if not self.transaction_id == other.transaction_id and self.amount == other.amount and self.sender_address == other.sender_address and self.signature == other.signature:
            return False
        for i in self.transaction_inputs:
            if i not in other.transaction_inputs:
                return False
        for i in self.transaction_outputs:
            if i not in other.transaction_outputs:
                return False
        return True

    def __str__(self):
        return f"sender_address: {self.sender_address}, receiver_address: {self.receiver_address}, amount: {self.amount}, signature: {self.signature}"
