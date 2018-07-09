--@create_users
CREATE TABLE users (
  uname TEXT PRIMARY KEY,
  pass_hash TEXT,
  salt TEXT
);

--@create_sessions
CREATE TABLE sessions (
  token TEXT PRIMARY KEY,
  expires DATE,
  uname TEXT,
  FOREIGN KEY (uname) REFERENCES users(uname) ON DELETE CASCADE
);

--@create_permissions
CREATE TABLE permissions (
  uname TEXT NOT NULL,
  ptype INTEGER NOT NULL,
  PRIMARY KEY (uname, ptype),
  FOREIGN KEY (uname) REFERENCES users(uname) ON DELETE CASCADE ,
  FOREIGN KEY (ptype) REFERENCES permission_types(ptype) ON DELETE CASCADE
);

--@create_permission_types
CREATE TABLE permission_types (
  ptype INTEGER PRIMARY KEY,
  pname TEXT UNIQUE
);

--@check_token_permission(token, permission_name, time_now)
SELECT 1 FROM permissions
  INNER JOIN users ON users.uname = permissions.uname
  INNER JOIN sessions ON sessions.uname = users.uname
  INNER JOIN permission_types ON permissions.ptype = permission_types.ptype
WHERE sessions.token = ? AND permission_types.pname = ? AND sessions.expires > ?;

--@get_session_user(session, expiry)
SELECT uname FROM sessions WHERE token = ? AND expires > ?;

--@create_user(uname, pass_hash, salt)
INSERT INTO users (uname, pass_hash, salt) VALUES (?, ?, ?);

--@change_password(pass_hash, salt, uname)
UPDATE users SET pass_hash = ?, salt = ? WHERE uname = ?;

--@get_pass_hash(uname)
SELECT pass_hash, salt FROM users WHERE uname = ?;

--@delete_user(uname)
DELETE FROM users WHERE uname = ?;

--@create_session(token, expiry, uname)
INSERT INTO sessions (token, expires, uname) VALUES (?, ?, ?);

--@expire_sessions(expiry)
DELETE FROM sessions WHERE expires < ?;

--@expire_sessions_user(uname)
DELETE FROM sessions WHERE uname = ?;

--@add_permission(uname, pname)
INSERT INTO permissions (uname, ptype) VALUES (?, (SELECT (ptype) FROM permission_types WHERE pname = ?));

--@get_permissions(uname)
SELECT permission_types.pname FROM permission_types
  INNER JOIN permissions ON permission_types.ptype = permissions.ptype
WHERE permissions.uname = ?;

--@remove_permission(uname, pname)
DELETE FROM permissions WHERE uname = ? AND ptype = (SELECT ptype FROM permission_types WHERE pname = ?);

--@add_permission_type(pname)
INSERT INTO permission_types (pname) VALUES (?);

--@delete_permission_type(pname)
DELETE FROM permission_types WHERE pname = ?;
