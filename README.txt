Cross Platform Bitwarden library and CLI with sudolikeaboss functionality.

This repo houses both python and rust versions.

STATUS:
	python version works, rust version does not fully work yet (pull requests, patches, etc welcome)
	This is very minimally working *for me* on macOS 10.13.  Bug reports, patches, etc. are welcome. I'm not yet using this in "production" i.e. as my daily driver, I'm still on 1password, but will now focus on moving my data over.

source repo lives @ https://fossil.birl.ca/bitwarden-cli/home
	But is mirrored to github: https://github.com/birlorg/bitwarden-cli
	Historic fun fact: all crypto code had to be stored outside the USA.

------------------------------------------------------------
EXAMPLE USAGE: 

ALIAS bw=bitwarden

GET HELP:
---------

$ bitwarden --help
Usage: bitwarden [OPTIONS] COMMAND [ARGS]...

  CLI main

Options:
  --url TEXT
  --identurl TEXT
  --debug / --no-debug
  --db TEXT
  --help                Show this message and exit.

Commands:
  deletedb    ***THIS ERASES DATA*** Flush and empty the...
  fetch_uuid  fetch by UUID.
  login       login to server.
  logout      logout from server, stop agent and forget all...
  pull        pull all records from server, updating local...
  register    register a new account on server.
  slab        run in slab mode.
  sql         query the local data store using SQL.
  status      Show various statistics.

$ bw sql --help
	Usage: bitwarden sql [OPTIONS] QUERY

	  query the local data store using SQL.

	  Basically just a wrapper around the records CLI.

	  Query: can either be a filename to run or a SQL query string. Query
	  Parameters:     Query parameters can be specified in key=value format, and
	  injected     into your query in :key format e.g.:     $ bitwarden sql
	  'select created_at from ciphers where uuid ~= :uuid' -p
	  uuid=84c1bf0a-b0e8-49c4-8e58-8d0fc0a247c4

	  Examples:     bw sql "select uuid from ciphers where uuid is not null"

	Options:
	  -p, --params TEXT
	  -f, --format [csv|tsv|json|yaml|html|xls|xlsx|dbf|latex|ods]
	  --help                          Show this message and exit.

login:
	bw login nobody@example.com
it will prompy you for a password. if you are a moron, you can specify it with --password <MY PASSWORD HERE> but don't be a moron.


SLAB mode:
	"sudolikeaboss is a simple application that aims to make your life as a dev, ops, or just a random person who likes to ssh and sudo into boxes much, much easier by allowing you to access your bitwarden passwords on the terminal. All you need is iterm2, bitwarden, a mac, and a dream." - from: https://github.com/ravenac95/sudolikeaboss

We support self-hosted installations just pass --url and --identurl
	The url will be saved indefinitely, you do not need to set it every time (not even when you login again, it will be remembered)
	see bw login --help for details.

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

NOTE: the rust and python are 2 different implementations that are not (currently) tied together.
you need not install both, just install one (the pythone one currently if you want it to work)..

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


--------------------------------
TODO planned(code welcome):

 * finish off minimal implementation of the python version (search, add, etc)
 * build and release executables for mac and windows. build Makefile to automate this.
 * finish off rust crypto and agent, port python version to use rust crypto and agent
 * add server support (i.e. can also act like a server, so you could for instance have your local browser and desktop talk locally and work 100% off-line)
 * fix up documentation in HTML(http://fossil-scm.org/index.html/doc/trunk/www/embeddeddoc.wiki) and make prettier.


Goals:
  * be a useful bitwarden tool that works on openBSD, debian, macOS and windows since these are the platforms I spend most of my time on.  UI is abysmal, thanks to @kspearrin for doing that slog, go pay him.
  * be able to work off-line completely if you wish. (slab mode already does this..mostly)

Non-Goals:
 * GUI's because writing them is misery. @kspearrin has this well-handled! YAY!

---------------------------------------------
repo stuff:

tools/fsl2git.sh
tools/git2fsl.sh
cd ../bitwarden-cli.git
git checkout trunk
git push -u origin trunk

