from noobcash.Blockchain import Blockchain
from noobcash.utils import blockchain_from_dict
import requests
from config import Config


MASTER_IP = f"{Config.MASTER_IP}:5000"


def test_blockchain_hash_validity():
    """
    Test whether every node's previous_hash is indeed the current_hash of its predecessor
    :return:
    """

    url = f"http://{MASTER_IP}/nodes/all"
    res = requests.get(url=url)
    ring = res.json()
    url_list = [f"http://{i['url']}/blockchain" for i in ring.values()]
    for url in url_list:
        print('-'*50)
        print(f'Eimai sto url: {url}')
        res = requests.get(url)
        res_json = res.json()
        blockchain : Blockchain = blockchain_from_dict(res_json)
        for idx, block in enumerate(blockchain.chain[1:]):
            if block.previousHash != blockchain.chain[idx].current_hash:
                print(f"Paixtike malakia me to block: {block} pou exei index {idx}")
                assert False
        print("komple")


def test_balance_sum():
    """
    The expected sum of balances should be 100*nodes
    Ask every node about its balance view, make sure they all add up to the correct ammount
    :return:
    """
    url = f"http://{MASTER_IP}/nodes/all"
    res = requests.get(url=url)
    ring = res.json()
    number_of_nodes = len(ring.keys())
    url_list = [f"http://{i['url']}/balance/" for i in ring.values()]
    for url in url_list:
        res = requests.get(url)
        res_json = res.json()
        print(res_json)
        assert sum(res_json.values()) == number_of_nodes*100

