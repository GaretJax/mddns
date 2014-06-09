from mddns.server import runserver


def main():
    server_address = ('0.0.0.0', 7000)
    runserver(server_address, 'ip.txt', 'token.txt', 10)
