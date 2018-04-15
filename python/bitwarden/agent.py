#!/usr/bin/env python
# pylint: disable=W0603
"""
agent code.

example call:
echo '{"agent_token":"super secret", "master_key": "secret", "timeout":30}' | agent 127.0.0.1:6277

curl --data '{"key":"super secret"}' http://localhost:6277/
{"master_key": "secret"}%
"""
import os
import logging
import json
import sys
import threading

import daemon
import daemon.pidfile
import standardpaths
import web

standardpaths.configure(
    application_name='bitwarden', organization_name='birl.org')

logFile = os.path.join(
    standardpaths.get_writable_path('app_local_data'), 'agent.log')
lh = logging.FileHandler(logFile)
lh.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
log = logging.getLogger(__name__)
log.addHandler(lh)
if os.getenv('DEBUG', False):
	# print("debug ls on")
	log.setLevel(logging.DEBUG)
# print("logging to:%s" % logFile)

pidPath = os.path.join(
    standardpaths.get_writable_path('app_local_data'), 'agent.pid')
pidFile = daemon.pidfile.PIDLockFile(pidPath)

urls = ('/agent/masterkey', 'masterkey')

secret = {}


def timeout():
	"""called when it's time to exit"""
	log.info("Exiting because we have outlived our welcome")
	web.httpserver.server.stop()


class masterkey:
	"""webpy index class.
	"""
	def POST(self):
		"""index post"""
		global secret
		try:
			data = json.loads(web.data())
		except json.JSONDecodeError:
			return json.dumps({'error': 'invalid JSON'})
		if data['key'] == secret['agent_token']:
			if data['exit']:
				log.info("exit called for")
				sys.exit(0)
			log.info("correct agent secret, returning master_key")
			return json.dumps({'master_key': secret['master_key']})
		else:
			log.warning("sent wrong agent key, denying access")
			return json.dumps({"error": "invalid agent_token"})
		log.warning("NO agent key sent. bad actor maybe?")
		return json.dumps({"error": "unknown error"})

	def GET(self):
		"""index get"""
		return json.dumps({"error": "POST JSON with the secret key"})


def daemonizedMain(secret):
	"""daemonize me, please!
	"""
	if secret['timeout'] > 0:
		log.debug("will timeout in %s seconds", secret['timeout'])
		threading.Timer(int(secret['timeout']), timeout).start()
	else:
		log.debug("no timeout being set.")
	log.debug("starting up webapp")
	app = web.application(urls, globals())
	app.run()


def main():
	"""main"""
	global secret
	global pidFile
	inp = sys.stdin.readline()
	try:
		secret = json.loads(inp)
	except json.JSONDecodeError:
		msg = "invalid JSON on stdin, send encryption key as JSON to stdin"
		log.error(msg)
		sys.exit(1)
	if 'agent_token' not in secret:
		log.error("invalid JSON, must have: agent_token: %s", secret)
	if 'master_key' not in secret:
		log.error("invalid JSON, must have: master_key:%s", secret)
		sys.exit()
	log.debug("secret recieved:%s", secret)
	if 'foreground' in secret:
		log.debug("not daemonizing")
		pidFile = None
		daemonizedMain(secret)
	else:
		log.debug("Daemonizing...")
		wd = standardpaths.get_writable_path('app_local_data')
		with daemon.DaemonContext(
		    working_directory=wd,
		    files_preserve=["agent.log"],
		    umask=0o002,
		    pidfile=pidFile):
			daemonizedMain(secret)


if __name__ == '__main__':
	main()
