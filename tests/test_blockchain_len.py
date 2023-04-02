import requests
from config import Config

MASTER_IP = f"{Config.MASTER_IP}:5000"


def test_len_master():
    url = f"http://{MASTER_IP}/blockchain"
    res = requests.get(url=url)
    blockchain_dict = res.json()
    master_len = len(blockchain_dict['chain'])
    print(f"Blockchain len {master_len}")
    assert master_len >= 1


def test_all_len():
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


def test_all_transaction_pool_empty():
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
