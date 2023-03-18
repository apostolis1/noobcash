import threading

import requests
from flask import Flask, jsonify, session, current_app, request
from flask import Blueprint
from rest_app.common import cache

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
    ip_addr = request.args.get('ip')
    port = request.args.get('port')
    public_key = request.args.get('public_key')
    print(f"Received registration request from ip {ip_addr} at port {port} with public_key {public_key}")
    existing_nodes = cache.get("nodes")
    if existing_nodes is None:
        existing_nodes = []
        print("Existing nodes is empty")
    new_node_id = len(existing_nodes)
    existing_nodes.append(
        {
            f"id_{new_node_id}":  {
                "url": f"{ip_addr}:{port}",
                "public_key": public_key
            }
        }
    )

    cache.set("nodes", existing_nodes)
    print(existing_nodes)
    print(f"Assigned node id {new_node_id} to ...")
    if len(existing_nodes) == current_app.config["NUMBER_OF_NODES"]:
        print("All nodes are here, sending information to them")
        # for node in existing_nodes:
        #     url = f"http://{list(node.values())[0]}/nodes/info"
        #     url = "http://127.0.0.1:5001/nodes/info"
        #     print(url)
        #     data = {
        #         "nodes": existing_nodes
        #     }
        #     res = requests.get(url=url)
        threading.Thread(target=notify_nodes, args=[existing_nodes]).start()
    return jsonify({
            f"id_{new_node_id}": f"{ip_addr}:{port}"
        }), 200


def notify_nodes(existing_nodes):
    for node in existing_nodes:
        ip_addr = node[list(node.keys())[0]]['url']
        url = f"http://{ip_addr}/nodes/info"
        # url = "http://127.0.0.1:5001/nodes/info"
        print(url)
        data = {
            "nodes": existing_nodes
        }
        res = requests.get(url=url, json=data)
    return


@route_blueprint.route(rule="/nodes/info")
def get_nodes_info():
    node_info = request.json
    print(node_info)
    cache.set("nodes", node_info)
    return "Success", 200


@route_blueprint.route(rule="/nodes/all")
def all_nodes_info():
    node_info = cache.get("nodes")
    print(node_info)
    return node_info, 200
