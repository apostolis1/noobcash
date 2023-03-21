from noobcash import Blockchain


def test_blockchain():
    nodes = 5
    bootstrap_address = "bootstrap_address"
    blockchain = Blockchain.Blockchain(nodes)
    assert blockchain.validate_chain()
    blockchain.GenesisBlock(bootstrap_address)
    assert blockchain.validate_chain()
