from flask import Flask, session
import requests
from Wallet import Wallet


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
        if is_first:
            cache.clear()
        cache.set("Transactions", {
            "A": 8746516,
            "B": 1451545
        })
        cache.set("PORT", port)
        master_url = "http://127.0.0.1:5000"
        print("Starting...")
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
        # Master node should add itself on the list of nodes
        else:
            master_node = {
                f"id_0": {
                    "url": f"127.0.0.1:{port}",
                    "public_key": public_key
                }
            }
            cache.set("nodes", [master_node])
        return app
