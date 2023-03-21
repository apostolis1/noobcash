from flask import Flask
import requests
from noobcash.Wallet import Wallet
from noobcash.Blockchain import Blockchain


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
        # Create a local copy of the blockchain
        blockchain = Blockchain(5)
        cache.set("blockchain", blockchain)
        # Create my wallet
        wallet = Wallet()
        public_key = wallet.get_public_key()
        cache.set("wallet", wallet)
        # Every node that is created except from the master node has to register itself,
        # meaning to notify the master node of its existence
        if not is_first:
            print("Registering node ...")
            data = {
                "ip": "127.0.0.1",
                "port": port,
                "public_key": public_key
            }
            register_url = f"{master_url}/register"
            res = requests.get(url=register_url, params=data)
            # print(res.json())
        # Master node should create the genesis block and add itself on the list of nodes
        else:
            blockchain.GenesisBlock(bootstrap_address=public_key)
            cache.set("blockchain", blockchain)
            master_node = {
                f"id_0": {
                    "url": f"127.0.0.1:{port}",
                    "public_key": public_key
                }
            }
            cache.set("nodes", [master_node])
        return app
