Cross Platform Bitwarden library and CLI with sudolikeaboss functionality.

This repo houses both python and rust versions.

STATUS:
	python version works, rust version does not fully work yet (pull requests, patches, etc welcome)
	This is very minimally working *for me* on macOS 10.13.  Bug reports, patches, etc. are welcome. I'm not yet using this in "production" i.e. as my daily driver, I'm still on 1password, but will now focus on moving my data over.

source repo lives @ https://fossil.birl.ca/bitwarden-cli/home
				But is mirrored to github: https://github.com/birlorg/bitwarden-cli

------------------------------------------------------------
EXAMPLE USAGE: (output not shown)

ALIAS bw=bitwarden

get help:
	bw --help

login:
	bw login nobody@example.com
it will prompy you for a password. if you are a moron, you can specify it with --password <MY PASSWORD HERE> but don't be a moron.

sync all the data from the server locally:
	bw sync

run in slab (sudolikeaboss) mode (details below)
	bw slab

logout, stop the agent and forget all the keys:	
	bw logout

SLAB mode:
	"sudolikeaboss is a simple application that aims to make your life as a dev, ops, or just a random person who likes to ssh and sudo into boxes much, much easier by allowing you to access your bitwarden passwords on the terminal. All you need is iterm2, bitwarden, a mac, and a dream." - from: https://github.com/ravenac95/sudolikeaboss

We support self-hosted installations just pass --url
	The url will be saved indefinitely, you do not need to set it every time (not even when you login again, it will be remembered)

-----------------------------------------------------------------------
SECURITY:

Bitwarden works by having a "master key" that is computed from your email and password.
This needs to be kept "safe", but this is a CLI program. We could store the master key on disk somewhere, but that's a bad idea.

The way we do this is with an in-memory 'agent' that listens on a 127.0.0.1 port (configurable, but defaults to 6277) see: python/bitwarden/agent.py for all the details. Bonus if you figure out why that port # :).  Ideally on POSIX platforms it would use a socket on disk somewhere to communicate, but I wanted this to work on Windows, so this is what we can do.. :)  patches welcoome to fix this up on POSIX.

when you login, it starts up the agent, with a timeout set to the login access_token timeout in seconds, since we do not currently support re-freshing the token.  At the end of the token lease, the agent will kill itself and stop running. (this is configurable, but not exported to the CLI yet -- patches welcome)

The agent requires a token to get the master key from it's in-memory store.  This is currently 16 bytes of os.urandom() on startup and is stored on disk, but changes every time a new agent runs.details are in python/bitwarden/db.py

This should mostly function fine on Windows, but is currently untested. bug reports and patches welcome.

-----------------------------------------------------------------------
INSTALLATION


rust installation:
	clone the repo (either fossil or git)
	cd rust
	cargo build --release
	cp target/release/bitwarden /usr/local/bin/bitwarden
	follow DB setup instructions below.
	
python installation:
	clone the repo (either fossil or git)
	cd python
	python3 setup.py install
	follow DB setup instructions below.

Common to both, the DB setup:
	If you have liquibase and the sqlite JDBC driver, run tools/lb.sh
	Otherwise copy over the blank DB (with schema installed) I include in the tools/ dir
	the directory it belongs in is platform dependent, run bitwarden and it will tell you.
	Alternatively you can put the DB wherever you like and always prepend --db to your commands (not recommended)


-------------------------------------------------------------------
TROUBLESHOOTING:
export DEBUG=true
and then run bitwarden.  It will output LOTS of stuff, some of it is security sensitive, so be careful when you copy/paste the logs.

-- fix up documentation: http://fossil-scm.org/index.html/doc/trunk/www/embeddeddoc.wiki
