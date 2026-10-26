import test from 'node:test';
import assert from 'node:assert/strict';
import {installDOM,flush,input} from './dom-harness.mjs';
installDOM();
const {Ha2NotificationsPanel,LANGUAGE_ENTITY,newRule}=await import('../../custom_components/ha2_notifications/static/panel.js');
const key='c'.repeat(32);
const job=(extra={})=>({job_key:key,source_instance:'host-fixture',profile:'default',job_id:'raw-id',name:'Guardar',schedule:'0 7 * * 1-5 (raw)',enabled:true,no_agent:false,delivery:'local',excerpt_available:true,present:true,policy:{enabled:false,content:'brief',mode:'cue',title:''},...extra});
const dto=(extra={})=>({revision:7,sources:[{source_instance:'host-fixture',profile:'default',online:true,last_seen:'2026-10-24T10:00:00Z'}],jobs:[job()],...extra});
const snap=(cron=dto())=>({revision:49,paused:false,rules:[],logs:[],queue_count:0,timezone:'UTC',target:{available:true,name:'Fixture'},hermes_cron:cron});
function mount(callWS){const p=new Ha2NotificationsPanel();p.hass={connection:{connected:true},user:{is_admin:true},states:{[LANGUAGE_ENTITY]:{state:'Español'}},callWS};p.connectedCallback();return p;}
function end(p){p.disconnectedCallback();}
const field=(p,name,k=key)=>p.shadowRoot.querySelector('#cron-'+k+'-'+name);
const language=(p,state)=>p.hass={...p.hass,states:{[LANGUAGE_ENTITY]:{state}}};
test('cron: native iterable NodeList without Array.find renders safely',async()=>{
 const p=mount(async()=>snap());await flush();
 const control=field(p,'content'), options=Array.from(control.querySelectorAll('option'));
 control.querySelectorAll=()=>({length:options.length,item:i=>options[i],[Symbol.iterator]:()=>options[Symbol.iterator]()});
 assert.doesNotThrow(()=>p._renderCron());
 assert.equal(options.find(o=>o.value==='excerpt').disabled,false);
 end(p);
});

