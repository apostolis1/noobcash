from flask import Flask, current_app
import requests
from noobcash.Wallet import Wallet
from noobcash.Blockchain import Blockchain
from noobcash.Node import Node
from noobcash.utils import *


def create_app(port, is_first=False):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    # app.config.from_object('config.Config')

    with app.app_context():
        from . import routes
        from .common import cache
        app.register_blueprint(routes.route_blueprint)
        # cache.init_app(app=app, config={"CACHE_TYPE": "filesystem", 'CACHE_DIR': '/tmp'})
        cache.init_app(app=app, config={"CACHE_TYPE": "simple"})
        cache.clear()

        cache.set("PORT", port)
        master_url = "http://127.0.0.1:5000"
        print("Starting...")
        nodes = current_app.config["NUMBER_OF_NODES"]
        capacity = current_app.config["CAPACITY"]
        difficulty = current_app.config["DIFFICULTY"]
        if is_first:
            blockchain = Blockchain(nodes, capacity=capacity, difficulty=difficulty)
            node = Node()
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
            cache.set("node", node)

        else:
            # Every node that is created except from the master node has to register itself,
            # meaning to notify the master node of its existence
            print("Registering node ...")
            node = Node()
            data = {
                "ip": "127.0.0.1",
                "port": port,
                "public_key": node.wallet.public_key
            }
            register_url = f"{master_url}/register"
            cache.set("node", node)
            res = requests.get(url=register_url, params=data)
            # # Get the current blockchain from bootstrap node
            # blockchain_url = f"{master_url}/blockchain"
            # blockchain_dict = requests.get(url=blockchain_url).json()
            # blockchain = blockchain_from_dict(blockchain_dict)
            # if not blockchain.validate_chain():
            #     raise Exception("Blockchain is not valid")
            # print("Blockchain received is valid")
            # node.blockchain = blockchain
            # utxos_dict = create_utxos_dict_from_transaction_list(blockchain.get_unspent_transaction_outputs())
            # node.utxos_dict = utxos_dict

            # print(res.json())
        return app
