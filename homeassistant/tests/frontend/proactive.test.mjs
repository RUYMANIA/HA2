import test from 'node:test';
import assert from 'node:assert/strict';
import {installDOM,flush,input} from './dom-harness.mjs';
installDOM();
const {Ha2NotificationsPanel,LANGUAGE_ENTITY}=await import('../../custom_components/ha2_notifications/static/panel.js');
const defaults=()=>({enabled:false,all_day:true,start:'09:00',end:'21:00',interval_minutes:60,mode:'cue'});
const snapshot=(patch={})=>({version:'0.3.0',revision:49,paused:false,rules:[],logs:[],queue_count:0,timezone:'Atlantic/Canary',target:{available:true,name:'Fixture',night_active:false},hermes_cron:{revision:7,sources:[],jobs:[]},proactive:{revision:3,config:defaults(),runtime:{status:'off',next_due_at:null},capabilities:{full_agent:true,session_binding:true,transcript_only:true,native_listen:true}},...patch});
function mount(callWS){const p=new Ha2NotificationsPanel();p.hass={connection:{connected:true},user:{is_admin:true},states:{[LANGUAGE_ENTITY]:{state:'Español'}},callWS};p.connectedCallback();return p;}

test('proactive: HA then cron then proactive closed exclusive accordions, activity last and no effects',async()=>{
 const calls=[];const p=mount(async q=>{calls.push(q);return snapshot();});await flush();try{
 const children=p.$('app').children,at=children.findIndex(x=>x.id==='connection');
 assert.deepEqual(children.slice(at+1).map(x=>x.id),['ha-notifications','hermes-cron','proactive','real-activity']);
 assert.deepEqual(p._accordions.map(x=>x.toggle.id),['ha-toggle','cron-toggle','proactive-toggle']);
 for(const key of ['proactive','cron','ha'])assert.equal(p.$(key+'-content').hidden,true);
 p.$('proactive-toggle').click();assert.equal(p.$('proactive-content').hidden,false);p.$('cron-toggle').click();assert.equal(p.$('proactive-content').hidden,true);
 assert.equal(p.$('proactive-enabled').checked,false);assert.equal(p.$('proactive-all-day').checked,true);assert.equal(p.$('proactive-interval').value,'60');
 const values=p.$('proactive-interval').querySelectorAll('option').map(x=>Number(x.value));assert.deepEqual(values,Array.from({length:48},(_,i)=>(i+1)*30));
 assert.deepEqual(p.$('proactive-mode').querySelectorAll('option').map(x=>x.value),['cue','voice']);
 assert.deepEqual(calls,[{type:'ha2_notifications/get'}]);assert.match(p.$('proactive-content').textContent,/noche|night/i);
 assert.doesNotMatch(p.$('proactive-content').textContent,/30 segundos|30 seconds/);
 }finally{p.disconnectedCallback();}
});

test('proactive: approved heading has no beta; domestic beta and drafts survive locale poll collapse without writes',async()=>{
 const calls=[];const p=mount(async q=>{calls.push(q);return snapshot();});await flush();try{
 assert.equal(p.$('proactive-toggle').querySelector('.beta-badge'),null);
 assert.equal(p.$('proactive-toggle').textContent,'Modo Proactivo');
 const badge=p.$('template-notice').querySelector('.beta-badge');assert.equal(badge.textContent,'MODO BETA');
 const form=p.$('proactive-form'),start=p.$('proactive-start');input(start,'10:30');
 for(const key of ['ha','cron','proactive']){p.$(key+'-toggle').click();assert.equal(p._accordions.filter(x=>!x.content.hidden).length,1);}
 p.hass={...p.hass,states:{[LANGUAGE_ENTITY]:{state:'English'}}};await p.refresh();
 assert.equal(p.$('proactive-toggle').querySelector('.beta-badge'),null);assert.equal(p.$('proactive-toggle').textContent,'Proactive mode');assert.equal(badge.textContent,'BETA MODE');
 assert.match(p.$('ha-toggle').textContent,/Scheduled notifications in Home Assistant/);
 assert.match(p.$('cron-toggle').textContent,/Hermes Agent scheduled task notifications/);
 p.hass={...p.hass,states:{[LANGUAGE_ENTITY]:{state:'Español'}}};
 assert.equal(badge.textContent,'MODO BETA');assert.equal(p.$('proactive-form'),form);assert.equal(p.$('proactive-start'),start);
 assert.equal(start.value,'10:30');assert.equal(p._proactive.revision,3);assert.equal(p._proactive.draft.enabled,false);
 assert.deepEqual(calls,[{type:'ha2_notifications/get'},{type:'ha2_notifications/get'}]);
 }finally{p.disconnectedCallback();}
});

