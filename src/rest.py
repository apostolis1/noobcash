import requests
from flask import Flask, jsonify, request, render_template, current_app
from flask_cors import CORS
from noobcash.Wallet import Wallet
from noobcash.Node import Node
from noobcash.Blockchain import Blockchain
from noobcash.Transaction import Transaction
from noobcash.utils import blockchain_from_dict, transaction_from_dict, create_transaction, block_from_dict, check_utxos
import time
import threading
from copy import deepcopy
from threading import get_ident

# App initialization and global declarations
app = Flask(__name__)
app.config.from_object('config.Config')
node: Node = Node()
transaction_pool = node.transaction_pool
CORS(app)
pool_get_lock = threading.Lock()
utxos_lock = threading.Lock()
blockchain_lock = threading.Lock()
thread_lock = threading.Lock()


# Route registration


@app.route('/health', methods=['GET'])
def get_transactions():
    """
    Simple healthcheck
    :return:
    """
    return "OK", 200


@app.route(rule="/nodes/all")
def all_nodes_info():
    """
    Endpoint to return information the node has about all the other nodes in the network
    :return:
    """
    node_info = node.ring
    # print(node_info)
    return jsonify(node_info), 200


@app.route(rule="/blockchain")
def get_blockchain():
    return jsonify(node.blockchain.to_dict()), 200


@app.route(rule="/register")
def register_node():
    """
    Endpoint where the bootstrap node is waiting for the info from other nodes
    Once all nodes are here it creates a new thread to notify them of each other's info
    :return:
    """
    ip_addr = request.args.get('ip')
    port = request.args.get('port')
    public_key = request.args.get('public_key')
    print(f"Received registration request from ip {ip_addr} at port {port} with public_key {public_key}")
    existing_nodes = node.ring
    new_node_id = len(existing_nodes)
    existing_nodes[f"id{new_node_id}"] = {
        "url": f"{ip_addr}:{port}",
        "public_key": public_key
    }
    print(f"Assigned node id {new_node_id} to ...")

    # Notify all nodes about node.ring
    if len(existing_nodes) == current_app.config["NUMBER_OF_NODES"]:
        print("All nodes are here, sending information to them")
        # Create new thread to notify the nodes of the network info
        threading.Thread(target=all_nodes_here, ).start()
    return jsonify({f"id{new_node_id}": f"{ip_addr}:{port}"}), 200


@app.route(rule="/transactions/create", methods=['POST'])
def create_transaction_endpoint():
    """
    Endpoint where each node is listening for new transactions to be broadcast
    Simply add transaction to pool of pending transactions
    :return: 
    """
    transaction_dict = request.json
    pool_get_lock.acquire()
    t = transaction_from_dict(transaction_dict)
    if not t.verify():
        print("Transaction received is not valid, not adding it to pool")
        pool_get_lock.release()
        return "Failed", 400
    transaction_pool.append(t)
    pool_get_lock.release()
    # Start new thread that handles the transactions from the pool
    threading.Thread(target=process_transaction_from_pool).start()
    return "Success", 200


def process_transaction_from_pool():
    with thread_lock:
        if not node.mining:
            pool_get_lock.acquire()
            if len(transaction_pool) == 0:
                pool_get_lock.release()
                print("Pool is empty, returning")
                return
            t: Transaction = transaction_pool.pop(0)
            print(f"{get_ident()} Popped transaction")
            pool_get_lock.release()
            utxos_lock.acquire()
            if not t.verify:
                utxos_lock.release()
                print(f"Transaction {t} could not be verified")
                return
            utxos_lock.release()
            blockchain_lock.acquire()
            try:
                node.add_transaction(t)
                blockchain_lock.release()
            except Exception as e:
                print(e)
                blockchain_lock.release()
            threading.Thread(target=process_transaction_from_pool).start()
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
    res = {}
    for k in node.blockchain.utxos_dict.keys():
        res[k] = [i.to_dict() for i in node.blockchain.utxos_dict[k]]
    return jsonify(res), 200


@app.route(rule="/transaction_pool")
def get_transaction_pool():
    result = {"transactions": [t.to_dict() for t in transaction_pool]}
    return result, 200


@app.route(rule="/block/get", methods=["POST"])
def receive_block():
    with thread_lock:
        # Endpoint where each node is waiting for blocks to be broadcasted
        # print("receive_block method has been called properly")
        block_dict = request.json
        block = block_from_dict(block_dict)
        print(f"Received Block with current hash: {block.current_hash} at {time.ctime()}")
        if block.current_hash is None:
            raise Exception("None current hash received")
        print(f"Mining value: {node.mining}")
        utxos_lock.acquire()
        print("Utxos_lock acquired")
        blockchain_lock.acquire()
        print("Blockchain lock acquired")
        node.add_block_to_blockchain(block)
        utxos_lock.release()
        print("Utxos lock released")
        blockchain_lock.release()
        print("Blockchain lock released")
        print(f"Added block to blockchain at {time.ctime()}")
        # Process next transaction in pool
        threading.Thread(target=process_transaction_from_pool).start()
    return "Success", 200


