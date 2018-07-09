--@create_scripts
CREATE TABLE scripts (
  id INTEGER PRIMARY KEY,
  script TEXT,
  description TEXT,
  fork BOOLEAN,
  public_token TEXT
);
