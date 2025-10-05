#!/usr/bin/python3

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Final, Optional, Tuple, final

from brownie._c_constants import ujson_dumps, ujson_loads


@final
class Cursor:
    __slots__ = "_lock", "_db", "_cur", "_execute", "_fetchone", "_fetchall"

    def __init__(self, filename: Path) -> None:
        self._lock: Final = threading.Lock()
        self.connect(filename)

    def connect(self, filename: Path) -> None:
        self._db = sqlite3.connect(str(filename), isolation_level=None, check_same_thread=False)
        self._cur = self._db.cursor()
        self._execute = self._cur.execute
        self._fetchone = self._cur.fetchone
        self._fetchall = self._cur.fetchall

    def insert(self, table: str, *values: Any) -> None:
        encoded = [ujson_dumps(i) if isinstance(i, (dict, list)) else i for i in values]
        with self._lock:
            self._execute(
                f"INSERT OR REPLACE INTO {table} VALUES ({','.join('?'*len(encoded))})", encoded
            )

    def execute(self, cmd: str, *args: Any) -> None:
        with self._lock:
            self._execute(cmd, *args)

    def fetchone(self, cmd: str, *args: Any) -> Optional[Tuple[Any, ...]]:
        with self._lock:
            self._execute(cmd, *args)
            if result := self._fetchone():
                return tuple(ujson_loads(i) if str(i).startswith(("[", "{")) else i for i in result)
            return None

    def fetchall(self, cmd: str, *args: Any) -> Any:
        with self._lock:
            self._execute(cmd, *args)
            return self._fetchall()

    def close(self) -> None:
        self._cur.close()
        self._db.close()
