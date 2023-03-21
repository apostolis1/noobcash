from noobcash.Blockchain import Blockchain
from noobcash.Block import Block
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
        try:
            utxos_dict[i.recipient].append(i)
        except KeyError:
            utxos_dict[i.recipient] = [i]
    transaction.sign_transaction(sender_wallet.private_key)
    return transaction


def print_utxos(dict_of_utxos):
    for k,v in dict_of_utxos.items():
        print(k)
        for i in v:
            print(i)


def transaction_from_dict(transaction_dict: dict) -> Transaction:
    # Helper function to create a Transaction Object from the corresponding dict
    # The dict should be created via the to_dict() method
    # Used when a transaction is converted to dict and transmitted via the rest api
    sender_address = transaction_dict["sender_address"]
    receiver_address = transaction_dict["receiver_address"]
    amount = transaction_dict["amount"]
    if transaction_dict["signature"] is None:
        signature = None
    else:
        signature = bytes.fromhex(transaction_dict["signature"])
    transaction_id = transaction_dict["transaction_id"]
    transaction_inputs = [transaction_output_from_dict(i) for i in transaction_dict["transaction_inputs"]]
    transaction_outputs = [transaction_output_from_dict(i) for i in transaction_dict["transaction_outputs"]]
    t = Transaction(sender_address, receiver_address, amount, transaction_inputs, transaction_id, signature, transaction_outputs)
    return t


def transaction_output_from_dict(transaction_output_dict: dict) -> TransactionOutput:
    # Helper function to create a TransactionOutput Object from the corresponding dict
    # The dict should be created via the to_dict() method
    # Used when a TransactionOutput is converted to dict and transmitted via the rest api
    transaction_id = transaction_output_dict["transaction_id"]
    recipient = transaction_output_dict["recipient"]
    amount = transaction_output_dict["amount"]
    unique_id = transaction_output_dict["unique_id"]
    transaction_output = TransactionOutput(transaction_id, recipient, amount, unique_id)
    return transaction_output


def block_from_dict(block_dict: dict) -> Block:
    index = block_dict["index"]
    previous_hash = block_dict["previousHash"]
    timestamp = block_dict["timestamp"]
    nonce = block_dict["nonce"]
    current_hash = block_dict["current_hash"]
    transactions = [transaction_from_dict(i) for i in block_dict["transactions"]]
    block = Block(index, previous_hash, nonce, current_hash, transactions, timestamp)
    return block


def blockchain_from_dict(blockchain_dict: dict) -> Blockchain:
    nodes = blockchain_dict["nodes"]
    chain = [block_from_dict(i) for i in blockchain_dict["chain"]]
    blockchain = Blockchain(nodes, chain)
    return blockchain


def create_utxos_dict_from_transaction_list(transaction_list: list):
    d = {}
    for transaction_output in transaction_list:
        try:
            d[transaction_output.recipient].append(transaction_output)
        except Exception as e:
            d[transaction_output.recipient] = [transaction_output]
    return d
