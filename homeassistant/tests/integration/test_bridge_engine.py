"""Actual Bridge -> actual Engine; only IO/clock/ack loss are fixture boundaries.
No HA startup, sockets, live DB, scheduler execution or Ball Sender.
"""
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
import unittest
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'tests/backend'))
# Namespace package avoids executing integration __init__.py / HA startup.
for name, path in [('custom_components',ROOT/'custom_components'),('custom_components.ha2_notifications',ROOT/'custom_components/ha2_notifications')]:
    module=types.ModuleType(name);module.__path__=[str(path)];sys.modules[name]=module
from custom_components.ha2_notifications.engine import Engine, Error
from hermes_bridge.bridge import Bridge, MemoryCheckpointStore, PreviewReader
from test_engine import MemoryStore, rule

class EngineClient:
    """Adapt only WS DTO wrapping; all decisions belong to production Engine."""
    def __init__(self, engine):
        self.engine=engine;self.calls=[];self.acks=[];self.lose_next_ack=False
    async def call(self, type, **payload):
        self.calls.append((type,copy.deepcopy(payload)))
        if type=='ha2_notifications/cron_sync':
            await self.engine.cron_sync(**payload)
            return {'hermes_cron':self.engine.cron_snapshot()}
        if type!='ha2_notifications/cron_result':raise AssertionError(type)
        ack=await self.engine.cron_result(**payload);self.acks.append(copy.deepcopy(ack))
        if self.lose_next_ack:
            self.lose_next_ack=False
            raise ConnectionError('fixture lost response AFTER durable ingest')
        return ack

class ForbiddenPreview:
    def __init__(self):self.calls=[]
    def read(self,*args,**kwargs):
        self.calls.append((args,kwargs));raise AssertionError('source preview must not be opened')

