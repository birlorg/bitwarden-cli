import bitwarden.crypto as crypto 
import logging
logging.basicConfig()
log=logging.getLogger('bitwarden')
log.setLevel(logging.DEBUG)
def test_bitwarden():
	masterKey = crypto.makeKey(b"password", b"nobody@example.com")
	print("masterKey:{}", masterKey)
	assert masterKey == b'\x95\xa9\xc3\xb6W\xfb\xa7r\x80\xbfY\xdf\xfc\x18S\x81\x9e+\xf7W\xd0\x1db\x92$\x1bN\x05\xf5\xb8s\xe7'
	expectedEncryptionKey, expectedMacKey = crypto.symmetricKey()
	protectedKey = crypto.makeEncKey(expectedEncryptionKey+expectedMacKey, masterKey)
	print("protectedkey:%s" % protectedKey)
	decryptedEncryptionKey, decryptedMacKey = crypto.decryptEncryptionKey(protectedKey, masterKey)
	assert decryptedEncryptionKey == expectedEncryptionKey
	assert decryptedMacKey == expectedMacKey
	#assert protectedKey == "0.uRcMe+Mc2nmOet4yWx9BwA==|PGQhpYUlTUq/vBEDj1KOHVMlTIH1eecMl0j80+Zu0VRVfFa7X/MWKdVM6OM/NfSZicFEwaLWqpyBlOrBXhR+trkX/dPRnfwJD2B93hnLNGQ="
	#decryptedProtectedKey = bw.decrypt(protectedKey, masterKey, None)
	#assert decryptedProtectedKey = 
	masterPasswordHash = crypto.hashedPassword("p4ssw0rd", "nobody@example.com")
	assert masterPasswordHash == "r5CFRR+n9NQI8a525FY+0BPR0HGOjVJX0cR1KEMnIOo="
	#decrypt("2.6DmdNKlm3a+9k/5DFg+pTg==|7q1Arwz/ZfKEx+fksV3yo0HMQdypHJvyiix6hzgF3gY=|7lSXqjfq5rD3/3ofNZVpgv1ags696B2XXJryiGjDZvk=", protectedKey, macKey)
	expectedPlainText = "a secret message"
	encryptedText = crypto.encrypt(expectedPlainText, decryptedEncryptionKey, decryptedMacKey)
	decryptedPlainText = crypto.decrypt(encryptedText, decryptedEncryptionKey, decryptedMacKey)
	assert decryptedPlainText == expectedPlainText

test_bitwarden()