test('proactive: exact independent revision save and successful next edit advance own revision',async()=>{
 const calls=[];let current=snapshot();const p=mount(async q=>{calls.push(structuredClone(q));if(q.type.endsWith('/proactive_config'))current={...current,proactive:{...current.proactive,revision:current.proactive.revision+1,config:structuredClone(q.config)}};return structuredClone(current);});await flush();try{
 input(p.$('proactive-enabled'),true);input(p.$('proactive-all-day'),false);input(p.$('proactive-start'),'22:00');input(p.$('proactive-end'),'06:00');input(p.$('proactive-interval'),'90');input(p.$('proactive-mode'),'voice');
 p.$('proactive-save').click();await flush();assert.deepEqual(calls.at(-1),{type:'ha2_notifications/proactive_config',expected_revision:3,config:{enabled:true,all_day:false,start:'22:00',end:'06:00',interval_minutes:90,mode:'voice'}});
 input(p.$('proactive-mode'),'cue');p.$('proactive-save').click();await flush();assert.equal(calls.at(-1).expected_revision,4);assert.equal(p.snapshot.revision,49);
 }finally{p.disconnectedCallback();}
});

test('proactive: poll locale collapse retain node draft and captured revision; conflicts do not expose errors',async()=>{
 let current=snapshot();const calls=[];const p=mount(async q=>{calls.push(q);if(q.type.endsWith('/proactive_config'))throw Object.assign(new Error('PRIVATE_UPSTREAM_TOKEN'),{code:'conflict'});return structuredClone(current);});await flush();try{
 const start=p.$('proactive-start');input(start,'10:30');input(p.$('proactive-all-day'),false);current.proactive.revision=12;await p.refresh();
 p.hass={...p.hass,states:{[LANGUAGE_ENTITY]:{state:'English'}}};p.$('proactive-toggle').click();p.$('ha-toggle').click();
 assert.equal(p.$('proactive-start'),start);assert.equal(start.value,'10:30');assert.equal(p._proactive.revision,3);
 p.$('proactive-save').click();await flush();assert.equal(calls.at(-1).expected_revision,3);assert.match(p.$('proactive-feedback').textContent,/changed|session|conflict/i);assert.ok(!p.shadowRoot.textContent.includes('PRIVATE_'));assert.equal(start.value,'10:30');
 p.$('proactive-reset').click();assert.equal(p._proactive.revision,12);
 }finally{p.disconnectedCallback();}
});

test('proactive: unknown capability blocks enable, offline admin and invalid config never write',async()=>{
 const calls=[];const data=snapshot();data.proactive.capabilities.native_listen=false;const p=mount(async q=>{calls.push(q);return structuredClone(data);});await flush();try{
 input(p.$('proactive-enabled'),true);await p._saveProactive();assert.equal(calls.length,1);
 input(p.$('proactive-enabled'),false);input(p.$('proactive-interval'),'45');await p._saveProactive();assert.equal(calls.length,1);
 input(p.$('proactive-interval'),'60');p.hass={...p.hass,connection:{connected:false}};await p._saveProactive();assert.equal(calls.length,1);
 p.hass={...p.hass,connection:{connected:true},user:{is_admin:false}};await p._saveProactive();assert.equal(calls.length,1);
 }finally{p.disconnectedCallback();}
});
