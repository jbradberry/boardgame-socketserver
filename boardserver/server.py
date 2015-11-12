import sys
import random
import ast
import gevent, gevent.local, gevent.queue, gevent.server


class Server(object):
    def __init__(self, board, addr=None, port=None):
        self.board = board
        self.states = []
        self.local = gevent.local.local()
        self.server = None
        # player message queues
        self.players = dict((x, gevent.queue.Queue())
                            for x in xrange(1, self.board.num_players+1))
        # random player selection
        self.player_numbers = gevent.queue.JoinableQueue()

        self.sender = {'player': self.send_player,
                       'update': self.send_update,
                       'action': self.send_action,
                       'winner': self.send_winner,
                       'error': self.send_error,
                       'illegal': self.send_illegal,}

        self.addr = addr if addr is not None else '127.0.0.1'
        self.port = port if port is not None else 4242

    def game_reset(self):
        while True:
            # initialize the game state
            del self.states[:]
            self.states.append(self.board.start())

            # update all players with the starting state and mark
            # player 1 to move
            for x in xrange(1, self.board.num_players+1):
                self.players[x].put_nowait(('update', (None, self.states[-1])))
            self.players[1].put_nowait(('action', ()))

            # randomize the player selection
            players = range(1, self.board.num_players+1)
            random.shuffle(players)
            for p in players:
                self.player_numbers.put_nowait(p)

            # block until all players have terminated
            self.player_numbers.join()

    def run(self):
        game = gevent.spawn(self.game_reset)
        self.server = gevent.server.StreamServer((self.addr, self.port),
                                                 self.connection)
        print "Starting server..."
        self.server.serve_forever()

        # FIXME: need a way of nicely shutting down.
        # print "Stopping server..."
        # self.server.stop()

    def connection(self, socket, address):
        print "connection:", socket
        self.local.socket = socket
        if self.player_numbers.empty():
            self.send_decline()
            return

        self.local.run = True
        self.local.player = self.player_numbers.get()
        self.sender['player'](self.local.player)

        action, update = None, (None, self.states[-1])
        while self.local.run:
            action, args = self.players[self.local.player].get()
            try:
                self.sender[action](*args)
                if action == 'action':
                    message = socket.recv(4096)
                    messages = message.rstrip().split('\r\n')
                    self.parse(messages[0]) # FIXME: support for multiple messages
                                            #        or out-of-band requests
                elif action == 'update':
                    update = args
            except Exception as e:
                print e
                socket.close()
                self.player_numbers.put_nowait(self.local.player)
                self.players[self.local.player].put_nowait(('update', update))
                if action == 'action':
                    self.players[self.local.player].put_nowait(('action', ()))
                self.local.run = False
        self.player_numbers.task_done()

    def parse(self, msg):
        if msg.startswith('play '):
            self.handle_play(ast.literal_eval(msg[5:]))
            return
        self.players[self.local.player].put(('error', (msg,)))

    def handle_play(self, play):
        if not self.board.is_legal(self.states, play):
            self.players[self.local.player].put(('illegal', (play,)))
            return

        self.states.append(self.board.next_state(self.states[-1], play))
        for x in xrange(1, self.board.num_players+1):
            self.players[x].put(('update', (play, self.states[-1])))

        winner = self.board.winner(self.states)
        if winner:
            for x in xrange(1, self.board.num_players+1):
                self.players[x].put(('winner', (winner,)))
        else:
            next_player = self.board.current_player(self.states[-1])
            self.players[next_player].put(('action', ()))

    def send_player(self, player):
        self.local.socket.sendall("player {0}\r\n".format(player))

    def send_decline(self):
        self.local.socket.sendall("decline 'Game in progress.'\r\n")
        self.local.socket.close()

    def send_error(self, msg):
        self.local.socket.sendall("error {0!r}\r\n".format(msg))
        self.players[self.local.player].put(('action', ()))

    def send_illegal(self, play):
        self.local.socket.sendall("illegal {0!r}\r\n".format(play))
        self.players[self.local.player].put(('action', ()))

    def send_update(self, play, state):
        self.local.socket.sendall(
            "update ({0!r}, {1!r})\r\n".format(play, state))

    def send_action(self):
        self.local.socket.sendall("action\r\n")

    def send_winner(self, winner):
        self.local.socket.sendall("winner {0}\r\n".format(winner))
        self.local.run = False
