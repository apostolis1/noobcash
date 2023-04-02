# from noobcash.Wallet import Wallet
# from noobcash.Transaction import Transaction
# from noobcash.TransactionOutput import TransactionOutput
from src.noobcash.utils import *
from random import randint


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
    assert transaction_dict["signature"] == transaction.signature.hex()
    assert transaction_dict["sender_address"] == transaction.sender_address
    assert transaction_dict["amount"] == transaction.amount
    for i in range(len(transaction_dict["transaction_inputs"])):
        assert transaction_output_from_dict(transaction_dict["transaction_inputs"][i]) == transaction.transaction_inputs[i]
    return

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
    return


def test_transaction_output_to_dict():
    # Verify that the TransactionOutput generated from a dict is the same as the original one
    wallet = Wallet()
    transaction_output_1 = TransactionOutput("1", wallet.address, 10)
    transaction_output_dict = transaction_output_1.to_dict()
    transaction_output_2 = transaction_output_from_dict(transaction_output_dict)
    assert transaction_output_1 == transaction_output_2
    return


def test_block_to_dict():
    # Verify that the Block generated from a dict is the same as the original one
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
    previous_hash = "random_hash"
    transaction = create_transaction(w1, w2.public_key, transfer_amount, dict_of_utxos)
    block = Block(0, previous_hash, list_of_transactions=[transaction], capacity=5)
    block_dict = block.to_dict()
    block_2 = block_from_dict(block_dict)
    assert block == block_2
    return


def test_blockchain_to_dict():
    # Verify that the Block generated from a dict is the same as the original one
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
    previous_hash = "random_hash"
    transaction = create_transaction(w1, w2.public_key, transfer_amount, dict_of_utxos)
    block = Block(0, previous_hash, list_of_transactions=[transaction], capacity=5)
    nodes = randint(1, 15)
    chain = [block]
    blockchain = Blockchain(nodes, chain, difficulty=3)
    blockchain_dict = blockchain.to_dict()
    blockchain_2 = blockchain_from_dict(blockchain_dict)
    assert blockchain == blockchain_2
    return


def test_utxos_from_genesis_blockchain():
    w1 = Wallet()
    nodes = randint(5, 15)
    blockchain = Blockchain(nodes, difficulty=3)
    blockchain.GenesisBlock(w1.address)
    utxos_dict = create_utxos_dict_from_transaction_list(blockchain.get_unspent_transaction_outputs())
    print(utxos_dict)
    assert len(utxos_dict[w1.address]) == 1
    assert sum([i.amount for i in utxos_dict[w1.address]]) == nodes*100
    return


def test_utxos_from_complex_blockchain():
    w1 = Wallet()
    w2 = Wallet()
    nodes = randint(1, 15)
    initial_amount = nodes*100
    amount_to_transfer = randint(1, initial_amount)
    blockchain = Blockchain(nodes)
    blockchain.GenesisBlock(w1.address)
    utxos_dict = create_utxos_dict_from_transaction_list(blockchain.get_unspent_transaction_outputs())
    t = create_transaction(w1, w2.address, amount_to_transfer, utxos_dict)
    last_block: Block = blockchain.getLastBlock()
    last_block.add_transaction(t)
    utxos_dict = create_utxos_dict_from_transaction_list(blockchain.get_unspent_transaction_outputs())
    print(utxos_dict)
    assert len(utxos_dict[w1.address]) == 1
    assert len(utxos_dict[w2.address]) == 1
    assert sum([i.amount for i in utxos_dict[w1.address]]) + sum([i.amount for i in utxos_dict[w2.address]]) == initial_amount
    # assert sum([i.amount for i in utxos_dict[w1.address]]) == nodes * 100
    return