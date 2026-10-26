"""Logical read-only SQLite snapshots; auxiliary WAL/SHM requires explicit consent."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3


def _authorize(action, arg1, arg2, database, trigger):
    allowed = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION,
               sqlite3.SQLITE_TRANSACTION, sqlite3.SQLITE_RECURSIVE}
    if action == sqlite3.SQLITE_PRAGMA:
        # No mutable PRAGMA is allowed after connection setup.
        return sqlite3.SQLITE_OK if arg1.lower() == 'query_only' and arg2 is None else sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION and (arg2 or '').lower() == 'load_extension':
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY


@contextmanager
def protected_snapshot(path, connect=sqlite3.connect, *, allow_auxiliary=False):
    path = Path(path).resolve(strict=True)
    with path.open('rb') as stream:
        header = stream.read(20)
    if len(header) < 20 or header[:16] != b'SQLite format 3\x00':
        raise ValueError('invalid_database')
    if not allow_auxiliary and header[18:20] == b'\x02\x02' and not all(Path(str(path)+s).is_file() for s in ('-wal', '-shm')):
        raise OSError('wal_unavailable')
    conn = None
    try:
        conn = connect(path.as_uri()+'?mode=ro', uri=True, timeout=1)
        conn.execute('PRAGMA query_only=ON')
        if hasattr(conn, 'enable_load_extension'):
            conn.enable_load_extension(False)
        conn.set_authorizer(_authorize)
        conn.execute('BEGIN')
        # Establish snapshot now; surface WAL open errors before yielding.
        conn.execute('SELECT count(*) FROM sqlite_schema').fetchone()
        yield conn
    finally:
        if conn is not None:
            try: conn.rollback()
            finally: conn.close()
