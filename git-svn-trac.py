# -*- coding: utf-8 -*-

import re
import sys
import os.path
import subprocess

from string import strip
from sqlalchemy import create_engine, sql
from sqlalchemy.schema import Table, MetaData
__doc__ = open('README.md').read()

def die(*messages):
    """Stop the execution of the script, optionally printing exit messages."""
    for m in messages:
        print(m)

    sys.exit(1)

def parse_args():
    """Validate the arguments and return git path, sqlalchemy engine and
    connection if successful. If not successful die.

    """
    args = sys.argv[1:]
    
    if len(args) != 2:
        die("Invalid arguments", __doc__)

    path, dsn = args

    if not os.path.isdir(path):
        die("Git path does not exist", __doc__)

    try:
        engine = create_engine(dsn)
        connection = engine.connect()
    except Exception, e:
        die("Couldn't connect to database: %s" % str(e))

    return path, engine, connection

def build_map(path):
    """Run git svn log and use the result to build a dictionary pointing
    from svn revision to short git hash.

    """
    cmd = 'cd %s && git svn log --oneline --show-commit' % path
    lines = subprocess.check_output(cmd, shell=True).split('\n')

    revmap = dict()
    for fragments in (l.split('|') for l in lines):
        
        if len(fragments) < 2:
            continue

        rev, hash = map(strip, fragments[:2])
        rev = rev.strip('r')

        revmap[rev] = hash

    return revmap

_pattern = re.compile(r'\[(\d+)\]')
def replace_reference(revmap, text):
    """Given the revision map go through the text and replace the revision
    numbers in brackets with git hashes. 

    """
    def handler(match):
        # get the new revision from the map or just leave the result
        # (it might get triggered by things that don't point to a revision, 
        # like python code within a comment)
        return '[%s]' % revmap.get(match.groups()[0], match.groups()[0])

    return re.sub(_pattern, handler, text)

def migrate_table(connection, revmap, table, keys, targets):
    """Replaces all svn references in the columns defined in the targets list with
    the git checksums. 

    Keys defines a list of columns which identify the record.
    Targets defines a list of columns which need replacing.

    """
    columns = keys + targets
    query = sql.select(columns)

    # load the records into memory
    detach = lambda r: r.values()
    records = map(detach, connection.execute(query))
    
    count = 0

    for record in records:
        change = False
        query = table.update()

        # build where clause with the key columns
        for i in range(0, len(keys)):
            query = query.where(keys[i]==record[i])

        # replace value and update query values
        for i in range(len(keys), len(columns)):
            replaced = replace_reference(revmap, record[i])
            column = targets[i - len(keys)].name
            query = query.values(**{column:replaced})

            # mark change
            change = change or record[i] != replaced

        if change:
            connection.execute(query)
            count += 1

    return count


def migrate(engine, connection, revmap):
    """Given engine, connection and revision map, go through the
    ticket descriptions and comments and migrate the svn revisions to
    git hashes.

    """
    metadata = MetaData()
    metadata.bind = engine

    tickets = Table('ticket', metadata, autoload=True)
    changes = Table('ticket_change', metadata, autoload=True)

    trans = connection.begin()
    try:

        count = migrate_table(connection, revmap,
            tickets, [tickets.c.id], 
            [tickets.c.description]
        )
        count += migrate_table(connection, revmap,
            changes, [changes.c.ticket, changes.c.time, changes.c.field], 
            [changes.c.newvalue]
        )

        trans.commit()
        
        print("Migrated %i records" % count)

    except Exception, e:
        trans.rollback()
        die("Migration error: %s" % repr(e), "Changes were rolled back")

if __name__=='__main__':
    path, engine, connection = parse_args()
    revmap = build_map(path)
    migrate(engine, connection, revmap)