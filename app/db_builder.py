import sqlite3
import hashlib
import sys

DB_FILE = "data.db"
text_factory = str
salt = b"I am a static, plaintext salt!!@#T gp127 They're actually more effective than one might think..."

from datetime import datetime
import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

def get_db():
  #this block of code returns the same connection so it connects with the same db file
  #for multiple users
    if 'db' not in g:
        # creates database with the path set in __init__.py
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.text_factory = text_factory
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
    # runs the commands in schema.sql which is a sql file
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


# salts and hashes the given string
def saltString(string, salt):
    return hashlib.pbkdf2_hmac('sha256', string.encode('utf-8'), salt, 100000)

# helper function to format list of entries in paged format
def pageEntries(entries, pageSize):
    pagedEntries = []
    # get a range of entries of size pageSize and append to pagedEntries
    # if the rest of the entries list is too short, appends only the rest of the entries list
    for i in range(0, len(entries), pageSize):
        pagedEntries += [entries[i:min(i + pageSize, len(entries))]]
    return pagedEntries

# helper function to limit characters
# session["error_msg"] = "character limit exceeded"
def validateInput(name, value, error_msg_output):
    # value is stripped of whitespace and name specifies the type of checks to run on value
    # validateInput runs the checks on value and appends error messages to error_msg
    # if there were error messages, the stripped value is returned and error_msg is appended to error_msg_output
    # otherwise the stripped value is returned
    error_msg = []
    value = value.strip()
    if name == "username":
        if value == "":
            error_msg += ["Username can not be blank or have only spaces"]
        if not value.replace("_", "").isalnum() or " " in value:
            error_msg += ["Username can have only letters, numbers, and underscores"]
        if auth_methods["checkUsername"](value):
            error_msg += ["Username already exists"]
        if len(value) > 100:
            error_msg += ["Username can have only 100 characters or fewer"]

    if name == "password":
        if len(value) < 8 or len(value) > 100:
            error_msg += ["Password must have between 8 and 100 characters"]

    if name == "blogname":
        if value == "":
            error_msg += ["Blog name can not be blank or have only spaces"]
        if len(value) > 100:
            error_msg += ["Blog name can have only 100 characters or fewer"]

    if name == "blogdescription":
        if len(value) > 250:
            error_msg += ["Blog description can have only 250 characters or fewer"]

    if name == "entrytitle":
        if value == "":
            error_msg += ["Entry title can not be blank or have only spaces"]
        if len(value) > 100:
            error_msg += ["Entry title can have only 100 characters or fewer"]

    if name == "entrypic":
        if sys.getsizeof(value) > 100000000:
            error_msg += ["Entry image can be only 100MB or smaller"]

    if name == "entrycontent":
        if value == "":
            error_msg += ["Entry content can not be blank or have only spaces"]
        if len(value) > 10000:
            error_msg += ["Entry content can have only 10000 characters or fewer"]

    if len(error_msg):
        error_msg_output += error_msg
        return value
    else:
        return value

