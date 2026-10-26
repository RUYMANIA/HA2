"""Cron metadata policy helpers. Effects remain in the one Engine/Store."""
from copy import deepcopy
from datetime import datetime
import re
import unicodedata
from uuid import uuid5, NAMESPACE_URL

DELIVERY={'local','telegram','discord','slack','email','other'}
OUTCOMES={'queued','delivered','suppressed','failed','not_configured','unknown'}

def empty():return {'revision':0,'sources':[],'jobs':[],'receipts':{}}

def text(value,limit,blank=False):
    if not isinstance(value,str) or len(value)>limit or (not blank and not value.strip()) or any(unicodedata.category(c).startswith('C') for c in value):raise ValueError
    value.encode('utf-8')
    return value

def token(value,limit):
    text(value,limit)
    if any(c.isspace() or c in '/\\' for c in value):raise ValueError
    return value

def key(source,profile,job,execution=None):
    parts=[source,profile,job]+([] if execution is None else [execution])
    return uuid5(NAMESPACE_URL,'/'.join(parts)).hex

def source_args(source,profile):
    token(source,64);token(profile,64)

def catalog(jobs):
    if not isinstance(jobs,list) or len(jobs)>512:raise ValueError
    result=[];seen=set()
    for j in jobs:
        if not isinstance(j,dict) or set(j)!=set(('job_id','name','schedule','enabled','no_agent','delivery','excerpt_available')):raise ValueError
        token(j['job_id'],128);text(j['name'],160,True);text(j['schedule'],160,True)
        if j['job_id'] in seen or j['delivery'] not in DELIVERY:raise ValueError
        if any(type(j[k]) is not bool for k in ('enabled','no_agent','excerpt_available')):raise ValueError
        seen.add(j['job_id']);result.append(deepcopy(j))
    return result

def sync(data,source,profile,jobs,now):
    state=data.setdefault('hermes_cron',empty());before=deepcopy(state['jobs'])
    by_id={j['job_id']:j for j in state['jobs'] if (j['source_instance'],j['profile'])==(source,profile)}
    for j in by_id.values():j['present']=False
    for incoming in jobs:
        j=by_id.get(incoming['job_id'])
        if j is None:
            j=dict(job_key=key(source,profile,incoming['job_id']),source_instance=source,profile=profile,policy=dict(enabled=False,content='brief',mode='cue',title=''),enabled_at=None)
            state['jobs'].append(j)
        j.update(incoming,present=True)
    sources=state['sources'];s=next((s for s in sources if (s['source_instance'],s['profile'])==(source,profile)),None)
    if s is None:
        s=dict(source_instance=source,profile=profile,last_seen=None);sources.append(s)
    s['last_seen']=now.isoformat()
    if state['jobs']!=before:state['revision']+=1
    return {j['job_key'] for j in state['jobs'] if not j['present']}

def envelope(result,now):
    required={'execution_id','finished_at','status','delivery_outcome'}
    if not isinstance(result,dict) or not required<=set(result) or set(result)-required-{'preview','silent'}:raise ValueError
    token(result['execution_id'],128)
    if result['status'] not in ('completed','failed','unknown') or result['delivery_outcome'] not in OUTCOMES:raise ValueError
    if 'silent' in result and type(result['silent']) is not bool:raise ValueError
    if 'preview' in result and (not isinstance(result['preview'],str) or len(result['preview'])>16384):raise ValueError
    text(result['finished_at'],64)
    finished=datetime.fromisoformat(result['finished_at'])
    if finished.tzinfo is None or (finished-now).total_seconds()>300:raise ValueError
    return finished

def excerpt(value):
    value=re.sub(r'^\s*(?:Voz|Voice)\s*:\s*','',value,flags=re.I)
    lines=[]
    for line in value.splitlines():
        if re.search(r'https?://|www\.|(?:token|password|passwd|secret|authorization|api[_-]?key)\s*[:=]|bearer\s|\b(?:sk-|ghp_|github_pat_)[A-Za-z0-9_-]+|\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',line,re.I):continue
        line=''.join(c for c in line if not unicodedata.category(c).startswith('C')).strip()
        if line:lines.append(line)
    return '\n'.join(lines[:3])[:400]

def synthetic(job,result):
    from .engine import DEFAULTS
    policy=job['policy'];status={'completed':'completada','failed':'fallida','unknown':'con estado desconocido'}[result['status']]
    body='Tarea '+status+'. Entrega original: '+{'queued':'en cola','delivered':'entregada','suppressed':'suprimida','failed':'fallida','not_configured':'no configurada','unknown':'desconocida'}[result['delivery_outcome']]+'.\n\nContenido completo en Hermes Agent.'
    preview=excerpt(result.get('preview','')) if policy['content']=='excerpt' and job['excerpt_available'] and result['status']=='completed' else ''
    if preview:body=preview+'\n\nExtracto del resultado de Hermes Agent.'
    item=deepcopy(DEFAULTS)
    name=job['name'] if job['name'].strip() else 'Tarea de Hermes'
    item.update(id=job['job_key'],name=name[:60],enabled=True,kind='result',title=policy['title'] or name[:32],body=body,mode=policy['mode'],trigger='manual',expiry_minutes=30,busy='wait')
    return item

def snapshot(data,now):
    state=data.get('hermes_cron',empty())
    sources=[]
    for s in state['sources']:
        last=s['last_seen'];age=(now-datetime.fromisoformat(last)).total_seconds() if last else float('inf')
        sources.append(dict(s,online=0<=age<=90))
    jobs=[{k:deepcopy(v) for k,v in j.items() if k!='enabled_at'} for j in state['jobs']]
    return dict(revision=state['revision'],sources=sources,jobs=jobs)
