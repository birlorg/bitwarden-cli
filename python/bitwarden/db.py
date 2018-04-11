"""
Database and configuration code.

"""
import base64
import functools
import os
import inspect
import pprint
import json
import logging
import signal
import subprocess
import time
# pylint: disable=E0611,E0401
from urllib.parse import urlparse
#pylint: disable=E0401
import records  # https://github.com/kennethreitz/records
import psutil
import requests
import standardpaths
standardpaths.configure(
    application_name='bitwarden', organization_name='birl.org')

log = logging.getLogger(__name__)
log.propagate = True


class UnimplementedError(Exception):
	"""for when I was too lazy"""
	pass


def badOrMissingDB(url):
	"""run when DB is either missing or not setup properly"""
	print("You need to run liquibase via tools/lb.sh")
	raise IOError("DB %s does not exist: You need to run tools/lb.sh" % url)


def isexception(obj):
	"""Given an object, return a boolean indicating whether it is an instance
    or subclass of :py:class:`Exception`.
    stolen from: https://github.com/kennethreitz/records/blob/master/records.py
    """
	if isinstance(obj, Exception):
		return True
	if inspect.isclass(obj) and issubclass(obj, Exception):
		return True
	return False


def connect(dbURL=None):
	"""connect to DB and return records.db instance"""
	parsedURL = urlparse(dbURL)
	if parsedURL.scheme != 'sqlite':
		raise UnimplementedError(
		    "DB scheme:{} is not currently supported, patches welcome.".format(
		        parsedURL.scheme))
	if not os.path.exists(parsedURL.path):
		badOrMissingDB(dbURL)
	# nobody can play with this file, except us, we don't play well with others.
	os.chmod(parsedURL.path, 0o0600)
	db = records.Database(dbURL)
	if 'config' not in db.get_table_names():
		badOrMissingDB(dbURL)
	return db


