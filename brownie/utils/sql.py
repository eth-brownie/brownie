#!/usr/bin/python3

import json
import sqlite3
import threading
from typing import Final, final


dumps: Final = json.dumps
loads: Final = json.loads


@final
class Cursor:
    def __init__(self, filename):
        self._lock: Final = threading.Lock()
        self._db: Final = sqlite3.connect(str(filename), isolation_level=None, check_same_thread=False)
        self._cur: Final = self._db.cursor()
        self._execute: Final = self._cur.execute
        self._fetchone: Final = self._cur.fetchone
        self._fetchall: Final = self._cur.fetchall

    def insert(self, table, *values):
        values = [dumps(i) if isinstance(i, (dict, list)) else i for i in values]
        with self._lock:
            self._execute(
                f"INSERT OR REPLACE INTO {table} VALUES ({','.join('?'*len(values))})", values
            )

    def execute(self, cmd, *args):
        with self._lock:
            self._execute(cmd, *args)

    def fetchone(self, cmd, *args):
        with self._lock:
            self._execute(cmd, *args)
            if result := self._fetchone():
                return tuple(loads(i) if str(i).startswith(("[", "{")) else i for i in result)

    def fetchall(self, cmd, *args):
        with self._lock:
            self._execute(cmd, *args)
            return self._fetchall()

    def close(self):
        self._cur.close()
        self._db.close()
