from src.noobcash.Transaction import Transaction
from src.noobcash.TransactionOutput import TransactionOutput
from src.noobcash.utils import create_transaction, print_utxos
from src.noobcash.Wallet import Wallet


def test_transaction_creation():
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
    print_utxos(dict_of_utxos)
    assert len(transaction.transaction_outputs) == 2
    balance_of_wallet1 = sum([i.amount for i in dict_of_utxos[w1.public_key]])
    balance_of_wallet2 = sum([i.amount for i in dict_of_utxos[w2.public_key]])
    assert balance_of_wallet1 == initial_amount - transfer_amount
    assert balance_of_wallet2 == initial_amount + transfer_amount
    print(transaction)
