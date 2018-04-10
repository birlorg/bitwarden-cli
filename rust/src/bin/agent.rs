/*
 *
 * TODO: implement loop using: https://github.com/tomaka/rouille/blob/cf49277ec2d58010e74d1eb5c081390d65a36935/src/lib.rs#L358
 * so that timeout can work.
 * need to learn how to delete object's again. 
 * learn how to build and embed into shipped python: https://github.com/getsentry/libsourcemap/blob/master/setup.py
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
#[macro_use] extern crate serde_derive;
#[macro_use] extern crate serde_json;
#[macro_use] extern crate rouille;

extern crate bitwarden;

use std::collections::HashMap;
use std::io;
use std::sync::Mutex;
use rouille::Request;
use rouille::Response;

// This struct contains the data that we store on the server about each client.
#[derive(Debug, Clone)]
struct SessionData { login: String }


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
    exit: bool
}
#[derive(Serialize)]
struct TokenResponse {
    master_key: String,
    error: String
}
//
//  echo '{"agent_token":"super secret", "master_key": "secret", "timeout":30, "port":"6278"}' |
//  target/debug/agent
fn main() {

    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();
    let setup: Setup = serde_json::from_str(&input).unwrap();
    println!("setup: {:?} {:?} {:?}", setup.master_key, setup.agent_token, setup.timeout);
    // Small message so that people don't need to read the source code.
    // Note that like all examples we only listen on `localhost`, so you can't access this server
    // from another machine than your own.
    println!("Now listening on localhost:{}", setup.port);

    // For the sake of the example, we are going to store the sessions data in a hashmap in memory.
    // This has the disadvantage that all the sessions are erased if the program reboots (for
    // example because of an update), and that if you start multiple processes of the same
    // application (for example for load balancing) then they won't share sessions.
    // Therefore in a real project you should store probably the sessions in a database of some
    // sort instead.
    //
    // We created a struct that contains the data that we store on the server for each session,
    // and a hashmap that associates each session ID with the data.
    let sessions_storage: Mutex<HashMap<String, SessionData>> = Mutex::new(HashMap::new());

    rouille::start_server(format!("localhost:{}",setup.port), move |request| {
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
                    sessions_storage.lock().unwrap().insert(session.id().to_owned(), d);

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
            // In order to retreive what the user sent us through the <form>, we use the
            // `post_input!` macro. This macro returns an error (if a field is missing for example),
            // so we use the `try_or_400!` macro to handle any possible error.
            //
            // If the macro is successful, `data` is an instance of a struct that has one member
            // for each field that we indicated in the macro.
            let token_request: TokenRequest = try_or_400!(rouille::input::json_input(request));

            // Just a small debug message for this example. You could also output something in the
            // logs in a real application.
            println!("Login attempt with agent_token {:?}", token_request.agent_token);

            // In this example all login attempts are successful in the password starts with the
            // letter 'b'. Of course in a real website you should check the credentials in a proper
            // way.
            if token_request.agent_token == setup.agent_token {
                // Logging the user in is done by writing the content of `session_data`.
                //
                // A minor warning here: in this demo we store in memory directly the data that
                // the user gave us. This data is not to be trusted and could contain anything,
                // including an attempt at XSS. Storing in memory what the user gave us is not
                // wrong, but we have to take care not to interpret it as HTML data for example.
                //*session_data = Some(SessionData { login: token_request.key});
                let token_response = TokenResponse {
                    error: "".to_string(),
                    master_key: setup.master_key.clone()
                };
                return Response::json(&token_response);

            } else {
                // We return a dummy response to indicate that the login failed. In a real
                // application you should probably use some sort of HTML templating instead.
                let token_response = TokenResponse {
                    error: "Invalid agent_token.".to_string(),
                    master_key: "".to_string()
                };
                return Response::html("Wrong login/password");
            }
        },

        (POST) (/logout) => {
            // This route is called when the user wants to log out.
            // We do so by simply erasing the content of `session_data`, which deletes the session.
            //*session_data = None;

            // We return a dummy response to indicate what happened. In a real application you
            // should probably use some sort of HTML templating instead.
            return Response::html(r#"Logout successful.
                                     <a href="/">Click here to go to the home</a>"#);
        },

        _ => Response::empty_404()
    );

    Response::empty_404()

}

