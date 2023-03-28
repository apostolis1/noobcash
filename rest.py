import requests
from flask import Flask, jsonify, request, render_template, current_app
from flask_cors import CORS
from noobcash.Wallet import Wallet
from noobcash.Node import Node
from noobcash.Blockchain import Blockchain
from noobcash.Transaction import Transaction
from noobcash.utils import blockchain_from_dict, transaction_from_dict, \
    create_transaction, block_from_dict, check_utxos
import time
import threading
from copy import deepcopy


# App initialization and global declarations
app = Flask(__name__)
app.config.from_object('config.Config')
node: Node = Node()
transaction_pool = []
CORS(app)
pool_get_lock = threading.Lock()
utxos_lock = threading.Lock()


# Route registration
@app.route('/health', methods=['GET'])
def get_transactions():
    return "OK", 200


@app.route(rule="/nodes/all")
def all_nodes_info():
    # Endpoint to return information the node has about all the other nodes in the network
    node_info = node.ring
    # print(node_info)
    return jsonify(node_info), 200


@app.route(rule="/blockchain")
def get_blockchain():
    return jsonify(node.blockchain.to_dict()), 200


@app.route(rule="/register")
def register_node():
    # Endpoint where the bootstrap node is waiting for the info from other nodes
    # Is responsible for everything that should be done when a node is trying to enter the system
    # meaning sending the blockchain copy, notifying all the nodes about the info of the entire network once
    # all the nodes have been registered
    ip_addr = request.args.get('ip')
    port = request.args.get('port')
    public_key = request.args.get('public_key')
    print(f"Received registration request from ip {ip_addr} at port {port} with public_key {public_key}")
    existing_nodes = node.ring
    new_node_id = len(existing_nodes)
    existing_nodes[f"id_{new_node_id}"] = {
        "url": f"{ip_addr}:{port}",
        "public_key": public_key
    }
    print(f"Assigned node id {new_node_id} to ...")

    # Notify all nodes about node.ring
    if len(existing_nodes) == current_app.config["NUMBER_OF_NODES"]:
        print("All nodes are here, sending information to them")
        # Create new thread to notify the nodes of the network info
        threading.Thread(target=all_nodes_here, ).start()
    return jsonify({f"id_{new_node_id}": f"{ip_addr}:{port}"}), 200


@app.route(rule="/transactions/create", methods=['POST'])
def create_transaction_endpoint():
    # Endpoint where each node is listening for new transactions to be broadcast
    # Simply add transaction to pool of pending transactions
    transaction_dict = request.json
    # print(transaction_dict)
    pool_get_lock.acquire()
    # print("Received transaction")
    t = transaction_from_dict(transaction_dict)
    # print(f"Receiver address: \t {t.receiver_address}")
    if not t.verify():
        print("Transaction received is not valid, not adding it to pool")
        return "Failed", 400
    transaction_pool.append(t)
    print(f"I sam inside create_transaction_endpoint() and I am appending transaction to pool with input amount: "
          f"{t.transaction_inputs[0].amount} and input id {t.transaction_inputs[0].unique_id[-5:]}")
    print(f"I sam inside create_transaction_endpoint() and I am appending transaction to pool output_0 with "
          f"amount: {t.transaction_outputs[0].amount} and input id {t.transaction_outputs[0].unique_id[-5:]}")
    print(f"I sam inside create_transaction_endpoint() and I am appending transaction to pool output_1 with "
          f"amount: {t.transaction_outputs[1].amount} and input id {t.transaction_outputs[1].unique_id[-5:]}")
    # print(f"Added transaction to pool, pool length is {len(transaction_pool)}")
    # for i in transaction_pool:
    #     print(f"Receiver address: \t {i.receiver_address}")
    pool_get_lock.release()
    # start new thread that handles the transactions from the pool
    threading.Thread(target=process_transaction_from_pool).start()
    return "Success", 200


