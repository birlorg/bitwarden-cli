extern crate bitwarden;

#[macro_use]
extern crate rouille;

fn main() {
    println!("Now listening on localhost:8000");

    // The `start_server` starts listening forever on the given address.
rouille::start_server("localhost:8000", move |request| {

}
