#!/usr/bin/env python3
"""
http://click.pocoo.org/5/complex/#building-a-git-clone
pylint: disable=W191
"""
import os
import logging

# pylint: disable=E0401
import click
import bitwarden.db
import bitwarden.crypto as crypto
import bitwarden.client as client
import standardpaths  # https://github.com/uranusjr/pystandardpaths

logging.basicConfig()
log = logging.getLogger(__name__)
bitwarden_log = logging.getLogger("bitwarden")
bitwarden_log.setLevel(logging.INFO)
bitwarden_log.propagate = True

standardpaths.configure(application_name='bitwarden',
                        organization_name='birl.org')


class CLI():
    """CLI class """

    def __init__(self, url=None, identurl=None, debug=False, dbURL=None):
        """initialize"""
        self.debug = debug
        if self.debug:
            bitwarden_log.setLevel(logging.DEBUG)
            log.setLevel(logging.DEBUG)
            log.debug("debug turned on")
        log.debug("db:%s", dbURL)
        self.db = bitwarden.db.connect(dbURL)
        self.config = bitwarden.db.Config(self.db)
        if url:
            self.config.url = url
        if identurl:
            self.config.identurl = identurl

# click docs: http://click.pocoo.org/6/complex/#building-a-git-clone


@click.group()
# default for URL is in the db.py file, so it will not be changed if already set..
@click.option('--url', envvar='BITWARDEN_URL', required=False, default=None)
@click.option('--identurl', envvar='BITWARDEN_IDENT_URL', required=False, default=None)
@click.option('--debug/--no-debug', default=False, envvar='DEBUG')
@click.option('--db', envvar='BITWARDEN_DB', default=None)
@click.pass_context
def cli(ctx, url, identurl, debug, db):
    """CLI main"""
    if not db:
        writePath = standardpaths.get_writable_path('app_local_data')
        filePath = os.path.join(writePath, 'bitwarden.sqlite')
        db = "sqlite:///{}".format(filePath)
        if not os.path.exists(writePath):
            # create config dir and make secure as possible.
            os.makedirs(writePath)
            os.chmod(writePath, 0o0700)
        if not os.path.exists(filePath):
            # pylint: disable=E501
            msg = "Database does not exist, use lb or copy tools/bitwarden.sqlite to:{}"
            print(msg.format(filePath))
    cli = CLI(url, identurl, debug, db)
    ctx.obj = cli


@cli.command()
@click.argument('email', required=True)
@click.password_option()
@click.option('--hint', default="", required=False)
@click.option('--name', envvar='USER', default="", required=False)
@click.pass_obj
def register(cli, email, password, name, hint):
    """register a new account on server."""
    log.debug("registering as:%s", email)
    cli.client = client.Client(cli.db, cli.debug)
    cli.client.register(email, password, name, hint)
    del password


@cli.command()
@click.argument('email', required=False)
@click.password_option()
@click.pass_obj
def login(cli, email, password):
    """login to server."""
    # log.debug("login as:%s", email)
    cli.client = client.Client(cli.db, cli.debug)
    cli.client.login(email, password)
    del password


@cli.command()
@click.pass_obj
def slab(cli):
    """run in slab mode."""
    cli.client = client.Client(cli.db, cli.debug)
    cli.client.slab()


@cli.command()
@click.pass_obj
def pull(cli):
    """pull all records from server, updating local store as needed."""
    # log.debug("login as:%s", email)
    cli.client = client.Client(cli.db, cli.debug)
    cli.client.pull()


@cli.command()
@click.pass_obj
def logout(cli):
    """logout from server, stop agent and forget all secret keys."""
    # log.debug("login as:%s", email)
    # cli.client = client.Client(cli.db, cli.debug)
    cli.config.master_key = None
    cli.config.token = None
    print("logged out, forgotten master_key and remote access_token.")
