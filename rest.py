import requests
from flask import Flask, jsonify, request, render_template, current_app
from flask_cors import CORS
from noobcash.Wallet import Wallet
from noobcash.Node import Node
from noobcash.Blockchain import Blockchain
from noobcash.utils import create_utxos_dict_from_transaction_list, blockchain_from_dict, transaction_from_dict, \
    create_transaction
import time
import threading


# App initialization and global declarations
app = Flask(__name__)
app.config.from_object('config.Config')
node = Node()
transaction_pool = []
CORS(app)


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
    print("Received transaction")
    t = transaction_from_dict(transaction_dict)
    if not t.verify():
        print("Transaction received is not valid, not adding it to pool")
        return "Failed", 400
    transaction_pool.append(t)

    return "Success", 200


@app.route(rule="/nodes/info", methods=["POST"])
def get_nodes_info():
    node_info = request.json["nodes"]
    node.ring = node_info
    return "Success", 200


@app.route(rule="/transaction_pool")
def get_transaction_pool():
    result = {"transactions": [t.to_dict() for t in transaction_pool]}
    return result, 200


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
        utxos = node.utxos_dict
        t = create_transaction(my_wallet, receiving_node["public_key"], 100, utxos)
        t.sign_transaction(my_wallet.private_key)
        node.utxos_dict = utxos
        threading.Thread(target=node.broadcast_transaction, args=[t]).start()


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
        utxos_dict = create_utxos_dict_from_transaction_list(blockchain.get_unspent_transaction_outputs())
        master_node = {
            "id_0": {
                "url": f"127.0.0.1:{port}",
                "public_key": node.wallet.public_key
            }
        }
        node.ring = master_node
        node.utxos_dict = utxos_dict
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
        utxos_dict = create_utxos_dict_from_transaction_list(blockchain.get_unspent_transaction_outputs())
        node.utxos_dict = utxos_dict

    app.run(host='0.0.0.0', port=port, threaded=False)
