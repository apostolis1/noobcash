from noobcash.Wallet import Wallet
from noobcash.Transaction import Transaction

receiver_wallet = Wallet()


wallet = Wallet()
# sender_address: str, sender_private_key: str, recipient_address: str, value):
transaction = Transaction(sender_address=wallet.public_key, recipient_address=receiver_wallet.public_key, value=5, transaction_inputs=[])
transaction.sign_transaction(wallet.private_key)
transaction.verify()
# print(wallet.public_key, wallet.private_key)
# print(transaction.signature)

wallet2 = Wallet()
# print(wallet2.public_key, wallet2.private_key)
transaction.sign_transaction(wallet2.private_key)
# print(transaction.signature)
transaction.verify()
