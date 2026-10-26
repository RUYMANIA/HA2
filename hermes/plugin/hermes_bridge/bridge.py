"""Deterministic, read-only cron observer; transport and ownership stay with host."""
import asyncio
import copy
import json
import re

_ID = re.compile(r'^[^\s/\\\x00-\x1f\x7f]+$')

def identifier(value, limit=128):
    if not isinstance(value, str) or not value or len(value) > limit or not _ID.fullmatch(value) or any(unicodedata.category(c).startswith('C') for c in value):
        raise ValueError('invalid_identifier')
    return value

def literal(value, limit):
    if not isinstance(value, str) or len(value) > limit or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError('invalid_metadata')
    return value

class CatalogReader:
    def __init__(self, home): self.path = Path(home) / 'cron/jobs.json'
    def read(self):
        with self.path.open(encoding='utf-8-sig') as stream:
            raw = stream.read(2_000_001)
        if len(raw) > 2_000_000: raise ValueError('catalog_too_large')
        data = json.loads(raw)
        rows = data.get('jobs') if isinstance(data, dict) else data
        if not isinstance(rows, list) or len(rows) > 512: raise ValueError('invalid_catalog')
        result = []; ids = set()
        for row in rows:
            if not isinstance(row, dict): raise ValueError('invalid_catalog')
            jid = identifier(row.get('id'))
            if jid in ids: raise ValueError('duplicate_job')
            ids.add(jid)
            schedule = row.get('schedule_display')
            if schedule is None:
                schedule = row.get('schedule', '')
                if isinstance(schedule, dict):
                    schedule = next((schedule[k] for k in ('display', 'value', 'expr', 'run_at') if isinstance(schedule.get(k), str)), '')
            no_agent = row.get('no_agent', False); enabled = row.get('enabled', True)
            if type(no_agent) is not bool or type(enabled) is not bool: raise ValueError('invalid_boolean')
            deliver = row.get('deliver', 'local')
            platform = deliver.split(':', 1)[0] if isinstance(deliver, str) else 'other'
            if platform not in {'local','telegram','discord','slack','email'}: platform = 'other'
            result.append(dict(job_id=jid, name=literal(row.get('name', ''),160), schedule=literal(schedule,160), enabled=enabled, no_agent=no_agent, delivery=platform, excerpt_available=not no_agent))
        return result
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
import sqlite3


def aware(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None: raise ValueError('naive_timestamp')
    return parsed

@contextmanager
def readonly_snapshot(path, connect=sqlite3.connect, *, allow_auxiliary=False):
    if allow_auxiliary:
        from .sqlite_reader import protected_snapshot
        with protected_snapshot(path, connect, allow_auxiliary=True) as conn:
            yield conn
        return
    path = Path(path).resolve()
    # A ro WAL open can create sidecars: refuse before SQLite if either is absent.
    with path.open('rb') as stream: header = stream.read(20)
    if len(header) < 20 or header[:16] != b'SQLite format 3\x00': raise ValueError('invalid_database')
    if header[18:20] == b'\x02\x02' and not all(Path(str(path)+suffix).is_file() for suffix in ('-wal','-shm')):
        raise OSError('wal_unavailable')
    conn = connect(path.as_uri()+'?mode=ro', uri=True, timeout=.1)
    try:
        conn.execute('PRAGMA query_only=ON')
        conn.execute('BEGIN')
        yield conn
    finally:
        conn.rollback(); conn.close()

class LedgerReader:
    def __init__(self, home, connect=sqlite3.connect, *, allow_auxiliary=False): self.path = Path(home)/'cron/executions.db'; self.connect = connect; self.allow_auxiliary = allow_auxiliary
    def read(self):
        with readonly_snapshot(self.path, self.connect, allow_auxiliary=self.allow_auxiliary) as conn:
            rows = conn.execute("SELECT id, job_id, status, source, finished_at, delivery_outcome FROM executions WHERE status IN ('completed','failed','unknown') ORDER BY julianday(finished_at) DESC, finished_at DESC, id DESC LIMIT 1000").fetchall()
        result = []
        for row in rows:
            try:
                identifier(row[0]); identifier(row[1]); aware(row[4])
                result.append(dict(zip(('id','job_id','status','source','finished_at','delivery_outcome'),row)))
            except (ValueError,TypeError): continue
        return sorted(result, key=lambda r: (aware(r['finished_at']), r['id']))

import hashlib
import unicodedata

_SECRET = re.compile(r'(?i)\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|token|password|passwd|secret|authorization)\s*[:=]\s*(?:bearer\s+)?[^\n]+|\bBearer\s+[A-Za-z0-9._~+/=-]+|\b(?:sk-|ghp_|github_pat_)[A-Za-z0-9_-]+|\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+')

def sanitize_preview(text):
    text = ''.join(c for c in text if c in '\n\t' or not unicodedata.category(c).startswith('C'))
    text = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'(?i)\b(?:https?://|www\.)\S+', '[URL]', text)
    text = _SECRET.sub('[REDACTED]', text)
    text = re.sub(r'[*_`#<>~|]', '', text)
    lines = [re.sub(r'\s+', ' ', line).strip() for line in text.splitlines()]
    return '\n'.join(line for line in lines if line)[:400] if len([line for line in lines if line]) <= 3 else '\n'.join([line for line in lines if line][:3])[:400]

