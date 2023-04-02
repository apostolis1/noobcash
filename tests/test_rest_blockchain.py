from noobcash.Blockchain import Blockchain
from noobcash.utils import blockchain_from_dict
import requests
from config import Config
import unittest


MASTER_IP = f"{Config.MASTER_IP}:5000"


class TestRestBlockchain(unittest.TestCase):
    def test_blockchain_hash_validity(self):
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
        assert True

    def test_balance_sum(self):
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

    def test_len_master(self):
        """
        Test the blockchain length of master node
        :return:
        """
        url = f"http://{MASTER_IP}/blockchain"
        res = requests.get(url=url)
        blockchain_dict = res.json()
        master_len = len(blockchain_dict['chain'])
        print(f"Blockchain len {master_len}")
        assert master_len >= 1

    def test_all_len(self):
        """
        Test that every node's blockchain has the same length
        :return:
        """
        url = f"http://{MASTER_IP}/blockchain"
        res = requests.get(url=url)
        blockchain_dict = res.json()
        master_len = len(blockchain_dict['chain'])

        lengths = []
        url = f"http://{MASTER_IP}/nodes/all"
        res = requests.get(url=url)

        ring = res.json()
        for url_node in ring.values():
            base_url = url_node['url']
            url = f"http://{base_url}/blockchain"
            res = requests.get(url=url)
            blockchain_dict = res.json()
            node_len = len(blockchain_dict['chain'])
            print(f"Blockchain from {base_url} len {node_len}")
            assert master_len == node_len

    def test_all_transaction_pool_empty(self):
        """
        Run this after all transactions are processed, make sure there is nothing left on transaction_pool
        :return:
        """

        url = f"http://{MASTER_IP}/nodes/all"
        res = requests.get(url=url)

        ring = res.json()
        for url_node in ring.values():
            base_url = url_node['url']
            url = f"http://{base_url}/transaction_pool"
            res = requests.get(url=url)
            t_pool = res.json()
            t_pool_len = len(t_pool['transactions'])
            print(f"Transaction pool from {base_url} len {t_pool_len}")
            assert t_pool_len == 0
