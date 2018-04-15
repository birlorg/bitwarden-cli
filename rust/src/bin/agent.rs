/*
 *
 * 
 * This code works now. it needs some serious cleanup however. wow is it gross.
 * 
 * learn how to build and embed into shipped python:
 *      https://github.com/mckaymatt/cookiecutter-pypackage-rust-cross-platform-publish
 *      https://pypi.python.org/pypi/setuptools-rust
 *      https://github.com/getsentry/milksnake
 *      https://github.com/getsentry/libsourcemap/blob/master/setup.py
 *
 * echo '{"agent_token":"super secret", "master_key": "secret", "timeout":30, "port":"6278"}' |
 * agent
 *
 * and the request:
 *curl --data '{"agent_token":"super secret"}' --header "Content-Type: application/json" http://localhost:6278
 *
 */
//#[macro_use]
extern crate serde;
#[macro_use]
extern crate serde_derive;

extern crate serde_json;
// #[macro_use]
extern crate bitwarden;
extern crate daemonize;
extern crate secstr;
extern crate tiny_http;

// use rouille::Request;
// use rouille::Response;
// use std::collections::HashMap;
use std::io;
// use std::sync::Mutex;
use secstr::*;
// use std::time::{SystemTime, UNIX_EPOCH};
use std::time::{Duration, Instant};
use std::fs::File;
use daemonize::Daemonize;

// This struct contains the data that we store on the server about each client.
#[derive(Debug, Clone)]
struct SessionData {
	login: String,
}

#[derive(Deserialize)]
struct Setup {
	master_key: String,
	agent_token: String,
	timeout: u64,
	port: isize,
	agent_location: String,
}
/* 
struct Secrets {
    agent_token: SecStr,
    master_key: SecStr,
} 
*/
#[derive(Deserialize)]
struct TokenRequest {
	agent_token: String,
	exit: bool,
}
#[derive(Serialize)]
struct TokenResponse {
	master_key: String,
	error: String,
}
//
//  echo '{"agent_token":"super secret", "master_key": "secret", "timeout":30, "port":"6278"}' |
//  target/debug/agent

fn serve(setup: Setup) {
	let secret_agent_token = SecStr::from(setup.agent_token);
	let secret_master_key = setup.master_key;
	// let secrets = Secrets {
	//    agent_token: SecStr::from(setup.agent_token),
	//   master_key: SecStr::from(setup.master_key),
	// };
	// set timeout to 1 year if bitwarden doesn't give us one.
	let mut timeout = Duration::new(31536000,0);
	if setup.timeout > 0 {
		timeout = Duration::new(setup.timeout, 0);
	}
	let port = setup.port;
	let server = tiny_http::Server::http(format!("localhost:{}", port)).unwrap();
	println!("Now listening on localhost:{}", port);

	let start_time = Instant::now();
	let mut exit = true;
	let receive_timeout = Duration::new(1, 0);

	// loop for freaking ever, or agent_timeout happens..
	while exit {
		// block for up to 1 second.
		let request = match server.recv_timeout(receive_timeout) {
			Ok(rq) => rq,
			Err(e) => {
				println!("error: {}", e);
				break;
			}
		};
		if request.is_some() {
			let mut rq = request.unwrap();
			let url = rq.url().to_string();
			let method = rq.method().to_string();
			let mut content_type = String::from("");
			for header in rq.headers() {
				println!("header: {} : {}", header.field, header.value);
				if header.field.to_string() == "Content-Type" {
					content_type = header.value.to_string();
				}
			}
			println!(
				"remote request from:{} requesting: {} method:{} content_type:{} ",
				rq.remote_addr().to_string(),
				url,
				method,
				content_type
			);
			// assert_eq(request.remote_addr(), "127.0.0.1");
			if method == "POST" {
				println!("post!");
				if content_type == "application/json" {
					println!("JSON!");
					let mut content = String::new();
					rq.as_reader().read_to_string(&mut content).unwrap();
					let token_request: TokenRequest = serde_json::from_str(&content).unwrap();
					if SecStr::from(token_request.agent_token) == secret_agent_token {
						if token_request.exit == true {
							println!("exit requested");
							std::process::exit(0);
						}
						// let local_master_key = secret_master_key;
						let token_response = TokenResponse {
							error: "".to_string(),
							master_key: secret_master_key.clone().to_string(),
						};
						let response = tiny_http::Response::from_string(
							serde_json::to_string(&token_response).unwrap(),
						);
						// return Response::json(&token_response);
						let _ = rq.respond(response);
					} else {
						let token_response = TokenResponse {
							error: "Invalid agent_token.".to_string(),
							master_key: "".to_string(),
						};
						let response = tiny_http::Response::from_string(
							serde_json::to_string(&token_response).unwrap(),
						);
						let _ = rq.respond(response);
					}
				} else {
					let token_response = TokenResponse {
						error: "Must send Content-Type: application/json".to_string(),
						master_key: "".to_string(),
					};
					let response = tiny_http::Response::from_string(
						serde_json::to_string(&token_response).unwrap(),
					);
					let _ = rq.respond(response);
				}
				// end server handler
			}
			}

		let now = Instant::now();
		if now.duration_since(start_time) > timeout {
			exit = false;
		}
	}
	println!("exiting because of timeout hit.");

}

fn main() {
	let mut input = String::new();
	io::stdin().read_line(&mut input).unwrap();
	let setup: Setup = serde_json::from_str(&input).unwrap();
	println!(
		"setup: {:?} {:?} {:?}",
		setup.master_key, setup.agent_token, setup.timeout
	);
	    let stdout = File::create(format!("{}/agent.out", setup.agent_location)).unwrap();
    	let stderr = File::create(format!("{}/agent.err", setup.agent_location)).unwrap();
	    let daemonize = Daemonize::new()
        .pid_file(format!("{}/agent.pid", setup.agent_location)) // Every method except `new` and `start`
        .chown_pid_file(true)      // is optional, see `Daemonize` documentation
        .working_directory(format!("{}",setup.agent_location)) // for default behaviour.
        //.user("nobody")
        //.group("daemon") // Group name
        //.group(2)        // or group id.
        .umask(0o027)    // Set umask, `0o027` by default.
        .stdout(stdout)  // Redirect stdout to `/tmp/daemon.out`.
        .stderr(stderr);  // Redirect stderr to `/tmp/daemon.err`.
        //.privileged_action(|| "Executed before drop privileges");

    match daemonize.start() {
        Ok(_) => println!("Success, daemonized"),
        Err(e) => eprintln!("Error, {}", e),
    }
	serve(setup);
}