class Config():
	"""Configuration settings.

    We define every possible config setting as a property so that every
    setting gets documented.  Otherwise nobody would bother.
    Plus it makes access in the rest of the code much easier :)
    """

	def __init__(self, db):
		self.db = db
		# defined from the perspective of a cipher object.
		self.encryptedValues = (
		    ("Data", "Name"),
		    ("Data", "Password"),
		    ("Data", "Uri"),
		)

	def set(self, key, value):
		"""set the key to equal value in the DB"""
		return self.db.query(
		    "INSERT OR REPLACE INTO config (key, value) VALUES (:key, :value)",
		    key=key,
		    value=value)

	def one(self, rows, default=None, as_dict=False, as_ordereddict=False):
		"""implement one from records trunk since it is not released yet"""
		try:
			record = rows[0]
		except IndexError:
			if isexception(default):
				#pylint: disable=E0702
				raise default
			return default
		try:
			rows[1]
		except IndexError:
			pass
		else:
			raise ValueError('RecordCollection contained more than one row. '
			                 'Expects only one row when using '
			                 'RecordCollection.one')
		if as_dict:
			return record.as_dict()
		elif as_ordereddict:
			return record.as_dict(ordered=True)
		else:
			return record

	def scalar(self, one, default=None):
		"""return single column from single row or default"""
		row = self.one(one)
		return row[0] if row else default

	def get(self, key, default=None):
		"""return value from DB or default if not set"""
		row = self.db.query("select value from config where key=:key", key=key)
		return self.scalar(row, default)

	@property
	def identurl(self):
		"""bitwarden URL"""
		return self.get('ident_url', 'https://identity.bitwarden.com')

	@identurl.setter
	def identurl(self, value):
		return self.set('ident_url', value)

	@property
	def url(self):
		"""bitwarden URL"""
		return self.get('url', 'https://api.bitwarden.com')

	@url.setter
	def url(self, value):
		return self.set('url', value)

	@property
	def email(self):
		"""bitwarden login email address."""
		return self.get('email', os.getenv("EMAIL", None))

	@email.setter
	def email(self, value):
		return self.set('email', value)

	@property
	def debug(self):
		"""debug"""
		return self.get('debug', False)

	@debug.setter
	def debug(self, value):
		"""debug setter"""
		return self.set('debug', value)

	@property
	def encryption_key(self):
		"""This is the encrypted encryption key."""
		return self.get('encryption_key', None)

	@encryption_key.setter
	def encryption_key(self, value):
		return self.set('encryption_key', value)

	@property
	def client_token(self):
		"""token from bitwarden server."""
		return json.loads(self.get('client_token', None))

	@client_token.setter
	def client_token(self, value):
		"""set token"""
		return self.set('client_token', json.dumps(value))

	@property
	def last_sync_time(self):
		"""last time we synchronized with the server."""
		return self.get('last_sync_time', None)

	@last_sync_time.setter
	def last_sync_time(self, value):
		"""set last_sync_time"""
		return self.set('last_sync_time', value)

	@property
	def slab_location(self):
		"""path to executable for slab to run to choose an entry.."""
		value = self.get('slab_location', None)
		return value

	@slab_location.setter
	def agent_location(self, value):
		"""setter"""
		return self.set('slab_location', value)


	@property
	def agent_location(self):
		"""path to agent executable.."""
		value = self.get('agent_location', None)
		if not value:
			# get last item off the stack, so we can rock the actual binary call path.
			value = os.path.dirname(os.path.abspath(inspect.stack()[-1][1]))
			value = os.path.join(value, 'bitwarden-agent')
		return value

	@agent_location.setter
	def agent_location(self, value):
		"""setter"""
		return self.set('agent_location', value)

	@property
	def agent_token(self):
		"""token to talk with agent."""
		return self.get('agent_token', None)

	@agent_token.setter
	def agent_token(self, value):
		"""set token"""
		return self.set('agent_token', value)

	@property
	def agent_timeout(self):
		"""
        timeout for the agent. <0 means no timeout.
        > 0 means timeout for that many seconds.
        """
		return int(self.get('agent_tiemout', 0))

	@agent_timeout.setter
	def agent_timeout(self, value):
		"""setter for agent_timeout"""
		return self.set('agent_timeout', int(value))

	@property
	def agent_port(self):
		"""
        localhost port that the agent listens to, when it's running.
        """
		return int(self.get('agent_port', 6277))

	@agent_port.setter
	def agent_port(self, value):
		"""setter for agent_port"""
		return self.set('agent_port', int(value))

	@functools.lru_cache(2)
	def get_master_key(self):
		"""
        we cache this call, so we can cache the master_key in process,
        so decryption goes WAY faster, since we do not have to call out
        to the agent every time we want to decrypt.
        This doesn't really affect security, since this code is only running
        long enough to do it's decryption and then exits.
        and code that doesn't need to decrypt stuff will never call us.
        """
		ret = None
		try:
			r = requests.post(
			    "http://127.0.0.1:{}".format(self.agent_port),
			    json={
			        'key': self.agent_token,
			        'exit': False
			    })
			if r.status_code != 200:
				log.error(r.text)
			try:
				key = r.json()
			except json.decoder.JSONDecodeError:
				log.error("problem json decoding:%s", r.text)
				return None
		except requests.exceptions.ConnectionError:
			log.error("agent not running, you must login.")
		try:
			ret = base64.b64decode(key['master_key'])
		except IndexError:
			log.error("expected master_key but agent returned:%s",
			          pprint.pformat(ret))
		return ret

	@property
	def master_key(self):
		"""
        master key that decrypts information.
        """
		return self.get_master_key()

	def isAgentRunning(self):
		"""return pid if agent is running, else None
        """
		pidFile = os.path.join(
		    standardpaths.get_writable_path('app_local_data'), 'agent.pid')
		if os.path.exists(pidFile):
			# agent already running, not so good for us.
			pid = int(open(pidFile, 'r').read())
			if psutil.pid_exists(pid):
				return pid
			else:
				# cleanup
				os.unlink(pidFile)
		return None

	@master_key.setter
	def master_key(self, value):
		"""setter for master key -- starts agent
        set value to None will stop agent and not restart it.
        """
		pid = self.isAgentRunning()
		if pid:
			os.kill(pid, signal.SIGTERM)
		if value is None:
			log.debug("value of none: shutdown agent, not starting it again")
			return
		key = base64.b64encode(value).decode('utf-8')
		agent_token = base64.b64encode(os.urandom(16)).decode('utf-8')
		cmd = [self.agent_location, '127.0.0.1:{}'.format(self.agent_port)]
		log.debug("running agent:%s", cmd)
		p = subprocess.Popen(
		    cmd,
		    stdin=subprocess.PIPE,
		    stderr=subprocess.PIPE,
		    stdout=subprocess.PIPE)
		data = {
		    'master_key': key,
		    'agent_token': agent_token,
		    'port': self.agent_port
		}
		timeout = self.agent_timeout
		if timeout > 0:
			data['tiemout'] = timeout
		else:
			log.debug("sending no timeout because:%s", timeout)
		log.debug("sending to agent:%s", pprint.pformat(data))
		out = json.dumps(data) + "\n"
		p.stdin.write(out.encode('utf-8'))
		self.agent_token = agent_token
		self.agent_timeout = time.time() + timeout
		out = p.communicate()
		log.debug("agent returned:%s:%s", out[0], out[1])
		return True
