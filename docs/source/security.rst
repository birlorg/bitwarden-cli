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
work on Windows, so this is what we can do.. :(  patches welcoome to fix this up
on POSIX.

when you login, it starts up the agent, with a timeout set to the login
access_token timeout in seconds, since we do not currently support re-freshing
the token.  At the end of the token lease, the agent will kill itself and stop
running. (this is configurable, but not exported to the CLI yet -- patches
welcome)

The agent requires a token to get the master key from it's in-memory store.
This is currently 16 bytes of os.urandom() on startup and is stored on disk, but
changes every time a new agent runs.details are in python/bitwarden/db.py

Python, for security code?!
---------------------------------

Well, to be fair the only other Bitwarden clients
are written in Javascript. But mostly python got me to an MVP very quickly,
so I can prototype how it all works and ensure a decent design, etc. I plan
on converting at least the agent and the crypto to Rust, but Crypto in Rust
is not well-tested and battle-hardened yet, since it's such a new ecosystem,
there has been some work on TLS in Rust, but we don't need TLS, we need other
crypto primitives. Python has solid, well-established crypto code. Dure it's
dynamically typed, and it's hard to ensure things really are gone when you
say they are. You can run the agent in Rust today, but it's not fully fleshed
out and is not integrated into the python package, yet. Once I figure that
all out, there will be no long-term secrets in Python, it will only
have short-lived secrets.

Security sensitive reports can be sent to:
bitwarden @at@ birl.ca
sending me security sensitive bits that also affect bitwarden proper will also be shared with them.

All new code commits by me should ne GPG signed now, as well as the releases on pypi.

You can GPG sign messages to me available via  keyserver hkps://hkps.pool.sks-keyservers.net
and here:

-----BEGIN PGP PUBLIC KEY BLOCK-----

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
Zr45w6sqPdt+nztUc6I+QHK2pgA+
=O8VJ
-----END PGP PUBLIC KEY BLOCK-----
