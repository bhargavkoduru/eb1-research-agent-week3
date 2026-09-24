"""Atomic per-viewer and global request allowances for a single demo server."""
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import sqlite3
import threading
from .config import RUNTIME, hosted, setting

_actor = ContextVar('eb1_viewer', default=None)
_live_lock = threading.Lock()


class UsageLimitError(RuntimeError):
    pass


class UsageLedger:
    def __init__(self, path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as con:
            con.execute('CREATE TABLE IF NOT EXISTS daily_usage (day TEXT, actor TEXT, kind TEXT, units INTEGER, PRIMARY KEY(day,actor,kind))')

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def reserve(self, actor, kind, units, viewer_limit, global_limit):
        if not actor or units < 1:
            raise UsageLimitError('An active demo session is required for model access.')
        day = datetime.now(timezone.utc).date().isoformat()
        with self.connect() as con:
            con.execute('BEGIN IMMEDIATE')
            used = con.execute('SELECT COALESCE(SUM(units),0) FROM daily_usage WHERE day=? AND actor=? AND kind=?', (day, actor, kind)).fetchone()[0]
            all_used = con.execute('SELECT COALESCE(SUM(units),0) FROM daily_usage WHERE day=? AND kind=?', (day, kind)).fetchone()[0]
            if used + units > viewer_limit or all_used + units > global_limit:
                raise UsageLimitError('The demo usage allowance is reached for today (UTC). Please try tomorrow or contact the project owner.')
            con.execute('INSERT INTO daily_usage VALUES(?,?,?,?) ON CONFLICT(day,actor,kind) DO UPDATE SET units=units+excluded.units', (day, actor, kind, units))

def ledger():
    return UsageLedger(RUNTIME / 'usage.sqlite')


@contextmanager
def live_operation(viewer):
    """Bound concurrent spend, reserve an action, and propagate identity to graph tools."""
    if not hosted():
        yield
        return
    if str(setting('EB1_ENABLE_LIVE_CALLS', 'true')).lower() not in ('1', 'true', 'yes'):
        raise UsageLimitError('Live model calls are paused by the project owner.')
    if not _live_lock.acquire(blocking=False):
        raise UsageLimitError('The demo is finishing another request. Please try again shortly.')
    token = None
    try:
        ledger().reserve(viewer, 'actions', 1, int(setting('EB1_VIEWER_DAILY_ACTIONS', 30)), int(setting('EB1_GLOBAL_DAILY_ACTIONS', 100)))
        token = _actor.set(viewer)
        yield
    finally:
        if token is not None:
            _actor.reset(token)
        _live_lock.release()


def reserve_provider_calls(units=2):
    if not hosted():
        return
    if str(setting('EB1_ENABLE_LIVE_CALLS', 'true')).lower() not in ('1', 'true', 'yes'):
        raise UsageLimitError('Live model calls are paused by the project owner.')
    ledger().reserve(_actor.get(), 'provider_attempts', units,
                     int(setting('EB1_VIEWER_DAILY_ATTEMPTS', 120)), int(setting('EB1_GLOBAL_DAILY_ATTEMPTS', 400)))
