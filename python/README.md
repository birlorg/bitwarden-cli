README for bitwarden in python

Crypto: https://help.bitwarden.com/crypto.html?
and https://github.com/jcs/bitwarden-ruby/blob/master/API.md

There is a command line program 'bitwarden' that handles everything.
But we need to keep the decryption key safe from prying eyes and code.  The way we do this is with an in-memory 'agent' that listens on a 127.0.0.1 port (configurable, but defaults to 6277)

when you login, it starts up the agent, with a timeout set to the login access_token timeout in seconds, since we do not currently support re-freshing the token.  At the end of the token lease, the agent will kill itself and stop running. (this is configurable, but not exported to the CLI yet -- patches welcome)

This should mostly function fine on Windows, but is currently untested. bug reports and patches welcome.

install:
	use pipenv:
		pipenv install 
		alias bw=`pipenv --venv`/bin/bitwarden
	or be old-school boring:
		python3 setup.py install
		executable should now be in your $PATH
	Eventually I'll build actual binaries -- patches using py2app and py2exe welcome.

example session:

ALIAS bw=bitwarden

get help:
	bw --help

login:
	bw --url https://api.bitwarden.com login nobody@example.com
it will prompy you for a password. if you are a moron, you can specify it with --password <MY PASSWORD HERE> but don't be a moron.
	the url will be saved indefinitely, you do not need to set it every time (not even when you login again, it will be remembered)

sync all the data from the server locally:
	bw sync

run in sudolikeaboss mode (details below)
	bw slab

search for an entry:
	bw url_search iamarockstar.com

fetch an entry:
	bw fetch <ID>

logout, stop the agent and forget all the keys:	
	bw logout

SLAB mode:
	sudolikeaboss is a simple application that aims to make your life as a dev, ops, or just a random person who likes to ssh and sudo into boxes much, much easier by allowing you to access your bitwarden passwords on the terminal. All you need is iterm2, bitwarden, a mac, and a dream.
	
	inspiration from: https://github.com/ravenac95/sudolikeaboss
