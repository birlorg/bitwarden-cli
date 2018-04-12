Cross Platform Bitwarden library and CLI with sudolikeaboss functionality.

This repo houses both python and rust versions.

source repo lives @ https://fossil.birl.ca/bitwarden-cli/home 
But is mirrored to github: 
	https://github.com/birlorg/bitwarden-cli

Documentation: https://fossil.birl.ca/bitwarden-cli/doc/trunk/docs/build/html/index.html

Historic fun fact: all crypto code had to be written and stored outside 
of the USA at one time.

------------------------------------------------------------ 
EXAMPLE USAGE: 

ALIAS bw=bitwarden

GET HELP:
---------

$ bitwarden --help
Usage: bitwarden [OPTIONS] COMMAND [ARGS]...

  Bitwarden CLI program.

Options:
  --url TEXT
  --identurl TEXT
  --debug / --no-debug
  --db TEXT
  --help                Show this message and exit.

Commands:
  deletedb    ***THIS ERASES DATA*** Flush and empty the...
  fetch_name  fetch by name.
  fetch_uuid  fetch by UUID.
  find        find query in username,uri this does a simpe...
  login       login to server.
  logout      logout from server, stop agent and forget all...
  pull        pull all records from server, updating local...
  register    register a new account on server.
  slab        run in slab mode.
  sql         query the local data store using SQL.
  status      Show various statistics.

$ bitwarden find --help
Usage: bitwarden find [OPTIONS] QUERY

  find query in username,uri

   this does a simpe python string find i.e.:

       if query in username:

   but searches against username and first url

   You can export it in almost any format you wish with -f

   to get the password once you found an entry use fetch_uuid

   complicated example:

    bw find example.com -f tsv --no-headers | fzf | cut -f 1 | xargs bitwarden fetch_uuid -p

  which means: find all entries with example.com in them, use fzf to select
  a record and return only the password.

Options:
  -f, --format [csv|tsv|json|yaml|html|xls|xlsx|dbf|latex|ods]
  --headers / --no-headers
  --help                          Show this message and exit.

---- USAGE:

login:
	bw login nobody@example.com

it will prompt you for a password. if you are
a moron, you can specify it with --password <MY PASSWORD HERE> but don't be a
moron.


SLAB mode: "sudolikeaboss is a simple application that aims to make your life as
a dev, ops, or just a random person who likes to ssh and sudo into boxes much,
much easier by allowing you to access your bitwarden passwords on the terminal.
All you need is iterm2, bitwarden, a mac, and a dream." - from:
https://github.com/ravenac95/sudolikeaboss

slab command for iTerm2: 

export LANG=en_CA.UTF-8;export LOCALE=en_CA.UTF-8; /usr/local/bin/bitwarden slab

if you speak a different language, change the LOCALE and LANG settings above.

We support self-hosted installations just pass --url and --identurl The url will
be saved indefinitely, you do not need to set it every time (not even when you
login again, it will be remembered) see bw login --help for details.

-----------------------------------------------------------------------
SECURITY:

Bitwarden works by having a "master key" that is computed from your email and
password.  This needs to be kept "safe", but this is a CLI program. We could
store the master key on disk somewhere, but that's a bad idea.

The way we do this is with an in-memory 'agent' that listens on a 127.0.0.1 port
(configurable, but defaults to 6277) see: python/bitwarden/agent.py for all the
details. Bonus if you figure out why that port # :).  Ideally on POSIX platforms
it would use a socket on disk somewhere to communicate, but I wanted this to
work on Windows, so this is what we can do.. :)  patches welcoome to fix this up
on POSIX.

when you login, it starts up the agent, with a timeout set to the login
access_token timeout in seconds, since we do not currently support re-freshing
the token.  At the end of the token lease, the agent will kill itself and stop
running. (this is configurable, but not exported to the CLI yet -- patches
welcome)

The agent requires a token to get the master key from it's in-memory store.
This is currently 16 bytes of os.urandom() on startup and is stored on disk, but
changes every time a new agent runs.details are in python/bitwarden/db.py

This should mostly function fine on Windows, but is currently untested. bug
reports and patches welcome.

-----------------------------------------------------------------------
INSTALLATION

NOTE: the rust and python are 2 different implementations that are not
(currently) tied together.  you need not install both, just install one (the
pythone one currently if you want it to work)..

rust installation:
	clone the repo (either fossil or git)
	cd rust cargo build --release
	cp target/release/bitwarden /usr/local/bin/bitwarden
	then follow DB setup instructions below.
	
python installation:
	clone the repo (either fossil or git)
	cd python
	python3 setup.py install
	then follow DB setup instructions below.

	or better yet, use pipenv.

Common to both, the DB setup:
If you have liquibase and the sqlite JDBC driver,
run tools/lb.sh Otherwise copy over the blank DB (with schema installed) I
include in the tools/ dir the directory it belongs in is platform dependent, run
bitwarden and it will tell you.  Alternatively you can put the DB wherever you
like and always prepend --db to your commands (not recommended)


-------------------------------------------------------------------
TROUBLESHOOTING:
export DEBUG=true and then run bitwarden. or bitwarden --debug <cmd>

It will output LOTS
of stuff, some of it is security sensitive, so be careful when you copy/paste
the logs.

either email or reach out via fossil or github tickets.


--------------------------------
TODO planned(code welcome):

 * Finish off minimal implementation(MVP) of the python version (add, etc)
 * Build and release executables for mac and windows. build Makefile to automate
   this.
 * Finish off rust crypto and agent, port python version to use rust crypto and
   agent
 * Add server support (i.e. can also act like a server, so you could for
   instance have your local browser and desktop talk locally and work 100%
   off-line)
 * Fix up documentation in
   HTML(http://fossil-scm.org/index.html/doc/trunk/www/embeddeddoc.wiki) and
   make prettier.


Goals:
  * be a useful bitwarden tool that works on openBSD, debian, macOS and windows
    since these are the platforms I spend most of my time on.  UI is abysmal,
    thanks to @kspearrin for doing that slog, go pay him, I do.
  * Be able to work off-line completely if you wish. This mostly works now.

Non-Goals:
 * GUI's because writing them is misery. @kspearrin has this well-handled! YAY!


The idea behind the CLI here is to think of the server as a place to push / pull
againt.  The local copy of the DB should be resilient and not erase anything
ever without explicitly saying so, so that full historic backups are possible.
think more like revision control. This is not fully fleshed out, at the time
of this writing..


-----------

Contributing:

If you use fossil, just send me a place to pull from or setup a login and
email/contact me and I will give you push rights.  if you refuse to use fossil,
you can email me patches.  Or you can use github and pull-requests, I guess.

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you shall be dual licensed as above, without any
additional terms or conditions.

License

Licensed under either of

    Apache License, Version 2.0 (LICENSE-APACHE or http://www.apache.org/licenses/LICENSE-2.0)
    MIT license (LICENSE-MIT or http://opensource.org/licenses/MIT) at your option.

email: bitwarden @at@ birl.ca
