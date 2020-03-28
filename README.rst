boardgame-socketserver
======================

A server for pluggable board game implementations, implemented using gevent.

The server included here is designed to work with
`jbradberry/boardgame-socketplayer
<https://github.com/jbradberry/boardgame-socketplayer>`_ and the Monte
Carlo Tree Search implementation `jbradberry/mcts
<https://github.com/jbradberry/mcts>`_.


Requirements
------------

* Python 2.7, 3.5+; PyPy is not supported by the server
* gevent
* six


Getting Started
---------------

To set up your local environment you should create a virtualenv and
install everything into it. ::

    $ mkvirtualenv boardgames

Pip install this repo, either from a local copy, ::

    $ pip install -e boardgame-socketserver

or from github, ::

    $ pip install git+https://github.com/jbradberry/boardgame-socketserver

To run the server with (for example) `Ultimate Tic Tac Toe
<https://github.com/jbradberry/ultimate_tictactoe>`_ ::

    $ board-serve.py t3

Optionally, the server ip address and port number can be added ::

    $ board-serve.py t3 0.0.0.0
    $ board-serve.py t3 0.0.0.0 8000

To connect a client as a human player, using `boardgame-socketplayer
<https://github.com/jbradberry/boardgame-socketplayer>`_ ::

    $ board-play.py t3 human
    $ board-play.py t3 human 192.168.1.1 8000   # with ip addr and port

To connect a client using one of the compatible `Monte Carlo Tree
Search AI <https://github.com/jbradberry/mcts>`_ players ::

    $ board-play.py t3 jrb.mcts.uct    # number of wins metric
    $ board-play.py t3 jrb.mcts.uctv   # point value of the board metric


Games
-----

Compatible games that have been implemented include:

* `Reversi <https://github.com/jbradberry/reversi>`_
* `Connect Four <https://github.com/jbradberry/connect-four>`_
* `Ultimate (or 9x9) Tic Tac Toe
  <https://github.com/jbradberry/ultimate_tictactoe>`_
* `Chong <https://github.com/jbradberry/chong>`_
