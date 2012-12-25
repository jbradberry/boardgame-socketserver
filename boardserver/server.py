import random
import ast
import gevent, gevent.local, gevent.queue, gevent.server


class Server(object):
    def __init__(self, board):
        self.board = board
        self.states = []
        self.local = gevent.local.local()
        self.server = None
        self.player_numbers = None
        self.players = None

    def run(self):
        self.sender = {'player': self.send_player,
                       'update': self.send_update,
                       'action': self.send_action,
                       'winner': self.send_winner,
                       'error': self.send_error,
                       'illegal': self.send_illegal,}

        # initialize the game state
        self.states.append(self.board.start())

        # randomize the player selection
        players = range(1, self.board.num_players+1)
        random.shuffle(players)
        self.player_numbers = gevent.queue.Queue()
        for p in players:
            self.player_numbers.put_nowait(p)

        # set up player message queues
        self.players = dict((x, gevent.queue.Queue())
                            for x in xrange(1, self.board.num_players+1))

        # update all players with the starting state and mark player 1 to move
        for x in xrange(1, self.board.num_players+1):
            self.players[x].put(('player', (x,)))
            self.players[x].put(('update', (None, self.states[-1])))
        self.players[1].put(('action', ()))

        self.server = gevent.server.StreamServer(
            ('0.0.0.0', 4242), self.connection)
        print "Starting server..."
        self.server.serve_forever()

    def connection(self, socket, address):
        self.local.socket = socket
        if self.player_numbers.empty():
            self.send_decline()
            return

        self.local.player = self.player_numbers.get()
        while True:
            action, args = self.players[self.local.player].get()
            self.sender[action](*args)
            if action == 'action':
                message = socket.recv(4096)
                messages = message.rstrip().split('\r\n')
                self.parse(messages[0]) # FIXME: support for multiple messages
                                        #        or out-of-band requests

    def parse(self, msg):
        if msg.startswith('play '):
            self.handle_play(ast.literal_eval(msg[5:]))
            return
        self.players[self.local.player].put(('error', (msg,)))

    def handle_play(self, play):
        if not self.board.is_legal(self.states[-1], play):
            self.players[self.local.player].put(('illegal', (play,)))
            return

        self.states.append(self.board.play(self.states[-1], play))
        for x in xrange(1, self.board.num_players+1):
            self.players[x].put(('update', (play, self.states[-1])))

        winner = self.board.winner(self.states)
        if winner:
            for x in xrange(1, self.board.num_players+1):
                self.players[x].put(('winner', (winner,)))
            print "Stopping server..."
            self.server.stop()
        else:
            next_player = self.local.player % self.board.num_players + 1
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
        raise gevent.GreenletExit
