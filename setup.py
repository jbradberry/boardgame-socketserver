from setuptools import setup

setup(
    name='BoardServer',
    version='0.1dev',
    author='Jeff Bradberry',
    author_email='jeff.bradberry@gmail.com',
    packages=['boardserver'],
    scripts=['bin/board-serve.py'],
    entry_points={'jrb_board.games': []},
    license='LICENSE',
    description="A generic board game socket server.",
)