class PreviewReader:
    """Only final_response crosses SQLite boundary; never decodes the full stored row."""
    def __init__(self, home, connect=sqlite3.connect, *, allow_auxiliary=False): self.path = Path(home)/'state.db'; self.connect = connect; self.allow_auxiliary = allow_auxiliary
    def read(self, job_id, execution_id, *, enabled=False):
        if enabled is not True: return {}
        identifier(job_id); identifier(execution_id)
        request = f'cron:{job_id}:{execution_id}'
        identity = json.dumps(['default','cron-owner',request], separators=(',',':'))
        target = 'local-' + hashlib.sha256(identity.encode()).hexdigest()
        try:
            with readonly_snapshot(self.path, self.connect, allow_auxiliary=self.allow_auxiliary) as conn:
                rows = conn.execute("SELECT admission_id FROM session_admissions WHERE principal_id=? AND target_session_id=? AND request_id=? AND status='terminal' LIMIT 2", ('cron-owner',target,request)).fetchall()
                if len(rows) != 1: return {}
                # encode_result/load_result never change final_response. Project it without
                # reconstructing assistant history. Only plain JSON and exact known v1 tags.
                row = conn.execute("""SELECT CASE WHEN json_valid(value) THEN CASE
                    WHEN json_type(value,'$.result.final_response')='text'
                    AND length(json_extract(value,'$.result.final_response')) <= 16384
                    AND (json_type(value,'$._stored') IS NULL OR
                        (json_type(value,'$._stored')='object'
                         AND json_type(value,'$._stored.v')='integer'
                         AND json_extract(value,'$._stored.v')=1
                         AND (SELECT count(*) FROM json_each(value,'$._stored'))=2
                         AND ((json_type(value,'$._stored.reply_ref')='integer' AND json_extract(value,'$._stored.reply_ref')>=0) OR json_type(value,'$._stored.raw') IS NOT NULL)))
                    THEN substr(json_extract(value,'$.result.final_response'),1,16384) END END
                    FROM state_meta WHERE key=? LIMIT 2""", ('gateway.admission.result.v1.'+rows[0][0],)).fetchall()
                if len(row) != 1 or not isinstance(row[0][0],str): return {}
                text = row[0][0]
            lines = [line.strip().upper() for line in text.strip().splitlines() if line.strip()]
            if lines and (lines[0] in {'[SILENT]','SILENT','NO_REPLY','NO REPLY'} or lines[-1] in {'[SILENT]','SILENT','NO_REPLY','NO REPLY'}): return {'silent': True}
            preview = sanitize_preview(text)
            return {'preview': preview} if preview else {}
        except (OSError,ValueError,TypeError,sqlite3.Error): return {}

class MemoryCheckpointStore:
    def __init__(self): self.value = None
    def load(self): return copy.deepcopy(self.value)
    def save(self, value): self.value = copy.deepcopy(value)

import os
import stat
import tempfile
import uuid
import inspect

class JSONCheckpointStore:
    """Single-owner store. Corrupt/foreign state fails closed, never resets baseline."""
    def __init__(self, path): self.path = Path(path)
    def load(self):
        try:
            fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW)
        except FileNotFoundError: return None
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_size > 1_000_000:
                raise ValueError('unsafe_checkpoint')
            with os.fdopen(fd, encoding='utf-8') as stream:
                fd = None
                return json.load(stream)
        except (OSError,json.JSONDecodeError) as exc: raise ValueError('invalid_checkpoint') from exc
        finally:
            if fd is not None: os.close(fd)
    def save(self, value):
        if self.path.is_symlink(): raise ValueError('unsafe_checkpoint')
        # Host creates private parent directory; never mkdir/chmod a live profile here.
        fd, name = tempfile.mkstemp(prefix='.'+self.path.name+'.', dir=self.path.parent)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as stream:
                json.dump(value,stream,separators=(',',':'),allow_nan=False)
                stream.flush(); os.fsync(stream.fileno())
            os.replace(name,self.path)
            directory = os.open(self.path.parent,os.O_RDONLY)
            try: os.fsync(directory)
            finally: os.close(directory)
        finally:
            if os.path.exists(name): os.unlink(name)

