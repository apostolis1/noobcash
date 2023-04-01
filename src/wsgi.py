from rest_app import create_app


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    if port == 5000:
        is_first = True
    else:
        is_first = False
    app = create_app(port, is_first)
    app.run(host='0.0.0.0', port=port, threaded=False)
