#!/usr/bin/python3

import json
import sqlite3
import threading


class Cursor:
    def __init__(self, filename):
        self._lock = threading.Lock()
        self.connect(filename)

    def connect(self, filename):
        self._db = sqlite3.connect(str(filename), isolation_level=None, check_same_thread=False)
        self._cur = self._db.cursor()

    def insert(self, table, *values):
        values = [json.dumps(i) if isinstance(i, (dict, list)) else i for i in values]
        with self._lock:
            self._cur.execute(
                f"INSERT OR REPLACE INTO {table} VALUES ({','.join('?'*len(values))})", values
            )

    def execute(self, cmd, *args):
        with self._lock:
            self._cur.execute(cmd, *args)

    def fetchone(self, cmd, *args):
        with self._lock:
            self._cur.execute(cmd, *args)
            result = self._cur.fetchone()
            if result:
                return tuple(json.loads(i) if str(i)[:1] in ("[", "{") else i for i in result)

    def fetchall(self, cmd, *args):
        with self._lock:
            self._cur.execute(cmd, *args)
            return self._cur.fetchall()

    def close(self):
        self._cur.close()
        self._db.close()
