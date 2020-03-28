#!/usr/bin/env python
from __future__ import absolute_import
import sys
from pkg_resources import iter_entry_points
from boardserver import server


board_plugins = dict(
    (ep.name, ep.load())
    for ep in iter_entry_points('jrb_board.games')
)


args = sys.argv[1:]
addr, port = None, None

board = board_plugins[args[0]]

if len(args) > 1:
    addr = args[1]
if len(args) > 2:
    port = int(args[2])


api = server.Server(board(), addr, port)
api.run()
