import json
import threading
import time

import requests
from flask import Flask, jsonify, session, current_app, request
from flask import Blueprint
from rest_app.common import cache
from noobcash.utils import *
from noobcash.Node import Node

route_blueprint = Blueprint('route_blueprint', __name__)


@route_blueprint.route(rule="/transactions/get")
def get_transactions():
    # transactions = blockchain.transactions
    transactions = cache.get("Transactions")
    response = {'transactions': transactions}
    print(transactions)
    return jsonify(response), 200


@route_blueprint.route(rule="/register")
def register_node():
    # Endpoint where the bootstrap node is waiting for the info from other nodes
    # Is responsible for everything that should be done when a node is trying to enter the system
    # meaning sending the blockchain copy, notifying all the nodes about the info of the entire network once
    # all the nodes have been registered
    ip_addr = request.args.get('ip')
    port = request.args.get('port')
    public_key = request.args.get('public_key')
    node: Node = cache.get("node")
    if node is None:
        raise Exception("Node is not found")
    print(f"Received registration request from ip {ip_addr} at port {port} with public_key {public_key}")
    # Add node to existing nodes
    existing_nodes = node.ring
    if existing_nodes is None:
        existing_nodes = {}
        print("Existing nodes is empty")
    # Assign id to node
    new_node_id = len(existing_nodes)
    existing_nodes[f"id_{new_node_id}"] = {
        "url": f"{ip_addr}:{port}",
        "public_key": public_key
    }
    # Create the transaction to transfer 100 nbc to new node
    # blockchain = cache.get("blockchain")
    my_wallet: Wallet = node.wallet
    utxos = node.utxos_dict
    t = create_transaction(my_wallet, public_key, 100, utxos)
    t.sign_transaction(my_wallet.private_key)
    t_dict = t.to_dict()
    with open('convert.json', 'w+') as convert_file:
        convert_file.write(json.dumps(t_dict))
    threading.Thread(target=node.broadcast_transaction, args=[t]).start()

    print(existing_nodes)
    print(f"Assigned node id {new_node_id} to ...")
    cache.set("node", node)
    if len(existing_nodes) == current_app.config["NUMBER_OF_NODES"]:
        print("All nodes are here, sending information to them")
        # Create new thread to notify the nodes of the network info
        threading.Thread(target=notify_nodes, args=[existing_nodes]).start()
    return jsonify({
            f"id_{new_node_id}": f"{ip_addr}:{port}"
        }), 200


def notify_nodes(existing_nodes: dict):
    # Notifies all the nodes that are already registered
    for node in existing_nodes.values():
        ip_addr = node['url']
        url = f"http://{ip_addr}/nodes/info"
        print(url)
        data = {
            "nodes": existing_nodes
        }
        res = requests.get(url=url, json=data)
    return

def send_transaction(transaction_dict):
    time.sleep(1)
    requests.post("http://127.0.0.1:5000/transactions/create", json=transaction_dict)
    requests.post("http://127.0.0.1:5001/transactions/create", json=transaction_dict)

@route_blueprint.route(rule="/nodes/info")
def get_nodes_info():
    node_info = request.json
    print(node_info)
    node: Node = cache.get("node")
    if node is None:
        raise Exception("Node not found")
    # TODO Make sure that the node is created and set in cache
    node.ring = node_info
    cache.set("node", node)
    return "Success", 200


@route_blueprint.route(rule="/nodes/all")
def all_nodes_info():
    # Endpoint to return information the node has about all the other nodes in the network
    node: Node = cache.get("node")
    node_info = node.ring
    print(node_info)
    return node_info, 200


@route_blueprint.route(rule="/blockchain")
def get_blockchain():
    node: Node = cache.get("node")
    blockchain = node.blockchain
    return blockchain.to_dict(), 200


@route_blueprint.route(rule="/transactions/create", methods=['POST'])
def create_transaction_endpoint():
    # Endpoint where each node is listening for new transactions to be broadcasted
    node: Node = cache.get("node")
    transaction_dict = request.json
    # print(transaction_dict)
    print("Received transaction")
    t = transaction_from_dict(transaction_dict)
    t.verify()
    blockchain = node.blockchain
    last_block: Block = blockchain.getLastBlock()
    last_block.add_transaction(t)
    utxos_dict = create_utxos_dict_from_transaction_list(blockchain.get_unspent_transaction_outputs())
    node.blockchain = blockchain
    node.utxos_dict = utxos_dict
    cache.set("node", node)
    return "Success", 200

@route_blueprint.route(rule="/utxos/get")
def get_utxos_dict():
    utxos_dict = cache.get("utxos")
    res = {}
    for k in utxos_dict.keys():
        res[k] = [i.to_dict() for i in utxos_dict[k]]
    return res, 200