def process_transaction_from_pool():
    # TODO: Check if lock needed
    if not node.mining:
        pool_get_lock.acquire()
        if len(transaction_pool) == 0:
            pool_get_lock.release()
            print("Pool is empty, returning")
            return
        t: Transaction = transaction_pool.pop(0)
        print(f"I sam inside process_transaction_from_pool() and I am pooping transaction from pool with input amount: "
              f"{t.transaction_inputs[0].amount} and input id {t.transaction_inputs[0].unique_id[-5:]}")
        print(f"I sam inside process_transaction_from_pool() and I am pooping transaction from pool with output_0 with "
              f"amount: {t.transaction_outputs[0].amount} and input id {t.transaction_outputs[0].unique_id[-5:]}")
        print(f"I sam inside process_transaction_from_pool() and I am pooping transaction from pool with output_1 with "
              f"amount: {t.transaction_outputs[1].amount} and input id {t.transaction_outputs[1].unique_id[-5:]}")
        # print(f"Removing transaction from pool, new pool length is {len(transaction_pool)}")
        pool_get_lock.release()
        utxos_lock.acquire()
        # print("Processing transaction ")
        # TODO:  this does not work as bootstrap node cannot find the t_input in node.utxos_dict
        # and thus it raises error
        if not t.verify():
            utxos_lock.release()
            return
        # We don't check our own transactions, because we have already removed the utxos during create_transaction
        # if not t.sender_address == node.wallet.address:
        #     print(f"I sam inside process_transaction_from_pool and I am processing transaction with input amount: "
        #           f"{t.transaction_inputs[0].amount} and input id {t.transaction_inputs[0].unique_id[-5:]}")
        #     print(f"I sam inside process_transaction_from_pool and I am processing transaction with output_0 with "
        #           f"amount: {t.transaction_outputs[0].amount} and input id {t.transaction_outputs[0].unique_id[-5:]}")
        #     print(f"I sam inside process_transaction_from_pool and I am processing transaction with output_1 with "
        #           f"amount: {t.transaction_outputs[1].amount} and input id {t.transaction_outputs[1].unique_id[-5:]}")
        #     for t_input in t.transaction_inputs:
        #         if t_input not in node.utxos_dict[t_input.recipient]:
        #             print(f"Cant find  input with id: {t_input.unique_id} and amount: {t_input.amount} in {[i.unique_id  for i in node.utxos_dict[t_input.recipient]]}")
        #         node.utxos_dict[t_input.recipient].remove(t_input)
        #     for t_output in t.transaction_outputs:
        #         try:
        #             node.utxos_dict[t_output.recipient].append(t_output)
        #         except KeyError:
        #             node.utxos_dict[t_output.recipient] = [t_output]
        # print(f"Processing transaction {t}")
        utxos_lock.release()
        node.add_transaction(t)
    else:
        print("Processing transaction halted because I am already mining, assuming someone will trigger me later")
    return


@app.route(rule="/nodes/info", methods=["POST"])
def get_nodes_info():
    node_info = request.json["nodes"]
    node.ring = node_info
    return "Success", 200


@app.route(rule="/utxos/all")
def get_utxos():
    print("Trying to get utxos from blockchain")
    res = {}
    for k in node.blockchain.utxos_dict.keys():
        res[k] = [i.to_dict() for i in node.blockchain.utxos_dict[k]]
    print("Got utxos from blockchain, returning")
    return res, 200


@app.route(rule="/transaction_pool")
def get_transaction_pool():
    result = {"transactions": [t.to_dict() for t in transaction_pool]}
    return result, 200


@app.route(rule="/block/get", methods=["POST"])
def receive_block():
    # TODO: Check if lock is needed when calling add_block_to_blockchain
    # Endpoint where each node is waiting for blocks to be broadcasted
    # print("receive_block method has been called properly")
    block_dict = request.json
    block = block_from_dict(block_dict)
    print(f"Received Block with current hash: {block.current_hash}")
    if block.current_hash is None:
        raise Exception("None current hash received")
    print(f"Mining value: {node.mining}")
    utxos_lock.acquire()
    utxos_copy = deepcopy(node.blockchain.utxos_dict)
    # Check the transactions in the block compared to the ones in the blockchain to see if we can add the block
    # if not check_utxos(utxos_copy, block):
    #     print(f"Current blockchain has length {len(node.blockchain.chain)}")
    #     print("Utxos are not good")
    #     utxos_lock.release()
    #     return "Utxos don't match, not adding to blockchain", 400
    # Add block to blockchain, this handles updating the utxos dict of the blockchain as well as our local utxos_dict
    node.add_block_to_blockchain(block)
    utxos_lock.release()
    # Process next transaction in pool
    threading.Thread(target=process_transaction_from_pool).start()
    return "Success", 200


