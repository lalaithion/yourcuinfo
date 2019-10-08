CREATE TABLE students (
  id SERIAL PRIMARY KEY,
  username VARCHAR NOT NULL,
  password VARCHAR NOT NULL,
  displayname VARCHAR,
  joined DATE
);

CREATE TABLE class_comments (
  id SERIAL PRIMARY KEY,
  ranking INTEGER,
  comment VARCHAR,
  upvotes INTEGER DEFAULT 0,
  downvotes INTEGER DEFAULT 0
);