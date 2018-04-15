"""
I act like a bitwarden client and interact with a remote bitwarden server
pylint: disable=W191
"""
import json
import pprint
import logging
import posixpath
import sys
import time
import requests
import standardpaths  # https://pystandardpaths.readthedocs.io/
import bitwarden.db as DB
import bitwarden.crypto as crypto
import bitwarden.slab as slab

log = logging.getLogger("bitwarden.client")
log.propagate = True

standardpaths.configure(
    application_name='bitwarden', organization_name='birl.org')
mfa_map = {'u2f': 4, 'yubikey': 3, 'duo': 2, 'authenticator': 0, 'email': 1}


class Client(object):
	"""
	Client API.

	Called by click from main.py, but in theory callable by anyone wanting to be a bitwarden client.

	"""
	def __init__(self, db, debug):
		self.db = db
		self.config = DB.Config(db)
		if debug:
			requests_log = logging.getLogger("urllib3")
			requests_log.setLevel(logging.DEBUG)
			requests_log.propagate = True
			log.setLevel(logging.DEBUG)

	def register(self, email, password, name, hint):
		"""
		register a new account with bitwarden server
		"""
		masterKey = crypto.makeKey(password, email)
		masterPasswordHash = crypto.hashedPassword(password, email)
		expectedEncryptionKey, expectedMacKey = crypto.symmetricKey()
		protectedKey = crypto.makeEncKey(
		    expectedEncryptionKey + expectedMacKey, masterKey)
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

	def login(self, email, password, timeout, mfa, mfa_token):
		""" login to bitwarden server.
		"""
		if not email:
			email = self.config.email
			if not email:
				log.error("Must give an email address, when not in config.")
		else:
			self.config.email = email
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
		if mfa:
			data["twoFactorToken"] = str(mfa_token)
			data["twoFactorProvider"] = mfa_map[mfa]
			data["towFactorRemember"] = 1
		log.debug("POST %s data of:%s", url, pprint.pformat(data))
		r = requests.post(url, data=data)
		# log.debug("returning:%s", r.text)
		if r.status_code == 200:
			token = r.json()
			token['token_expires'] = time.time() + token['expires_in']
			self.config.client_token = token
			log.debug("token set:%s", pprint.pformat(token))
			if timeout < 0:
				self.config.agent_timeout = 0
			elif timeout == 0:
				log.debug("timeout 0, setting to:%s", token['expires_in'])
				self.config.agent_timeout = token['expires_in']
			elif timeout > 0:
				self.config.agent_timeout = timeout
			else:
				log.error("bad timeout %s: This should be impossible, please yell @ someone.", timeout)
			log.debug("timeout set to %s because arg was %s: %s", self.config.agent_timeout, timeout, type(timeout))
			self.config.master_key = masterKey
			self.config.encryption_key = token['Key']
			return True
		else:
			log.error("bad client login got %s data returned:%s",
			          r.status_code, r.text)
			return False

	def _decrypt(self, value):
		"""decrypt a value
        assumes input to be a cipherstring of encryption type 2.
        """
		encryptionKey = self.config.encryption_key
		if not encryptionKey:
			log.error("you must run pull first")
			sys.exit(1)
		masterKey = self.config.master_key
		if not masterKey:
			log.error("No agent running! you must login first.")
			sys.exit(1)
		decryptedEncryptionKey, macKey = crypto.decryptEncryptionKey(
		    encryptionKey, masterKey)
		value = crypto.decrypt(value, decryptedEncryptionKey, macKey)
		return value

	def fetchName(self, name, pwonly, decrypt, fulldecrypt):
		"""
		fetch from local DB cipher entries by name.
        """
		ret = self.find(name, nameOnly=True)
		if not ret:
			return
		if len(ret) > 1:
			log.error("found more than 1 record, only returning the first.")
		uuid = ret[0]['uuid']
		return self.fetchUUID(uuid, pwonly, decrypt, fulldecrypt)

	def fetchUUID(self, uuid, pwonly, decrypt, fulldecrypt):
		"""
		fetch from local DB cipher entries by UUID
        """
		ret = None
		data = self.db.query(
		    "select json from ciphers where uuid=:uuid",
		    uuid=uuid).first()['json']
		data = json.loads(data)
		if pwonly:
			pw = data['Login']['Password']
			pw = self._decrypt(pw)
			ret = pw
		elif decrypt:
			log.error("unimplemented")
		elif fulldecrypt:
			log.error("unimplemented")
		else:
			ret = json.dumps(
			    data, indent=4, sort_keys=True, ensure_ascii=False)
		return ret

	def find(self, query, nameOnly=False):
		"""find stuff"""
		ciphers = self.db.query("select uuid, name, uri from ciphers")
		results = []
		for cipher in ciphers:
			c = {'uuid': None, 'name': None, 'uri': None}
			c['uuid'] = cipher['uuid']
			c['name'] = self._decrypt(cipher['name'])
			if query in c['name']:
				results.append(c)
			if not nameOnly:
				if cipher['uri']:
					c['uri'] = self._decrypt(cipher['uri'])
					if query in c['uri']:
						results.append(c)
		return results

	def slab(self):
		"""operate in sudolikeaboss mode"""
		encryptionKey = self.config.encryption_key
		if not encryptionKey:
			log.error("you must run pull first")
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
				if not row['uri']:
					url = ''
				else:
					url = crypto.decrypt(row['uri'], decryptedEncryptionKey,
				                     macKey)
			except IOError:
				data = self.db.query(
				    "select json from ciphers where uuid=:uuid",
				    uuid=row['uuid']).first()['json']
				log.debug(
				    json.dumps(
				        json.loads(data),
				        indent=4,
				        sort_keys=True,
				        ensure_ascii=False))
				continue
			log.debug(url)
			if 'sudolikeaboss://' in url:
				if row['name']:
					name = crypto.decrypt(row['name'], decryptedEncryptionKey,
					                      macKey)
					choices.append(name)
					choiceMap[name] = row['uuid']
		log.debug("choices:%s", choices)
		selected = slab.choice(choices, self.config.slab_location)
		if not selected:
			log.debug("no choice selected")
			return None
		selectedUUID = choiceMap[selected]
		row = self.db.query(
		    "select json from ciphers where uuid=:uuid",
		    uuid=selectedUUID).first()
		data = json.loads(row['json'])
		password = data['Login']['Password']
		print("{}".format(
		    crypto.decrypt(password, decryptedEncryptionKey, macKey)))

	def pull(self):
		"""pull from remote server"""
		token = self.config.client_token
		if not token:
			raise IOError("You must login first.")
		if time.time() > token['token_expires']:
			raise IOError("Token has expired, please login again.")
		log.debug("url base:%s", self.config.url)
		url = posixpath.join(self.config.url, 'sync')
		header = {"Authorization": "Bearer {}".format(token['access_token'])}
		log.debug("sync call to:%s with header:%s", url, header)
		ret = requests.get(url, headers=header).json()
		log.debug("sync returned:%s", pprint.pformat(ret))
		EncryptedEncryptionKey = ret['Profile']['Key']
		if not self.config.encryption_key:
			self.config.encryption_key = EncryptedEncryptionKey
		for cipher in ret['Ciphers']:
			try:
				uri = cipher['Data']['Uri']
			except KeyError:
				uri = None
			uuid = cipher['Id']
			update = self.db.query(
			    "select uuid from ciphers where uuid=:uuid",
			    uuid=uuid).first()
			if update:
				# pylint: disable=C0301
				# pylint: disable=C0301
				qry = "update ciphers set name=:name, uri=:uri, json=:json, updated_at=DATETIME('NOW') where uuid=:uuid"
			else:
				qry = "insert into ciphers (uuid,  name, uri, json, created_at, updated_at) VALUES (:uuid, :name,:uri,:json,DATETIME('NOW'),DATETIME('NOW'))"
			self.db.query(
			    qry,
			    uuid=uuid,
			    name=cipher['Name'],
			    uri=uri,
			    json=json.dumps(cipher))
		self.config.last_sync_time = time.asctime()
		return "pull finished"
