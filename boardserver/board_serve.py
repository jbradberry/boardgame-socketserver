#!/usr/bin/env python
from importlib.metadata import entry_points
import sys

from boardserver import server


board_plugins = {ep.name: ep.load() for ep in entry_points(group='jrb_board.games')}


def main():
    args = sys.argv[1:]
    addr, port = None, None

    board = board_plugins[args[0]]

    if len(args) > 1:
        addr = args[1]
    if len(args) > 2:
        port = int(args[2])


    api = server.Server(board(), addr, port)
    api.run()
