import requests

MASTER_IP = "127.0.0.1:5000"


def get_ring() -> dict:
    url = f"http://{MASTER_IP}/nodes/all"
    res = requests.get(url=url)
    return res.json()


def view_transactions(args):
    print("Transactions are...")

    return


def create_transaction(args):
    print("Create transaction")
    print(args)
    ring = get_ring()
    sender = args.sender
    receiver = args.receiver
    amount = args.amount
    try:
        base_url = ring[sender]['url']
    except KeyError:
        print(f"Not a valid sender, valid options are {[i for i in ring.keys()]}")
        return
    try:
        receiver_address = ring[receiver]['public_key']
    except KeyError:
        print(f"Not a valid receiver, valid options are {[i for i in ring.keys()]}")
        return
    url = f"http://{base_url}/transactions/new"
    data = {
        'receiver_address': receiver_address,
        'amount': amount
    }
    res = requests.post(url=url, json=data)
    if res.status_code == 200:
        print("Successfully created transaction")
    else:
        print(f"Something went wrong, got status code {res.status_code}")
    return


def transactions_from_file(args):
    file = args.file
    sender = args.sender
    print(args)
    print(f"Creating transactions from file {file}")
    ring = get_ring()
    try:
        with open(file, 'r') as f:
            for line in f.readlines():
                line_split = line.split()
                receiver = line_split[0]
                amount = int(line_split[1])
                try:
                    base_url = ring[sender]['url']
                except KeyError:
                    print(f"Not a valid sender, valid options are {[i for i in ring.keys()]}")
                    return
                try:
                    receiver_address = ring[receiver]['public_key']
                except KeyError:
                    print(f"Not a valid receiver, valid options are {[i for i in ring.keys()]}")
                    return
                url = f"http://{base_url}/transactions/new"
                data = {
                    'receiver_address': receiver_address,
                    'amount': amount
                }
                res = requests.post(url=url, json=data)
    except Exception as e:
        print(e)
    return


def balance(args):
    print("Showing balance")


if __name__ == '__main__':

    from argparse import ArgumentParser
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='name',help='')

    parser_t = subparsers.add_parser('t', help='a help')
    parser_t.add_argument('-s', '--sender', type=str, help='sender id, eg id0')
    parser_t.add_argument('-r', '--receiver', type=str, help='receiver id, eg id0')
    parser_t.add_argument('-a', '--amount',  type=int, help='amount of money to send')
    parser_t.set_defaults(func=create_transaction)

    parser_view = subparsers.add_parser('view', help='view transactions')
    parser_view.set_defaults(func=view_transactions)

    parser_balance = subparsers.add_parser('balance', help='view transactions')
    parser_balance.set_defaults(func=balance)

    parser_file = subparsers.add_parser('f', help='create transactions from file')
    parser_file.add_argument('-s', '--sender', type=str, help='sender id, eg id0')
    parser_file.add_argument('-f', '--file', type=str, help='file path')
    parser_file.set_defaults(func=transactions_from_file)

    args = parser.parse_args()
    args.func(args)