test('cron: catalogue section is after connection, separate from HA, OFF authoritative and raw metadata',async()=>{
 const calls=[];const p=mount(async r=>{calls.push(r);return snap();});await flush();
 const root=p.shadowRoot,main=root.querySelector('main');
 assert.ok(root.querySelector('#hermes-cron'),'new section exists');
 const connectionIndex=main.children.findIndex(n=>n.id==='connection');assert.equal(main.children[connectionIndex+1].id,'ha-notifications');assert.equal(main.children[connectionIndex+2].id,'hermes-cron');
 assert.equal(main.children[connectionIndex+3].id,'proactive');assert.equal(main.children.at(-1).id,'real-activity');
 assert.equal(root.querySelector('#hermes-cron').querySelector('#cron-content').querySelector('#cron-catalog'),root.querySelector('#cron-catalog'));
 assert.equal(root.querySelector('#ha-notifications').querySelector('#ha-content').querySelector('#rules'),root.querySelector('#rules'));
 assert.equal(root.querySelector('#real-activity').parentNode,main);assert.equal(root.querySelector('#real-activity').querySelector('#logs'),root.querySelector('#logs'));
 assert.equal(root.querySelector('#cron-heading').textContent,'Notificación de Tareas programadas en Hermes Agent');
 assert.equal(root.querySelector('#ha-heading').textContent,'Avisos programados en Home Assistant');
 assert.equal(field(p,'enabled').checked,false);assert.match(root.querySelector('#hermes-cron').textContent,/Guardar.*default.*0 7 \* \* 1-5 \(raw\)/s);
 assert.match(field(p,'state').textContent,/Cron activo/);assert.match(root.querySelector('#hermes-cron').textContent,/no pausa/);
 assert.deepEqual(calls,[{type:'ha2_notifications/get'}]);end(p);
});
test('v030 accordions: exclusive closed accessible group preserves drafts revision nodes and activity',async()=>{
 let reply=snap();const calls=[];const p=mount(async r=>{calls.push(r);return structuredClone(reply);});await flush();
 const cron=p.$('cron-toggle'),ha=p.$('ha-toggle');assert.ok(cron,'native heading button');
 for(const id of ['cron','ha']){const b=p.$(id+'-toggle');assert.equal(b.tagName,'BUTTON');assert.equal(b.type,'button');assert.equal(b.getAttribute('aria-controls'),id+'-content');assert.equal(b.getAttribute('aria-expanded'),'false');assert.equal(p.$(id+'-content').hidden,true);assert.ok(b.textContent.length);}
 const form=field(p,'form'),title=field(p,'title');input(title,'Unsaved literal');const revision=p._cronRows.get(key).revision;
 cron.focus();cron.click();assert.equal(document.activeElement,cron);assert.equal(cron.getAttribute('aria-expanded'),'true');ha.click();assert.equal(cron.getAttribute('aria-expanded'),'false');assert.equal(ha.getAttribute('aria-expanded'),'true');ha.click();assert.equal(ha.getAttribute('aria-expanded'),'false');
 const e=new Event('keydown',{cancelable:true});Object.defineProperty(e,'key',{value:'ArrowDown'});ha.dispatchEvent(e);assert.equal(document.activeElement,cron);assert.equal(e.defaultPrevented,true);
 const rule={...newRule('reminder'),name:'Draft',title:'Title',body:'Body'};p.openEditor(rule,true);const body=p.$('edit-body');input(body,'HA draft');p.$('logs').scrollTop=83;
 reply=snap(dto({revision:8}));await p.refresh();language(p,'English');cron.click();ha.click();
 assert.equal(field(p,'form'),form);assert.equal(field(p,'title'),title);assert.equal(title.value,'Unsaved literal');assert.equal(p._cronRows.get(key).revision,revision);assert.equal(p.$('edit-body'),body);assert.equal(body.value,'HA draft');assert.equal(p.editing.revision,49);assert.equal(p.$('logs').scrollTop,83);assert.equal(p.$('real-activity').hidden,false);assert.equal(p.$('ha-content').querySelector('#logs'),null);assert.ok(calls.every(r=>r.type==='ha2_notifications/get'));end(p);
});
test('cron: offline is read-only including explicit reset, scripts cannot select excerpts, unknown is not online',async()=>{
 let reply=snap(dto({jobs:[job({no_agent:true,excerpt_available:false})]}));const calls=[];const p=mount(async r=>{calls.push(r);return structuredClone(reply);});await flush();
 assert.equal(field(p,'content').querySelectorAll('option').find(o=>o.value==='excerpt').disabled,true);
 input(field(p,'content'),'excerpt');field(p,'save').click();await flush();assert.equal(calls.length,1);assert.match(field(p,'feedback').textContent,/Revisa contenido/);
 input(field(p,'content'),'brief');const enabled=field(p,'enabled');input(enabled,true);
 reply=snap(dto({revision:8,sources:[{source_instance:'host-fixture',profile:'default',online:false,last_seen:'2026-10-01T00:00:00Z'}]}));await p.refresh();
 assert.equal(enabled.disabled,true);assert.equal(field(p,'reset').disabled,true,'offline has no editable controls');assert.equal(field(p,'save').disabled,true);assert.match(p.shadowRoot.querySelector('#hermes-cron').textContent,/Fuente sin conexión.*2026-10-01/);
 reply=snap(dto({sources:[]}));await p.refresh();assert.match(p.shadowRoot.querySelector('#hermes-cron').textContent,/desconocida/);assert.equal(field(p,'save').disabled,true);
 reply=snap(dto());await p.refresh();p.hass={...p.hass,connection:{connected:false}};assert.equal(field(p,'save').disabled,true);await p._saveCron(key);const count=calls.length;
 p.hass={...p.hass,connection:{connected:true},user:{is_admin:false}};await p._saveCron(key);assert.equal(calls.length,count);end(p);
});
test('cron: high/low catalogue polls retain nodes and draft, absent DTO is compatible and no extra requests',async()=>{
 let reply=snap();const calls=[];const p=mount(async r=>{calls.push(r);return structuredClone(reply);});await flush();const title=field(p,'title'),enabled=field(p,'enabled');input(title,'User raw');input(enabled,true);
 const second=job({job_key:'d'.repeat(32),name:'Second raw',policy:{enabled:false,content:'brief',mode:'cue',title:''}});
 reply=snap(dto({revision:8,jobs:[job(),second]}));await p.refresh();assert.equal(field(p,'title'),title);assert.equal(field(p,'enabled','d'.repeat(32)).checked,false);
 reply=snap(dto({revision:9,jobs:[second]}));await p.refresh();assert.equal(field(p,'title'),title);assert.equal(title.value,'User raw');assert.equal(field(p,'save').disabled,true);assert.match(field(p,'state').textContent,/ausente/);
 reply=snap(dto({revision:10,jobs:[job(),second]}));await p.refresh();assert.equal(field(p,'enabled'),enabled);assert.equal(enabled.checked,true);assert.equal(p._cronRows.get(key).revision,7);
 reply=snap(null);await p.refresh();assert.match(p.shadowRoot.querySelector('#cron-catalog').textContent,/Sin catálogo/);language(p,'English');assert.match(p.shadowRoot.querySelector('#cron-catalog').textContent,/No Hermes catalog/);
 reply=snap(dto());await p.refresh();assert.equal(field(p,'title'),title);assert.ok(calls.every(r=>r.type==='ha2_notifications/get'));end(p);
});
test('cron: public errors bilingual, UTF8 limits, no mute, no bodies or sync/result writes',async()=>{
 let failure;const calls=[];const p=mount(async r=>{calls.push(r);if(failure && r.type.endsWith('/cron_policy'))throw Object.assign(new Error('PRIVATE_BODY_URL'),{code:failure});return snap();});await flush();
 for(const code of ['unavailable','not_found','unauthorized','invalid_policy','unknown_error']){failure=code;field(p,'save').click();await flush();assert.ok(field(p,'feedback').textContent.length);assert.ok(!p.shadowRoot.textContent.includes('PRIVATE_BODY_URL'));language(p,'English');assert.match(field(p,'feedback').textContent,/preserved/i);language(p,'Español');}
 const before=calls.length;input(field(p,'title'),'😀'.repeat(33));field(p,'save').click();await flush();assert.equal(calls.length,before);assert.equal(field(p,'title').value,'😀'.repeat(33));
 input(field(p,'title'),'😀'.repeat(32));failure=null;field(p,'save').click();await flush();assert.equal(calls.length,before+1);
 assert.deepEqual(field(p,'mode').querySelectorAll('option').map(o=>o.value),['cue','voice']);assert.ok(!/mute/i.test(p.shadowRoot.querySelector('#hermes-cron').textContent));assert.ok(calls.every(r=>['ha2_notifications/get','ha2_notifications/cron_policy'].includes(r.type)));end(p);
});
test('cron: open HA editor, preview and log scroll survive cron save, stale get and detached write ignored',async()=>{
 let resolvePolicy,resolveGet,waitGet=false;const base={...newRule('reminder'),id:'a'.repeat(32),name:'HA raw',title:'HA',body:'Body'};
 const withHA=()=>({...snap(),rules:[base],logs:[{id:'l',name:'Log',status:'queued'}]});
 const p=mount(async r=>r.type.endsWith('/cron_policy')?new Promise(a=>resolvePolicy=a):waitGet?new Promise(a=>resolveGet=a):withHA());await flush();p.openEditor(base);const body=p.$('edit-body');input(body,'Unsaved HA');const preview=p.$('preview');p.$('logs').scrollTop=123;
 waitGet=true;const pending=p.refresh();field(p,'save').click();await flush();resolvePolicy({...withHA(),hermes_cron:dto({revision:8})});await flush();resolveGet({...snap(),revision:1});await pending;
 assert.equal(p.snapshot.revision,49);assert.equal(p.$('edit-body'),body);assert.equal(body.value,'Unsaved HA');assert.equal(p.$('editor').open,true);assert.equal(p.$('preview'),preview);assert.equal(p.$('logs').scrollTop,123);
 field(p,'save').click();await flush();end(p);resolvePolicy({...snap(),revision:999});await flush();assert.equal(p.snapshot.revision,49);
});
test('cron: save exact policy only, captured revision independent of HA49, double-click and public conflict',async()=>{
 let reply=snap(),reject,resolve;const calls=[];const p=mount(async r=>{calls.push(structuredClone(r));if(r.type.endsWith('/cron_policy'))return new Promise((a,b)=>{resolve=a;reject=b;});return structuredClone(reply);});await flush();
 const title=field(p,'title'),enabled=field(p,'enabled');input(title,'Guardar');input(enabled,true);input(field(p,'mode'),'voice');input(field(p,'content'),'excerpt');
 reply=snap(dto({revision:8,jobs:[job({enabled:false})]}));await p.refresh();language(p,'English');
 assert.equal(field(p,'enabled'),enabled);assert.equal(enabled.checked,true);assert.equal(title.value,'Guardar');assert.equal(field(p,'save').textContent,'Save');assert.match(field(p,'state').textContent,/Cron paused/);
 field(p,'save').click();field(p,'save').click();await flush();
 const expected={type:'ha2_notifications/cron_policy',job_key:key,expected_revision:7,enabled:true,content:'excerpt',mode:'voice',title:'Guardar'};
 assert.deepEqual(calls.at(-1),expected);assert.equal(calls.filter(r=>r.type.endsWith('/cron_policy')).length,1);assert.equal(enabled.disabled,true);assert.equal(p.snapshot.hermes_cron.jobs[0].policy.enabled,false);
 reject(Object.assign(new Error('PRIVATE_EXECUTION_BODY_TOKEN'),{code:'conflict'}));await flush();
 assert.match(field(p,'feedback').textContent,/another panel|another session/);assert.equal(title.value,'Guardar');assert.ok(!p.shadowRoot.textContent.includes('PRIVATE_EXECUTION_BODY_TOKEN'));
 field(p,'save').click();await flush();assert.deepEqual(calls.at(-1),expected);
 resolve(snap(dto({revision:9,jobs:[job({policy:{enabled:true,content:'excerpt',mode:'voice',title:'Guardar'}})]})));await flush();assert.match(field(p,'feedback').textContent,/saved/);assert.equal(p.snapshot.revision,49);
 assert.equal(p._cronRows.get(key).revision,7,'only explicit reset advances captured revision');
 field(p,'reset').click();assert.equal(p._cronRows.get(key).revision,9);end(p);
});