def all_nodes_here():
    time.sleep(2)
    existing_nodes = node.ring
    for n in existing_nodes.values():
        ip_addr = n['url']
        url = f"http://{ip_addr}/nodes/info"
        print(url)
        data = {
            "nodes": existing_nodes
        }
        requests.post(url=url, json=data)
    time.sleep(1)
    for receiving_node in existing_nodes.values():
        my_wallet: Wallet = node.wallet
        if receiving_node["public_key"] == my_wallet.public_key:
            continue
        utxos_lock.acquire()
        utxos = node.my_utxos
        # print("Utxos before are:")
        # for i in utxos[node.wallet.address]:
        #     print(str(i))
        t = create_transaction(my_wallet, receiving_node["public_key"], 100, utxos)
        # TODO: perhaps this signing here is not needed as I sign the transaction
        # inside create_transaction method
        # print("Utxos after are:")
        # for i in utxos[node.wallet.address]:
        #     print(str(i))
        t.sign_transaction(my_wallet.private_key)
        node.my_utxos = utxos
        # print(
        #     f"Changed my utxos to {[str(i) for i in node.utxos_dict[node.wallet.address]]} inside all_nodes_here()")
        #
        # print(f"I sam inside all_nodes_here() and I am processing transaction with input amount: "
        #       f"{t.transaction_inputs[0].amount} and input id {t.transaction_inputs[0].unique_id[-5:]}")
        # print(f"I sam inside all_nodes_here() and I am processing transaction with output_0 with "
        #       f"amount: {t.transaction_outputs[0].amount} and input id {t.transaction_outputs[0].unique_id[-5:]}")
        # print(f"I sam inside all_nodes_here() and I am processing transaction with output_1 with "
        #       f"amount: {t.transaction_outputs[1].amount} and input id {t.transaction_outputs[1].unique_id[-5:]}")
        utxos_lock.release()
        thread = threading.Thread(target=node.broadcast_transaction, args=[t])
        thread.start()
        thread.join()
        time.sleep(5)
        # print(f"Successfully broadcasted transaction {t}")


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    nodes = app.config["NUMBER_OF_NODES"]
    capacity = app.config["CAPACITY"]
    difficulty = app.config["DIFFICULTY"]
    master_url = app.config["MASTER_URL"]
    is_bootstrap = (port == 5000)
    if is_bootstrap:
        print("Initialization for bootstrap node")
        blockchain = Blockchain(nodes, capacity=capacity, difficulty=difficulty)
        blockchain.GenesisBlock(node.wallet.public_key)
        node.blockchain = blockchain
        master_node = {
            "id_0": {
                "url": f"127.0.0.1:{port}",
                "public_key": node.wallet.public_key
            }
        }
        node.ring = master_node
        # node.utxos_dict = {node.wallet.public_key : deepcopy(node.blockchain.chain[0].list_of_transactions[0].transaction_outputs)}
        try:
            node.my_utxos = deepcopy(node.blockchain.utxos_dict[node.wallet.address])
        except KeyError:
            node.my_utxos = []
    else:
        print("Creating participation node")
        data = {
            "ip": "127.0.0.1", # TODO : Make this our current ip
            "port": port,
            "public_key": node.wallet.public_key
        }
        register_url = f"{master_url}/register"
        requests.get(url=register_url, params=data)
        blockchain_url = f"{master_url}/blockchain"
        blockchain_dict = requests.get(url=blockchain_url).json()
        blockchain = blockchain_from_dict(blockchain_dict)
        if not blockchain.validate_chain():
            raise Exception("Blockchain is not valid")
        print("Blockchain received is valid")
        node.blockchain = blockchain
        # If there are transaction outputs for us, get them, otherwise the list is empty
        try:
            node.my_utxos = deepcopy(node.blockchain.utxos_dict[node.wallet.address])
        except KeyError:
            node.my_utxos = []
        
    app.run(host='0.0.0.0', port=port, threaded=True)