@app.route('/transactions/new', methods=["POST"])
def create_transaction_cli():
    """
    For compatibility with the cli we want an endpoint that we can use to create a transaction given some basic params,
    the receiver and the amount. We can't use directly /transactions/create because that one expects a valid transaction
    dict as input, which requires Node information that the cli doesn't have. So we use this endpoint as an intermediate
    endpoint which handles the Transaction object creation and broadcasts it.
    """
    receiver_address = request.json['receiver_address']
    amount = request.json['amount']
    my_wallet: Wallet = node.wallet
    utxos_lock.acquire()
    utxos = node.my_utxos

    t = create_transaction(my_wallet, receiver_address, amount, utxos)
    if t is None:
        print("Not enough money, transaction is None")
        utxos_lock.release()
        return "Failed", 402
    t.sign_transaction(my_wallet.private_key)
    node.my_utxos = utxos
    utxos_lock.release()
    thread = threading.Thread(target=node.broadcast_transaction, args=[t])
    thread.start()
    thread.join()
    return "Success", 200


@app.route(rule="/balance/")
def get_balance_for_all_nodes():
    """
    We don't lock here, even though for 'consistency' we would have to
    However, if there are multiple transactions ongoing in the network, consistency doesn't really exist since
    even if we lock, from the moment this endpoint returns and the moment the user reads the information the
    balance might change either way
    So we can avoid using a lock here, since it wouldn't really benefit the end user even if it would be a better
    software engineering practice
    :return:
    """
    key_to_id = {}
    for k,v in node.ring.items():
        key_to_id[v["public_key"]] = k
    res = {}
    for k, utxos in node.blockchain.utxos_dict.items():
        res[key_to_id[k]] = sum([i.amount for i in utxos])
    return jsonify(res), 200


def all_nodes_here():
    print(f"All nodes are here at {time.ctime()}")
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
        t = create_transaction(my_wallet, receiving_node["public_key"], 100, utxos)
        if t is None:

            print("Something went wrong")
        # TODO: perhaps this signing here is not needed as I sign the transaction
        t.sign_transaction(my_wallet.private_key)
        node.my_utxos = utxos
        utxos_lock.release()
        thread = threading.Thread(target=node.broadcast_transaction, args=[t])
        thread.start()
        thread.join()
        time.sleep(3)


@app.route("/blockchain_length/")
def get_blockchain_length():
    # Return the current length of the blockchain
    # Used in resolve_conflicts
    # TODO: Check if chain lock is needed here
    return {"length": (len(node.blockchain.chain))}, 200


@app.route("/blockchain_differences/", methods=["POST"])
def get_blockchain_differences():
    # blockchain_lock.acquire()
    sender_hashed = request.json["hashes"]
    print(f"Received {len(sender_hashed)} hashes, I have {len(node.blockchain.chain)}")
    start_idx = None
    for idx, block_hash in enumerate(sender_hashed):
        if node.blockchain.chain[idx].current_hash != block_hash:
            start_idx = idx
            break
    if start_idx is None:
        start_idx = len(sender_hashed)
    blocks_to_send = node.blockchain.chain[start_idx:]
    print(f"Difference found in position {start_idx}, will send {len(blocks_to_send)} blocks")
    if len(blocks_to_send) >= 1:
        print(f"The last block I will send has hash {blocks_to_send[-1].current_hash}")
    else:
        print("Blocks to send is empty inside get_blockchain_differences")
    blocks_dict = [i.to_dict() for i in blocks_to_send]
    # TODO: I need to send also UTXOs, current_block and transaction_pool
    transaction_pool_dict = [i.to_dict() for i in transaction_pool]
    return {
        "blocks": blocks_dict,
        "conflict_idx": start_idx,
        "transaction_pool": transaction_pool_dict,
        "blockchain_utxos": {k: [i.to_dict() for i in v] for k, v in node.blockchain.utxos_dict.items()},
        "current_block_utxos": {k: [i.to_dict() for i in v] for k, v in node.blockchain.current_block_utxos.items()}
    }, 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-i', '--ip', default='0.0.0.0', type=str, help='IP to listen on')

    args = parser.parse_args()
    port = args.port
    node_ip = args.ip
    nodes = app.config["NUMBER_OF_NODES"]
    capacity = app.config["CAPACITY"]
    difficulty = app.config["DIFFICULTY"]
    master_ip = app.config["MASTER_IP"]
    master_url = f"http://{master_ip}:5000"
    is_bootstrap = (port == 5000)
    print(f"The init of the system started at {time.ctime()}")
    if is_bootstrap:
        print("Initialization for bootstrap node")
        blockchain = Blockchain(nodes, capacity=capacity, difficulty=difficulty)
        blockchain.GenesisBlock(node.wallet.public_key)
        node.blockchain = blockchain
        master_node = {
            "id0": {
                "url": f"{master_ip}:{port}",
                "public_key": node.wallet.public_key
            }
        }
        node.ring = master_node
        try:
            node.my_utxos = deepcopy(node.blockchain.utxos_dict[node.wallet.address])
        except KeyError:
            node.my_utxos = []
    else:
        print("Creating participation node")
        data = {
            "ip": node_ip,
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
        
    app.run(host=node_ip, port=port, threaded=True)
