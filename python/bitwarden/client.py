"""
I act like a bitwarden client and interact with a remote bitwarden server
pylint: disable=W191
"""
import base64
import os
import json
import pprint
import logging
import posixpath
import signal
import sys
import time
# pylint: disable=E0401
import psutil  # https://psutil.readthedocs.io/en/latest/
import requests
import standardpaths  # https://pystandardpaths.readthedocs.io/
import bitwarden.db as DB
import bitwarden.crypto as crypto
import bitwarden.slab as slab

log = logging.getLogger(__name__)
log.propagate = True

standardpaths.configure(application_name='bitwarden',
                        organization_name='birl.org')


class Client(object):
    def __init__(self, db, debug):
        self.db = db
        self.config = DB.Config(db)
        if debug:
            requests_log = logging.getLogger("urllib3")
            requests_log.setLevel(logging.DEBUG)
            requests_log.propagate = True
            log.setLevel(logging.DEBUG)

    def register(self, email, password, name, hint):
        """register a new account with bitwarden server"""
        masterKey = crypto.makeKey(password, email)
        masterPasswordHash = crypto.hashedPassword(password, email)
        expectedEncryptionKey, expectedMacKey = crypto.symmetricKey()
        protectedKey = crypto.makeEncKey(
            expectedEncryptionKey+expectedMacKey, masterKey)
        self.config.encrypted_key = protectedKey

        data = {
            "name": name,
            "email": email,
            "masterPasswordHash": str(masterPasswordHash),
            "masterPasswordHint": hint,
            "key": protectedKey
        }
        url = posixpath.join(self.config.url, 'accounts', 'register')
        log.debug("registering to: %s with:%s", url, pprint.pformat(data))
        return requests.post(url, json=data)

    def login(self, email, password):
        masterKey = crypto.makeKey(password, email)
        masterPasswordHash = crypto.hashedPassword(password, email)
        del password
        log.info("client login as %s", email)
        log.debug("identURL:%s", self.config.identurl)
        url = posixpath.join(self.config.identurl, 'connect', 'token')
        data = {
            "grant_type": "password",
            "username": email,
            "password": masterPasswordHash,
            "scope": "api offline_access",
            "client_id": "browser",
            "deviceType": 3,
            "deviceIdentifier": "aac2e34a-44db-42ab-a733-5322dd582c3d",
            "deviceName": "firefox",
            "devicePushToken": ""
        }
        log.debug("POST %s data of:%s", url, pprint.pformat(data))
        r = requests.post(url, data=data)
        # log.debug("returning:%s", r.text)
        if r.status_code == 200:
            token = r.json()
            token['token_expires'] = time.time()+token['expires_in']
            self.config.client_token = token
            log.debug("token set:%s", pprint.pformat(token))
            self.config.master_key = masterKey
            self.config.encryption_key = token['Key']
            return True
        else:
            log.error("bad client login got %s data returned:%s",
                      r.status_code, r.text)
            return False

    def slab(self):
        """operate in sudolikeaboss mode"""
        encryptionKey = self.config.encryption_key
        if not encryptionKey:
            log.error("you must run sync first")
            sys.exit(1)
        masterKey = self.config.master_key
        if not masterKey:
            log.error("no agent running!")
            sys.exit(1)
        decryptedEncryptionKey, macKey = crypto.decryptEncryptionKey(
            encryptionKey, masterKey)
        qry = "SELECT uuid, name, uri from ciphers"
        choices = []
        choiceMap = {}
        for row in self.db.query(qry):
            log.debug(row)
            try:
                url = crypto.decrypt(
                    row['uri'], decryptedEncryptionKey, macKey)
            except IOError:
                data = self.db.query(
                    "select json from ciphers where uuid=:uuid", uuid=row['uuid']).first()['json']
                log.debug(json.dumps(json.loads(data), indent=4,
                          sort_keys=True, ensure_ascii=False))
                continue
            log.debug(url)
            if 'sudolikeaboss://' in url:
                if row['name']:
                    name = crypto.decrypt(
                        row['name'], decryptedEncryptionKey, macKey)
                    choices.append(name)
                    choiceMap[name] = row['uuid']
        log.debug("choices:%s", choices)
        selected = slab.choice(choices)
        selectedUUID = choiceMap[selected]
        row = self.db.query(
            "select json from ciphers where uuid=:uuid", uuid=selectedUUID).first()
        data = json.loads(row['json'])
        password = data['Login']['Password']
        print("{}".format(crypto.decrypt(password, decryptedEncryptionKey, macKey)))

    def sync(self):
        """sync with remote server"""
        token=self.config.client_token
        if not token:
            raise IOError("You must login first.")
        if time.time() > token['token_expires']:
            raise IOError("Token has expired, please login again.")
        log.debug("url base:%s", self.config.url)
        url=posixpath.join(self.config.url, 'sync')
        header={"Authorization": "Bearer {}".format(token['access_token'])}
        log.debug("sync call to:%s with header:%s", url, header)
        ret=requests.get(url, headers=header).json()
        log.debug("sync returned:%s", pprint.pformat(ret))
        EncryptedEncryptionKey=ret['Profile']['Key']
        if not self.config.encryption_key:
            self.config.encryption_key=EncryptedEncryptionKey
        for cipher in ret['Ciphers']:
            uuid=cipher['Id']
            update=self.db.query(
                "select uuid from ciphers where uuid=:uuid", uuid=uuid).first()
            if update:
                qry="update ciphers set name=:name, uri=:uri, json=:json, updated_at=DATETIME('NOW') where uuid=:uuid"
            else:
                qry="insert into ciphers (uuid,  name, uri, json, created_at, updated_at) VALUES (:uuid, :name,:uri,:json,DATETIME('NOW'),DATETIME('NOW'))"
            self.db.query(qry, uuid=uuid, name=cipher['Name'],
                          uri=cipher['Data']['Uri'], json=json.dumps(cipher))
        return "sync finished"
       # url = ret['Ciphers'][0]['Data']['Uri']
       # password = ret['Ciphers'][0]['Data']['Password']
       # username = ret['Ciphers'][0]['Data']['Username']
       # log.debug("EncryptedEncryptionKey:%s", EncryptedEncryptionKey)
       # log.debug("master_key:%s", self.config.master_key)
       # encryptionKey, macKey = crypto.decryptEncryptionKey(
       #     EncryptedEncryptionKey, self.config.master_key)
       # log.debug("encryptionKey:%s", encryptionKey)
       # log.debug("macKey:%s", macKey)
       # log.debug("macKey length:%s", len(macKey))
       # # log.debug("encrypted username:%s", username)
       # # username = crypto.decrypt(username, encryptionKey, macKey)
       # # log.debug("decrypted username:%s", username)
       # log.debug("encryptedURL:%s", url)
       # url = crypto.decrypt(url, encryptionKey, macKey)
       # log.debug("decrypted url:%s", url)
       # log.debug("encryptedPAssword:%s", password)
       # password = crypto.decrypt(password, encryptionKey, macKey)
       # log.debug("decrypted password:%s", password)
