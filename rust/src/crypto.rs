/*
*	Crypto for Bitwarden against openSSL.
*	
*/
extern crate openssl;
extern crate rustc_serialize as serialize;
use serialize::base64;
// use serialize::base64::FromBase64;
 use serialize::base64::ToBase64;
// use std::io;

pub fn hmac_openssl(key: &[u8], messages: &str) -> String {
    let pkey = openssl::pkey::PKey::hmac(&key).unwrap();
    let mut signer = openssl::sign::Signer::new(openssl::hash::MessageDigest::sha256(), &pkey).unwrap();
    signer.update(messages.as_bytes()).unwrap();
    let mut result = String::from("");
    result.push_str(&signer.sign_to_vec().unwrap().to_base64(base64::STANDARD)[..]);
    return result;
}


//make a master key.
pub fn make_key(password: &str, salt: &str) -> [u8; 32] {
    // 256-bit derived key
    //  hashlib.pbkdf2_hmac('sha256', password, salt, 5000, dklen=32)
    //let mut dk = [0u8; 32];
    //let mut dk = [0u8; 32];
    let mut derived_key= [0; 32];
    openssl::pkcs5::pbkdf2_hmac(&password.as_bytes(),salt.as_bytes(), 5000, openssl::hash::MessageDigest::sha256(), &mut derived_key).unwrap();
    //let mut result = String::from("");
    //result.push_str(&derived_key.to_base64(base64::STANDARD)[..]);
    return derived_key;
}

//# base64-encode a wrapped, stretched password+salt for signup/login
pub fn hashed_password(password: &str, salt: &str) -> String {
    let key = make_key(password, salt);
    //let mut derived_key = [0u8; 32];
    let mut derived_key = [0; 32];
    openssl::pkcs5::pbkdf2_hmac(&password.as_bytes(),salt.as_bytes(), 1, openssl::hash::MessageDigest::sha256(), &mut derived_key).unwrap();
    let mut result = String::from("");
    result.push_str(&derived_key.to_base64(base64::STANDARD)[..]);
    return result;
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_hashed_password() {
        let result = hashed_password("password", "nobody@example.com");
        let expected = "2cj6A0brDusMjVlVqcBW2a+kiOQDqZDCEB40NshJE7o=";
        assert_eq!(expected, result);
    }
    #[test]
    fn test_make_key() {
        let expected = b"\x95\xa9\xc3\xb6W\xfb\xa7r\x80\xbfY\xdf\xfc\x18S\x81\x9e+\xf7W\xd0\x1db\x92$\x1bN\x05\xf5\xb8s\xe7";
        let result = make_key("password", "nobody@example.com");
        assert_eq!(expected, &result);
    }
    #[test]
    fn test_decrypt_encrypted_key() {
        let expected = b"";
        //let result = decrypt_encrypted_key("0.QjjRqI96zTTB7/z3wHInzg==|WHl3wQjcPmZJ4wgADXywOhMB6RILrqPcivCJc50OkivznCRaFTBXVe6MudDxYcJEu6M7RMVQfz71LEcmcy/DFOT5veHR9YCdp4kQj3t4Tx0=",);
        //assert_eq!(expected, &result);
    }
}
