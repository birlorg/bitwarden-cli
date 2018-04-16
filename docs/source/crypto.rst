.. _cryptography:

Cryptography
============

TODO: do the other Encryption Types as well.

There is not a good writeup of how the cryptography in Bitwarden actually works.
Bitwarden briefly covers it here_ . They also have a web page
showing the crypto_ and @jcs wrote up the API_: which covers the crypto, but glosses over some things.

I've written the client crypto code for Bitwarden in python and rust, so feel like it's good to share
what I've learned about how it all works.

We start with your email and password, these are the building blocks that everything is built from.

Your email address will be brought down to lowercase, and then will become the salt for everything.
This makes sense, since you want salts to be unique, and email addresses are unique. If you want a 
tough salt, use a tough email address.

Every "Cipher" or login entry in Bitwarden is using symmetric encryption, specifically AES-256-CBC with PKCS#7 padding.

To decrypt something you need the encrypted text, which in Bitwarden comes in the form of a "CipherString"
You also need the decryption Key and you need a mac key (to handle the HMAC_ part: 

CipherStrings
-----------------

Cipher Strings include:
  * Encryption type (so far 8 are setup)
  * iv (the initialization vector to AES)
  * ct (the encrypted text aka "cipher text")
  * mac (the Message authentication code to verify this message is not tampered with) - Optional.
  
An example CipherString:
  
  2.6DmdNKlm3a+9k/5DFg+pTg==|7q1Arwz/ZfKEx+fksV3yo0HMQdypHJvyiix6hzgF3gY=|7lSXqjfq5rD3/3ofNZVpgv1ags696B2XXJryiGjDZvk=

Cipher Strings have 2 different seperators, a . and a |  The period seperates the encryptType from the iv and rest of the string.
the iv, ct and mac are seperated by a | symbol.
the iv, ct and mac are base64 encoded via RFC3548_. 

Cipherstrings are what Bitwarden speaks across the API and what gets stored on disk.

So back to decryption.  We get a CipherString but we still need a decryptionKey and a macKey. 

Getting a decryptionKey and macKey
----------------------------------------------

To get these, we have to go back to our email and password.

When you register and create an account, 2 "secret" things are created, a "master password hash"
and a "key" what I call a protectedKey.

The Master Key is created by 5000 rounds of pbkdf2_hmac see
`bitwarden.crypto.makeKey`_ for details, using your email as salt and your
password as key.

This master key is *never* sent anywhere, it's very important to keep it safe when it exists.

To create a Protected Key, we just randomly generate 64 bytes of data, with
16 bits of random iv and encrypt it with AES-CBC using the MasterKey, which
we just talked about. Creation happens in the makeEncKey_ and then gets
turned into a CipherString, which becomes the Protected Key.

The protectedKey is what we care about, it's a combination of the
decryptionKey and macKey that we need, stuffed inside of a CipherString. The
protectedKey gets a unique encryption type (0) and does not get a MAC. Since
it's inside of a CipherString, we know it's encrypted, so we have to decrypt
it. To decrypt it we need the MasterKey.

The Master key can then be used as the key to decrypt the protectedKey see
`bitwarden.crypto.decryptEncryptionKey`_ We decrypt using AES CBC, and we
will get back 64 bytes of plaintext. the first half [0:32] will be the
decryptionKey for CipherStrings of encryption type > 0. The second half
(32:64) will be the macKey.

Decryption
-------------

Now we have our Master Key and macKey, we can decrypt. It's also pretty
straightforward. We decode the CipherString to get the ct, iv and mac. Then
we compute a mac (iv + ct) using SHA256 HMAC and compare it to the mac we got
from the CipherString. See macsEqual_ for comparison details.

Assuming our macs are equal, we can decrypt with AES-CBC to get padded plaintext.
Then we use PKCS7 padding scheme to unpad (as described by Section 10.3, step 2, of RFC2315_)

decryption is implemented in decrypt_

Encryption
-------------

To encrypt, we need the plaintext to encrypt, the masterKey and the macKey.
Then we pad using PKCS7, the reverse of unpadding above. then AES-CBC again
and then compute an SHA256 HMAC. This is implemented in encrypt_



.. _RFC3548: https://tools.ietf.org/html/rfc3548.html
.. _RFC2315: https://tools.ietf.org/html/rfc2315.html
.. _HMAC: https://en.wikipedia.org/wiki/HMAC
.. _API: https://github.com/jcs/bitwarden-ruby/blob/master/API.md 
.. _here: https://help.bitwarden.com/article/what-encryption-is-used/
.. _crypto: https://help.bitwarden.com/crypto.html
.. _makeEncKey: internals.html#bitwarden.crypto.makeEncKey
.. _bitwarden.crypto.makeKey: internals.html#bitwarden.crypto.makeKey
.. _bitwarden.crypto.decryptEncryptionKey: internals.html#bitwarden.crypto.decryptEncryptionKey
.. _macsEqual: internals.html#bitwarden.crypto.macsEqual
.. _encrypt: internals.html#bitwarden.crypto.encrypt
.. _decrypt: internals.html#bitwarden.crypto.decrypt
