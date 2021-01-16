import sqlite3

from datetime import datetime
import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
  #this block of code returns the same connection so it connects with the same db file
  #for multiple users
    if 'db' not in g:
        # creates database with the path set in __init__.py
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    # returns the database if there is a database in g, otherwise returns sets db to None
    db = g.pop('db', None)
    # if there was a database stored in g, the database is closed
    if db is not None:
        db.close()

#Reads the sql file and executes the commands in it
def init_db():
    db = get_db()
    # runs the commands in schema.sql
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

# makes it so that you can run command 'flask init-db' from the command line
# and it initializes the database
@click.command('init-db')
@with_appcontext
def init_db_command():
    # clears the existing data and create new tables.
    init_db()
    # prints to command line that the database is initialized
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    # enables init-db command
    app.cli.add_command(init_db_command)


# db methods for each blueprint
def check_username(username):
    db = get_db()
    data = db.execute("SELECT COUNT(*) FROM users WHERE username=?", (username,)).fetchone()
    exist = data[0] != 0
    return exist

def check_credentials(username, password):
    db = get_db()
    exist = False
    for row in db.execute("SELECT * FROM users"):
        exist = exist or (username == row[0] and password == row[1])
    return exist

def add_user(username, password, title, description):
    db = get_db()
    current = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    db.execute("INSERT INTO users VALUES (?, ?)", (username, password))
    db.execute("INSERT INTO blogs (user, name, description, time) VALUES (?, ?, ?, ?)", (username, title, description, current))
    ofBlog = db.execute("SELECT MAX(blogId) FROM blogs").fetchone()[0]
    db.execute("INSERT INTO entries (body, time, ofBlog) VALUES (?, ? , ?)", ("Hello World", current, ofBlog))
    db.commit()

#The purpose of this dictionary is so that we can easily associate a db method with
#authentication methods in the actual writing of the code by calling the keys
#of the dictionary.
auth_methods = {
    'check_username': check_username,
    'check_credentials': check_credentials,
    'add_user': add_user,
}