from noobcash.Blockchain import Blockchain
from noobcash.Block import Block
from noobcash.Wallet import Wallet
from noobcash.Transaction import Transaction
from noobcash.TransactionOutput import TransactionOutput
from copy import deepcopy


def create_transaction(sender_wallet: Wallet, receiver_address, amount, utxos_list: list):
    previous_amount = sum(i.amount for i in utxos_list)
    # if amount > previous_amount:
    #     raise Exception()
    utxos_to_spend = Transaction.find_transaction_inputs_for_amount(utxos_list, amount)
    # for i in utxos_to_spend:
    #     print(i)
    inputs = utxos_to_spend
    # Actually spend them
    for i in inputs:
        utxos_list.remove(i)

    transaction = Transaction(sender_address=sender_wallet.public_key, recipient_address=receiver_address, value=amount,
                              transaction_inputs=inputs)
    outputs = transaction.create_transaction_outputs(previous_amount)
    transaction.transaction_outputs = outputs
    # update the list of utxos
    # The first output is always the remaining amount to us
    utxos_list.append(outputs[0])
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
    if current_hash is None:
        raise Exception("current_hash is None")
    transactions = [transaction_from_dict(i) for i in block_dict["transactions"]]
    block = Block(index, previous_hash, nonce, current_hash, transactions, timestamp, capacity=block_dict["capacity"])
    return block


def blockchain_from_dict(blockchain_dict: dict) -> Blockchain:
    nodes = blockchain_dict["nodes"]
    chain = [block_from_dict(i) for i in blockchain_dict["chain"]]
    capacity = blockchain_dict["capacity"]
    difficulty = blockchain_dict["difficulty"]
    utxos_dict = {
        k: [transaction_output_from_dict(i) for i in v] for k, v in blockchain_dict["utxos_dict"].items()
    }
    blockchain = Blockchain(nodes, chain, capacity, difficulty, utxos_dict)
    return blockchain


def create_utxos_dict_from_transaction_list(transaction_list: list):
    d = {}
    for transaction_output in transaction_list:
        try:
            d[transaction_output.recipient].append(transaction_output)
        except Exception as e:
            d[transaction_output.recipient] = [transaction_output]
    return d


def check_utxos(utxos_dict_, block: Block) ->bool:
    utxos_dict = deepcopy(utxos_dict_)
    for transaction in block.list_of_transactions:
        sender = transaction.sender_address
        for t_input in transaction.transaction_inputs:
            if t_input not in utxos_dict[sender]:
                print(f"Can't find {t_input.unique_id} with sender {sender[-4:]}")
                return False
        for t_output in transaction.transaction_outputs:
            try:
                utxos_dict[t_output.recipient].append(t_output)
            except KeyError:
                utxos_dict[t_output.recipient] = [t_output]
    return True
