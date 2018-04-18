//extern crate crypto;
extern crate rand;
extern crate reqwest;
extern crate rustc_serialize as serialize;
extern crate uuid;
// extern crate openssl;

//  #[macro_use]
extern crate serde_json;

//use crypto::buffer::{ReadBuffer, WriteBuffer};
//use crypto::hmac;
//use crypto::mac::Mac;
//use crypto::symmetriccipher;
// use serialize::base64;
// use serialize::base64::FromBase64;
// use serialize::base64::ToBase64;
// use std::io;
mod crypto;

// api/accounts/register implementation.
/*
pub fn register(url: &reqwest::Url, email: &String, password: &String) -> String {
    let master_password_hash = crypto::hashed_password(password, email);
    let master_key = make_key(password, &email);
    let (val0, val1) = crypto::symmetric_key();
    let mut sym_key = Vec::new();
    sym_key.clone_from_slice(&val0);
    sym_key.clone_from_slice(&val1);
    let protected_key = make_encrypted_key(sym_key, master_key.unwrap());
    let signup_json = json!({
        "name": null,
        "email": email,
        "masterPasswordHash": master_password_hash,
        "masterPasswordHint":null,
        "key": protected_key, 
   });
}
*/

// api/connect/token implementation.
pub fn login(url: &reqwest::Url, email: &String, password: &String) -> String {
    //let internal_key = make_key(password, &email);
    let master_password_hash = crypto::hashed_password(&password, &email);
    drop(password);
    //let id = uuid::Uuid::new_v5(&uuid::NAMESPACE_DNS, "foo").to_string();
    let id = "49a521be-c920-4cba-b6ba-f170c3993669";
    //println!("uuid:{}", id);
    let params = [
        ("grant_type", "password"),
        ("username", email),
        ("password", &master_password_hash),
        ("scope", "api offline_access"),
        ("client_id", "browser"),
        ("deviceType", "3"),
        ("deviceIdentifier", id),
        ("deviceName", "firefox"),
        ("devicePushToken", ""),
    ];
    //let url = reqwest::url::Url::parse(url);
    //let register_url = format!("{}/api/accounts/register", url);
    let client = reqwest::Client::new();
    let mut response = client
        .post(url.join("/identity/connect/token").unwrap())
        .form(&params)
        .send()
        .unwrap();
    // println!("register post:{:?}", res);
    if response.status().is_success() {
        println!("success!");
    } else if response.status().is_server_error() {
        println!("server error!");
    } else {
        println!("Something else happened. Status: {:?}", response.status());
    }
    let response_body = response.text();
    return response_body.unwrap();
}
