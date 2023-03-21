from Crypto.Hash import SHA256
from time import time


class TransactionOutput:
    def __init__(self, transaction_id, recipient, amount):
        self.transaction_id = transaction_id
        self.recipient = recipient
        self.amount = amount
        self.unique_id = self.get_unique_id()

    def get_unique_id(self):
        value_to_hash = self.transaction_id + self.recipient + str(self.amount) + str(time())
        hash_object = SHA256.new(data=value_to_hash.encode())
        return hash_object.hexdigest()

    def __str__(self):
        return f"Transaction Id: {self.transaction_id} Recipient:{self.recipient} Amount: {self.amount} UniqueId: {self.unique_id}"

    def to_dict(self):
        res = {
            "transaction_id": self.transaction_id,
            "recipient": self.recipient,
            "amount": self.amount,
            "unique_id": self.unique_id,
        }
        return res
