Bitwarden library and CLI

This repo houses both python and rust versions.

STATUS:
	python crypto totally works as a client as do these commands:
			login, sync, logout
		However this is just proof of concept and is not secure (stores key and token directly in the DB. )
		sync just decrypts the first Cipher's url, password and username.  It doesn't actually update the DB.
	rust crypto is not fully functional.. yet.

	Python's version will probably not get much more work from me, as I want the rust version to be the one I actually use.
	However, I'm using this to learn rust, so I may be a bit slow with it and might move along with python version.. 

source repo lives @ https://fossil.birl.ca/bitwarden/home
				But is mirrored to github:

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
	Otherwise copy over the blank DB (with schema installed) I include in the tools/ dir:
		mkdir -p ~/.config/bitwarden
		cp tools/bitwarden.sqlite ~/.config/bitwarden

API docs: https://github.com/jcs/bitwarden-ruby/blob/master/API.md

Library dependency docs:
	clap: https://clap.rs/
		https://github.com/kbknapp/clap-rs

