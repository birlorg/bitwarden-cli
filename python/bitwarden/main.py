#!/usr/bin/env python3
"""
http://click.pocoo.org/5/complex/#building-a-git-clone
pylint: disable=W191
"""
import os
import json
import logging

# pylint: disable=E0401
import click
import bitwarden.db
import bitwarden.crypto as crypto
import bitwarden.client as client
import standardpaths  # https://github.com/uranusjr/pystandardpaths
import tablib  # http://docs.python-tablib.org/en/master/

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
        self.dbURL = dbURL
        self.config = bitwarden.db.Config(self.db)
        if url:
            self.config.url = url
        if identurl:
            self.config.identurl = identurl


@click.group()
# default for URL is in the db.py file, so it will not be changed if already set..
@click.option('--url', envvar='BITWARDEN_URL', required=False, default=None)
@click.option('--identurl', envvar='BITWARDEN_IDENT_URL', required=False, default=None)
@click.option('--debug/--no-debug', default=False, envvar='DEBUG')
@click.option('--db', envvar='BITWARDEN_DB', default=None)
@click.pass_context
def cli(ctx, url, identurl, debug, db):
    """Bitwarden CLI program."""
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
@click.argument('email', required=True)
@click.option('--timeout', "-t", default=0)
@click.password_option()
@click.pass_obj
def login(cli, email, password, timeout):
    """login to server.

    --timeout is how long the agent should run for in seconds.
    By default (value of 0) timeout will be set to the length of the login
    access token defined by the server.
    If set to a negative value (say -t -1) then the agent
    will never stop, until you call the logout command.

    email is optional, as it remembers the email from previous logins.

    example:
        $ bitwarden login nobody@example.com
        Password:

        self hosted:
        bitwarden --url https://bitwarden.example.com/api --identurl https://bitwarden.example.com/identity login nobody@example.com --timeout 28800

        login to a self-hosted bitwarden-ruby or bitwarden-go server @ bitwarden.example.com URL.
        timeout of the agent set to 8hrs. (so you can work offline all day)

    NOTES:
        * if you login to a self-hosted instance, you *MUST* set both
        --url and --identurl see above example for likely settings.
        * --timeout does not change the access token server timeout.
            so server operations may require you to re-login.
        * --url and --identurl are saved for you, so you only have
            to define them one time.
    """
    # log.debug("login as:%s", email)
    cli.client = client.Client(cli.db, cli.debug)
    cli.client.login(email, password, timeout)
    del password


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to empty the db?')
@click.pass_obj
def deletedb(cli):
    """***THIS ERASES DATA*** Flush and empty the database of all values.

    ***THIS ERASES DATA***

    This gives you a nice clean fresh feeling, and erases all values
    including any configuration and settings.
    so be *CAREFUL* and *SURE* you want to do this, before
    doing so.

    ***THIS ERASES DATA***
    """
    for table in cli.db.get_table_names():
        cli.db.query("delete from :tablename", tablename=table)
        log.debug("all data erased from %s", table)


@cli.command()
@click.pass_obj
def status(cli):
    """Show various statistics.

    Advanced examples:
    get last sync time:
        bw status | grep Sync| cut -f 2
    get agent pid if it is running:
        bw status | grep PID | cut -f 2
    """
    stats = {}
    stats['Password Entries '] = str(cli.db.query(
        "select count() as count from ciphers").first()['count'])
    stats['Agent Location   '] = cli.config.agent_location
    stats['Last Sync Time   '] = str(cli.config.last_sync_time)
    stats['Database Location'] = cli.dbURL.replace('sqlite:///', '')
    stats['Agent PID        '] = str(cli.config.isAgentRunning())
    for k, v in stats.items():
        row = "".join((click.style(k, fg="blue"), ":\t", v))
        click.echo(row)


@cli.command()
@click.pass_obj
def slab(cli):
    """run in slab mode."""
    cli.client = client.Client(cli.db, cli.debug)
    cli.client.slab()


@cli.command()
@click.option('--pwonly', "-p", is_flag=True, default=False)
@click.option('--decrypt/--no-decrypt', "-d", is_flag=True, default=False)
@click.option('--fulldecrypt', is_flag=True, default=False)
@click.argument("uuid", required=True)
@click.pass_obj
def fetch_uuid(cli, uuid, pwonly, decrypt, fulldecrypt):
    """fetch by UUID.

    --pwonly (or -p) will return ONLY the password, in decrypted form.
    --decrypted (or -d) will return the json object with all
        encrypted fields decrypted, except the password.
    --fulldecrypt just like --decrypted, except will return
        the password decrypted as well.

    output format is always pretty printed JSON, unless --pwonly is set.
    """
    cli.client = client.Client(cli.db, cli.debug)
    click.echo(cli.client.fetchUUID(uuid, pwonly, decrypt, fulldecrypt))


@cli.command()
@click.pass_obj
@click.argument("query", required=True)
@click.option("--params", "-p", required=False, multiple=True)
@click.option('--format', "-f", type=click.Choice(
    ['csv', 'tsv', 'json', 'yaml', 'html', 'xls', 'xlsx', 'dbf', 'latex', 'ods']),
    required=False, default=None)
def sql(cli, query, params, format):
    """query the local data store using SQL.

    Basically just a wrapper around the records CLI.

    Query: can either be a filename to run or a SQL query string.
    Query Parameters:
        Query parameters can be specified in key=value format, and injected
        into your query in :key format e.g.:
        $ bitwarden sql 'select created_at from ciphers where uuid ~= :uuid' -p uuid=84c1bf0a-b0e8-49c4-8e58-8d0fc0a247c4

    Examples:
        show all uuid entries:
            bw sql "select uuid from ciphers where uuid is not null"

        show all local config settings and their values if they are defined:
            bw sql "select key, value from config" -f tsv
    """
    try:
        params = dict([i.split('=') for i in params])
    except ValueError:
        print('Parameters must be given in key=value format.')
        print("params given:%s" % params)
        exit(6)
    # if a file, run it.
    if os.path.isfile(query):
        rows = cli.db.query_file(query, **params)
    # Execute the query as a string.
    else:
        rows = cli.db.query(query, **params)
    if format is None:
        print(rows.dataset)
    else:
        print(rows.export(format))
    return


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
