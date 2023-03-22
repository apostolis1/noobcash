from noobcash import Blockchain


def test_empty_validity():
    nodes = 5
    blockchain = Blockchain.Blockchain(nodes, difficulty=2)
    assert blockchain.validate_chain()


def test_genesis_validity():
    nodes = 5
    bootstrap_address = "bootstrap_address"
    blockchain = Blockchain.Blockchain(nodes, difficulty=2)
    blockchain.GenesisBlock(bootstrap_address)
    assert blockchain.validate_chain()
    assert len(blockchain.chain) == 1
    genesis_block = blockchain.chain[0]
    assert genesis_block.previousHash == "1"
    assert genesis_block.nonce == 0

