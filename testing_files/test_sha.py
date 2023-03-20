from Crypto.Hash import SHA256
import random

for i in range(1000000):
    random_num = random.randint(10**5,10**6)
    hash_object = SHA256.new(data=str(random_num).encode())
    if (hash_object.hexdigest().startswith('00000')):
        print(hash_object.hexdigest())