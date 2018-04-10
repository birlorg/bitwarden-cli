/*
 *
 * TODO: implement loop using: https://github.com/tomaka/rouille/blob/cf49277ec2d58010e74d1eb5c081390d65a36935/src/lib.rs#L358
 * so that timeout can work.
 * learn how to build and embed into shipped python:
 *      https://github.com/mckaymatt/cookiecutter-pypackage-rust-cross-platform-publish
 *      https://pypi.python.org/pypi/setuptools-rust
 *      https://github.com/getsentry/milksnake
 *      https://github.com/getsentry/libsourcemap/blob/master/setup.py
 *
 * otherwise this is just about ready to go. Will need to fix db.py to alter how it calls out to
 * the agent.
 * echo '{"agent_token":"super secret", "master_key": "secret", "timeout":30, "port":"6278"}' |
 * agent
 *
 * and the request:
 *curl --data '{"agent_token":"super secret"}' --header "Content-Type: application/json" http://localhost:6278
 *
 */
#[macro_use]
extern crate serde;
#[macro_use]
extern crate serde_derive;
#[macro_use]
extern crate serde_json;
#[macro_use]
extern crate rouille;
extern crate daemonize;
extern crate bitwarden;

use rouille::Request;
use rouille::Response;
use std::collections::HashMap;
use std::io;
use std::sync::Mutex;

// This struct contains the data that we store on the server about each client.
#[derive(Debug, Clone)]
struct SessionData {
    login: String,
}

#[derive(Deserialize)]
struct Setup {
    master_key: String,
    agent_token: String,
    timeout: u8,
    port: String,
}
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
fn main() {
    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();
    let setup: Setup = serde_json::from_str(&input).unwrap();
    println!(
        "setup: {:?} {:?} {:?}",
        setup.master_key, setup.agent_token, setup.timeout
    );
    println!("Now listening on localhost:{}", setup.port);

    let sessions_storage: Mutex<HashMap<String, SessionData>> = Mutex::new(HashMap::new());

    rouille::start_server(format!("localhost:{}", setup.port), move |request| {
        rouille::log(&request, io::stdout(), || {
            // We call `session::session` in order to assign a unique identifier to each client.
            // This identifier is tracked through a cookie that is automatically appended to the
            // response.
            //
            // The parameters of the function are the name of the cookie (here "SID") and the
            // duration of the session in seconds (here, one hour).
            rouille::session::session(request, "SID", 3600, |session| {
                // If the client already has an identifier from a previous request, we try to load
                // the existing session data. If we successfully load data from `sessions_storage`,
                // we make a copy of the data in order to avoid locking the session for too long.
                //
                // We thus obtain a `Option<SessionData>`.
                let mut session_data = if session.client_has_sid() {
                    if let Some(data) = sessions_storage.lock().unwrap().get(session.id()) {
                        Some(data.clone())
                    } else {
                        None
                    }
                } else {
                    None
                };

                // Use a separate function to actually handle the request, for readability.
                // We pass a mutable reference to the `Option<SessionData>` so that the function
                // is free to modify it.
                let response = handle_route(&request, &setup);

                // Since the function call to `handle_route` can modify the session data, we have
                // to store it back in the `sessions_storage` when necessary.
                if let Some(d) = session_data {
                    sessions_storage
                        .lock()
                        .unwrap()
                        .insert(session.id().to_owned(), d);
                } else if session.client_has_sid() {
                    // If `handle_route` erased the content of the `Option`, we remove the session
                    // from the storage. This is only done if the client already has an identifier,
                    // otherwise calling `session.id()` will assign one.
                    sessions_storage.lock().unwrap().remove(session.id());
                }

                // During the whole handling of the request, the `sessions_storage` mutex was only
                // briefly locked twice. This shouldn't have a lot of influence on performances.

                response
            })
        })
    });
}

// This is the function that truly handles the routes.
//
// The `session_data` parameter holds what we know about the client. It can be modified by the
// body of this function. Keep in my mind that the way we designed `session_data` is appropriate
// for most situations but not all. If for example you want to keep track of the pages that the
// user visited, you should design it in another way, otherwise the data of some requests will
// overwrite the data of other requests.
fn handle_route(request: &Request, setup: &Setup) -> Response {
    // First we handle the routes that are always accessible and always the same, no matter whether
    // the user is logged in or not.
    router!(request,
        (POST) (/) => {
            let token_request: TokenRequest = try_or_400!(rouille::input::json_input(request));

            println!("Login attempt with agent_token {:?}", token_request.agent_token);

            if token_request.agent_token == setup.agent_token {
                if token_request.exit == true {
                    println!("exit requested");
                    std::process::exit(0);
                }
                let token_response = TokenResponse {
                    error: "".to_string(),
                    master_key: setup.master_key.clone()
                };
                return Response::json(&token_response);

            } else {
                // We return a dummy response to indicate that the login failed.
                let token_response = TokenResponse {
                    error: "Invalid agent_token.".to_string(),
                    master_key: "".to_string()
                };
                return Response::json(&token_response);
            }
        },

        (POST) (/logout) => {
            // unused. but here so I can expand if I want to
            return Response::html(r#"Logout successful.
                                     <a href="/">Click here to go to the home</a>"#);
        },

        _ => Response::empty_404()
    );

    Response::empty_404()
}