# makes users and entries table in database if they do not exist already
def createTables():
    db = get_db()
    db.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT,
              password TEXT, blogname TEXT, blogdescription TEXT, time DATETIME);""") #
    db.execute("""CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY,
              userID INTEGER, time DATETIME, title TEXT, post TEXT, pic TEXT);""")
    db.execute('CREATE TABLE IF NOT EXISTS followers (userID INTEGER, followerID INTEGER);')
    db.commit()

salt = "plain text salt.. hi. salting is a little different with the refactoring, but it still works i think"

# adds user info to user table
def register(username, password, blogname, blogdescription):
    db = get_db()
    #Finds the current date and time based on the local time
    dateAndTimeTup = db.execute("SELECT datetime('now','localtime');").fetchone()
    dateAndTime = str(''.join(map(str, dateAndTimeTup)))
    command = "INSERT INTO users (username, password, blogname, blogdescription, time) VALUES (?,?,?,?,?);"
    password = generate_password_hash(password + salt)
    db.execute(command, (username, password, blogname, blogdescription, dateAndTime))
    db.commit()

# returns whether or not username is in user table
def checkUsername(username):
    db = get_db()
    found = False
    for row in db.execute("SELECT * FROM users;"):
        found = found or (username == row[1])
    db.commit()
    return found

# returns information about a user from the specified column
# col can be 'id', 'password', 'blogname', or 'blogdescription'
def getInfo(username, col):
    if checkUsername(username):
        db = get_db()
        #Finds the user with the correct username
        info = db.execute("SELECT " + col + " FROM users WHERE username=?;", [username]).fetchone()[0]
        db.commit()
        return info
    return None

#Gets a username based on a user id
def getUsername(userID):
    db = get_db()
    info = db.execute("SELECT username FROM users WHERE id=?;", [userID]).fetchone()
    db.commit()
    if info is None:
        return info
    return info[0]

# changes a user's blog info given a new blog name and description
def updateBlogInfo(username, blogname, desc):
    if checkUsername(username):
        db = get_db()
        db.execute("UPDATE users SET blogname=? WHERE username=?;", (blogname, username))
        db.execute("UPDATE users SET blogdescription=? WHERE username=?;", (desc, username))
        db.commit()

# converts rows in database to a dictionary
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# returns a list of dictionaries containing each blog's info
def getBlogs():
    db = get_db()
    blogs = db.execute("SELECT * from users ORDER BY time DESC;").fetchall()
    db.commit()
    return [dict(i) for i in blogs]

#Adds an entry to the entries table
def addEntry(userID, title, post, pic):
    db = get_db()
    #Gets the current date and time
    dateAndTimeTup = db.execute("SELECT datetime('now','localtime');").fetchone()
    dateAndTime = str(''.join(map(str, dateAndTimeTup)))
    command = "INSERT INTO entries (userID, time, title, post, pic) VALUES (?,?,?,?,?);"
    #Executes command
    db.execute(command, (str(userID), dateAndTime, title, post, pic))
    #New time of entry
    db.execute("UPDATE users SET time=? WHERE id=?;", (dateAndTime, str(userID)))
    db.commit()

#Edits a past entry based on id
def editEntry(entryID, title, post, pic):
    db = get_db()
    dateAndTimeTup = db.execute("SELECT datetime('now','localtime');").fetchone()
    dateAndTime = str(''.join(map(str, dateAndTimeTup)))
    #Updates the entries
    db.execute("UPDATE entries SET title=? WHERE id=?;", (title, str(entryID)))
    db.execute("UPDATE entries SET post=? WHERE id=?;", (post, str(entryID)))
    db.execute("UPDATE entries SET time=? WHERE id=?;", (dateAndTime, str(entryID)))
    db.execute("UPDATE entries SET pic=? WHERE id=?;", (pic, str(entryID)))
    userID = db.execute("SELECT userID FROM entries WHERE id=?;", [str(entryID)]).fetchone()
    db.execute("UPDATE users SET time=? WHERE id=?;", (dateAndTime, str(userID[0])))
    db.commit()

#Gets all of a users entries
def getEntries(userID):
    db = get_db()
    entries = db.execute("SELECT * FROM entries WHERE userID=? ORDER BY time DESC;", [str(userID)]).fetchall()
    db.commit()
    return [dict(i) for i in entries]

#Gets an entries information based on entryID
def getEntryInfo(entryID, col):
    db = get_db()
    info = db.execute("SELECT " + col + " FROM entries WHERE id=?;", [str(entryID)]).fetchone()[0]
    db.commit()
    return info

#deletes an entry
def deleteEntry(entryID):
    db = get_db()
    db.execute("DELETE FROM entries WHERE id=?;", [str(entryID)])
    db.commit()

#searches the database's entries for a specific word
def search(criteria):
    db = get_db()
    criteria_list = ['%' + i.replace('%', '[%]') + '%' for i in criteria.split()]
    command = "SELECT * FROM entries WHERE (post LIKE ?"
    for x in criteria_list[1:]:
        command += " AND post LIKE ?"
    command += ") OR (title LIKE ?"
    for x in criteria_list[1:]:
        command += " AND title LIKE ?"
    command += ");"
    entries = db.execute(command, criteria_list + criteria_list).fetchall()
    db.commit()
    return [dict(i) for i in entries]
  

# adds row to followers table if it doesn't already exist
# users with followerID follws user with userID
def addFollower(userID, followerID):
    if not checkFollower(userID, followerID):
        db = get_db()
        command = "INSERT INTO followers VALUES (?,?);"
        db.execute(command, (userID, followerID))
        db.commit()

# removes row with specified info from followers table
def removeFollower(userID, followerID):
    db = get_db()
    db.execute("DELETE FROM followers WHERE userID=? AND followerID=?;", (str(userID), str(followerID)))
    db.commit()

# return whether or not a user-follower pair exists
def checkFollower(userID, followerID):
    db = get_db()
    found = db.execute("SELECT * FROM followers WHERE userID=? AND followerID=?;",
                      (str(userID), str(followerID))).fetchone()
    db.commit()
    return found is not None

# returns a list of dictionaries of blogs a user is following
def getFollowedBlogs(followerID):
    db = get_db()
    followedUsers = db.execute("SELECT userID FROM followers WHERE followerID=?;", [str(followerID)]).fetchall()
    blogs = []
    for user in followedUsers:
        blog = db.execute("SELECT * FROM users WHERE id=?;", [str(user["userID"])]).fetchone()
        blogs.append(blog)
    db.commit()
    return [dict(i) for i in blogs]

#Clears everything
def clearAll():
    clearEntries()
    clearUsers()
    clearFollowers()

def clear():
    db = get_db()
    db.execute("DROP TABLE entries;")
    db.commit()

# deletes all users from the database (for testing purposes)
def clearUsers():
    db = get_db()
    db.execute("DELETE from users;")
    db.commit()

# Delete a specific user
def clearUser(username):
    db = get_db()
    db.execute("DELETE from users WHERE username=?;", [username])
    db.commit()

# deletes everything in followers table
def clearFollowers():
    db = get_db()
    db.execute("DELETE from followers;")
    db.commit()

#Clears all entries, bugfixxing
def clearEntries():
    db = get_db()
    db.execute("DELETE from entries;")
    db.commit()

# prints user table (for testing purposes)
def printDatabase():
    db = get_db()
    print("--------Users Table-----------")
    for row in db.execute("SELECT * FROM users;"):
        print(list(row))
    print("-------Entries Table----------")
    for row in db.execute("SELECT * FROM entries;"):
        print(list(row))
    db.commit()

#create a dictionary of method name: method for auth methods
auth_methods = {
    'addUser': register,
    'checkUsername': checkUsername,
    'getPwd': getInfo, 
    'salt': salt
}

#create a dictionary of method name: method for blog/entry methods 
blog_methods = {
  'getInfo': getInfo,
  'getUsername': getUsername,
  'updateBlogInfo': updateBlogInfo,
  'getBlogs': getBlogs,
  'addEntry': addEntry,
  'editEntry': editEntry,
  'getEntries': getEntries,
  'getEntryInfo': getEntryInfo,
  'deleteEntry': deleteEntry
}

search_methods = {
  'search': search
}

follow_methods = {
  'addFollower': addFollower,
  'removeFollower': removeFollower,
  'checkFollower': checkFollower,
  'getFollowedBlogs': getFollowedBlogs
}

createTables()

'''if __name__ == "__main__":
    clearAll()
    clear()
    createTables()
    register("userA", saltString("passsssssss", salt), "my first blog", "A very cool lil blog")
    register("userB", saltString("passsssssss", salt), "I hate the other blog", "I am raging schizophrenic")
    register("userC", saltString("passsssssss", salt), "Cute Dog Pictures", "Cute dog pictures")

    addEntry("1", "Hey guys!", "Hows it going", "")
    addEntry("2", "Stop", "get off", "")
    addEntry("1", "Why are you mean :(", "You guys alright?", "")
    addEntry("3", "Dog", "imagine a dog here", "")
    addEntry("1", "oh god", "Hahah hey", "")
    deleteEntry("4")

    addFollower(1, 2)  # 2 follows 1
    addFollower(2, 1)  # 1 follows 2
    addFollower(3, 2)  # 2 follows 3
    # removeFollower(1,2)

    print(checkFollower(2, 1))
    print(checkFollower(1, 2))
    print(getFollowedBlogs(2))
'''

printDatabase()
getBlogs()
