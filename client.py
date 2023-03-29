import requests

MASTER_IP = "127.0.0.1:5000"


def get_ring():
    url = f"http://{MASTER_IP}/nodes/all"
    res = requests.get(url=url)
    return res.json()


def view_transactions(args):
    print("Transactions are...")
    return


def create_transaction(args):
    print("Create transaction")


if __name__ == '__main__':

    from argparse import ArgumentParser
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='name',help='')

    parser_t = subparsers.add_parser('t', help='a help')
    parser_t.add_argument('-s', '--sender', type=str, help='sender id, eg id_0')
    parser_t.add_argument('-r', '--receiver', type=str, help='receiver id, eg id_0')
    parser_t.add_argument('-a', '--amount',  type=int, help='amount of money to send')
    parser_t.set_defaults(func=create_transaction)

    parser_view = subparsers.add_parser('view', help='view transactions')
    parser_view.set_defaults(func=view_transactions)

    args = parser.parse_args()
    args.func(args)
    ring = get_ring()

