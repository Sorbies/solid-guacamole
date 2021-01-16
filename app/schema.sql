-- This file is for conveniently creating the db as a script, it is NOT to store
-- methods that manipulate the db.

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS blogs;
DROP TABLE IF EXISTS entries;


CREATE TABLE users (
    username TEXT PRIMARY KEY, 
    password TEXT NOT NULL
);

CREATE TABLE blogs (
    blogId INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user TEXT NOT NULL, 
    name TEXT NOT NULL, 
    description TEXT NOT NULL, 
    time TEXT NOT NULL
);

CREATE TABLE entries (  
    entryId INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    body TEXT NOT NULL,
    time TEXT NOT NULL,
    ofBlog INTEGER, 
    FOREIGN KEY (ofBlog) REFERENCES blogs (blogId)
);