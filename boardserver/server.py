from __future__ import absolute_import
from __future__ import print_function
import json
import random
import sys

import gevent, gevent.local, gevent.queue, gevent.server
from six.moves import range


class Server(object):
    def __init__(self, board, addr=None, port=None):
        self.board = board
        self.states = []
        self.local = gevent.local.local()
        self.server = None
        # player message queues
        self.players = dict((x, gevent.queue.Queue())
                            for x in range(1, self.board.num_players+1))
        # random player selection
        self.player_numbers = gevent.queue.JoinableQueue()

        self.addr = addr if addr is not None else '127.0.0.1'
        self.port = port if port is not None else 4242

    def game_reset(self):
        while True:
            # initialize the game state
            del self.states[:]
            state = self.board.starting_state()
            self.states.append(state)

            # update all players with the starting state
            state = self.board.to_json_state(state)
            # board = self.board.get_description()
            for x in range(1, self.board.num_players+1):
                self.players[x].put_nowait({
                    'type': 'update',
                    'board': None,  # board,
                    'state': state,
                })

            # randomize the player selection
            players = list(range(1, self.board.num_players+1))
            random.shuffle(players)
            for p in players:
                self.player_numbers.put_nowait(p)

            # block until all players have terminated
            self.player_numbers.join()

    def run(self):
        game = gevent.spawn(self.game_reset)
        self.server = gevent.server.StreamServer((self.addr, self.port),
                                                 self.connection)
        print("Starting server...")
        self.server.serve_forever()

        # FIXME: need a way of nicely shutting down.
        # print "Stopping server..."
        # self.server.stop()

    def connection(self, socket, address):
        print("connection:", socket)
        self.local.socket = socket
        if self.player_numbers.empty():
            self.send({
                'type': 'decline', 'message': "Game in progress."
            })
            socket.close()
            return

        self.local.run = True
        self.local.player = self.player_numbers.get()
        self.send({'type': 'player', 'message': self.local.player})

        while self.local.run:
            data = self.players[self.local.player].get()
            try:
                self.send(data)
                if data.get('winners') is not None:
                    self.local.run = False

                elif data.get('state', {}).get('player') == self.local.player:
                    message = ''
                    while not message.endswith('\r\n'):
                        message += socket.recv(4096).decode('utf-8')
                    messages = message.rstrip().split('\r\n')
                    self.parse(messages[0]) # FIXME: support for multiple messages
                                            #        or out-of-band requests
            except Exception as e:
                print(e)
                socket.close()
                self.player_numbers.put_nowait(self.local.player)
                self.players[self.local.player].put_nowait(data)
                self.local.run = False
        self.player_numbers.task_done()

    def parse(self, msg):
        try:
            data = json.loads(msg)
            if data.get('type') != 'action':
                raise Exception
            self.handle_action(data)
        except Exception:
            self.players[self.local.player].put({
                'type': 'error', 'message': msg
            })

    def handle_action(self, data):
        action = self.board.to_compact_action(data['message'])
        if not self.board.is_legal(self.states[-1], action):
            self.players[self.local.player].put({
                'type': 'illegal', 'message': data['message'],
            })
            return

        self.states.append(self.board.next_state(self.states, action))
        state = self.board.to_json_state(self.states[-1])

        # TODO: provide a json object describing the board used
        data = {
            'type': 'update',
            'board': None,
            'state': state,
            'last_action': {
                'player': self.board.previous_player(self.states[-1]),
                'action': data['message'],
                'sequence': len(self.states),
            },
        }
        if self.board.is_ended(self.states[-1]):
            data['winners'] = self.board.win_values(self.states[-1])
            data['points'] = self.board.points_values(self.states[-1])

        for x in range(1, self.board.num_players+1):
            self.players[x].put(data)

    def send(self, data):
        self.local.socket.sendall("{0}\r\n".format(json.dumps(data)).encode('utf-8'))
