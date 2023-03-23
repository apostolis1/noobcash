import json
import threading
import time
from copy import deepcopy
import requests
from flask import Flask, jsonify, session, current_app, request
from flask import Blueprint
from rest_app.common import cache
from noobcash.utils import *
from noobcash.Node import Node

route_blueprint = Blueprint('route_blueprint', __name__)


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


    # print(existing_nodes)
    print(f"Assigned node id {new_node_id} to ...")
    cache.set("node", node)
    if len(existing_nodes) == current_app.config["NUMBER_OF_NODES"]:
        print("All nodes are here, sending information to them")
        # Create new thread to notify the nodes of the network info
        threading.Thread(target=all_nodes_here, args=[existing_nodes, node]).start()
    return jsonify({f"id_{new_node_id}": f"{ip_addr}:{port}"}), 200


def all_nodes_here(existing_nodes: dict, node: Node):
    time.sleep(2)
    blockchain_to_send = node.blockchain
    for n in existing_nodes.values():
        ip_addr = n['url']
        url = f"http://{ip_addr}/nodes/info"
        print(url)
        data = {
            "nodes": existing_nodes
        }
        requests.get(url=url, json=data)
        url = f"http://{ip_addr}/blockchain/get"
        requests.post(url=url, json=blockchain_to_send.to_dict())

    # Create transactions for each node
    for receiving_node in existing_nodes.values():
        my_wallet: Wallet = node.wallet
        if receiving_node["public_key"] == my_wallet.public_key:
            continue
        utxos = node.utxos_dict
        t = create_transaction(my_wallet, receiving_node["public_key"], 100, utxos)
        t.sign_transaction(my_wallet.private_key)
        node.utxos_dict = utxos
        cache.set("node", node)
        threading.Thread(target=node.broadcast_transaction, args=[t]).start()
    return

# def notify_nodes(existing_nodes: dict):
#     # Notifies all the nodes that are already registered
#     time.sleep(2)  # TODO remove this sleep, sleep when timeout instead
#     for node in existing_nodes.values():
#         ip_addr = node['url']
#         url = f"http://{ip_addr}/nodes/info"
#         print(url)
#         data = {
#             "nodes": existing_nodes
#         }
#         res = requests.get(url=url, json=data)
#         requests.
#     return


@route_blueprint.route(rule="/nodes/info")
def get_nodes_info():
    node_info = request.json["nodes"]
    # print(node_info)
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
    # print(node_info)
    return jsonify(node_info), 200


@route_blueprint.route(rule="/blockchain")
def get_blockchain():
    node: Node = cache.get("node")
    return jsonify(node.blockchain.to_dict()), 200


@route_blueprint.route(rule="/blockchain/get", methods=["POST"])
def receive_blockchain():
    node: Node = cache.get("node")
    blockchain_dict = request.json
    blockchain = blockchain_from_dict(blockchain_dict)
    # We need to send only valid blocks that are added to the chain, not the ones we are working on
    node.blockchain = blockchain
    cache.set("node", node)
    return "Success", 200


@route_blueprint.route(rule="/block/get", methods=["POST"])
def receive_block():
    # Endpoint where each node is waiting for blocks to be broadcasted
    print("receive_block method has been called properly")
    node: Node = cache.get("node")
    block_dict = request.json
    block = block_from_dict(block_dict)
    print(f"Received Block with current hash: {block.current_hash}")
    if block.current_hash is None:
        raise Exception("None current hash received")
    node.add_block_to_blockchain(block)

    # print(f"Received Last_Block with current hash: {node.blockchain.getLastBlock().current_hash}")
    cache.set("node", node)
    # print(node.blockchain.chain)
    return "Success", 200


@route_blueprint.route(rule="/transactions/create", methods=['POST'])
def create_transaction_endpoint():
    # Endpoint where each node is listening for new transactions to be broadcast
    node: Node = cache.get("node")
    transaction_dict = request.json
    # print(transaction_dict)
    print("Received transaction")
    t = transaction_from_dict(transaction_dict)
    t.verify()
    blockchain = node.blockchain
    # Add the new transaction to a correct block
    node.add_transaction(t)
    # last_block: Block = blockchain.getLastBlock()
    # last_block.add_transaction(t)
    utxos_dict = create_utxos_dict_from_transaction_list(blockchain.get_unspent_transaction_outputs())
    node.blockchain = blockchain
    node.utxos_dict = utxos_dict
    cache.set("node", node)
    return "Success", 200


@route_blueprint.route(rule="/utxos/get")
def get_utxos_dict():
    node: Node = cache.get("node")
    utxos_dict = node.utxos_dict
    res = {}
    for k in utxos_dict.keys():
        res[k] = [i.to_dict() for i in utxos_dict[k]]
    return jsonify(res), 200


# @route_blueprint.route(rule="/blocks/create", methods=['POST'])
# def create_block_endpoint():
#     # TODO: Complete this
#     # Endpoint where each node is listening for new blocks to be broadcast
#     # Should check if we are mining already and stop in that case
#     node: Node = cache.get("node")
#     block_dict = request.json
#     print("Received block")
#     b = block_from_dict(block_dict)
#     blockchain = node.blockchain
#     if not b.validate_block(difficulty=blockchain.difficulty):
#         print("Block is not valid")
#         return "Failed", 400
#     # TODO: Check if mining thread is alive, if so kill it
#     # TODO: Make sure utxos get updated, maybe call generate_utxos_from_chain ?
#
#     cache.set("node", node)
#     return "Success", 200
