from noobcash.Blockchain import Blockchain
from noobcash.utils import blockchain_from_dict
import requests
from noobcash.Block import Block

url_list = [f"http://127.0.0.1:500{i}/blockchain" for i in range(5)]

for url in url_list:
    print('-'*50)
    print(f'Eimai sto url: {url}')
    res = requests.get(url)
    res_json = res.json()
    blockchain : Blockchain = blockchain_from_dict(res_json)
    for idx, block in enumerate(blockchain.chain[1:]):
        if block.previousHash != blockchain.chain[idx].current_hash:
            print(f"Paixtike malakia me to block: {block} pou exei index {idx}")
            break
    print("komple")
