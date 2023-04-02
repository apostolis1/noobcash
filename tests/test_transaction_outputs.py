from noobcash.Wallet import Wallet
from noobcash.Transaction import Transaction
from noobcash.TransactionOutput import TransactionOutput

def print_utxos(dict_of_utxos):
    for k,v in dict_of_utxos.items():
        print(k)
        for i in v:
            print(i)


wallet1 = Wallet()
wallet2 = Wallet()

transaction_output1 = TransactionOutput("1", wallet1.address, 100)
transaction_output2 = TransactionOutput("2", wallet2.address, 100)

dict_of_utxos = {
    "id0": [],
    "id1": [transaction_output1],
    "id2": [transaction_output2],

}

address_to_id = {
    wallet1.address: "id1",
    wallet2.address: "id2"
}

previous_amount = sum(i.amount for i in dict_of_utxos["id1"])

utxos_to_spend = Transaction.find_transaction_inputs_for_amount(dict_of_utxos["id1"], 10)
for i in utxos_to_spend:
    print(i)

inputs = utxos_to_spend
# Actually spend them
for i in inputs:
    for j in dict_of_utxos[address_to_id[i.recipient]]:
        if i.unique_id == j.unique_id:
            print("found")
            dict_of_utxos[address_to_id[i.recipient]].remove(j)

transaction = Transaction(sender_address=wallet1.address, recipient_address=wallet2.address, value=5, transaction_inputs=inputs)
outputs = transaction.create_transaction_outputs(previous_amount)
transaction.transaction_outputs = outputs
transaction.sign_transaction(wallet1.private_key)
transaction.verify()

for i in outputs:
    print(i)
    dict_of_utxos[address_to_id[i.recipient]].append(i)


print(dict_of_utxos)


print("*"*50)

previous_amount = sum(i.amount for i in dict_of_utxos["id2"])

utxos_to_spend = Transaction.find_transaction_inputs_for_amount(dict_of_utxos["id2"], 105)
for i in utxos_to_spend:
    print(i)

inputs = utxos_to_spend
# Actually spend them
for i in inputs:
    for j in dict_of_utxos[address_to_id[i.recipient]]:
        if i.unique_id == j.unique_id:
            print("found")
            dict_of_utxos[address_to_id[i.recipient]].remove(j)

transaction = Transaction(sender_address=wallet2.address, recipient_address=wallet1.address, value=105, transaction_inputs=inputs)
outputs = transaction.create_transaction_outputs(previous_amount)
transaction.transaction_outputs = outputs
transaction.sign_transaction(wallet1.private_key)
transaction.verify()

for i in outputs:
    print(i)
    dict_of_utxos[address_to_id[i.recipient]].append(i)


print_utxos(dict_of_utxos)
