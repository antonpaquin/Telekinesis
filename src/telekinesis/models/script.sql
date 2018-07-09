--@get_script_by_id (script_id)
SELECT id, script, description, fork, public_token FROM scripts WHERE id = ?;

--@get_all_scripts
SELECT id, script, description, fork, public_token FROM scripts;

--@put_script (script, description, fork, public_token)
INSERT INTO scripts (script, description, fork, public_token) VALUES (?, ?, ?, ?);

--@get_last_id
SELECT last_insert_rowid();

--@update_script (script, description, fork, script_id, public_token)
UPDATE scripts SET script = ?, description = ?, fork = ?, public_token = ? WHERE id = ?;

--@delete_script (script_id)
DELETE FROM scripts WHERE id = ?;
