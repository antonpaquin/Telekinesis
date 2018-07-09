import sqlite3


def load_sql(fname):
    with open(fname, 'r') as sql_f:
        lines = [l.rstrip() for l in sql_f.readlines()]

    res = {}
    name = ''
    for line in lines:
        if line.startswith('--@'):
            name = line[3:]
            if '(' in name:
                name = name[:name.find('(')]
            name = name.strip()
            query = []
        elif line.endswith(';'):
            query.append(line)
            res[name] = '\n'.join(query)
        else:
            query.append(line)
    return res


class SqlConn:
    def __init__(self, db_location):
        self.db_location = db_location

    def __enter__(self) -> sqlite3.Cursor:
        self.conn = sqlite3.connect(self.db_location)
        self.cur = self.conn.cursor()
        self.cur.execute('PRAGMA foreign_keys = ON;')
        return self.cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_tb is not None:
            self.cur.close()
            self.conn.close()
            return False

        self.cur.close()
        self.conn.commit()
        self.conn.close()
