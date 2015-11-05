boardgame-socketserver
======================

A server for pluggable board game implementations, implemented using gevent.


Requirements
------------

You need to have the following system packages installed:

* Python >= 2.6


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

To connect a client as a human player, using `boardgame-socketplayer <https://github.com/jbradberry/boardgame-socketplayer>`_ ::

    $ board-play.py t3 human
    $ board-play.py t3 human 192.168.1.1 8000   # with ip addr and port
