.. Bitwarden CLI documentation master file, created by
   sphinx-quickstart on Wed Apr 11 13:25:23 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Bitwarden CLI's documentation!
=========================================
Cross Platform Bitwarden library and CLI with sudolikeaboss functionality.

Source repo lives @ https://fossil.birl.ca/bitwarden-cli/home 
But is mirrored to github: 
https://github.com/birlorg/bitwarden-cli

The repository houses both rust and python versions. The python version is more feature complete,
and is meant as a useable proof of concept or minimally viable program. It's still up for decision
how much functionality will be in the rust version, at least the crypto and the agent will be fully implemented.
Ideally the entire program would be in Rust, but rust is still a very new language and all the magic happy 
libraries one might want are not as fleshed out as the very mature python ecosystem.

This program, documentation, sources, etc. currently have no relationship with Bitwarden proper,
other than the main author pays a Families subscription fee, despite my actual Ciphers being stored in an off-line
self-hosted version of Bitwarden. Just because bitwarden *can* run over the public internet doesn't mean it has to.

Historic fun fact: all crypto code needed to be written and stored outside 
of the USA at one time.

Goals:
  * Be a useful bitwarden tool that works on Windows and Modern POSIX(macOS, BSD, Linux, etc) platforms.
  * Be able to work off-line completely if you wish. This mostly works now.

Non-Goals:
 * GUI's because writing them is misery. Bitwarden writes these for us, go pay
 them (regardless of self-hosted or not), I do.

The idea behind the CLI here is to think of the server as a place to push / pull
againt.  The local copy of the DB should be resilient and not erase anything
ever without explicitly saying so, so that full historic backups are possible.
think more like revision control. This is not fully fleshed out, at the time
of this writing..

Documentation Contents
----------------------

This part of the documentation guides you through all of the library's
usage patterns.

.. toctree::
  :maxdepth: 2

  installation
  commands
  security
  crypto
  troubleshooting

API Reference
-------------

If you are looking for information on a specific function, class, or
method, this part of the documentation is for you.

.. toctree::
   :maxdepth: 2

   internals

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
