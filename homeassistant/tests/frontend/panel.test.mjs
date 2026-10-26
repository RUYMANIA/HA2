import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {installDOM, flush, input} from './dom-harness.mjs';
const env = installDOM();
const path = new URL('../../custom_components/ha2_notifications/static/panel.js', import.meta.url);
let mod;
try { mod = await import(path.href); } catch (error) { mod = {}; }
test('v030 version: offline before get, snapshot authority, bilingual and no extra calls',async()=>{
 const calls=[];let resolve;const p=panelWith(req=>{calls.push(req);return new Promise(r=>resolve=r);});const root=p.shadowRoot;
 assert.equal(root.querySelector('#panel-version')?.textContent,'Versión del panel: —');
 assert.ok(root.querySelector('#panel-version').parentNode.textContent.includes('Home Hermes Agent Assitant'));
 assert.ok(root.textContent.includes('RUYMANIA · NOTIFICACIONES'));
 resolve(snapshot({version:'0.2.0'}));await flush();assert.equal(root.querySelector('#panel-version').textContent,'Versión del panel: 0.2.0');
 locale(p,'English');assert.equal(root.querySelector('#panel-version').textContent,'Panel version: 0.2.0');
 p.snapshot=snapshot({version:'0.3.0'});p._renderRuntime();assert.equal(root.querySelector('#panel-version').textContent,'Panel version: 0.3.0');
 p.hass={...p.hass,connection:{connected:false}};assert.equal(root.querySelector('#panel-version').textContent,'Panel version: 0.3.0');assert.deepEqual(calls,[{type:'ha2_notifications/get'}]);detach(p);
});
test('v030 beta: home event template only, state editor follows When without type or payload drift',async()=>{
 const calls=[];const p=panelWith(async r=>{calls.push(r);return snapshot();});await flush();const root=p.shadowRoot;
 assert.equal(root.querySelector('#template-notice').querySelector('.beta-badge')?.textContent,'MODO BETA');
 for(const kind of ['weather','reminder','result'])assert.equal(root.querySelector('#template-'+kind).querySelector('.beta-badge'),null);
 p.openEditor(rule({kind:'notice',trigger:'state'}));const badge=root.querySelector('#editor-beta');assert.ok(badge);assert.equal(badge.hidden,false);assert.equal(badge.textContent,'MODO BETA');const body=root.querySelector('#edit-body');input(body,'Literal');
 const draft=structuredClone(p.editing.rule);locale(p,'English');assert.equal(badge.textContent,'BETA MODE');assert.deepEqual(p.editing.rule,draft);
 input(root.querySelector('#edit-trigger'),'manual');assert.equal(badge.hidden,true);input(root.querySelector('#edit-trigger'),'state');assert.equal(badge.hidden,false);assert.equal(root.querySelector('#edit-body'),body);assert.equal(body.value,'Literal');assert.equal(p.editing.rule.kind,'notice');assert.equal(root.querySelector('#edit-kind'),null);
 for(const kind of ['weather','reminder','result']){p.openEditor(rule({kind,trigger:'manual'}));assert.equal(root.querySelector('#editor-beta').hidden,true);input(root.querySelector('#edit-trigger'),'state');assert.equal(root.querySelector('#editor-beta').hidden,false);assert.equal(p.editing.rule.kind,kind);assert.ok(!Object.keys(p.editing.rule).some(k=>/beta/i.test(k)));}
 assert.deepEqual(calls,[{type:'ha2_notifications/get'}]);const source=await readFile(path,'utf8');assert.match(source,/\.beta-badge\{[^}]*background:#ffca28[^}]*color:#241a00/);detach(p);
});
test('v011 copy: literal hero, filter label and single accessible reminder', async () => {
  const panel=panelWith(async()=>snapshot());await flush();const root=panel.shadowRoot;
  assert.equal(root.querySelector('h1').textContent,'Tu casa, en una Bola.');
  assert.ok(root.textContent.includes('Elige qué quieres recibir, cuándo y cómo. Las reglas para tú Bola se coordinan aquí, en Home Assistant.'));
  assert.equal(root.querySelector('#filter-label').textContent,'Mostrar los avisos de tipo:');
  assert.equal(root.querySelector('#remember').querySelectorAll('li').map(n=>n.textContent).join('\n'),'-Durante el modo noche la Ball no mostrará por pantalla los avisos ni audio.\n-El contenido de los avisos puede ser privado. Si la Ball es compartida, elija con cuidado qué se muestra o se lee.');
  detach(panel);
});
test('v011 connection: named target only connected with true availability and online HA', async () => {
  let reply=snapshot();const panel=panelWith(async()=>reply);await flush();const root=panel.shadowRoot;
  assert.equal(root.querySelector('#connection').textContent,'Ball fixture está conectado a Home Assistant.');
  for(const available of [false,null,undefined]){reply=snapshot({target:{name:'Destino fixture',available}});await panel.refresh();assert.ok(!root.querySelector('#connection').textContent.includes('está conectado'));assert.match(root.querySelector('#connection').textContent,available===false?/no está disponible/:/desconocida/);}
  panel.hass={...panel.hass,connection:{connected:false}};assert.match(root.querySelector('#connection').textContent,/desconectado/);detach(panel);
});
test('v012 fixed kind: editor cannot change type selected in the template chooser', async () => {
  const calls=[];const panel=panelWith(async request=>{calls.push(request);return snapshot();});await flush();const root=panel.shadowRoot;
  for(const [kind,title,pattern] of [['notice','Nuevo evento doméstico',/transición.*otro dispositivo/],['reminder','Nuevo recordatorio',/fecha.*días/],['weather','Nuevo aviso de Tiempo',/datos.*Home Assistant.*pronóstico/],['result','Nuevo resultado manual',/petición.*no.*automático/]]){
    root.querySelector('#new').click();root.querySelector('#template-'+kind).click();
    assert.equal(root.querySelector('#edit-kind'),null,'Type selection belongs only to the template chooser');
    assert.equal(panel.editing.rule.kind,kind);
    assert.equal(root.querySelector('#editor-heading').textContent,title);assert.match(root.querySelector('#kind-description').textContent,pattern);
    assert.equal(root.querySelector('#edit-form').children[1].id,'kind-description');
    clickLabel(root.querySelector('#editor'),'Cancelar');
    assert.equal(root.querySelector('#editor').open,false);
  }
  panel.openEditor(rule({kind:'reminder'}));
  assert.equal(root.querySelector('#edit-kind'),null,'Existing notices also keep their original type');
  assert.equal(panel.editing.rule.kind,'reminder');assert.equal(calls.length,1,'Opening and cancelling editors does not write');detach(panel);
});
test('v011 pause: checked switch is authoritative, guarded and rolls back failed requests', async () => {
  let resolve,reject;const calls=[];const panel=panelWith(async req=>{calls.push(req);return req.type.endsWith('/pause')?new Promise((a,b)=>{resolve=a;reject=b;}):snapshot();});await flush();const root=panel.shadowRoot,control=root.querySelector('#pause');
  assert.equal(control.tagName,'INPUT');assert.equal(control.type,'checkbox');assert.equal(control.role,'switch');assert.equal(control.checked,false);assert.match(control.parentNode.textContent,/Pausar todos los avisos.*Off/);
  assert.match(root.querySelector('style').textContent,/#pause\{[^}]*appearance:none/, 'The On/Off indicator must render as a slider, not the browser checkbox');
  input(control,true);await flush();assert.equal(control.disabled,true);assert.equal(control.checked,false,'pending is not confirmed pause');assert.equal(calls.at(-1).paused,true);
  reject(new Error('fixture'));await flush();assert.equal(control.checked,false);assert.equal(control.disabled,false);
  input(control,true);resolve(snapshot({paused:true,revision:5}));await flush();assert.equal(control.checked,true);assert.match(control.parentNode.textContent,/On/);
  panel.hass={...panel.hass,connection:{connected:false}};assert.equal(control.disabled,true);detach(panel);
});
test('v011 cards: name pause and toggle before source, local keyboard preview and isolated actions', async () => {
  const calls=[];const panel=panelWith(async req=>{calls.push(req);return snapshot({paused:true,rules:[rule(),rule({id:'b'.repeat(32),name:'Segundo',enabled:true})]});});await flush();const root=panel.shadowRoot;
  let cards=root.querySelectorAll('article');assert.equal(cards[1].children[0].tagName,'H3');assert.equal(cards[1].children[1].textContent,'Pausa global');assert.equal(cards[1].children[2].textContent,'Desactivar');assert.match(cards[1].textContent,/Habilitado/);assert.match(cards[1].querySelector('.schedule').textContent,/^Se ejecuta:/);assert.ok(!root.querySelectorAll('button').some(b=>b.textContent==='Ver'));
  assert.equal(cards[1].tabIndex,0);cards[1].click();assert.equal(panel.selected,'b'.repeat(32));assert.equal(calls.length,1);
  cards=root.querySelectorAll('article');cards[0].focus();for(const key of ['Enter',' ']){const e=new Event('keydown',{bubbles:true,cancelable:true});Object.defineProperty(e,'key',{value:key});root.querySelectorAll('article')[0].dispatchEvent(e);assert.equal(panel.selected,'a'.repeat(32));assert.equal(e.defaultPrevented,true);}
  const second=root.querySelectorAll('article')[1];clickLabel(second,'Editar');assert.equal(panel.selected,'a'.repeat(32));assert.equal(calls.length,1);
  clickLabel(second,'Desactivar');await flush();assert.equal(panel.selected,'a'.repeat(32));assert.equal(calls.at(-1).type,'ha2_notifications/toggle');detach(panel);
});
test('v011 activity: newest first, bounded accessible scrolling and stable nodes across polls', async () => {
  const logs=Array.from({length:50},(_,i)=>({id:String(i),at:`2026-10-23T10:${String(i).padStart(2,'0')}:00Z`,name:`Evento ${i}`,status:'queued'}));
  let reply=snapshot({logs});const panel=panelWith(async()=>structuredClone(reply));await flush();const root=panel.shadowRoot,region=root.querySelector('#logs');
  assert.equal(region.role,'region');assert.equal(region.tabIndex,0);assert.match(region.getAttribute('aria-label'),/Actividad/);assert.match(region.children[0].textContent,/Evento 49/);assert.equal(region.children.length,50);
  const first=region.children[0];region.scrollTop=140;await panel.refresh();assert.equal(region.children[0],first);assert.equal(region.scrollTop,140);
  reply=snapshot({logs:[...logs.slice(1),{id:'new',at:'2026-10-23T11:00:00Z',name:'Nuevo',status:'waiting'}]});await panel.refresh();assert.equal(region.scrollTop,140);assert.equal(region.children[1],first);assert.match(region.children[0].textContent,/Nuevo/);
  const source=await readFile(path,'utf8');assert.match(source,/#logs\{[^}]*max-height:360px[^}]*overflow-y:auto/);detach(panel);
});
test('v011 catalog: validated catalog accepts vacuum and other domains, rejects absent and unusable states', () => {
  const entities=[{entity_id:'vacuum.robot'},{entity_id:'binary_sensor.puerta'},{entity_id:'number.umbral'}];
  for(const [entity_id,to_state] of [['vacuum.robot','cleaning'],['binary_sensor.puerta','on'],['number.umbral','42.5']])assert.deepEqual(mod.validateRule(rule({kind:'notice',trigger:'state',entity_id,to_state}),entities),[]);
  for(const [entity_id,to_state] of [['vacuum.ausente','cleaning'],['vacuum.robot','unknown'],['vacuum.robot','unavailable'],['vacuum.robot',' ']])assert.ok(mod.validateRule(rule({kind:'notice',trigger:'state',entity_id,to_state}),entities).length);
});
test('v011 entities: real select and raw editable state suggestions follow catalog without draft loss', async () => {
  const entities=[{entity_id:'vacuum.robot',name:'Robot del salón',state:'docked',state_options:['cleaning','docked','unknown',''],state_options_source:'domain'},{entity_id:'binary_sensor.puerta',name:'Puerta principal',state:'off',state_options:['on','off'],state_options_source:'domain'},{entity_id:'number.umbral',name:'Umbral',state:'21.5',state_options:['21.5'],state_options_source:'current'}];
  const calls=[];const panel=panelWith(async req=>{calls.push(req);return snapshot({entity_options:entities});});await flush();panel.openEditor(mod.newRule('notice'),true);const root=panel.shadowRoot,entity=root.querySelector('#edit-entity_id'),to=root.querySelector('#edit-to_state');
  assert.equal(entity.tagName,'SELECT');assert.equal(entity.querySelectorAll('option')[0].value,'');assert.match(entity.textContent,/Robot del salón.*vacuum.robot/);assert.equal(to.getAttribute('list'),'state-options');
  input(root.querySelector('#edit-name'),'No perder nombre');input(root.querySelector('#edit-body'),'No perder texto');
  for(const [id,expected,current] of [['vacuum.robot',['cleaning','docked'],'docked'],['binary_sensor.puerta',['on','off'],'off'],['number.umbral',['21.5'],'21.5']]){
    input(entity,id);assert.deepEqual(root.querySelector('#state-options').querySelectorAll('option').map(n=>n.value),expected);assert.equal(to.value,'');assert.match(root.querySelector('#state-help').textContent,new RegExp(current.replace('.','\\.')));assert.match(root.querySelector('#state-help').textContent,/on.*off.*sin traducir/);assert.equal(root.querySelector('#edit-name').value,'No perder nombre');assert.equal(root.querySelector('#edit-body').value,'No perder texto');
    assert.equal(root.querySelector('#state-suggestions').querySelectorAll('button').length,expected.length);
  }
  input(to,'42.75');assert.equal(panel.editing.rule.to_state,'42.75');assert.deepEqual(mod.validateRule({...panel.editing.rule,title:'Umbral'},entities),[]);
  input(entity,'binary_sensor.puerta');clickLabel(root.querySelector('#state-suggestions'),'on');assert.equal(to.value,'on');assert.equal(panel.editing.rule.to_state,'on');assert.equal(calls.length,1);detach(panel);
});
test('v011 action isolation: second card test and nested keyboard never select or send without confirmation', async () => {
  const calls=[];const panel=panelWith(async req=>{calls.push(req);return snapshot({rules:[rule(),rule({id:'b'.repeat(32),name:'Segundo'})]});});await flush();const root=panel.shadowRoot,card=root.querySelectorAll('article')[1];
  const testButton=clickLabel(card,'Probar real…');assert.equal(panel.selected,'a'.repeat(32));assert.equal(calls.length,1);assert.equal(root.querySelector('#confirm').open,true);
  const e=new Event('keydown',{bubbles:true,cancelable:true});Object.defineProperty(e,'key',{value:' '});testButton.dispatchEvent(e);assert.equal(e.defaultPrevented,false);assert.equal(panel.selected,'a'.repeat(32));
  clickLabel(root.querySelector('#confirm'),'Cancelar acción');assert.equal(calls.length,1);detach(panel);
});
test('slice 1: validates canonical UTF8 limits and fresh templates are disabled, no forecast fabricated', () => {
  assert.equal(typeof mod.validateRule, 'function', 'production validator is not implemented');
  const rule = mod.newRule('notice');
  assert.equal(rule.enabled, false);
  Object.assign(rule, {name:'Aviso', title:'Casa', body:'Hola', trigger:'manual'});
  assert.deepEqual(mod.validateRule(rule, []), []);
  rule.body = '€'.repeat(1366);
  assert.match(mod.validateRule(rule, []).join(' '), /4096/);
  const weather = mod.newRule('weather');
  assert.equal(weather.body, '');
  assert.equal(weather.enabled, false);
  assert.ok(mod.validateRule({...weather,name:'Tiempo',title:'Tiempo',trigger:'manual'}, []).length === 0);
});

const snapshot = (extra={}) => ({version:'0.1.0',revision:4,paused:false,rules:[],logs:[],queue_count:0,timezone:'Atlantic/Canary',weather_entity:'weather.forecast_casa',target:{name:'Ball fixture',available:true,night_active:false},entity_options:[],capabilities:{voice:true,triggers:['weekly','once','state','manual']},...extra});
function panelWith(callWS) {
  const C = customElements.get('ha2-notifications-panel');
  assert.equal(typeof C,'function','native custom element not registered');
  const panel = new C(); panel.isConnected=true;
  panel.hass={connection:{connected:true},user:{is_admin:true},states:{'select.xiaozhi_ball_v2_language':{state:'Español',attributes:{options:['English','Español']}}},callWS};
  panel.connectedCallback(); return panel;
}
test('slice 2: native hass snapshot, visible poll, honest empty state and disconnect cleanup', async () => {
  const calls=[];
  const panel=panelWith(async req=>{calls.push(req);return snapshot();});
  await flush();
  assert.deepEqual(calls,[{type:'ha2_notifications/get'}]);
  const root=panel.shadowRoot;
  assert.match(root.textContent,/Home Hermes Agent Assitant/);
  assert.match(root.querySelector('#rules').textContent,/Todavía no hay avisos/);
  assert.match(root.querySelector('#system').textContent,/Ball fixture/);
  assert.equal(env.intervals.size,1);
  const timer=[...env.intervals.values()][0];assert.ok(timer.ms>=4000 && timer.ms<=5000);
  document.visibilityState='hidden';document.dispatchEvent(new Event('visibilitychange'));
  assert.equal(env.intervals.size,0);
  document.visibilityState='visible';document.dispatchEvent(new Event('visibilitychange'));await flush();
  assert.equal(calls.length,2);
  panel.isConnected=false;panel.disconnectedCallback();
  assert.equal(env.intervals.size,0);
  assert.equal(document.listeners.get('visibilitychange').size,0);
});
const rule = (extra={}) => ({...mod.newRule('reminder'),id:'a'.repeat(32),name:'Aviso fixture',title:'Prueba',body:'Contenido fixture',trigger:'manual',...extra});
function clickLabel(root,label) {const b=root.querySelectorAll('button').find(b=>b.textContent===label);assert.ok(b,`button ${label} exists`);b.click();return b;}
function detach(panel) {panel.isConnected=false;panel.disconnectedCallback();}
test('slice 3: real editor survives poll, conflict and queue errors; captured configuration revision on save', async () => {
  let reply=snapshot({rules:[rule()]});const calls=[];
  const panel=panelWith(async req=>{calls.push(structuredClone(req));if(reply instanceof Error)throw reply;return structuredClone(reply);});
  await flush();const root=panel.shadowRoot;
  clickLabel(root,'Editar');
  const field=root.querySelector('#edit-body');assert.ok(field,'editor is rendered');
  input(field,'Mi texto sin guardar');
  reply=snapshot({revision:5,rules:[rule({body:'Cambio externo'})],logs:[{id:'l',name:'Real fixture',status:'queued'}]});
  await panel.refresh();
  assert.equal(root.querySelector('#edit-body'),field,'poll must not replace editor nodes');
  assert.equal(field.value,'Mi texto sin guardar');
  assert.equal(panel.selected,'a'.repeat(32));
  reply=Object.assign(new Error('raw private exception must not leak'),{code:'conflict'});
  root.querySelector('#edit-form').dispatchEvent(new Event('submit',{cancelable:true}));await flush();
  assert.equal(calls.at(-1).expected_revision,4,'revision captured at open, not latest snapshot');
  assert.equal(calls.at(-1).rule.body,'Mi texto sin guardar');
  assert.equal(root.querySelector('#editor').open,true);
  assert.equal(field.value,'Mi texto sin guardar');
  assert.match(root.querySelector('#edit-error').textContent,/otro panel|otra sesión/i);
  assert.ok(!root.textContent.includes('raw private exception'));
  reply=Object.assign(new Error('PRIVATE_LANGUAGE_FAILURE_TOKEN'),{code:'queue_full'});
  root.querySelector('#edit-form').dispatchEvent(new Event('submit',{cancelable:true}));await flush();
  assert.equal(field.value,'Mi texto sin guardar');assert.match(root.querySelector('#edit-error').textContent,/cola/i);
  reply=snapshot({revision:6,rules:[rule({body:'Mi texto sin guardar'})],saved_id:'a'.repeat(32)});
  root.querySelector('#edit-form').dispatchEvent(new Event('submit',{cancelable:true}));await flush();
  assert.equal(root.querySelector('#editor').open,false);
  assert.equal(panel.snapshot.rules[0].body,'Mi texto sin guardar');
  detach(panel);
});
test('slice 3: new weather template has automatic body and saves disabled; weekly once and state fields use contract', async () => {
  const calls=[];const entities=[{entity_id:'sensor.lavadora',name:'Lavadora',state:'idle'}];
  const panel=panelWith(async req=>{calls.push(req);return snapshot({entity_options:entities,saved_id:'b'.repeat(32)});});await flush();const root=panel.shadowRoot;
  root.querySelector('#new').click();root.querySelector('#template-weather').click();
  assert.equal(root.querySelector('#editor').open,true);
  assert.equal(root.querySelector('#edit-enabled').checked,false);
  assert.equal(root.querySelector('#edit-body').disabled,true);
  input(root.querySelector('#edit-name'),'Tiempo casa');input(root.querySelector('#edit-title'),'Tiempo');
  input(root.querySelector('#edit-trigger'),'once');
  assert.equal(root.querySelector('#date-field').hidden,false);
  input(root.querySelector('#edit-date'),'2026-11-01');input(root.querySelector('#edit-time'),'07:30');
  root.querySelector('#edit-form').dispatchEvent(new Event('submit',{cancelable:true}));await flush();
  assert.equal(calls.at(-1).rule.date,'2026-11-01');assert.equal(calls.at(-1).rule.time,'07:30');assert.equal(calls.at(-1).rule.body,'');assert.equal(calls.at(-1).rule.enabled,false);
  root.querySelector('#new').click();root.querySelector('#template-notice').click();
  assert.equal(root.querySelector('#state-fields').hidden,false);
  assert.equal(root.querySelector('#edit-entity_id').tagName,'SELECT');
  assert.match(root.querySelector('#edit-entity_id').textContent,/Lavadora/);
  detach(panel);
});
test('slice 4: explicit real test confirmation queues, never claims delivered; pause blocks even open confirmation', async () => {
  let reply=snapshot({rules:[rule()]});const calls=[];
  const panel=panelWith(async req=>{calls.push(req);if(reply instanceof Error)throw reply;return structuredClone(reply);});await flush();const root=panel.shadowRoot;
  root.querySelector('article').click();assert.equal(calls.length,1,'preview does no WS');
  clickLabel(root,'Probar real…');assert.equal(calls.length,1,'confirmation is mandatory');
  assert.match(root.querySelector('#confirm').textContent,/incluso.*deshabilitado/);
  reply=snapshot({rules:[rule()],queued_request_id:'c'.repeat(32),queue_count:1,logs:[{id:'log',status:'queued',name:'Aviso fixture'}]});
  root.querySelector('#confirm-action').click();await flush();
  assert.deepEqual(calls.at(-1),{type:'ha2_notifications/test',rule_id:'a'.repeat(32)});
  assert.match(root.querySelector('#connection').textContent,/encolada/);
  assert.match(root.querySelector('#connection').textContent,/No confirma entrega/);
  assert.match(root.querySelector('#logs').textContent,/En cola/);
  assert.equal(panel.snapshot.revision,4,'activity does not invent a config revision');
  clickLabel(root,'Probar real…');reply=snapshot({paused:true,rules:[rule()]});await panel.refresh();
  const count=calls.length;root.querySelector('#confirm-action').click();await flush();
  assert.equal(calls.length,count,'pause observed after dialog opened blocks sending');
  detach(panel);
});
test('slice 4: unchanged hass state updates do not postpone visible polling forever', async () => {
  const panel=panelWith(async()=>snapshot());await flush();const timer=panel._timer;
  panel.hass={...panel.hass,states:{'sensor.test':{state:'1'}}};
  assert.equal(panel._timer,timer,'unrelated HA updates must not reset polling deadline');
  detach(panel);
});
test('slice 5: off-screen panel stops polling and intersection observer cleans up', async () => {
  let callback,disconnected=false;
  globalThis.IntersectionObserver=class {constructor(fn){callback=fn;}observe(){}disconnect(){disconnected=true;}};
  const calls=[];const panel=panelWith(async req=>{calls.push(req);return snapshot();});await flush();
  assert.equal(typeof callback,'function','panel visibility observer is required');
  callback([{isIntersecting:false}]);assert.equal(env.intervals.size,0);
  await panel.refresh();assert.equal(calls.length,1);
  callback([{isIntersecting:true}]);await flush();assert.equal(calls.length,2);
  detach(panel);assert.equal(disconnected,true);delete globalThis.IntersectionObserver;
});
test('slice 5: disconnected pending mutation must not lock a reattached panel or overwrite a newer snapshot', async () => {
  let resolveSave;const calls=[];
  const panel=panelWith(async req=>{calls.push(req);if(req.type.endsWith('/pause'))return new Promise(r=>resolveSave=r);return snapshot();});await flush();
  input(panel.shadowRoot.querySelector('#pause'),true);await flush();assert.equal(panel._busy,true);
  detach(panel);panel.isConnected=true;panel.connectedCallback();await flush();
  assert.equal(panel._busy,false,'abandoned request must not prevent fresh read');
  assert.equal(calls.at(-1).type,'ha2_notifications/get');
  resolveSave(snapshot({revision:99,paused:true}));await flush();assert.equal(panel.snapshot.revision,4);
  detach(panel);
});
test('slice 6: conflict reload must not discard unsaved edits when get fails', async () => {
  let reject=false;const panel=panelWith(async req=>{if(reject)throw Object.assign(new Error('PRIVATE_LANGUAGE_FAILURE_TOKEN'),{code:req.type.endsWith('/save')?'conflict':'unavailable'});return snapshot({rules:[rule()]});});await flush();const root=panel.shadowRoot;
  clickLabel(root,'Editar');const body=root.querySelector('#edit-body');input(body,'Texto a conservar');reject=true;
  root.querySelector('#edit-form').dispatchEvent(new Event('submit',{cancelable:true}));await flush();
  clickLabel(root,'Recargar aviso (descarta cambios)…');root.querySelector('#confirm-action').click();await flush();
  assert.equal(root.querySelector('#edit-body'),body);
  assert.equal(body.value,'Texto a conservar');assert.equal(panel.editing.revision,4);
  detach(panel);
});
test('slice 6: pending save freezes editor controls to avoid losing post-submit input', async () => {
  let resolve;const panel=panelWith(async req=>req.type.endsWith('/save')?new Promise(r=>resolve=r):snapshot({rules:[rule()]}));await flush();const root=panel.shadowRoot;
  clickLabel(root,'Editar');root.querySelector('#edit-form').dispatchEvent(new Event('submit',{cancelable:true}));await flush();
  assert.equal(root.querySelector('#edit-body').disabled,true);
  assert.equal(root.querySelector('#new').disabled,true);
  resolve(snapshot({rules:[rule()],saved_id:'a'.repeat(32)}));await flush();
  assert.equal(root.querySelector('#edit-body').disabled,false);
  detach(panel);
});

test('regression: UTF8/codepoint and canonical numeric/date/weekly/state boundaries', () => {
  const base=rule();const good=[{title:'😀'.repeat(32)}, {body:'€'.repeat(1365)+'x'}, {expiry_minutes:1,cooldown_seconds:0}, {expiry_minutes:1440,cooldown_seconds:86400}, {trigger:'once',date:'2028-02-29',time:'23:59'}, {trigger:'weekly',days:[0,6],time:'00:00'}, {trigger:'state',entity_id:'sensor.test',to_state:'done',from_state:''}];
  for(const extra of good)assert.deepEqual(mod.validateRule({...base,...extra},[{entity_id:'sensor.test'}]),[],JSON.stringify(extra));
  const bad=[{title:'😀'.repeat(33)}, {body:'€'.repeat(1366)}, {body:'x'.repeat(4001)}, {title:' '}, {body:' '}, {name:'x'.repeat(61)}, {expiry_minutes:0}, {expiry_minutes:1441}, {expiry_minutes:1.5}, {cooldown_seconds:86401}, {trigger:'once',date:'2026-02-29'}, {trigger:'weekly',days:[]}, {trigger:'weekly',days:[1,1]}, {trigger:'weekly',days:[7]}, {trigger:'weekly',time:'24:00'}, {trigger:'state',entity_id:'weather.test',to_state:'done'}, {trigger:'state',entity_id:'sensor.test',to_state:'unknown'}, {trigger:'state',entity_id:'sensor.test',to_state:'on',from_state:'unavailable'}, {mode:'silent'}, {busy:'interrupt'}];
  for(const extra of bad)assert.ok(mod.validateRule({...base,...extra},[{entity_id:'sensor.test'}]).length>0,JSON.stringify(extra));
});
test('regression: selection persists through filter and gets a real fallback after deletion', () => {
  const rules=[rule(),rule({id:'b'.repeat(32),trigger:'weekly'})];
  assert.deepEqual(mod.selectRule(rules,rules[0].id,'schedule'),{visible:[rules[1]],selected:rules[0].id});
  assert.equal(mod.selectRule([rules[1]],rules[0].id).selected,rules[1].id);
  assert.equal(mod.selectRule([],rules[0].id).selected,null);
});
test('regression: toggle, pause and confirmed delete use real WS and complete returned snapshots', async () => {
  const calls=[];let reply=snapshot({rules:[rule()]});
  const panel=panelWith(async req=>{calls.push(req);return structuredClone(reply);});await flush();const root=panel.shadowRoot;
  reply=snapshot({revision:5,rules:[rule({enabled:true})]});clickLabel(root,'Activar');await flush();
  assert.deepEqual(calls.at(-1),{type:'ha2_notifications/toggle',rule_id:'a'.repeat(32),enabled:true,expected_revision:4});
  reply=snapshot({revision:6,paused:true,rules:[rule({enabled:true})]});input(root.querySelector('#pause'),true);await flush();
  assert.deepEqual(calls.at(-1),{type:'ha2_notifications/pause',paused:true,expected_revision:5});assert.equal(root.querySelector('#paused').hidden,false);
  clickLabel(root,'Editar');root.querySelector('#delete').click();const count=calls.length;
  assert.equal(root.querySelector('#confirm').open,true);assert.equal(calls.length,count);
  clickLabel(root,'Cancelar acción');assert.equal(calls.length,count);
  root.querySelector('#delete').click();reply=snapshot({revision:7,paused:true});root.querySelector('#confirm-action').click();await flush();
  assert.deepEqual(calls.at(-1),{type:'ha2_notifications/delete',rule_id:'a'.repeat(32),expected_revision:6});
  assert.equal(root.querySelector('#editor').open,false);assert.match(root.querySelector('#rules').textContent,/Todavía/);
  detach(panel);
});
test('regression: rejected client validation does not write WS or truncate editor input', async () => {
  const calls=[];const panel=panelWith(async req=>{calls.push(req);return snapshot({rules:[rule()]});});await flush();const root=panel.shadowRoot;
  clickLabel(root,'Editar');const body=root.querySelector('#edit-body');input(body,'€'.repeat(1366));
  root.querySelector('#edit-form').dispatchEvent(new Event('submit',{cancelable:true}));await flush();
  assert.equal(calls.length,1);assert.match(root.querySelector('#edit-error').textContent,/4096/);assert.equal(body.value.length,1366);
  detach(panel);
});
test('regression: test queue errors and backend validation never leak raw exception messages', async () => {
  let error=null;const calls=[];const panel=panelWith(async req=>{calls.push(req);if(error)throw error;return snapshot({rules:[rule()]});});await flush();const root=panel.shadowRoot;
  for(const [code,pattern] of [['queue_full',/cola/],['paused',/pausa/i],['unavailable',/disponibles/],['config_error',/configuración/],['unknown_error',/No se pudo confirmar/]]){
    error=Object.assign(new Error('http://secret.invalid/token'),{code});clickLabel(root,'Probar real…');root.querySelector('#confirm-action').click();await flush();
    assert.match(root.querySelector('#connection').textContent,pattern);assert.ok(!root.textContent.includes('secret.invalid'));assert.equal(panel.snapshot.queue_count,0);
  }
  detach(panel);
});
test('regression: full runtime snapshot updates activity without mutating config revision or open form', async () => {
  let reply=snapshot({rules:[rule()]});const panel=panelWith(async()=>structuredClone(reply));await flush();const root=panel.shadowRoot;
  clickLabel(root,'Editar');const title=root.querySelector('#edit-title');input(title,'Título conservado');
  for(const status of ['queued','waiting','delivered','audio_done','night_silent','expired','failed','uncertain','cancelled']){
    reply=snapshot({rules:[rule()],logs:[{id:'log',at:'2026-10-22T10:00:00+01:00',name:'Registro fixture',status,reason:'Motivo seguro'}]});await panel.refresh();
    assert.equal(panel.snapshot.revision,4);assert.equal(panel.editing.revision,4);assert.equal(root.querySelector('#edit-title'),title);assert.equal(title.value,'Título conservado');assert.match(root.querySelector('#logs').textContent,/Registro fixture/);
  }
  assert.match(root.querySelector('#logs').textContent,/Cancelado/);detach(panel);
});
test('regression: stale get cannot overwrite a completed config mutation', async () => {
  let resolveGet;let initial=true;
  const panel=panelWith(async req=>{if(req.type.endsWith('/get')){if(initial){initial=false;return snapshot({rules:[rule()]});}return new Promise(r=>resolveGet=r);}return snapshot({revision:5,paused:true,rules:[rule()]});});await flush();
  const pending=panel.refresh();input(panel.shadowRoot.querySelector('#pause'),true);await flush();assert.equal(panel.snapshot.revision,5);
  resolveGet(snapshot({revision:4}));await pending;assert.equal(panel.snapshot.revision,5);assert.equal(panel.snapshot.paused,true);detach(panel);
});
test('regression: offline/admin state is honest and does not issue writes; reconnect gets real data', async () => {
  const calls=[];const panel=panelWith(async req=>{calls.push(req);return snapshot({target:{name:null,available:null,night_active:null}});});await flush();const root=panel.shadowRoot;
  assert.match(root.querySelector('#system').textContent,/sin identificar/);assert.match(root.querySelector('#system').textContent,/desconocid/);
  panel.hass={...panel.hass,connection:{connected:false}};assert.equal(env.intervals.size,0);assert.match(root.querySelector('#connection').textContent,/desactualizados/);
  input(root.querySelector('#pause'),true);await flush();assert.equal(calls.length,1);
  panel.hass={...panel.hass,connection:{connected:true}};await flush();assert.equal(calls.length,2);
  panel.hass={...panel.hass,user:{is_admin:false}};await panel.refresh();assert.equal(calls.length,2);assert.match(root.querySelector('#connection').textContent,/administradores/);detach(panel);
});
test('regression: labels preserve literal brand, configured timezone and no remote/interpolated HTML production path', async () => {
  const panel=panelWith(async()=>snapshot({rules:[rule({body:'<img src=x onerror=alert(1)>'})]}));await flush();const root=panel.shadowRoot;
  clickLabel(root,'Editar');assert.match(root.querySelector('#editor').textContent,/Atlantic\/Canary/);
  assert.match(root.textContent,/Home Hermes Agent Assitant/);assert.ok(!root.querySelector('img'));
  const source=await readFile(path,'utf8');assert.ok(!/innerHTML|eval\(|new Function|fetch\(|new WebSocket|localStorage|sessionStorage/.test(source));assert.ok(!source.includes('22:00'));detach(panel);
});


test('v013 device gear: localized right-side icon opens the exact registered device',async()=>{
 const calls=[],navigated=[];let resolve;const device='7c8416edc59fa706a331fa7513f37860';
 const panel=panelWith(async req=>{calls.push(req);return req.type==='config/entity_registry/get'?new Promise(r=>resolve=r):snapshot();});await flush();panel._navigateDevice=path=>navigated.push(path);const root=panel.shadowRoot,gear=root.querySelector('#device-info');
 assert.ok(gear,'Gear next to language');assert.equal(gear.parentNode,root.querySelector('#language').parentNode);assert.equal(gear.querySelector('ha-icon').icon,'mdi:cog');assert.equal(gear.getAttribute('aria-label'),'Información del dispositivo');
 gear.click();assert.equal(gear.disabled,true);assert.deepEqual(calls.at(-1),{type:'config/entity_registry/get',entity_id:mod.LANGUAGE_ENTITY});assert.deepEqual(navigated,[]);
 resolve({entity_id:mod.LANGUAGE_ENTITY,device_id:device});await flush();assert.deepEqual(navigated,['/config/devices/device/'+device]);locale(panel,'English');assert.equal(gear.getAttribute('aria-label'),'Device information');detach(panel);
});

test('v013 device gear guards: missing foreign malformed private errors and stale responses never navigate',async()=>{
 let answer={},calls=0,resolve;const paths=[];const panel=panelWith(async req=>{if(req.type==='config/entity_registry/get'){calls++;if(answer instanceof Error)throw answer;if(answer==='pending')return new Promise(r=>resolve=r);return answer;}return snapshot();});await flush();panel._navigateDevice=path=>paths.push(path);
 for(const reply of [{},{entity_id:'select.other',device_id:'a'.repeat(32)},{entity_id:mod.LANGUAGE_ENTITY,device_id:'../bad'},new Error('PRIVATE_DEVICE_TOKEN')]){answer=reply;await panel._openDeviceInfo();assert.deepEqual(paths,[]);assert.match(panel.shadowRoot.querySelector('#connection').textContent,/información del dispositivo/);assert.ok(!panel.shadowRoot.textContent.includes('PRIVATE_DEVICE_TOKEN'));}
 locale(panel,'English');assert.match(panel.shadowRoot.querySelector('#connection').textContent,/device information/);
 const count=calls;panel.hass={...panel.hass,connection:{connected:false}};await panel._openDeviceInfo();assert.equal(calls,count);panel.hass={...panel.hass,connection:{connected:true},user:{is_admin:false}};await panel._openDeviceInfo();assert.equal(calls,count);
 panel.hass={...panel.hass,user:{is_admin:true}};await flush();answer='pending';const pending=panel._openDeviceInfo();detach(panel);resolve({entity_id:mod.LANGUAGE_ENTITY,device_id:'a'.repeat(32)});await pending;assert.deepEqual(paths,[]);
});

test('parent language guard: never write before the panel is connected', async()=>{
 let writes=0;const fresh=new mod.Ha2NotificationsPanel();
 fresh.hass={user:{is_admin:true},connection:{connected:true},callWS:async()=>snapshot(),callService:async()=>writes++,states:{[mod.LANGUAGE_ENTITY]:{state:'Español',attributes:{options:['English','Español']}}}};
 try{await fresh._changeLanguage('English');assert.equal(writes,0);}finally{fresh.disconnectedCallback();}
});

test('language vertical 1: entity authority and external update without writes', async()=>{
 assert.equal(mod.LANGUAGE_ENTITY,'select.xiaozhi_ball_v2_language');
 const panel=panelWith(async()=>snapshot());await flush();const root=panel.shadowRoot;
 assert.equal(root.querySelector('#language').value,'Español');
 panel.hass={...panel.hass,states:{[mod.LANGUAGE_ENTITY]:{state:'English',attributes:{options:['English','Español']}}}};
 assert.equal(root.querySelector('#language').value,'English');assert.equal(root.querySelector('h1').textContent,'Your home, in a Ball.');detach(panel);
});

function locale(panel,state) {panel.hass={...panel.hass,states:{[mod.LANGUAGE_ENTITY]:{state,attributes:{options:['English','Español']}}}};}
test('language vertical 2: service shape, no optimism, ack round-trip and late rejection ignored',async()=>{
 const calls=[];let reject;const panel=panelWith(async()=>snapshot());await flush();const root=panel.shadowRoot;
 panel.hass={...panel.hass,callService:(...args)=>{calls.push(args);return new Promise((_,r)=>reject=r);}};
 input(root.querySelector('#language'),'English');assert.deepEqual(calls,[['select','select_option',{entity_id:mod.LANGUAGE_ENTITY,option:'English'}]]);
 assert.equal(root.querySelector('#language').value,'Español');assert.equal(root.querySelector('#language').disabled,true);
 locale(panel,'English');assert.equal(root.querySelector('#language').value,'English');assert.equal(root.querySelector('#language').disabled,false);
 reject(new Error('PRIVATE_LANGUAGE_FAILURE_TOKEN'));await flush();assert.ok(!root.textContent.includes('PRIVATE_LANGUAGE_FAILURE_TOKEN'));
 panel.hass={...panel.hass,callService:async(...args)=>calls.push(args)};
 input(root.querySelector('#language'),'Español');await flush();assert.equal(root.querySelector('#language').value,'English');assert.equal(root.querySelector('#language').disabled,true);
 locale(panel,'Español');assert.equal(root.querySelector('#language').value,'Español');assert.equal(env.timeouts.size,0);detach(panel);
});
test('language vertical 2: failures timeout detach unavailable and guest guarded',async()=>{
 const panel=panelWith(async()=>snapshot());await flush();const root=panel.shadowRoot;
 panel.hass={...panel.hass,callService:async()=>{throw new Error('PRIVATE_LANGUAGE_FAILURE_TOKEN')}};
 input(root.querySelector('#language'),'English');await flush();assert.equal(root.querySelector('#language').value,'Español');assert.match(root.querySelector('#connection').textContent,/No se pudo cambiar/);assert.ok(!root.textContent.includes('PRIVATE_LANGUAGE_FAILURE_TOKEN'));
 panel.hass={...panel.hass,callService:async()=>{}};input(root.querySelector('#language'),'English');await flush();
 const timer=[...env.timeouts.values()][0];assert.ok(timer.ms>=8000 && timer.ms<=10000);timer.fn();assert.equal(root.querySelector('#language').value,'Español');assert.match(root.querySelector('#connection').textContent,/sin confirmar/);
 input(root.querySelector('#language'),'English');detach(panel);assert.equal(env.timeouts.size,0);
 panel.connectedCallback();await flush();locale(panel,'unavailable');assert.equal(root.querySelector('#language').disabled,true);
 locale(panel,'English');panel.hass={...panel.hass,user:{is_admin:false}};assert.equal(root.querySelector('#language').disabled,true);detach(panel);
});
test('language vertical 3: every editor and confirmation translate in place with literal user data',async()=>{
 const panel=panelWith(async()=>snapshot({rules:[rule({name:'Guardar',title:'Guardar',body:'Guardar'.repeat(700)})]}));await flush();const root=panel.shadowRoot;
 for(const kind of ['weather','reminder','notice','result']){
  locale(panel,'Español');panel.openEditor({...rule({kind,name:'Guardar',title:'Guardar',body:'Guardar'.repeat(700)})});
  const body=root.querySelector('#edit-body'),title=root.querySelector('#edit-title'),form=root.querySelector('#edit-form'),revision=panel.editing.revision;
  locale(panel,'English');assert.equal(root.querySelector('#edit-body'),body);assert.equal(body.value,'Guardar'.repeat(700));assert.equal(title.value,'Guardar');assert.equal(panel.editing.revision,revision);assert.equal(root.querySelector('#save').textContent,'Save');
  assert.ok(form.textContent.includes('Notification name'));assert.equal(root.querySelector('#edit-kind'),null);assert.match(root.querySelector('#editor-heading').textContent,/Edit/);
  locale(panel,'Español');assert.equal(root.querySelector('#save').textContent,'Guardar');assert.equal(root.querySelector('#edit-body'),body);
 }
 panel.testRule(panel.snapshot.rules[0]);const action=root.querySelector('#confirm-action');locale(panel,'English');assert.equal(root.querySelector('#confirm-action'),action);assert.match(root.querySelector('#confirm').textContent,/send to the Ball/);assert.ok(root.querySelector('#confirm').textContent.includes('Guardar'));detach(panel);
});

test('language vertical 4: dynamic schedules system counts days validation and modal messages bilingual',async()=>{
 const panel=panelWith(async()=>snapshot({rules:[rule({trigger:'weekly',days:[0,6]})],entity_options:[{entity_id:'sensor.test',name:'Guardar',state:'Guardar',state_options:['Guardar'],state_options_source:'declared'}],logs:[{id:'log',name:'Guardar',status:'queued'}]}));await flush();const root=panel.shadowRoot;
 panel.openEditor(rule({trigger:'state',entity_id:'sensor.test',to_state:'Guardar'}));const body=root.querySelector('#edit-body');locale(panel,'English');
 assert.match(root.querySelector('#system').textContent,/enabled.*Queue:/);assert.match(root.querySelector('.schedule').textContent,/Monday.*Sunday/);
 assert.match(root.querySelector('#state-help').textContent,/Current state: Guardar/);assert.match(root.querySelector('#text-count').textContent,/Title:/);assert.match(root.querySelector('#logs').textContent,/Guardar.*Queued/);
 assert.equal(root.querySelector('#days-field').querySelectorAll('button')[0].getAttribute('aria-label'),'Monday');
 input(root.querySelector('#edit-title'),'');await panel.saveEditor();assert.match(root.querySelector('#edit-error').textContent,/required field/);locale(panel,'Español');assert.match(root.querySelector('#edit-error').textContent,/campo obligatorio/);assert.equal(root.querySelector('#edit-body'),body);
 panel.deleteEditing();locale(panel,'English');assert.match(root.querySelector('#confirm').textContent,/will be deleted/);detach(panel);
});

test('language vertical 5: reattach enables selector, absent authority defaults English without writes, guards malformed options',async()=>{
 const panel=panelWith(async()=>snapshot());await flush();let writes=0;panel.hass={...panel.hass,callService:async()=>writes++};detach(panel);panel.connectedCallback();await flush();assert.equal(panel.shadowRoot.querySelector('#language').disabled,false);detach(panel);
 const fresh=new mod.Ha2NotificationsPanel();fresh.hass={user:{is_admin:true},connection:{connected:true},callWS:async()=>snapshot(),callService:async()=>writes++};fresh.connectedCallback();await flush();const control=fresh.shadowRoot.querySelector('#language');assert.equal(control.value,'English');assert.equal(control.disabled,true);assert.equal(writes,0);
 locale(fresh,'Español');fresh.hass={...fresh.hass,states:{[mod.LANGUAGE_ENTITY]:{state:'Español',attributes:{options:['Español']}}}};assert.equal(control.disabled,true);await fresh._changeLanguage('English');assert.equal(writes,0);locale(fresh,'unknown');assert.equal(control.value,'Español');detach(fresh);
});

test('language preservation: live draft selection days checkbox preview and activity scroll remain literal',async()=>{
 const panel=panelWith(async()=>snapshot({rules:[rule({name:'Guardar',title:'Guardar',body:'Guardar'})],logs:[{id:'log',name:'Guardar',status:'queued'}]}));await flush();const root=panel.shadowRoot;
 panel.openEditor(rule({trigger:'weekly',name:'Guardar'}));input(root.querySelector('#edit-body'),'Guardar'.repeat(700));input(root.querySelector('#edit-title'),'Guardar');input(root.querySelector('#edit-enabled'),true);
 root.querySelector('#days-field').querySelectorAll('button')[5].click();input(root.querySelector('#edit-mode'),'voice');
 const fields=['name','body','title','enabled','mode'].map(key=>root.querySelector('#edit-'+key));const draft=structuredClone(panel.editing.rule),preview=root.querySelector('#preview').children[0],firstLog=root.querySelector('#logs').children[0];root.querySelector('#logs').scrollTop=123;
 for(const language of ['English','Español','English']){locale(panel,language);assert.deepEqual(panel.editing.rule,draft);assert.equal(panel.editing.revision,4);assert.equal(panel.selected,'a'.repeat(32));assert.equal(root.querySelector('#preview').children[0],preview);assert.equal(root.querySelector('#preview').querySelector('p').textContent,'Guardar');assert.equal(root.querySelector('#logs').children[0],firstLog);assert.equal(root.querySelector('#logs').scrollTop,123);for(let i=0;i<fields.length;i++)assert.equal(root.querySelector('#edit-'+['name','body','title','enabled','mode'][i]),fields[i]);}
 for(const kind of ['weather','reminder','notice','result']){panel.openEditor(mod.newRule(kind),true);assert.match(root.querySelector('#editor-heading').textContent,/^New/);locale(panel,'Español');assert.match(root.querySelector('#editor-heading').textContent,/^Nuev/);locale(panel,'English');assert.equal(root.querySelector('#edit-kind'),null);}detach(panel);
});

test('language guard: malformed options cannot authorize writes or throw',async()=>{
 const panel=panelWith(async()=>snapshot());await flush();let writes=0;
 for(const options of ['EnglishEspañol',{},null]){assert.doesNotThrow(()=>{panel.hass={...panel.hass,callService:async()=>writes++,states:{[mod.LANGUAGE_ENTITY]:{state:'Español',attributes:{options}}}};});assert.equal(panel.shadowRoot.querySelector('#language').disabled,true);await panel._changeLanguage('English');}assert.equal(writes,0);detach(panel);
});
