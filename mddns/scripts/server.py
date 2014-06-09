from mddns.server import runserver
import argparse
from configparser import SafeConfigParser


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=argparse.FileType())
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    config = SafeConfigParser()
    config.read(args.config)
    runserver(config)
