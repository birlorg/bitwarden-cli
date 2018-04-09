"""
Bitwarden crypto functions.

Yes, this code is UGLY, The  bitwarden documentation is either
missing, inconsistent or confusing.

This needs a refactor, but unknown if I will get to it before I move back to rust
where this code probably should live for reals.

See tests/test_bitwarden.py if you want to make sense of this ugly.
refactors are welcome.

"""
import base64
import os
import logging
import hmac
import hashlib
#pylint: disable=E0401
import cryptography
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hmac as Cipherhmac
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
log = logging.getLogger(__name__)
log.propagate = True


class UnimplementedError(Exception):
    pass


def makeKey(password, salt):
    """make master key"""
    if not hasattr(password, 'decode'):
        password = password.encode('utf-8')
    if not hasattr(salt, 'decode'):
        salt = salt.lower()
        salt = salt.encode('utf-8')
    # log.debug("salt:%s", salt)
    return hashlib.pbkdf2_hmac('sha256', password, salt, 5000, dklen=32)


def hashedPassword(password, salt):
    """base64-encode a wrapped, stretched password+salt for signup/login
    """
    if not hasattr(password, 'decode'):
        password = password.encode('utf-8')
    key = makeKey(password, salt)
    return base64.b64encode(
        hashlib.pbkdf2_hmac('sha256', key, password, 1,
                            dklen=32)).decode('utf-8')


def encodeCipherString(enctype, iv, ct, mac):
    """return bitwarden cipherstring"""
    ret = "{}.{}|{}".format(enctype, iv.decode('utf-8'), ct.decode('utf-8'))
    if mac:
        return ret + '|' + mac.decode('utf-8')
    return ret


def decodeCipherString(cipherString):
    """decode a cipher tring into it's parts"""
    mac = None
    encryptionType = int(cipherString[0:1])
    # all that are currently defined: https://github.com/bitwarden/browser/blob/f1262147a33f302b5e569f13f56739f05bbec362/src/services/constantsService.js#L13-L21
    assert encryptionType < 9
    if encryptionType == 0:
        iv, ct = cipherString[2:].split("|", 2)
    else:
        iv, ct, mac = cipherString[2:].split("|", 3)
    iv = base64.b64decode(iv)
    ct = base64.b64decode(ct)
    if mac:
        mac = base64.b64decode(mac)[0:32]
    return encryptionType, iv, ct, mac


def symmetricKey():
    """create symmetrickey"""
    pt = os.urandom(64)
    encryptionKey = pt[:32]
    macKey = pt[32:64]
    return encryptionKey, macKey


def makeEncKey(symmetricKey, key):
    """encrypt random bytes with a key to make new encryption key"""
    pt = symmetricKey
    iv = os.urandom(16)
    cipher = cryptography.hazmat.primitives.ciphers.Cipher(
        algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(pt) + encryptor.finalize()
    return encodeCipherString(0, base64.b64encode(iv), base64.b64encode(ct),
                              None)


def macsEqual(mac1, mac2):
    """compare two hmacs, with double hmac verification"""
    cmpKey = os.urandom(32)
    # log.debug("macsEqual lengths:%s:%s:%s", len(cmpKey), len(mac1), len(mac2))
    hmac1 = hmac.new(cmpKey, mac1, 'sha256').digest()
    hmac2 = hmac.new(cmpKey, mac2, 'sha256').digest()
    return hmac1 == hmac2


def unpad(s):
    """unpad encryption.
    Clearly I don't understand how bitwarden does this.
    the desktop and browser code do not talk about it, so it must
    be done at a lower level, but i have yet to track down that code.
    and python clearly doesn't do it for me, so either the python 
    peeps don't get it either, or there is some confusion somehwere.

    """
    # return s[:-ord(s[len(s) - 1:])]
    # log.debug("unpad before:%s", s)
    padChars = ('\x06', '\x0b', '\u000e', '\u00010', '\u0002', '\b',
                "\n", '\t', '\r', '\f', '\u0007')
    for c in padChars:
        s = s.replace(c, '')
    # log.debug("unpad after:%s", ret)
    return s


def pad(blockSize, s):
    """pad encryption if needed"""
    return s + (
        blockSize - len(s) % blockSize) * chr(blockSize - len(s) % blockSize)


def decryptEncryptionKey(cipherString, key):
    """decryptEncryptionKey
    returns encryptionKey and macKey
    """
    encryptionType, iv, cipherText, mac = decodeCipherString(cipherString)
    # log.debug("mac:%s",  mac)
    # log.debug("iv:%s", iv)
    # log.debug("ct:%s", cipherText)
    assert mac is None
    if encryptionType != 0:
        raise UnimplementedError("can not decrypt type:%s" % encryptionType)
    cipher = cryptography.hazmat.primitives.ciphers.Cipher(
        algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    plainText = decryptor.update(cipherText) + decryptor.finalize()
    # log.debug("mackey before unpad:%s", plainText[32:])
    return plainText[:32], plainText[32:64]


def decrypt(cipherString, key, macKey, decode=True):
    """decrypt a CipherString and return plaintext
    """
    encryptionType, iv, ct, mac = decodeCipherString(cipherString)
    if encryptionType != 2:
        raise UnimplementedError("can not decrypt {} decryption method".format(
            cipherString[0]))
    cmac = hmac.new(macKey, iv + ct, 'sha256').digest()
    #hash = Cipherhmac.HMAC(macKey, hashes.SHA256(), backend=default_backend())
    # hash.update(iv)
    # hash.update(ct)i cmac = hash.finalize()
    if not macsEqual(mac, cmac):
        log.debug("macsEqual error:%s:%s", mac, cmac)
        raise IOError("Invalid mac on decrypt")
    #key = hashlib.sha256(key).digest()
    cipher = cryptography.hazmat.primitives.ciphers.Cipher(
        algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    plainText = decryptor.update(ct) + decryptor.finalize()
    #log.debug("before unpad:%s", plainText)
    if decode:
        return unpad(plainText.decode('utf-8'))
    return plainText


def encrypt(pt, key, macKey):
    """
    encrypt+mac a value with a key and mac key and random iv, return cipherString
    """
    if not hasattr(pt, 'decode'):
        pt = bytes(pt, 'utf-8')
    iv = os.urandom(16)
    #key = hashlib.sha256(key).digest()
    cipher = cryptography.hazmat.primitives.ciphers.Cipher(
        algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(pt) + encryptor.finalize()
    mac = hmac.new(macKey, iv + ct, 'sha256').digest()
    return encodeCipherString(2, base64.b64encode(iv), base64.b64encode(ct),
                              base64.b64encode(mac))
