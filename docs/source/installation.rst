.. _installation:

Installation
=============


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
