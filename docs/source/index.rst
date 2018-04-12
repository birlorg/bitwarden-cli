.. Bitwarden CLI documentation master file, created by
   sphinx-quickstart on Wed Apr 11 13:25:23 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Bitwarden CLI's documentation!
=========================================
Cross Platform Bitwarden library and CLI with sudolikeaboss functionality.

This repo houses both python and rust versions.

STATUS: python version works, rust version does not fully work yet (pull
requests, patches, etc welcome) 
patches, bug reports and code welcome.
the python version is meant as an MVP.
Unknown at this time if the python version will just call out to rust
or if rust will entirely replace python.
at the very least the agent should exist in rust, and not python.

source repo lives @ https://fossil.birl.ca/bitwarden-cli/home 
But is mirrored to github: 
https://github.com/birlorg/bitwarden-cli
Historic fun fact: all crypto code had to be stored outside 
of the USA at one time.


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

Documentation Contents
----------------------

This part of the documentation guides you through all of the library's
usage patterns.

.. toctree::
  :maxdepth: 2

  installation
  commands
  security
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