class Bridge:
    def __init__(self, home, source_instance, client, *, clock=None, checkpoint_store=None):
        self.home = Path(home)
        self.source_instance = identifier(source_instance, 64)
        self.catalog_reader = CatalogReader(home)
        self.ledger_reader = LedgerReader(home)
        self.preview_reader = PreviewReader(home)
        self.next_ledger = None; self.last_report = {}
        self.jobs = {}; self.policies = {}; self.next_sync = None
        self.client = client
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.checkpoint_store = checkpoint_store or MemoryCheckpointStore()
        self.sleep = asyncio.sleep
        self.state = self.checkpoint_store.load()
        if self.state is None:
            stamp = self.clock().isoformat(); aware(stamp)
            self.state = {'version':1, 'source_instance':self.source_instance, 'profile':'default', 'nonce':uuid.uuid4().hex, 'epoch':stamp, 'seen':[], 'watermark':stamp}
            self.checkpoint_store.save(self.state)
        else:
            if not isinstance(self.state, dict) or self.state.get('version') != 1 or self.state.get('source_instance') != self.source_instance or self.state.get('profile') != 'default': raise ValueError('checkpoint_identity')
            aware(self.state['epoch']); aware(self.state['watermark'])
            if not re.fullmatch('[0-9a-f]{32}',self.state.get('nonce','')) or not isinstance(self.state.get('seen'),list) or len(self.state['seen']) > 4096: raise ValueError('checkpoint_shape')
            for item in self.state['seen']: identifier(item)
    async def _call(self, type, **payload):
        result = self.client.call(type, **payload)
        return await result if inspect.isawaitable(result) else result
    async def run(self):
        delay = 1
        while True:
            try:
                report = await self.tick()
                failed = any(v == 'unavailable' for v in report.values())
            except asyncio.CancelledError: raise
            except Exception:
                self.last_report = {'observer':'unavailable'}; failed = True
            await self.sleep(delay if failed else 1)
            delay = min(delay * 2,30) if failed else 1
    async def tick(self):
        now = self.clock().timestamp()
        report = {'catalog': 'cached', 'ledger': self.last_report.get('ledger', 'unavailable')}
        if self.next_sync is None or now >= self.next_sync:
            self.next_sync = now + 30
            try:
                jobs = await asyncio.to_thread(self.catalog_reader.read)
                snapshot = await self._call('ha2_notifications/cron_sync', source_instance=self.source_instance, profile='default', jobs=jobs)
                new_jobs = {j['job_id']: j for j in jobs}
                report['diff'] = {'added':len(new_jobs.keys()-self.jobs.keys()), 'removed':len(self.jobs.keys()-new_jobs.keys()), 'changed':sum(new_jobs[k] != self.jobs[k] for k in new_jobs.keys() & self.jobs.keys())}
                self.jobs = new_jobs
                dto = snapshot.get('hermes_cron', {})
                self.policies = {j['job_id']: j.get('policy', {}) for j in dto.get('jobs', []) if j.get('source_instance') == self.source_instance and j.get('profile') == 'default'}
                report['catalog'] = 'ok'
                report['count'] = len(jobs)
            except Exception:
                report['catalog'] = 'unavailable'
                self.policies = {}
        if self.next_ledger is None or now >= self.next_ledger:
            self.next_ledger = now + 5
            try:
                rows = await asyncio.to_thread(self.ledger_reader.read)
                report['ledger'] = 'ok'
            except Exception:
                rows = []; report['ledger'] = 'unavailable'
            for row in rows:
                finished = aware(row['finished_at'])
                age = now - finished.timestamp()
                if finished <= aware(self.state['epoch']) or row['id'] in self.state['seen'] or row['source'] in {'direct','manual'} or age > 1800 or age < -300:
                    continue
                envelope = dict(execution_id=row['id'], finished_at=row['finished_at'], status=row['status'], delivery_outcome=row['delivery_outcome'] if row['delivery_outcome'] in {'queued','delivered','suppressed','failed','not_configured','unknown'} else 'unknown')
                policy = self.policies.get(row['job_id'], {})
                job = self.jobs.get(row['job_id'], {})
                if policy.get('enabled') is True and policy.get('content') == 'excerpt' and job.get('no_agent') is False:
                    envelope.update(await asyncio.to_thread(self.preview_reader.read, row['job_id'], row['id'], enabled=True))
                try:
                    ack = await self._call('ha2_notifications/cron_result', source_instance=self.source_instance, profile='default', job_id=row['job_id'], result=envelope)
                    if not isinstance(ack, dict) or ack.get('accepted') is not True or ack.get('outcome') not in {'queued','duplicate','disabled','expired','silent','paused','missing_job'}:
                        continue
                    candidate = copy.deepcopy(self.state)
                    candidate['seen'] = (candidate['seen'] + [row['id']])[-4096:]
                    candidate['watermark'] = max(aware(candidate['watermark']), finished).isoformat()
                    await asyncio.to_thread(self.checkpoint_store.save, candidate)
                    self.state = candidate
                except Exception:
                    report['transport'] = 'unavailable'
        self.last_report = report
        return report
