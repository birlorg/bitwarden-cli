.. _security:

Security
=============



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