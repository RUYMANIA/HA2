"""Durable policy engine. All effects and clocks are injected boundaries."""
from __future__ import annotations
import asyncio
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import re
from uuid import uuid4, uuid5, NAMESPACE_URL
from zoneinfo import ZoneInfo

class Error(Exception):
    """Public allow-listed reason; never carry upstream exception text."""

def identifier(value):
    if not isinstance(value,str) or not re.fullmatch(r'[a-f0-9]{32}',value):
        raise Error('invalid_rule')
    return value

DEFAULTS={'id':'','name':'','enabled':False,'kind':'notice','title':'','body':'',
          'mode':'cue','trigger':'weekly','time':'07:30','days':[0,1,2,3,4],
          'date':'','entity_id':'','to_state':'','from_state':'',
          'expiry_minutes':30,'busy':'wait','cooldown_seconds':60}


def local_instants(day, clock, tz):
    naive=datetime.fromisoformat(day+'T'+clock)
    values=[]
    for fold in (0,1):
        aware=naive.replace(tzinfo=tz,fold=fold).astimezone(timezone.utc)
        if aware.astimezone(tz).replace(tzinfo=None)==naive and aware not in values:
            values.append(aware)
    return sorted(values)


def normalize(raw,tz,entities):
    try:
        if not isinstance(raw,dict) or set(raw)-set(DEFAULTS): raise ValueError
        item=deepcopy(DEFAULTS); item.update(raw)
        if not isinstance(item['id'],str): raise ValueError
        item['id']=identifier(item['id']) if item['id'] else uuid4().hex
        for key,limit,byte_limit,blank in (('name',60,240,False),('title',32,128,False),('body',4000,4096,item['kind']=='weather')):
            text=item[key]
            if not isinstance(text,str) or (not blank and not text.strip()) or len(text)>limit or len(text.encode('utf-8'))>byte_limit or any(ord(c)<32 and c not in '\n\t' for c in text): raise ValueError
        if type(item['enabled']) is not bool: raise ValueError
        for key,allowed in (('kind',('notice','reminder','weather','result')),('mode',('cue','voice')),('trigger',('weekly','once','state','manual')),('busy',('wait','drop'))):
            if item[key] not in allowed: raise ValueError
        for key,lo,hi in (('expiry_minutes',1,1440),('cooldown_seconds',0,86400)):
            if type(item[key]) is not int or not lo<=item[key]<=hi: raise ValueError
        if not isinstance(item['time'],str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',item['time']): raise ValueError
        if not isinstance(item['days'],list) or any(type(x) is not int or x not in range(7) for x in item['days']): raise ValueError
        item['days']=sorted(set(item['days']))
        for key in ('date','entity_id','to_state','from_state'):
            if not isinstance(item[key],str) or len(item[key])>255: raise ValueError
        if item['trigger']=='weekly' and not item['days']: raise ValueError
        if item['trigger']=='once':
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',item['date']) or len(local_instants(item['date'],item['time'],tz))!=1: raise ValueError
        if item['trigger']=='state' and (item['entity_id'] not in entities or not item['to_state'].strip() or item['to_state'] in ('unknown','unavailable')): raise ValueError
        return item
    except (ValueError,TypeError,UnicodeError):
        raise Error('invalid_rule') from None


class Engine:
    def __init__(self, store, timezone_name, clock, entities):
        self.store, self.clock, self.entities = store, clock, entities
        self.tz = ZoneInfo(timezone_name)
        self.lock = asyncio.Lock()
        self.delivery_lock = asyncio.Lock()
        self.data = {'revision':0,'paused':False,'rules':[],'queue':[], 'logs':[], 'seen':{},'cooldowns':{}}

    async def load(self):
        loaded = await self.store.async_load()
        if loaded is not None:
            self.data = loaded
            data=deepcopy(loaded)
            for item in list(data['queue']):
                if item['phase']=='submitted': self.finish(data,item,'uncertain','restart_after_claim')
                elif item['expires']<=self.clock().timestamp(): self.finish(data,item,'expired','relevance_elapsed')
                else: item['phase']='queued'
            if data!=loaded: await self.commit(data)

    async def commit(self, data):
        try:
            await self.store.async_save(deepcopy(data))
        except Exception:
            raise Error('unavailable') from None
        self.data = data

    def cron_snapshot(self):
        from . import cron_notifications as cron
        return cron.snapshot(self.data,self.clock())

    async def cron_sync(self,source_instance,profile,jobs):
        from . import cron_notifications as cron
        try:
            cron.source_args(source_instance,profile);jobs=cron.catalog(jobs)
        except (ValueError,TypeError,UnicodeError):raise Error('invalid_rule') from None
        async with self.lock:
            data=deepcopy(self.data)
            removed=cron.sync(data,source_instance,profile,jobs,self.clock())
            for q in list(data['queue']):
                if q.get('origin',{}).get('job_key') in removed:self.finish(data,q,'cancelled','configuration_changed')
            if data!=self.data:await self.commit(data)

    async def cron_policy(self,job_key,expected_revision,enabled,content,mode,title):
        from . import cron_notifications as cron
        try:
            identifier(job_key);cron.text(title,32,True)
            if len(title.encode('utf-8'))>128 or type(enabled) is not bool or content not in ('brief','excerpt') or mode not in ('cue','voice'):raise ValueError
        except (ValueError,TypeError,UnicodeError):raise Error('invalid_rule') from None
        async with self.lock:
            data=deepcopy(self.data);state=data.setdefault('hermes_cron',cron.empty())
            if type(expected_revision) is not int or expected_revision!=state['revision']:raise Error('conflict')
            job=next((j for j in state['jobs'] if j['job_key']==job_key),None)
            if job is None:raise Error('not_found')
            if content=='excerpt' and not job['excerpt_available']:raise Error('invalid_rule')
            policy=dict(enabled=enabled,content=content,mode=mode,title=title)
            if policy==job['policy']:return
            if enabled and not job['policy']['enabled']:job['enabled_at']=self.clock().isoformat()
            job['policy']=policy;state['revision']+=1
            if not enabled:
                for q in list(data['queue']):
                    if q.get('origin',{}).get('job_key')==job_key:self.finish(data,q,'cancelled','configuration_changed')
            await self.commit(data)

    async def cron_result(self,source_instance,profile,job_id,result):
        from . import cron_notifications as cron
        try:
            cron.source_args(source_instance,profile);cron.token(job_id,128)
            finished=cron.envelope(result,self.clock())
        except (ValueError,TypeError,UnicodeError,OverflowError):raise Error('invalid_rule') from None
        async with self.lock:
            now=self.clock().timestamp();data=deepcopy(self.data)
            state=data.setdefault('hermes_cron',cron.empty())
            rid=cron.key(source_instance,profile,job_id,result['execution_id'])
            receipts=state['receipts']={k:v for k,v in state['receipts'].items() if v['until']>now}
            if rid in receipts:
                previous=receipts[rid]
                return dict(accepted=True,outcome='duplicate',request_id=previous['request_id'])
            job_key=cron.key(source_instance,profile,job_id)
            job=next((j for j in state['jobs'] if j['job_key']==job_key and j['present']),None)
            if finished.timestamp()+1800<=now:outcome='expired'
            elif job is None:outcome='missing_job'
            elif not job['policy']['enabled'] or not job.get('enabled_at') or finished<datetime.fromisoformat(job['enabled_at']):outcome='disabled'
            elif result.get('silent',False):outcome='silent'
            elif data['paused']:outcome='paused'
            else:outcome='queued'
            if len(receipts)>=4096:raise Error('queue_full')
            origin=dict(source_instance=source_instance,profile=profile,job_id=job_id,job_key=job_key,execution_id=result['execution_id'])
            request_id=None
            if outcome=='queued':
                request_id=self.append(data,cron.synthetic(job,result),request_id=rid,due=finished.timestamp(),origin=origin)
            else:
                self.log(data,dict(request_id=rid,rule_id=job_key,rule={'name':job['name'][:60] if job else 'Hermes Agent','kind':'result'},origin=origin),outcome)
            receipts[rid]=dict(until=now+172800,request_id=request_id,outcome=outcome)
            await self.commit(data)
            return dict(accepted=True,outcome=outcome,request_id=request_id)

    async def command(self, action, **args):
        async with self.lock:
            if type(args.get('expected_revision')) is not int or args['expected_revision'] != self.data['revision']:
                raise Error('conflict')
            data=deepcopy(self.data)
            result=None
            if action == 'save':
                item=normalize(args['rule'],self.tz,self.entities())
                result=item['id']
                old=next((r for r in data['rules'] if r['id']==result),None)
                if args['rule'].get('id') and old is None: raise Error('not_found')
                data['rules']=[r for r in data['rules'] if r['id']!=result]+[item]
            elif action in ('delete','toggle'):
                item=next((r for r in data['rules'] if r['id']==args.get('id')),None)
                if item is None: raise Error('not_found')
                if action=='delete': data['rules'].remove(item)
                else:
                    if type(args.get('enabled')) is not bool: raise Error('invalid_rule')
                    item['enabled']=args['enabled']
            elif action == 'pause':
                if type(args.get('paused')) is not bool: raise Error('invalid_rule')
                data['paused']=args['paused']
            else:
                raise Error('invalid_rule')
            for queued in list(data['queue']):
                if data['paused'] or (action in ('save','delete','toggle') and queued['rule_id']==(result or args.get('id'))):
                    self.finish(data,queued,'cancelled','configuration_changed')
            data['revision']+=1
            await self.commit(data)
            return result

    def log(self,data,item,status,reason=''):
        data['logs'].append({'id':item['request_id'],'at':self.clock().isoformat(),
                             'rule_id':item['rule_id'],'name':item['rule']['name'],
                             'status':status,'reason':reason,
                             'source':('proactive' if item.get('source')=='proactive' else
                                       'hermes_cron' if item.get('origin',{}).get('job_key') else 'home_assistant'),
                             'kind':item['rule'].get('kind'),
                             'trigger':item['rule'].get('trigger')})
        if 'origin' in item:data['logs'][-1]['origin']=deepcopy(item['origin'])
        data['logs']=data['logs'][-200:]

    def finish(self,data,item,status,reason=''):
        self.log(data,item,status,reason)
        data['queue']=[q for q in data['queue'] if q['request_id']!=item['request_id']]

    def append(self,data,item,request_id=None,occurrence=None,due=None,origin=None):
        now=self.clock().timestamp()
        request_id=identifier(request_id) if request_id is not None else uuid4().hex
        key=occurrence or 'request:'+request_id
        request_key='request:'+request_id
        data['seen']={k:v for k,v in data['seen'].items() if v['until']>now}
        for candidate in (key,request_key):
            if candidate in data['seen']: return data['seen'][candidate]['request_id']
        if len(data['queue'])>=32 or len(data['seen'])+len({key,request_key})>4096: raise Error('queue_full')
        queued={'request_id':request_id,'rule_id':item['id'],'rule':deepcopy(item),
                'expires':(now if due is None else due)+item['expiry_minutes']*60,'phase':'queued',
                'next_attempt':now,'attempts':0}
        data['seen'][key]={'request_id':request_id,'until':now+172800}
        data['seen'][request_key]={'request_id':request_id,'until':now+172800}
        if origin is not None:queued['origin']=deepcopy(origin)
        data['queue'].append(queued)
        self.log(data,queued,'queued')
        return request_id

    async def step(self,sender):
        async with self.delivery_lock:
            async with self.lock:
                data=deepcopy(self.data); now=self.clock().timestamp()
                for item in list(data['queue']):
                    if item['phase']=='submitted': self.finish(data,item,'uncertain','uncommitted_delivery_result')
                    elif item['expires']<=now: self.finish(data,item,'expired','relevance_elapsed')
                if data!=self.data: await self.commit(data)
                if data['paused']: return
                item=next((q for q in data['queue'] if q['next_attempt']<=now),None)
                if item is None: return
                item=deepcopy(item)
            readiness=await sender.readiness()
            if readiness!='ready':
                async with self.lock:
                    data=deepcopy(self.data)
                    current=next((q for q in data['queue'] if q['request_id']==item['request_id']),None)
                    if current is None: return
                    current['attempts']+=1
                    if item['rule']['busy']=='drop' or current['attempts']>=120:
                        self.finish(data,current,'failed',readiness)
                    else:
                        current['next_attempt']=self.clock().timestamp()+min(60,5*current['attempts'])
                        if current['attempts']==1: self.log(data,current,'waiting',readiness)
                    await self.commit(data)
                return
            def valid():
                return not self.data['paused'] and self.clock().timestamp()<item['expires'] and any(q['request_id']==item['request_id'] for q in self.data['queue'])
            async def claim(generation):
                async with self.lock:
                    if not valid(): raise Error('cancelled')
                    data=deepcopy(self.data)
                    current=next(q for q in data['queue'] if q['request_id']==item['request_id'])
                    current.update(phase='submitted',baseline_generation=generation)
                    await self.commit(data)
            try:
                status,reason=await sender.deliver(item,claim,valid)
            except asyncio.CancelledError:
                raise  # A submitted claim stays durable and will recover uncertain.
            except Exception:
                current=next((q for q in self.data['queue'] if q['request_id']==item['request_id']),None)
                status,reason=('uncertain','delivery_interrupted') if current and current['phase']=='submitted' else ('failed','preparation_failed')
            async with self.lock:
                data=deepcopy(self.data)
                current=next((q for q in data['queue'] if q['request_id']==item['request_id']),None)
                if current:
                    if status=='waiting' and current['phase']=='queued':
                        current['attempts']+=1
                        if current['rule']['busy']=='drop' or current['attempts']>=120:
                            self.finish(data,current,'failed',reason)
                        else:
                            current['next_attempt']=self.clock().timestamp()+min(60,5*current['attempts'])
                            if current['attempts']==1: self.log(data,current,'waiting',reason)
                    else: self.finish(data,current,status,reason)
                    await self.commit(data)

    async def schedule(self):
        async with self.lock:
            if self.data['paused']: return
            data=deepcopy(self.data)
            now=self.clock(); local=now.astimezone(self.tz)
            for item in data['rules']:
                if not item['enabled'] or item['trigger'] not in ('weekly','once'): continue
                candidates=[]
                if item['trigger']=='once':
                    candidates=local_instants(item['date'],item['time'],self.tz)
                else:
                    for back in (1,0):
                        day=(local-timedelta(days=back)).date()
                        if day.weekday() in item['days']:
                            candidates.extend(local_instants(day.isoformat(),item['time'],self.tz)[:1])
                candidates=[due for due in candidates if 0<=(now-due).total_seconds()<item['expiry_minutes']*60]
                if not candidates: continue
                due=max(candidates)
                key=item['id']+':'+due.astimezone(self.tz).strftime('%Y-%m-%dT%H:%M')
                try: self.append(data,item,occurrence=key,due=due.timestamp())
                except Error as exc:
                    if str(exc)!='queue_full': raise
                    request_id=uuid5(NAMESPACE_URL,'ha2:queue_full:'+key).hex
                    if not any(log['id']==request_id for log in data['logs']):
                        self.log(data,{'request_id':request_id,'rule_id':item['id'],'rule':item},'waiting','queue_full')
            if data!=self.data: await self.commit(data)

    async def state_changed(self,entity_id,old,new):
        if old in (None,'unknown','unavailable') or new in (None,'unknown','unavailable') or old==new: return
        async with self.lock:
            if self.data['paused']: return
            data=deepcopy(self.data); now=self.clock().timestamp()
            for item in data['rules']:
                if not item['enabled'] or item['trigger']!='state' or item['entity_id']!=entity_id or item['to_state']!=new or (item['from_state'] and item['from_state']!=old): continue
                if now-data['cooldowns'].get(item['id'],float('-inf'))<item['cooldown_seconds']: continue
                try: self.append(data,item)
                except Error as exc:
                    if str(exc)!='queue_full': raise
                    self.log(data,{'request_id':uuid4().hex,'rule_id':item['id'],'rule':item},'failed','queue_full')
                    continue
                data['cooldowns'][item['id']]=now
            if data!=self.data: await self.commit(data)

    async def enqueue(self,rule_id=None,*,request_id=None,manual=None):
        async with self.lock:
            if self.data['paused']: raise Error('paused')
            if rule_id is not None:
                item=next((r for r in self.data['rules'] if r['id']==rule_id),None)
                if item is None: raise Error('not_found')
            else:
                item=normalize(dict(manual or {},name='Resultado manual',trigger='manual'),self.tz,self.entities())
            data=deepcopy(self.data)
            result=self.append(data,item,request_id=request_id)
            await self.commit(data)
            return result
