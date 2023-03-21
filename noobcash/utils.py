from noobcash.Blockchain import Blockchain
from noobcash.Wallet import Wallet
from noobcash.Transaction import Transaction
from noobcash.TransactionOutput import TransactionOutput


def create_transaction(sender_wallet: Wallet, receiver_address, amount, utxos_dict: dict):
    # utxos_dict = {
    #   address1: [utxo0, utxo1 ,...],
    #   address2: [utxo0, utxo1, ...],
    #   }
    #
    sender_utxos = utxos_dict[sender_wallet.public_key]
    previous_amount = sum(i.amount for i in sender_utxos)
    # if amount > previous_amount:
    #     raise Exception()
    utxos_to_spend = Transaction.find_transaction_inputs_for_amount(sender_utxos, amount)
    # for i in utxos_to_spend:
    #     print(i)
    inputs = utxos_to_spend
    # Actually spend them
    for i in inputs:
        for j in utxos_dict[sender_wallet.public_key]:
            if i.unique_id == j.unique_id:
                # print("found")
                utxos_dict[sender_wallet.public_key].remove(j)

    transaction = Transaction(sender_address=sender_wallet.public_key, recipient_address=receiver_address, value=amount,
                              transaction_inputs=inputs)
    outputs = transaction.create_transaction_outputs(previous_amount)
    transaction.transaction_outputs = outputs
    # update the list of utxos
    for i in outputs:
        # print(i)
        utxos_dict[i.recipient].append(i)
    transaction.sign_transaction(sender_wallet.private_key)
    return transaction


def print_utxos(dict_of_utxos):
    for k,v in dict_of_utxos.items():
        print(k)
        for i in v:
            print(i)