class BridgeEngineGate(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.addCleanup(self.tmp.cleanup)
        self.home=Path(self.tmp.name);(self.home/'cron').mkdir()
        self.now=datetime(2026,10,24,12,tzinfo=timezone.utc)
        self.store=MemoryStore();self.e=Engine(self.store,'UTC',lambda:self.now,lambda:set());await self.e.load()
        for n in range(4):
            await self.e.command('save',rule=rule(),expected_revision=n)
        # Explicit fixture of existing production shape, NOT a live Store read.
        self.e.data['revision']=49;self.store.data=copy.deepcopy(self.e.data)
        self.original_rules=copy.deepcopy(self.e.data['rules'])
        self.job=dict(id='job1',name='Fixture task',schedule_display='cada 5 min',enabled=True,no_agent=False,deliver='local',prompt='PRIVATE NOT EXPORTED')
        self.catalog([self.job]);self.jobs_bytes=(self.home/'cron/jobs.json').read_bytes()
        with sqlite3.connect(self.home/'cron/executions.db') as db:
            db.execute('CREATE TABLE executions(id TEXT,job_id TEXT,status TEXT,source TEXT,finished_at TEXT,delivery_outcome TEXT)')
        self.client=EngineClient(self.e);self.checkpoint=MemoryCheckpointStore()
        self.b=Bridge(self.home,'fixture-host',self.client,clock=lambda:self.now,checkpoint_store=self.checkpoint)
        self.preview=ForbiddenPreview();self.b.preview_reader=self.preview
    def catalog(self,jobs):
        (self.home/'cron/jobs.json').write_text(json.dumps({'jobs':jobs}),encoding='utf-8')
    def advance(self,seconds=30):self.now+=timedelta(seconds=seconds)
    def ledger(self,eid,job='job1',finished=None,status='completed'):
        with sqlite3.connect(self.home/'cron/executions.db') as db:
            db.execute('INSERT INTO executions VALUES(?,?,?,?,?,?)',(eid,job,status,'scheduler',(finished or self.now).isoformat(),'unknown'))
    def job_dto(self,jid='job1'):
        return next(j for j in self.e.cron_snapshot()['jobs'] if j['job_id']==jid)
    async def policy(self,jid='job1',**kw):
        dto=self.e.cron_snapshot()
        args=dict(job_key=self.job_dto(jid)['job_key'],expected_revision=dto['revision'],enabled=True,content='brief',mode='cue',title='')
        args.update(kw);await self.e.cron_policy(**args)
    async def tick(self):
        report=await self.b.tick();self.assertEqual(report['ledger'],'ok');return report
    def preserved(self,expected_jobs=None):
        self.assertEqual(self.e.data['revision'],49)
        self.assertEqual(self.e.data['rules'],self.original_rules)
        self.assertEqual(len(self.e.data['rules']),4)
        self.assertEqual((self.home/'cron/jobs.json').read_bytes(),self.jobs_bytes if expected_jobs is None else expected_jobs)
    async def test_new_off_enable_cutoff_baseline_then_single_queue(self):
        self.ledger('historical',finished=self.now-timedelta(seconds=1))
        await self.tick();self.assertFalse(self.job_dto()['policy']['enabled']);self.assertEqual(self.e.data['queue'],[])
        self.advance(5);self.ledger('while-off');await self.tick()
        self.assertEqual(self.client.acks[-1]['outcome'],'disabled')
        self.advance(5);await self.policy()
        self.ledger('pre-enable',finished=self.now-timedelta(seconds=1))
        self.advance();await self.tick()
        self.assertEqual(self.client.acks[-1]['outcome'],'disabled');self.assertEqual(self.e.data['queue'],[])
        self.advance(1);self.ledger('after-enabled');self.advance(5);await self.tick()
        self.assertEqual(len(self.e.data['queue']),1)
        q=self.e.data['queue'][0];self.assertEqual(q['origin']['execution_id'],'after-enabled')
        self.assertEqual(q['rule']['mode'],'cue');self.assertIn('Contenido completo en Hermes Agent.',q['rule']['body'])
        self.assertEqual(self.preview.calls,[]);self.preserved()
    async def test_lost_ack_retries_actual_engine_dedupe_and_restart(self):
        await self.tick();await self.policy();self.advance();await self.tick()
        self.advance(1);self.ledger('lost');self.client.lose_next_ack=True;self.advance(5);await self.tick()
        self.assertEqual(self.checkpoint.load()['seen'],[]);self.assertEqual(len(self.e.data['queue']),1)
        rid=self.client.acks[-1]['request_id'];self.advance(5);await self.tick()
        self.assertEqual([a['outcome'] for a in self.client.acks],['queued','duplicate'])
        self.assertEqual(self.client.acks[-1]['request_id'],rid);self.assertEqual(self.checkpoint.load()['seen'],['lost'])
        count=len(self.client.calls);await self.e.load()
        self.b=Bridge(self.home,'fixture-host',self.client,clock=lambda:self.now,checkpoint_store=self.checkpoint)
        self.b.preview_reader=self.preview;await self.tick()
        self.assertEqual(len(self.client.calls),count+1);self.assertEqual(len(self.e.data['queue']),1);self.preserved()
    async def test_catalog_add_remove_off_preserves_rules_revision_and_job_file(self):
        await self.tick();await self.policy();self.advance(1);self.ledger('pending');self.advance(5);await self.tick()
        replacement=dict(self.job,id='job2');self.catalog([replacement]);expected=(self.home/'cron/jobs.json').read_bytes()
        self.advance();report=await self.tick()
        self.assertEqual(report['diff'],dict(added=1,removed=1,changed=0))
        self.assertFalse(self.job_dto()['present']);self.assertTrue(self.job_dto()['policy']['enabled'])
        self.assertFalse(self.job_dto('job2')['policy']['enabled']);self.assertEqual(self.e.data['queue'],[])
        self.preserved(expected)
    async def test_no_agent_brief_cannot_read_preview_and_excerpt_policy_rejected(self):
        self.catalog([dict(self.job,no_agent=True)]);self.jobs_bytes=(self.home/'cron/jobs.json').read_bytes()
        await self.tick();self.assertFalse(self.job_dto()['excerpt_available'])
        with self.assertRaisesRegex(Error,'invalid_rule'):await self.policy(content='excerpt')
        await self.policy(mode='voice');self.advance();await self.tick()
        self.advance(1);self.ledger('script');self.advance(5);await self.tick()
        self.assertEqual(self.preview.calls,[]);self.assertEqual(self.client.acks[-1]['outcome'],'queued')
        self.assertEqual(self.e.data['queue'][0]['rule']['mode'],'voice');self.preserved()
    async def test_unknown_job_and_no_result_never_queue(self):
        await self.tick();await self.policy();self.advance();await self.tick()
        self.assertEqual(self.e.data['queue'],[])
        self.advance(1);self.ledger('orphan',job='missing');self.advance(5);await self.tick()
        self.assertEqual(self.client.acks[-1]['outcome'],'missing_job');self.assertEqual(self.e.data['queue'],[])
        self.assertEqual(self.checkpoint.load()['seen'],['orphan']);self.preserved()
    async def test_real_correlated_preview_is_bounded_and_source_local_not_guessed(self):
        await self.tick();await self.policy(content='excerpt');self.advance();await self.tick()
        eid='excerpt';request='cron:job1:'+eid
        target='local-'+hashlib.sha256(json.dumps(['default','cron-owner',request],separators=(',',':')).encode()).hexdigest()
        with sqlite3.connect(self.home/'state.db') as db:
            db.execute('CREATE TABLE session_admissions(admission_id TEXT,principal_id TEXT,target_session_id TEXT,request_id TEXT,status TEXT)')
            db.execute('CREATE TABLE state_meta(key TEXT,value TEXT)')
            db.execute('INSERT INTO session_admissions VALUES(?,?,?,?,?)',('a','cron-owner',target,request,'terminal'))
            db.execute('INSERT INTO state_meta VALUES(?,?)',('gateway.admission.result.v1.a',json.dumps({'result':{'final_response':'Voz: Primera\nSegunda\n'+'x'*500+'\nCuarta','messages':['PRIVATE']}})))
        self.b.preview_reader=PreviewReader(self.home)
        self.advance(1);self.ledger(eid);self.advance(5);await self.tick()
        payload=self.client.calls[-1][1]['result'];self.assertLessEqual(len(payload['preview']),400);self.assertLessEqual(len(payload['preview'].splitlines()),3)
        body=self.e.data['queue'][0]['rule']['body'];self.assertIn('Extracto del resultado de Hermes Agent.',body)
        self.assertNotIn('Voz:',body);self.assertNotIn('PRIVATE',body);self.assertNotIn('Telegram',body);self.preserved()
    async def test_queue_full_retries_without_ack_or_ttl_extension(self):
        await self.tick();await self.policy();self.advance();await self.tick()
        for _ in range(32):await self.e.enqueue(manual=rule())
        self.advance(1);finished=self.now;self.ledger('backpressure');self.advance(5);await self.tick()
        self.assertEqual(self.checkpoint.load()['seen'],[]);self.assertEqual(self.client.acks,[])
        # Fixture frees manual work; no real sender is ever called.
        self.e.data['queue'].clear();self.advance(5);await self.tick()
        self.assertEqual(self.client.acks[-1]['outcome'],'queued');self.assertEqual(len(self.e.data['queue']),1)
        self.assertEqual(self.e.data['queue'][0]['expires'],finished.timestamp()+1800);self.preserved()
