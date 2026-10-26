/* TEST ONLY: local hass.callWS / hass.callService boundaries. Not an integration/backend simulator.
   Fixed runtime fields and manual outcomes are fixtures, not scheduler/transport logic. */
// TEST ONLY frozen inventory. No live catalogue, execution IDs or task bodies.
const CRON_FIXTURE={revision:7,sources:[{source_instance:'host-fixture',profile:'default',online:true,last_seen:'2026-10-24T10:00:00Z'}],jobs:[
 {job_key:'c'.repeat(32),source_instance:'host-fixture',profile:'default',job_id:'fixture-agent',name:'Tarea Agent FIXTURE',schedule:'0 7 * * 1-5',enabled:true,no_agent:false,delivery:'local',excerpt_available:true,present:true,policy:{enabled:false,content:'brief',mode:'cue',title:''}},
 {job_key:'d'.repeat(32),source_instance:'host-fixture',profile:'default',job_id:'fixture-script',name:'Script FIXTURE',schedule:'every 30m (raw)',enabled:false,no_agent:true,delivery:'local',excerpt_available:false,present:true,policy:{enabled:false,content:'brief',mode:'cue',title:''}}
]};
const FIXTURE_ID='f'.repeat(32);
const emptyFixture=()=>({version:'0.2.0',revision:0,paused:false,rules:[],logs:[],queue_count:0,hermes_cron:structuredClone(CRON_FIXTURE),
  timezone:'Atlantic/Canary',weather_entity:'weather.fixture_no_real',
  target:{name:'Ball FIXTURE (no existe conexión)',available:true,night_active:false,card_active:false,menu_open:false,player_idle:true},
  entity_options:[{entity_id:'sensor.fixture_lavadora',name:'Lavadora FIXTURE',state:'idle',state_options:['idle','running','done'],state_options_source:'declared'},{entity_id:'binary_sensor.fixture_puerta',name:'Puerta FIXTURE',state:'off',state_options:['on','off'],state_options_source:'domain'},{entity_id:'vacuum.fixture_robot',name:'Robot del salón FIXTURE',state:'docked',state_options:['cleaning','docked','returning','idle','paused','error'],state_options_source:'domain'},{entity_id:'number.fixture_umbral',name:'Umbral FIXTURE',state:'21.5',state_options:['21.5'],state_options_source:'current'}],
  capabilities:{voice:true,triggers:['weekly','once','state','manual']}});
