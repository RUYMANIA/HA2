import asyncio
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone, timedelta

STAGE = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('bridge_core', STAGE / 'hermes_bridge/bridge.py')
core = None
if SPEC and Path(SPEC.origin).exists():
    core = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(core)

class Clock:
    def __init__(self): self.value = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)
    def __call__(self): return self.value
    def advance(self, seconds): self.value += timedelta(seconds=seconds)

class Client:
    def __init__(self): self.calls = []; self.outcome = 'disabled'; self.offline = False; self.policy = {}
    async def call(self, type, **payload):
        if self.offline: raise ConnectionError('private upstream body')
        self.calls.append((type, payload))
        if type.endswith('cron_sync'):
            return {'hermes_cron': {'revision': 1, 'sources': [], 'jobs': [dict(j, source_instance='host', profile='default', policy=self.policy) for j in payload['jobs']]}}
        if self.outcome == 'queue_full': raise RuntimeError('queue_full')
        return {'accepted': getattr(self, 'accepted', True), 'outcome': self.outcome, 'request_id': None}

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name); (self.home/'cron').mkdir()
        self.clock = Clock(); self.client = Client()
        self.job = {'id': 'job1', 'name': 'Literal name', 'schedule_display': 'cada 5 min', 'enabled': True, 'no_agent': False, 'deliver': 'telegram:PRIVATE'}
        self.catalog([self.job])
    def catalog(self, jobs): (self.home/'cron/jobs.json').write_text(json.dumps({'jobs': jobs}))
    def bridge(self, **kw):
        self.assertIsNotNone(core, 'deterministic Bridge core must exist')
        return core.Bridge(self.home, 'host', self.client, clock=self.clock, checkpoint_store=core.MemoryCheckpointStore(), **kw)
    def tick(self, b): return asyncio.run(b.tick())
    def ledger(self, rows):
        path = self.home/'cron/executions.db'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS executions(id TEXT, job_id TEXT, status TEXT, source TEXT, finished_at TEXT, delivery_outcome TEXT)')
            db.executemany('INSERT INTO executions VALUES(?,?,?,?,?,?)', rows)
    def row(self, id='exec1', **kw):
        d = dict(id=id, job_id='job1', status='completed', source='scheduler', finished_at=self.clock().isoformat(), delivery_outcome='delivered'); d.update(kw)
        return tuple(d[k] for k in ('id','job_id','status','source','finished_at','delivery_outcome'))
    def results(self): return [p for t,p in self.client.calls if t.endswith('cron_result')]
    def test_catalog_allowlist_reopens_and_invalid_is_not_deletion(self):
        b = self.bridge(); self.tick(b)
        sync = [p for t,p in self.client.calls if t.endswith('cron_sync')]
        self.assertEqual(len(sync), 1)
        self.assertEqual(sync[0]['jobs'][0], {'job_id': 'job1', 'name': 'Literal name', 'schedule': 'cada 5 min', 'enabled': True, 'no_agent': False, 'delivery': 'telegram', 'excerpt_available': True})
        (self.home/'cron/jobs.json').write_text('{broken')
        self.clock.advance(30); report = self.tick(b)
        self.assertEqual(report['catalog'], 'unavailable')
        self.assertEqual(len(self.client.calls), 1)
        replacement = self.home/'cron/replacement.json'; replacement.write_text('{"jobs":[]}'); replacement.replace(self.home/'cron/jobs.json')
        self.clock.advance(30); self.tick(b)
        self.assertEqual(self.client.calls[-1][1]['jobs'], [])
    def test_metadata_all_modes_ties_restart_retry_and_direct_excluded(self):
        b = self.bridge(); self.tick(b); self.clock.advance(1)
        self.ledger([self.row('exec1'), self.row('exec2', status='failed'), self.row('manual', source='direct'), self.row('naive', finished_at='2026-10-24T12:00:01')])
        self.client.outcome = 'queue_full'; self.clock.advance(5); self.tick(b)
        self.assertEqual([p.get('job_id') for p in self.results()], ['job1','job1'])
        self.assertEqual([p['result']['execution_id'] for p in self.results()], ['exec1','exec2'])
        self.assertEqual(b.checkpoint_store.load()['seen'], [])
        self.client.outcome = 'disabled'; self.clock.advance(5); self.tick(b)
        self.assertEqual([p['result']['execution_id'] for p in self.results()], ['exec1','exec2','exec1','exec2'])
        self.assertNotIn('preview', self.results()[-1]['result'])
        self.assertEqual(set(b.checkpoint_store.load()['seen']), {'exec1','exec2'})
        restarted = core.Bridge(self.home,'host',self.client,clock=self.clock,checkpoint_store=b.checkpoint_store)
        self.tick(restarted); self.assertEqual(len(self.results()),4)
    def test_false_ack_does_not_consume_execution(self):
        b=self.bridge();self.tick(b);self.clock.advance(1);self.ledger([self.row()]);self.client.accepted=False
        self.clock.advance(5);self.tick(b)
        self.assertEqual(b.checkpoint_store.load()['seen'],[])
        self.client.accepted=True;self.clock.advance(5);self.tick(b)
        self.assertEqual(b.checkpoint_store.load()['seen'],['exec1'])
        self.assertEqual([p['job_id'] for p in self.results()],['job1','job1'])

    def test_ledger_missing_and_missing_wal_fail_closed(self):
        b = self.bridge(); original = b.checkpoint_store.load(); self.tick(b)
        self.assertEqual(b.last_report['ledger'], 'unavailable')
        self.assertEqual(b.checkpoint_store.load(), original)
        path = self.home/'cron/executions.db'; path.write_bytes(b'not a database')
        self.clock.advance(5); self.tick(b)
        self.assertEqual(b.last_report['ledger'], 'unavailable')
        self.assertEqual(b.checkpoint_store.load(), original)
    def state_fixture(self, text, *, ambiguous=False, codec=None):
        import hashlib
        request = 'cron:job1:exec1'
        target = 'local-' + hashlib.sha256(json.dumps(['default','cron-owner',request], separators=(',',':')).encode()).hexdigest()
        value = {'result': {'final_response': text, 'cron_result': ['PRIVATE'], 'messages': ['PRIVATE']}}
        if codec is not None: value['_stored'] = codec
        with sqlite3.connect(self.home/'state.db') as db:
            db.execute('CREATE TABLE session_admissions(admission_id TEXT, principal_id TEXT, target_session_id TEXT, request_id TEXT, status TEXT, payload_json TEXT)')
            db.execute('CREATE TABLE state_meta(key TEXT, value TEXT)')
            db.execute('INSERT INTO session_admissions VALUES(?,?,?,?,?,?)',('a','cron-owner',target,request,'terminal','PRIVATE'))
            if ambiguous: db.execute('INSERT INTO session_admissions VALUES(?,?,?,?,?,?)',('b','cron-owner',target,request,'terminal','PRIVATE'))
            db.execute('INSERT INTO state_meta VALUES(?,?)',('gateway.admission.result.v1.a',json.dumps(value)))
    def test_opt_in_exact_projection_privacy_sanitization_and_no_agent(self):
        self.state_fixture('**Hola** https://secret.test/a?token=ABC\napi_key=SUPERSECRET\nListo\nCuarta')
        b = self.bridge(); self.tick(b); self.clock.advance(1); self.ledger([self.row()])
        self.client.policy = {'enabled': True, 'content': 'excerpt', 'mode': 'voice'}
        queries = []
        def connect(*args, **kwargs):
            db = sqlite3.connect(*args,**kwargs); db.set_trace_callback(queries.append); return db
        b.preview_reader = core.PreviewReader(self.home, connect=connect)
        self.clock.advance(30); self.tick(b)
        preview = self.results()[-1]['result']['preview']
        self.assertNotIn('SUPERSECRET',preview); self.assertNotIn('secret.test',preview); self.assertNotIn('**',preview)
        self.assertLessEqual(len(preview),400); self.assertLessEqual(len(preview.splitlines()),3)
        sql = ' '.join(queries).lower()
        for forbidden in ('select *','cron_result','payload_json','messages'): self.assertNotIn(forbidden,sql)
        self.assertIn('final_response',sql)
        self.assertNotIn('SUPERSECRET',json.dumps(b.checkpoint_store.load()))
        self.job['no_agent'] = True; self.catalog([self.job]); self.clock.advance(1); self.ledger([self.row('exec2')])
        queries.clear(); self.clock.advance(30); self.tick(b)
        self.assertNotIn('preview',self.results()[-1]['result']); self.assertEqual(queries,[])
    def test_silent_unknown_codec_and_ambiguous_are_safe(self):
        self.assertTrue(hasattr(core,'PreviewReader'), 'opt-in projection reader required')
        self.state_fixture('[SILENT]')
        reader = core.PreviewReader(self.home)
        self.assertEqual(reader.read('job1','exec1',enabled=False),{})
        self.assertEqual(reader.read('job1','exec1',enabled=True),{'silent': True})
        with sqlite3.connect(self.home/'state.db') as db:
            db.execute('UPDATE state_meta SET value=?',(json.dumps({'_stored':{'v':99}, 'result':{'final_response':'PRIVATE'}}),))
        self.assertEqual(reader.read('job1','exec1',enabled=True),{})
        with sqlite3.connect(self.home/'state.db') as db:
            db.execute("INSERT INTO session_admissions SELECT 'b',principal_id,target_session_id,request_id,status,payload_json FROM session_admissions LIMIT 1")
        self.assertEqual(reader.read('job1','exec1',enabled=True),{})
    def test_json_checkpoint_guards_mode_durability_and_corruption(self):
        self.assertTrue(hasattr(core,'JSONCheckpointStore'), 'atomic durable checkpoint required')
        store = core.JSONCheckpointStore(self.home/'checkpoint.json')
        b = core.Bridge(self.home,'host',self.client,clock=self.clock,checkpoint_store=store)
        saved = store.load(); self.assertEqual(saved['source_instance'],'host'); self.assertEqual(len(saved['nonce']),32)
        self.assertEqual((self.home/'checkpoint.json').stat().st_mode & 0o777,0o600)
        self.clock.advance(30)
        self.assertEqual(core.Bridge(self.home,'host',self.client,clock=self.clock,checkpoint_store=store).state,saved)
        with self.assertRaises(ValueError): core.Bridge(self.home,'another',self.client,clock=self.clock,checkpoint_store=store)
        (self.home/'checkpoint.json').write_text('broken')
        with self.assertRaises(ValueError): core.Bridge(self.home,'host',self.client,clock=self.clock,checkpoint_store=store)
    def test_run_cancellation_backoff_and_sync_client_boundary(self):
        self.assertTrue(hasattr(core.Bridge,'run'), 'cancellable observer required')
        b = self.bridge(); delays=[]
        async def sleep(delay):
            delays.append(delay)
            if len(delays)==3: raise asyncio.CancelledError()
            self.clock.advance(delay)
        b.sleep = sleep
        with self.assertRaises(asyncio.CancelledError): asyncio.run(b.run())
        self.assertEqual(delays,[1,2,4])
        class SyncClient:
            def call(self,type,**payload): return {'hermes_cron': {'jobs':[]}}
        b.client = SyncClient(); self.clock.advance(30)
        self.assertEqual(self.tick(b)['catalog'],'ok')
    def test_queue_full_ttl_not_refreshed_and_wal_preflight(self):
        b=self.bridge(); self.tick(b); self.clock.advance(1); self.ledger([self.row()]); self.client.outcome='queue_full'
        self.clock.advance(5); self.tick(b); self.assertEqual(len(self.results()),1)
        self.clock.advance(1800); self.tick(b); self.assertEqual(len(self.results()),1)
        path=self.home/'cron/executions.db'
        with path.open('r+b') as stream: stream.seek(18); stream.write(bytes([2,2]))
        connected=[]
        def no_connect(*a,**k): connected.append(True); raise AssertionError('must not open WAL without sidecars')
        reader=core.LedgerReader(self.home,connect=no_connect)
        with self.assertRaises(OSError): reader.read()
        self.assertEqual(connected,[])
        self.assertFalse(Path(str(path)+'-wal').exists()); self.assertFalse(Path(str(path)+'-shm').exists())
    def test_preview_missing_empty_nonjson_codec_and_long_silent_fallback(self):
        self.state_fixture('safe')
        reader=core.PreviewReader(self.home)
        values=['not JSON',json.dumps({'result':{'final_response':''}}),json.dumps({'result':{'final_response':'x'*17000+'\n[SILENT]'}}),json.dumps({'_stored':{'v':1,'reply_ref':-1},'result':{'final_response':'unsafe'}})]
        for value in values:
            with self.subTest(value_length=len(value)):
                with sqlite3.connect(self.home/'state.db') as db: db.execute('UPDATE state_meta SET value=?',(value,))
                self.assertEqual(reader.read('job1','exec1',enabled=True),{})
    def test_catalog_count_diff_and_identifiers_not_repaired(self):
        b=self.bridge(); self.tick(b)
        self.assertEqual(b.last_report['diff'], {'added':1,'changed':0,'removed':0})
        self.job['id']=' job1'; self.catalog([self.job]); self.clock.advance(30); self.tick(b)
        self.assertEqual(b.last_report['catalog'],'unavailable')
        self.assertEqual(len([1 for t,p in self.client.calls if t.endswith('cron_sync')]),1)
    def test_statuses_terminal_acks_and_ha_offline_checkpoint(self):
        b=self.bridge(); self.tick(b); self.clock.advance(1)
        self.ledger([self.row('e1',status='completed'),self.row('e2',status='failed'),self.row('e3',status='unknown',delivery_outcome='SECRET')])
        self.client.offline=True; self.clock.advance(5); self.tick(b)
        self.assertEqual(b.state['seen'],[])
        self.client.offline=False; self.clock.advance(5); self.tick(b)
        self.assertEqual({p['result']['status'] for p in self.results()},{'completed','failed','unknown'})
        self.assertEqual(self.results()[-1]['result']['delivery_outcome'],'unknown')
        self.assertEqual(set(b.state['seen']),{'e1','e2','e3'})
    def test_bounded_thousand_equal_timestamp_scan(self):
        b=self.bridge(); self.tick(b); self.clock.advance(1)
        self.ledger([self.row(f'e{i:04d}') for i in range(1000)])
        self.clock.advance(5); self.tick(b)
        self.assertEqual(len(self.results()),1000)
        self.assertEqual(len(set(b.state['seen'])),1000)
        self.clock.advance(5); self.tick(b); self.assertEqual(len(self.results()),1000)
    def test_unicode_controls_and_quoted_secrets_are_removed(self):
        self.assertNotIn('SECOND',core.sanitize_preview('api_key="FIRST SECOND"'))
        with self.assertRaises(ValueError): core.identifier('job\u202e1')
    def test_initial_baseline_is_durable_before_offline(self):
        self.ledger([self.row()]); self.client.offline = True
        b = self.bridge(); self.tick(b)
        self.assertEqual(b.checkpoint_store.load()['epoch'], self.clock().isoformat())
        self.client.offline = False; self.clock.advance(31); self.tick(b)
        self.assertEqual(self.results(), [])

if __name__ == '__main__': unittest.main()
