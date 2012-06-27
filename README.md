svn-git-trac - Migrate Trac Tickets Referencing Svn to Git
==========================================================

Will replace all texts in ticket and ticket_changes that reference svn 
(like [12345]) to the git hash equivalent (like [0a1bc3f]). 
Uses sqlalchemy.core for db backend abstraction which enables it to 
connect to all databases supported by trac.

Requirements
------------
 
 * OSX / Linux
 * Python 2.7 

Git Svn Repository
------------------

For this script to work a git repository must exist on the local machine
which was created using git svn clone with metadata intact. 
To see if your git folder fulfills this requirement try to run 
the following command:

    git svn log --oneline --show-commit

If this command, run in the git folder, returns something along these lines:

    r12345 | 0abc123 | Fixed the flux capacitator
    ...

Then you are good to go!

Installation
------------

1. Create a Virtual Environment

    mkdir git-svn-trac
    cd git-svn-trac
    virtualenv --no-site-packages -p python2.7 .
    source bin/activate

2. Run pip, using the requirements fitting for your database

    pip install -r mysql-requirements.txt
    or
    pip install -r sqlite-requirements.txt
    or
    pip install -r postgres-requirements.txt

3. Create a backup of your git folder and database!

Usage
-----

    python git-svn-trac.py gitfolder dsn

Examples
--------
    
    python git-svn-trac.py ~/helloworld/ mysql+pymysql://user:password@localhost/trac

    python git-svn-trac.py ~/project/ sqlite:///home/user/trac.db

    python git-svn-trac.py ~/project/ postgres+psycopg2://user:password@localhsot/trac

Author
------

Denis Krienbühl for Seantis GmbH

License
-------

Public Domain

This program is free software. It comes without any warranty!
