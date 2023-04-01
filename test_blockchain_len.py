import requests

MASTER_IP = "127.0.0.1:5000"
url = f"http://{MASTER_IP}/blockchain"
res = requests.get(url=url)
blockchain_dict = res.json()
print(f"Blockchain len {len(blockchain_dict['chain'])}")
