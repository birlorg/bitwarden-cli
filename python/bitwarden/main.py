#!/usr/bin/env python3
"""
http://click.pocoo.org/5/complex/#building-a-git-clone
pylint: disable=W191
"""
import os
import json
import logging
import sys

# pylint: disable=E0401
import click
import bitwarden.db
import bitwarden.crypto as crypto
import bitwarden.client as client
import standardpaths  # https://github.com/uranusjr/pystandardpaths
import tablib  # http://docs.python-tablib.org/en/master/

click.disable_unicode_literals_warning = True

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
        self.client = client.Client(self.db, self.debug)


@click.group()
# default for URL is in the db.py file, so it will not be changed if already set..
@click.option('--url', envvar='BITWARDEN_URL', required=False, default=None)
@click.option('--identurl', envvar='BITWARDEN_IDENT_URL', required=False, default=None)
@click.option('--debug/--no-debug', default=False, envvar='DEBUG')
@click.option('--db', envvar='BITWARDEN_DB', default=None)
@click.version_option()
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
            msg = "Database does not exist." + os.linesep
            msg += "You can use Liquibase and generate it," + os.linesep
            msg += "or for the lazy:" + os.linesep
            msg += "curl -o {} https://fossil.birl.ca/bitwarden-cli/doc/trunk/tools/bitwarden.sqlite"
            print(msg.format(filePath))
            sys.exit(2)
    cli = CLI(url, identurl, debug, db)
    ctx.obj = cli


@cli.command()
@click.argument('email', required=True)
@click.option('--password', prompt=True, hide_input=True)
@click.option('--hint', default="", required=False)
@click.option('--name', envvar='USER', default="", required=False)
@click.pass_obj
def register(cli, email, password, name, hint):
    """register a new account on server."""
    log.debug("registering as:%s", email)
    cli.client.register(email, password, name, hint)
    del password


@cli.command()
@click.argument('email', required=True)
@click.option('--timeout', "-t", default=0)
@click.option('--password', prompt=True, hide_input=True)
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

        self hosted (bitwarden-ruby or bitwarden-go):

        login to a self-hosted bitwarden-ruby or bitwarden-go server @ bitwarden.example.com URL. with an 8hr agent timeout(so you can work offline all day).

        bitwarden --url https://bitwarden.example.com/api --identurl https://bitwarden.example.com/identity login nobody@example.com --timeout 28800

        self hosted bitwarden proper:

            unknown at this time. 

    NOTES:
        * if you login to a self-hosted instance, you *MUST* set both
        --url and --identurl see above example for likely settings.
        * --timeout does not change the access token server timeout.
            so server operations may require you to re-login.
        * --url and --identurl are saved for you, so you only have
            to define them one time.
    """
    # log.debug("login as:%s", email)
    cli.client.login(email, password, timeout)
    del password


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to empty the db?')
@click.pass_obj
def emtpydb(cli):
    """Flush and empty the database of all values.

    ***THIS ERASES DATA***

    This gives you a nice clean fresh feeling, and erases all values
    including any configuration and settings.
    so be *CAREFUL* and be *SURE* you want to do this, before
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
    """run in slab mode.

    iterm2 coprocess command:

export LANG=en_CA.UTF-8;export LOCALE=en_CA.UTF-8; /usr/local/bin/bitwarden slab

    You may need to change the LOCAL and LANG settings and the path above.

        which bitwarden

    should get you the path. and echo $LANG should get you the locale and lang
    settings.

    slab mode searches and displays only uri's that equal:
    sudolikeaboss://local

    I recommend: brew install choose-gui. and then bitwarden slab will be all
    the more amazing. more info on the chooser here:
    https://github.com/sdegutis/choose
    """
    cli.client.slab()


@cli.command()
@click.option('--pwonly', "-p", is_flag=True, default=False)
@click.option('--decrypt/--no-decrypt', "-d", is_flag=True, default=False)
@click.option('--fulldecrypt', is_flag=True, default=False)
@click.argument("uuid", required=True)
@click.pass_obj
def fetch_uuid(cli, uuid, pwonly, decrypt, fulldecrypt):
    """fetch by UUID.

    This will be quite fast, as it only has to decrypt 1 cipher record.

    --pwonly (or -p) will return ONLY the password, in decrypted form.
    --decrypted (or -d) will return the json object with all
        encrypted fields decrypted, except the password.
    --fulldecrypt just like --decrypted, except will return
        the password decrypted as well.

    output format is always pretty printed JSON, unless --pwonly is set.
    """
    click.echo(cli.client.fetchUUID(uuid, pwonly, decrypt, fulldecrypt))

@cli.command()
@click.option('--pwonly', "-p", is_flag=True, default=False)
@click.option('--decrypt/--no-decrypt', "-d", is_flag=True, default=False)
@click.option('--fulldecrypt', is_flag=True, default=False)
@click.argument("name", required=True)
@click.pass_obj
def fetch_name(cli, name, pwonly, decrypt, fulldecrypt):
    """fetch by name.

    This will be relatively slow, as it has to decrypt every single name
    to compare before it finds the right one.

    --pwonly (or -p) will return ONLY the password, in decrypted form.
    --decrypted (or -d) will return the json object with all
        encrypted fields decrypted, except the password.
    --fulldecrypt just like --decrypted, except will return
        the password decrypted as well.

    output format is always pretty printed JSON, unless --pwonly is set.
    """
    click.echo(cli.client.fetchName(name, pwonly, decrypt, fulldecrypt))

@cli.command()
@click.pass_obj
@click.option('--format', "-f", type=click.Choice(
    ['csv', 'tsv', 'json', 'yaml', 'html', 'xls', 'xlsx', 'dbf', 'latex', 'ods']),
    required=False, default=None)
@click.option('--headers/--no-headers', default=True)
@click.argument("query", required=True)
def find(cli, query, format, headers):
    """find query in username,uri

    this does a simpe python string find i.e.:

        if query in username:

    but searches against username and first url

    You can export it in almost any format you wish with -f

    to get the password once you found an entry use fetch_uuid 

    complicated example:
   
    \b
    bw find example.com -f tsv --no-headers | fzf | cut -f 1 | xargs bitwarden fetch_uuid -p

   which means: find all entries with example.com in them, use fzf
   to select a record and return only the password.
    """
    ret = cli.client.find(query)
    if ret:
        d = tablib.Dataset()
        if headers:
            d.headers = ret[0].keys()
        for row in ret:
            try:
                d.append(row.values())
            except tablib.core.InvalidDimensions:
                log.error("can not add row:%s", row)
        if format:
            click.echo(d.export(format))
        else:
            click.echo(d)


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

    you can get the results back in pretty much any format you wish:
    ['csv', 'tsv', 'json', 'yaml', 'html', 'xls', 'xlsx', 'dbf', 'latex', 'ods']),

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
    cli.client.pull()


@cli.command()
@click.pass_obj
def logout(cli):
    """logout from server, stop agent and forget all secret keys."""
    # log.debug("login as:%s", email)
    cli.config.master_key = None
    cli.config.token = None
    print("logged out, forgotten master_key and remote access_token.")
