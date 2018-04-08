target/debug/bitwarden: src/*.rs
	cargo build
release: src/*.rs
	cargo build --release
	touch release
test: src/*.rs
	cargo test
	touch test