let fixtureState=emptyFixture(),nextError=null;
const fixtureCalls=[];
const fixturePanel=document.createElement('ha2-notifications-panel');
const fixtureHass={states:{[LANGUAGE_ENTITY]:{state:'English',attributes:{options:['English','Español']}}},
  // TEST ONLY service boundary: a later hass setter is the confirmation, not this response.
  callService:async(domain,service,data)=>{
    fixtureCalls.push({domain,service,data:structuredClone(data),boundary:'TEST ONLY select service'});
    document.querySelector('#fixture-calls').textContent=JSON.stringify(fixtureCalls,null,2);
    if(domain!=='select' || service!=='select_option' || data.entity_id!==LANGUAGE_ENTITY || !['English','Español'].includes(data.option))throw {code:'invalid_fixture_service'};
    setTimeout(()=>{fixtureHass.states={[LANGUAGE_ENTITY]:{state:data.option,attributes:{options:['English','Español']}}};fixturePanel.hass={...fixtureHass};},250);
  },user:{is_admin:true},connection:{connected:true},callWS:async req=>{
  fixtureCalls.push(structuredClone(req));
  document.querySelector('#fixture-calls').textContent=JSON.stringify(fixtureCalls,null,2);
  const command=req.type.split('/')[1];
  if(command!=='get' && nextError){const code=nextError;nextError=null;throw {code,message:'TEST ONLY boundary rejection'};}
  // Only UI round-trips; no persistence, clock, transport, scheduling or audio.
  if(command==='cron_policy'){
    // TEST ONLY exact UI payload boundary. Never invokes an actual Hermes task.
    if(req.expected_revision!==fixtureState.hermes_cron.revision)throw {code:'conflict'};
    const target=fixtureState.hermes_cron.jobs.find(j=>j.job_key===req.job_key);if(!target)throw {code:'not_found'};
    target.policy={enabled:req.enabled,content:req.content,mode:req.mode,title:req.title};fixtureState.hermes_cron.revision++;
  }
  if(command==='save'){
    const saved={...req.rule,id:req.rule.id || FIXTURE_ID};
    fixtureState.rules=[...fixtureState.rules.filter(r=>r.id!==saved.id),saved];fixtureState.revision++;
    return {...structuredClone(fixtureState),saved_id:saved.id};
  }
  if(command==='delete'){fixtureState.rules=fixtureState.rules.filter(r=>r.id!==req.rule_id);fixtureState.revision++;}
  if(command==='toggle'){fixtureState.rules=fixtureState.rules.map(r=>r.id===req.rule_id?{...r,enabled:req.enabled}:r);fixtureState.revision++;}
  if(command==='pause'){fixtureState.paused=req.paused;fixtureState.revision++;}
  if(command==='test'){
    if(fixtureState.paused)throw {code:'paused'};
    fixtureState.queue_count=1;
    fixtureState.logs=[{id:'fixture-log',at:'FIXTURE · sin reloj real',rule_id:req.rule_id,name:'Petición de prueba FIXTURE',status:'queued',reason:'Respuesta de frontera local, NO ENTREGA REAL'}];
    return {...structuredClone(fixtureState),queued_request_id:'e'.repeat(32)};
  }
  return structuredClone(fixtureState);
}};
fixturePanel.hass=fixtureHass;document.querySelector('#mount').append(fixturePanel);
const fixtureAction=(id,action)=>document.querySelector('#'+id).addEventListener('click',async()=>{action();await fixturePanel.refresh();});
fixtureAction('fixture-empty',()=>{fixtureState=emptyFixture();nextError=null;});
fixtureAction('fixture-cards',()=>{fixtureState=emptyFixture();fixtureState.rules=[
  {...newRule('reminder'),id:'1'.repeat(32),name:'Recordatorio FIXTURE',title:'Recoger el paquete',body:'Texto de revisión visual. No existe una tarea conectada.',trigger:'weekly',enabled:false},
  {...newRule('weather'),id:'2'.repeat(32),name:'Tiempo FIXTURE',title:'Tiempo en casa',enabled:false},
  {...newRule('notice'),id:'3'.repeat(32),name:'Puerta FIXTURE',title:'Puerta abierta',body:'Aviso de prueba visual.',entity_id:'binary_sensor.fixture_puerta',to_state:'on'},
  {...newRule('result'),id:'4'.repeat(32),name:'Resultado manual FIXTURE',title:'Resultado',body:'Sólo bajo petición. No hay tareas Hermes enlazadas.'}
];});
fixtureAction('fixture-logs',()=>{fixtureState.logs=Array.from({length:50},(_,i)=>({id:`fixture-log-${i}`,at:`2026-10-23T10:${String(i).padStart(2,'0')}:00Z`,name:`Actividad FIXTURE ${i}`,status:i%2?'queued':'waiting',reason:'Registro de revisión local; ningún envío real'}));});
fixtureAction('fixture-availability',()=>{fixtureState.target.available=fixtureState.target.available===true?false:fixtureState.target.available===false?null:true;});
fixtureAction('fixture-night',()=>{fixtureState.target.night_active=!fixtureState.target.night_active;});
fixtureAction('fixture-offline',()=>{fixtureHass.connection={connected:!fixtureHass.connection.connected};fixturePanel.hass={...fixtureHass};});
fixtureAction('fixture-conflict',()=>{nextError='conflict';});
fixtureAction('fixture-queue',()=>{nextError='queue_full';});
document.querySelector('#fixture-theme').addEventListener('click',()=>document.body.classList.toggle('dark'));
