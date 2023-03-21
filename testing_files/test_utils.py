from noobcash.Wallet import Wallet
from noobcash.Transaction import Transaction
from noobcash.TransactionOutput import TransactionOutput
from noobcash.utils import *


def test_transaction_to_dict():
    # Verify that the values on the Transaction dict are the same as the original ones in the Transaction Object
    w1 = Wallet()
    w2 = Wallet()
    initial_amount = 100
    transfer_amount = 10
    transaction_output1 = TransactionOutput("1", w1.address, initial_amount)
    transaction_output2 = TransactionOutput("50", w2.address, initial_amount)
    dict_of_utxos = {
        w1.public_key: [transaction_output1],
        w2.public_key: [transaction_output2],
    }
    transaction = create_transaction(w1, w2.public_key, transfer_amount, dict_of_utxos)
    transaction_dict = transaction.to_dict()
    assert transaction_dict["transaction_id"] == transaction.transaction_id
    assert transaction_dict["signature"] == transaction.signature
    assert transaction_dict["sender_address"] == transaction.sender_address
    assert transaction_dict["amount"] == transaction.amount
    for i in range(len(transaction_dict["transaction_inputs"])):
        assert transaction_dict["transaction_inputs"][i] == transaction.transaction_inputs[i]


def test_transaction_from_dict():
    # Verify that the transaction generated from a dict is the same as the original one
    w1 = Wallet()
    w2 = Wallet()
    initial_amount = 100
    transfer_amount = 10
    transaction_output1 = TransactionOutput("1", w1.address, initial_amount)
    transaction_output2 = TransactionOutput("50", w2.address, initial_amount)
    dict_of_utxos = {
        w1.public_key: [transaction_output1],
        w2.public_key: [transaction_output2],
    }
    transaction = create_transaction(w1, w2.public_key, transfer_amount, dict_of_utxos)
    transaction_dict = transaction.to_dict()
    transaction_2 = transaction_from_dict(transaction_dict)
    print("*"*100)
    print(transaction)
    print("*"*100)
    print(transaction_2)
    print("*"*100)
    assert transaction_2 == transaction
