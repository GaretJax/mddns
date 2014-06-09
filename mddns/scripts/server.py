from mddns.server import runserver
import argparse


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--interval', type=int, default=10)
    parser.add_argument('-t', '--token', default='/var/run/mddns/token')
    parser.add_argument('-p', '--port', default=7253, type=int)
    parser.add_argument('-i', '--interface', default='0.0.0.0')
    parser.add_argument('ipfile')
    parser.add_argument('endpoint')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    server_address = (args.interface, args.port)
    runserver(server_address, args.ipfile, args.token, args.interval,
              args.endpoint)
