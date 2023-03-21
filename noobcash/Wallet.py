import binascii

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4


class Wallet:
	def __init__(self):
		key = RSA.generate(2048)
		self.private_key = key.export_key()
		self.public_key = key.publickey().export_key("OpenSSH").decode()
		self.address = self.public_key
		self.transactions = []

	def balance(self):
		...

	def get_public_key(self):
		return self.public_key
