/* HA² Notifications 0.2.0 — native Home Assistant custom panel. No external I/O. */
export const LANGUAGE_ENTITY = 'select.xiaozhi_ball_v2_language';
const EN = {
  "MODO BETA": "BETA MODE",
  "Tu casa, en una Bola.": "Your home, in a Ball.",
  "Elige qué quieres recibir, cuándo y cómo. Las reglas para tú Bola se coordinan aquí, en Home Assistant.": "Choose what to receive, when and how. Rules for your Ball are coordinated here, in Home Assistant.",
  "RUYMANIA · NOTIFICACIONES": "RUYMANIA · NOTIFICATIONS",
  "Mostrar los avisos de tipo:": "Show notifications by type:",
  "Filtrar avisos": "Filter notifications",
  "Todos los avisos": "All notifications",
  "Por horario": "By schedule",
  "Por estado": "By state",
  "Bajo petición": "On request",
  "Pausar todos los avisos": "Pause all notifications",
  "+ Nuevo aviso": "+ New notification",
  "Pausa global: se bloquean también las pruebas reales.": "Global pause: real tests are also blocked.",
  "Reglas de notificación": "Notification rules",
  "RECUERDA:": "REMEMBER:",
  "-Durante el modo noche la Ball no mostrará por pantalla los avisos ni audio.": "-During night mode the Ball will not display notifications or play audio.",
  "-El contenido de los avisos puede ser privado. Si la Ball es compartida, elija con cuidado qué se muestra o se lee.": "-Notification content may be private. If the Ball is shared, choose carefully what is displayed or read aloud.",
  "Actividad real": "Real activity",
  "Log de Actividad": "Activity Log",
  "Envíos y ejecuciones hacia la Ball · hasta 200 eventos recientes; no es un historial ilimitado.": "Sends and executions towards the Ball · up to 200 recent events; not an unlimited history.",
  "Proactivo": "Proactive",
  "Invitación a conversar": "Invitation to chat",
  "Origen no disponible (registro anterior)": "Source unavailable (legacy record)",
  "Tipo no disponible": "Type unavailable",
  "Nombre no disponible": "Name unavailable",
  "Resultado no disponible": "Outcome unavailable",
  "Aceptado (no confirma finalización)": "Accepted (does not confirm completion)",
  "Completado": "Completed",
  "No completado": "Not completed",
  "No disponible": "Unavailable",
  "Oportunidad omitida": "Opportunity skipped",
  "Generando invitación": "Generating invitation",
  "Presentando invitación": "Presenting invitation",
  "Oportunidad reservada": "Opportunity claimed",
  "Previsualización orientativa": "Illustrative preview",
  "Así llegaría a la Ball": "How it would appear on the Ball",
  "Aproximación visual · no envía ni reproduce audio": "Visual approximation · does not send or play audio",
  "Acceso reservado a administradores.": "Administrator access only.",
  "Home Assistant desconectado. Los datos visibles pueden estar desactualizados.": "Home Assistant disconnected. Visible data may be outdated.",
  "Cargando configuración real…": "Loading real configuration…",
  "Disponibilidad de la Ball desconocida.": "Ball availability unknown.",
  "Reintentar": "Retry",
  "Pausa global": "Global pause",
  "Desactivar": "Disable",
  "Activar": "Enable",
  "Habilitado": "Enabled",
  "Deshabilitado": "Disabled",
  "Editar": "Edit",
  "Probar real…": "Real test…",
  "No hay avisos en este filtro.": "No notifications match this filter.",
  "Todavía no hay avisos.": "No notifications yet.",
  "Esperando datos reales…": "Waiting for real data…",
  "Crear un aviso": "Create a notification",
  "No se cargan ejemplos.": "No examples are loaded.",
  "Log de Actividad, eventos recientes primero": "Activity Log, newest events first",
  "Aviso": "Notification",
  "Sin actividad registrada. No se ha inventado ninguna entrega.": "No activity recorded. No delivery has been fabricated.",
  "El resumen se generará con los datos meteorológicos HA al enviar.": "The summary will be generated from HA weather data when sent.",
  "Pantalla aproximada: 30 s, independiente de la caducidad del envío. De noche puede recibirse sin pantalla ni audio.": "Approximate display time: 30 s, independent of delivery expiry. At night it may be received without display or audio.",
  "Selecciona un aviso para ver su contenido. Esta vista no envía nada.": "Select a notification to see its content. This view sends nothing.",
  "Nuevo aviso": "New notification",
  "¿Qué quieres recibir?": "What would you like to receive?",
  "Cerrar": "Close",
  "Resumen de los datos meteorológicos HA.": "Summary of HA weather data.",
  "Bajo petición; no conecta tareas automáticamente.": "On request; does not connect tasks automatically.",
  "Transición concreta de una entidad HA.": "Specific state transition of an HA entity.",
  "Una vez o ciertos días de la semana.": "Once or on selected days of the week.",
  "Los nuevos avisos se guardan deshabilitados. Actívalos después desde su tarjeta.": "New notifications are saved disabled. Enable them afterwards from their card.",
  "Editor de aviso": "Notification editor",
  "Confirmación de acción real": "Confirm real action",
  "Nombre del aviso": "Notification name",
  "Cuándo": "When",
  "Semana": "Weekly",
  "Una sola vez": "Once",
  "Cambio de estado HA": "HA state change",
  "Presentación": "Presentation",
  "Texto + tres notas": "Text + three notes",
  "Texto + locución": "Text + speech",
  "Si la Ball está ocupada": "If the Ball is busy",
  "Esperar hasta caducar": "Wait until expiry",
  "Descartar si está ocupada": "Drop if busy",
  "Fecha puntual en la zona HA": "One-off date in the HA timezone",
  "Días de la semana": "Days of the week",
  "Elige una entidad…": "Choose an entity…",
  "Entidad HA (elige del catálogo)": "HA entity (choose from catalog)",
  "Cuando pase al estado": "When it changes to state",
  "Estados sugeridos": "Suggested states",
  "Desde el estado (opcional)": "From state (optional)",
  "Se comprueba una transición real; no se dispara por el estado inicial ni por unknown/unavailable. Escribe el valor exacto de estado, no una plantilla.": "A real transition is checked; the initial state and unknown/unavailable do not trigger it. Enter the exact state value, not a template.",
  "Bajo petición desde el panel o una acción HA. No hay un enlace automático a tareas Hermes.": "On request from the panel or an HA action. There is no automatic link to Hermes tasks.",
  "Título de la tarjeta (32 caracteres / 128 bytes UTF-8)": "Card title (32 characters / 128 UTF-8 bytes)",
  "Texto (4000 caracteres / 4096 bytes UTF-8)": "Text (4000 characters / 4096 UTF-8 bytes)",
  "Caducidad del envío (minutos)": "Delivery expiry (minutes)",
  "Evitar repeticiones (segundos)": "Prevent repeats (seconds)",
  "Caducidad = relevancia en cola, no tiempo en pantalla. La tarjeta permanece unos 30 segundos; el modo noche real puede impedir pantalla y audio. Los horarios se validan en HA, incluidos cambios de hora/DST.": "Expiry = relevance in the queue, not time on screen. The card remains for about 30 seconds; real night mode may prevent display and audio. Schedules are validated in HA, including DST changes.",
  "Se creará deshabilitado; actívalo después en su tarjeta.": "It will be created disabled; enable it afterwards from its card.",
  "Aviso habilitado": "Notification enabled",
  "Privacidad: la Ball es compartida. El texto puede aparecer en pantalla y la locución puede oírse.": "Privacy: the Ball is shared. Text may appear on screen and speech may be heard.",
  "Editar aviso": "Edit notification",
  "Cerrar editor": "Close editor",
  "Borrar…": "Delete…",
  "Cancelar": "Cancel",
  "Guardar": "Save",
  "Estados sugeridos:": "Suggested states:",
  "Sin estados sugeridos; escribe el valor exacto.": "No suggested states; enter the exact value.",
  "Elige una entidad del catálogo HA para ver su estado actual y sus sugerencias. El destino no se rellena automáticamente.": "Choose an entity from the HA catalog to see its current state and suggestions. The target state is not filled automatically.",
  "Recargar aviso (descarta cambios)…": "Reload notification (discard changes)…",
  "Descartar edición": "Discard edits",
  "Se perderán los campos sin guardar. ¿Recargar la versión actual?": "Unsaved fields will be lost. Reload the current version?",
  "No se pudo recargar. Se conserva tu edición; reintenta cuando haya conexión.": "Could not reload. Your edits are preserved; retry when connected.",
  "El aviso ya no existe. Cierra este editor y crea uno nuevo si lo necesitas.": "The notification no longer exists. Close this editor and create another if needed.",
  "Cancelar acción": "Cancel action",
  "Confirmar": "Confirm",
  "Borrar aviso": "Delete notification",
  "Pausa global: las pruebas reales también están bloqueadas.": "Global pause: real tests are also blocked.",
  "Probar real: envío a la Ball": "Real test: send to the Ball",
  "Home Assistant desconectado. Se conserva la edición.": "Home Assistant disconnected. Your edits are preserved.",
  "Configuración guardada en Home Assistant.": "Configuration saved in Home Assistant.",
  "La configuración cambió en otro panel u otra sesión. Se conserva tu edición. Recarga explícitamente antes de volver a guardar.": "Configuration changed in another panel or session. Your edits are preserved. Explicitly reload before saving again.",
  "HA rechazó la regla: revisa límites, entidad, fecha y hora en la zona HA (incluido DST). Se conserva la edición.": "HA rejected the rule: check limits, entity, date and time in the HA timezone (including DST). Your edits are preserved.",
  "El aviso ya no existe. Se conserva la edición.": "The notification no longer exists. Your edits are preserved.",
  "La pausa global bloquea también las pruebas reales.": "Global pause also blocks real tests.",
  "La cola está llena. No se ha confirmado un nuevo envío.": "The queue is full. A new send has not been confirmed.",
  "La Ball o los servicios HA no están disponibles.": "The Ball or HA services are unavailable.",
  "Revisa la configuración real de la integración, destino y voz.": "Check the real integration, target and voice configuration.",
  "No se pudo confirmar la operación. Revisa la conexión y la actividad antes de repetir un envío.": "Could not confirm the operation. Check the connection and activity before sending again.",
  "No se pudo cargar la configuración. Revisa la conexión y reintenta.": "Could not load configuration. Check the connection and retry.",
  "Tiempo": "Weather",
  "Recordatorio": "Reminder",
  "Evento doméstico": "Home event",
  "Resultado manual": "Manual result",
  "Nuevo aviso de Tiempo": "New weather notification",
  "Nuevo recordatorio": "New reminder",
  "Nuevo evento doméstico": "New home event",
  "Nuevo resultado manual": "New manual result",
  "Muestra los datos meteorológicos actuales de Home Assistant al enviar; no inventa un pronóstico.": "Shows current Home Assistant weather data when sent; does not invent a forecast.",
  "Te recuerda algo en una fecha concreta o en los días de la semana que elijas.": "Reminds you on a specific date or on the weekdays you choose.",
  "Avisa al detectar una transición de estado de otro dispositivo de Home Assistant.": "Notifies you when another Home Assistant device changes state.",
  "Muestra un resultado bajo petición; no crea un enlace automático con tareas de Hermes.": "Shows a result on request; does not create an automatic link to Hermes tasks.",
  "En cola": "Queued",
  "Esperando": "Waiting",
  "Recibido por la Ball (no confirma lectura)": "Received by the Ball (does not confirm reading)",
  "Locución finalizada": "Speech finished",
  "Recepción nocturna sin audio": "Night-time reception without audio",
  "Caducado": "Expired",
  "Fallido": "Failed",
  "Entrega incierta: no repetir a ciegas": "Uncertain delivery: do not retry blindly",
  "Cancelado": "Cancelled",
  "Idioma": "Language",
  "Información del dispositivo": "Device information",
  "No se pudo abrir la información del dispositivo. Revisa su registro en Home Assistant.": "Could not open device information. Check its registry entry in Home Assistant.",
  "No se pudo cambiar el idioma. Se mantiene el idioma confirmado.": "Could not change language. The confirmed language is retained.",
  "Cambio de idioma sin confirmar. Se mantiene el idioma real.": "Language change not confirmed. The actual language is retained."
};
export const DAY_NAMES = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'];
export function newRule(kind = 'notice') {
  return {name: '', enabled: false, kind, title: '', body: '', mode: 'cue',
    trigger: kind === 'result' ? 'manual' : kind === 'notice' ? 'state' : 'weekly',
    time: '07:30', days: [0, 1, 2, 3, 4], date: '', entity_id: '', to_state: '',
    from_state: '', expiry_minutes: 30, busy: 'wait', cooldown_seconds: 60};
}
const VALIDATION_EN={"Tipo de aviso no válido.": "Invalid notification type.", "Presentación no válida.": "Invalid presentation.", "Política de ocupación no válida.": "Invalid busy policy.", "Disparador no válido.": "Invalid trigger.", "Hora HH:MM no válida.": "Invalid HH:MM time.", "Selecciona días válidos de la semana.": "Select valid weekdays.", "Fecha puntual no válida.": "Invalid one-off date.", "Selecciona una entidad válida del catálogo HA.": "Select a valid entity from the HA catalog.", "El estado de destino debe ser concreto y disponible.": "The target state must be specific and available.", "Estado de origen no válido.": "Invalid source state.", "Caducidad: entre 1 y 1440 minutos.": "Expiry: between 1 and 1440 minutes.", "Antirrepetición: entre 0 y 86400 segundos.": "Repeat prevention: between 0 and 86400 seconds."};
export function validateRule(r, entities = [], language='Español') {
  const errors = [], bytes = s => new TextEncoder().encode(s).length;
  const text = (key, max, maxBytes, optional = false) => {
    const s = r[key];
    if (typeof s !== 'string' || (!optional && !s.trim())) errors.push(`${key}: campo obligatorio.`);
    else if ([...s].length > max || bytes(s) > maxBytes) errors.push(`${key}: máximo ${max} caracteres / ${maxBytes} bytes UTF-8; no se recorta.`);
  };
  text('name', 60, Infinity); text('title', 32, 128); text('body', 4000, 4096, r.kind === 'weather');
  if (!['reminder','weather','result','notice'].includes(r.kind)) errors.push('Tipo de aviso no válido.');
  if (!['cue','voice'].includes(r.mode)) errors.push('Presentación no válida.');
  if (!['wait','drop'].includes(r.busy)) errors.push('Política de ocupación no válida.');
  if (!['weekly','once','state','manual'].includes(r.trigger)) errors.push('Disparador no válido.');
  if (['weekly','once'].includes(r.trigger) && !/^([01]\d|2[0-3]):[0-5]\d$/.test(r.time)) errors.push('Hora HH:MM no válida.');
  if (r.trigger === 'weekly' && (!Array.isArray(r.days) || !r.days.length || new Set(r.days).size !== r.days.length || r.days.some(d => !Number.isInteger(d) || d < 0 || d > 6))) errors.push('Selecciona días válidos de la semana.');
  if (r.trigger === 'once') {
    const date = typeof r.date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(r.date) ? new Date(`${r.date}T12:00:00Z`) : null;
    if (!date || !Number.isFinite(date.getTime()) || date.toISOString().slice(0,10) !== r.date) errors.push('Fecha puntual no válida.');
  }
  if (r.trigger === 'state') {
    if (!entities.some(e => e.entity_id === r.entity_id)) errors.push('Selecciona una entidad válida del catálogo HA.');
    if (typeof r.to_state !== 'string' || !r.to_state.trim() || ['unknown','unavailable'].includes(r.to_state.trim())) errors.push('El estado de destino debe ser concreto y disponible.');
    if (typeof r.from_state !== 'string' || ['unknown','unavailable'].includes(r.from_state.trim())) errors.push('Estado de origen no válido.');
  }
  if (!Number.isInteger(r.expiry_minutes) || r.expiry_minutes < 1 || r.expiry_minutes > 1440) errors.push('Caducidad: entre 1 y 1440 minutos.');
  if (!Number.isInteger(r.cooldown_seconds) || r.cooldown_seconds < 0 || r.cooldown_seconds > 86400) errors.push('Antirrepetición: entre 0 y 86400 segundos.');
  if(language==='English')return errors.map(error=>{
    const required=error.match(/^(\w+): campo obligatorio\.$/);if(required)return `${required[1]}: required field.`;
    const limit=error.match(/^(\w+): máximo (.+) caracteres \/ (.+) bytes UTF-8; no se recorta\.$/);if(limit)return `${limit[1]}: maximum ${limit[2]} characters / ${limit[3]} UTF-8 bytes; never truncated.`;
    return VALIDATION_EN[error] || error;
  });
  return errors;
}

function node(tag, props = {}, ...children) {
  const element = document.createElement(tag);
  for (const [key,value] of Object.entries(props)) {
    if(value===undefined)continue;
    if(value?.ha2UI){value.owner._bind(element,key,value.read);continue;}
    if (key.startsWith('on')) element.addEventListener(key.slice(2), value);
    else if (key === 'class' || key.startsWith('aria-') || key.startsWith('data-')) element.setAttribute(key,value);
    else element[key] = value;
  }
  for(const child of children.filter(c=>c!==null && c!==undefined)) {
    if(child?.ha2UI){const text=document.createTextNode('');child.owner._bind(text,'textContent',child.read);element.append(text);}else element.append(child);
  }
  return element;
}
function button(label, action, props = {}) {return node('button',{type:'button',onclick:action,...props},label);}
const MODE = r => r.mode === 'voice' ? 'Texto + locución' : 'Texto + tres notas';
const KINDS = {weather:'Tiempo',reminder:'Recordatorio',notice:'Evento doméstico',result:'Resultado manual'};
const NEW_TITLES = {weather:'Nuevo aviso de Tiempo',reminder:'Nuevo recordatorio',notice:'Nuevo evento doméstico',result:'Nuevo resultado manual'};
const DESCRIPTIONS = {weather:'Muestra los datos meteorológicos actuales de Home Assistant al enviar; no inventa un pronóstico.',reminder:'Te recuerda algo en una fecha concreta o en los días de la semana que elijas.',notice:'Avisa al detectar una transición de estado de otro dispositivo de Home Assistant.',result:'Muestra un resultado bajo petición; no crea un enlace automático con tareas de Hermes.'};
const STATUS = {queued:'En cola',waiting:'Esperando',delivered:'Recibido por la Ball (no confirma lectura)',audio_done:'Locución finalizada',night_silent:'Recepción nocturna sin audio',expired:'Caducado',failed:'Fallido',uncertain:'Entrega incierta: no repetir a ciegas',cancelled:'Cancelado',accepted:'Aceptado (no confirma finalización)',completed:'Completado',not_completed:'No completado',skipped:'Oportunidad omitida',generating:'Generando invitación',presenting:'Presentando invitación',claimed:'Oportunidad reservada'};
const EN_DAYS=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
export function whenRule(r,zone='Zona HA',language='Español') {
  const en=language==='English';
  if (r.trigger === 'manual') return en?'On request · no automatic link to Hermes tasks':'Bajo petición · sin enlace automático a tareas Hermes';
  if (r.trigger === 'state') return `${r.entity_id}: ${r.from_state || (en?'any valid state':'cualquier estado válido')} → ${r.to_state}`;
  return `${r.trigger === 'once' ? r.date : r.days.map(d => (en?EN_DAYS:DAY_NAMES)[d]).join(' · ')} · ${r.time} · ${zone}`;
}
export function selectRule(rules,selected,filter='all') {
  const visible = rules.filter(r => filter === 'all' || (filter === 'schedule' ? ['weekly','once'].includes(r.trigger) : r.trigger === filter));
  return {visible,selected:rules.some(r => r.id === selected) ? selected : (visible[0]?.id ?? rules[0]?.id ?? null)};
}
const CSS = `
.beta-badge{display:inline-block;background:#ffca28;color:#241a00;border:2px solid #795000;border-radius:6px;padding:5px 10px;margin:8px 0;font-size:12px;font-weight:900;letter-spacing:.08em}
#real-activity{margin-top:24px}.accordion{margin-top:24px}.accordion h2{margin:0}.accordion h2 button{width:100%;text-align:left;font-weight:700;font-size:inherit;padding:16px}.accordion h2 button::after{content:'+';float:right}.accordion h2 button[aria-expanded=true]::after{content:'−'}.accordion [role=region]{padding-top:16px}#panel-version{letter-spacing:normal;font-size:12px}
#hermes-cron{margin-top:24px}#ha-heading{margin-top:24px}.cron-job{border:1px solid var(--edge);border-radius:16px;background:var(--surface);padding:18px;margin:12px 0;overflow-wrap:anywhere}.cron-job .actions{margin-top:12px}.cron-job input[type=checkbox]{width:auto;min-height:24px}.cron-job p[role=status]{margin-top:10px}.cron-job h3{font-size:16px}
#proactive-enabled{appearance:none;-webkit-appearance:none;position:relative;display:inline-block;flex:none;width:44px;height:24px;min-height:24px;padding:0;margin:0;border:1px solid var(--edge);border-radius:99px;background:var(--muted);cursor:pointer;vertical-align:middle}#proactive-enabled::before{content:'';position:absolute;left:2px;top:2px;width:18px;height:18px;border-radius:50%;background:var(--surface)}#proactive-enabled:checked{background:var(--tone)}#proactive-enabled:checked::before{left:22px}#proactive-enabled:focus-visible{outline:2px solid var(--tone);outline-offset:3px}
#device-info{display:inline-flex;align-items:center;justify-content:center;padding:8px}#device-info ha-icon{display:inline-flex;width:24px;height:24px}
#language{min-width:120px}.language-control{margin-left:auto;display:flex;align-items:center;gap:8px}
#pause{appearance:none;-webkit-appearance:none;position:relative;display:inline-block;flex:none;width:44px;height:24px;min-height:24px;padding:0;margin:0;border:1px solid var(--edge);border-radius:99px;background:var(--muted);cursor:pointer;vertical-align:middle;transition:background .15s}#pause::before{content:'';position:absolute;left:2px;top:2px;width:18px;height:18px;border-radius:50%;background:var(--surface);transition:left .15s}#pause:checked{background:var(--tone)}#pause:checked::before{left:calc(100% - 20px)}#pause:disabled{opacity:.5;cursor:not-allowed}
#logs{max-height:360px;overflow-y:auto;overscroll-behavior:contain;scrollbar-gutter:stable}#logs .log{min-height:96px;display:grid;grid-template-columns:minmax(125px,.8fr) minmax(0,1.5fr) minmax(0,1.3fr);gap:6px 16px;align-items:start;overflow-wrap:anywhere}#logs .log>*{min-width:0}#logs .log-time{grid-column:1/-1;font-variant-numeric:tabular-nums}#logs .log-source{color:var(--tone)}@media(max-width:650px){#logs .log{grid-template-columns:minmax(0,1fr);gap:5px}#logs .log-time{grid-column:auto}}.card{cursor:pointer}.card:focus-visible{outline:2px solid var(--tone);outline-offset:3px}.card .source{display:block;margin-top:10px}#remember ul{list-style:none;margin:0;padding:0}#remember li+li{margin-top:8px}
:host{display:block;color:var(--primary-text-color,#20252c);background:var(--primary-background-color,#f5f7f9);font:14px/1.5 system-ui,-apple-system,sans-serif;--edge:var(--divider-color,#dde2e8);--surface:var(--card-background-color,#fff);--tone:var(--primary-color,#087f8c);--muted:var(--secondary-text-color,#657281);--soft:color-mix(in srgb,var(--tone) 9%,var(--surface))}
*{box-sizing:border-box}[hidden]{display:none!important}button,input,textarea,select{font:inherit;color:inherit}button{cursor:pointer;border:1px solid var(--edge);border-radius:10px;padding:8px 12px;background:var(--surface)}button:hover{border-color:var(--tone);background:var(--soft)}button:disabled{opacity:.5;cursor:not-allowed}button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:2px solid var(--tone);outline-offset:3px}.primary{background:var(--tone);color:var(--text-primary-color,#fff);font-weight:700}.app{max-width:1200px;margin:auto;padding:26px}.brand,.row,.toolbar,.actions{display:flex;gap:12px;align-items:center;flex-wrap:wrap}.brandmark{font-size:34px;font-weight:850;letter-spacing:-2px}.brand small{display:block;font-size:10px;letter-spacing:1.5px}.muted,small{color:var(--muted)}h1{font-size:clamp(26px,3vw,36px);letter-spacing:-1px;margin:26px 0 5px}h2{font-size:18px;margin:0 0 12px}h3,p{margin:0 0 8px}.toolbar{justify-content:space-between;margin:22px 0}.workspace{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:20px;align-items:start}.rules{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.card,.pane,.activity,.empty{border:1px solid var(--edge);border-radius:16px;background:var(--surface);padding:18px}.card.selected{border-color:var(--tone);box-shadow:0 0 0 1px var(--tone)}.card h3{font-size:16px;overflow-wrap:anywhere}.card .actions{gap:7px;margin-top:12px}.card button{font-size:12px;padding:6px 9px}.schedule{margin-top:12px;color:var(--muted);font-size:12px;overflow-wrap:anywhere}.badge{display:inline-block;background:var(--soft);padding:3px 9px;border-radius:99px;font-size:11px}.empty{grid-column:1/-1;padding:35px;text-align:center}.notice{background:var(--soft);border-left:3px solid var(--tone);padding:12px;margin:15px 0}.error{border-left-color:var(--error-color,#ba1a1a)}.system{margin-top:15px;color:var(--muted)}.ball{width:245px;height:245px;max-width:100%;border-radius:50%;background:#101b24;color:#f2f5f9;margin:18px auto;padding:40px 30px;text-align:center;display:flex;flex-direction:column;justify-content:center;overflow:hidden;box-shadow:inset 0 0 0 5px #2c3945}.ball b{font-size:17px;line-height:1.2;overflow-wrap:anywhere}.ball p{font-size:12px;white-space:pre-wrap;overflow:hidden;overflow-wrap:anywhere;display:-webkit-box;-webkit-line-clamp:5;-webkit-box-orient:vertical}.ball small{font-size:10px;color:#b7d3d9}.activity{margin-top:18px}.log{padding:10px 0;border-bottom:1px solid var(--edge);overflow-wrap:anywhere}.log small{display:block}.footnote{font-size:12px;color:var(--muted);margin-top:15px}dialog{color:inherit;background:var(--surface);border:1px solid var(--edge);border-radius:18px;max-width:720px;width:calc(100% - 24px);max-height:90vh;padding:22px}dialog::backdrop{background:#0008}.dialog-head{display:flex;justify-content:space-between;align-items:center;gap:15px;margin-bottom:15px}.form-grid,.templates{display:grid;grid-template-columns:1fr 1fr;gap:15px}.field{display:flex;flex-direction:column;gap:5px}.wide{grid-column:1/-1}input,select,textarea{width:100%;min-width:0;background:var(--surface);border:1px solid var(--edge);border-radius:8px;padding:9px}input[type=checkbox]{width:auto}.check{display:flex;gap:8px;align-items:center}.days{display:flex;flex-wrap:wrap;gap:6px}.days button[aria-pressed=true]{background:var(--tone);color:var(--text-primary-color,#fff)}textarea{min-height:110px;resize:vertical}.template{text-align:left;padding:20px}.template strong,.template small{display:block}.dialog-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:20px}.status{white-space:pre-wrap}.pane{position:sticky;top:15px}
@media(max-width:900px){.rules{grid-template-columns:1fr}.workspace{grid-template-columns:minmax(0,1fr) 280px}}@media(max-width:650px){.app{padding:16px}.workspace{grid-template-columns:1fr}.pane{position:static}.form-grid,.templates{grid-template-columns:1fr}.wide{grid-column:auto}.toolbar .actions{width:100%}dialog{padding:16px}.brand strong{font-size:12px}}
`;

export class Ha2NotificationsPanel extends HTMLElement {
  constructor() {
    super();this.attachShadow({mode:'open'});this.snapshot=null;this.selected=null;this.filter='all';this._busy=false;this._active=false;this._serial=0;this._timer=null;this._message='';
    this._language='English';this._bindings=new Set();this._languageSerial=0;this._deviceSerial=0;this._deviceBusy=false;
    this._visibility=()=>{this._syncTimer();if(document.visibilityState==='visible')this.refresh();};
  }
  _both(es,en) {return this._ui(()=>this._language==='English'?en():es());}
  _day(d) {return (this._language==='English'?EN_DAYS:DAY_NAMES)[d];}
  _tr(es) {return this._language==='Español'?es:(EN[es] ?? es);}
  _ui(value) {return {ha2UI:true,owner:this,read:typeof value==='function'?value:()=>this._tr(value),toString(){return this.read();}};}
  _bind(element,key,read) {const update=()=>{const value=read();if(key.startsWith('aria-'))element.setAttribute(key,value);else element[key]=value;};for(const old of this._bindings)if(old.element===element && old.key===key)this._bindings.delete(old);this._bindings.add({element,key,update});update();}
  _setUI(element,value) {element.replaceChildren();const text=document.createTextNode('');element.append(text);this._bind(text,'textContent',value.read);}
  _syncLanguage() {
    const state=this._hass?.states?.[LANGUAGE_ENTITY]?.state;
    if(['English','Español'].includes(state))this._language=state;
    if(this._languagePending && state===this._languagePending.option){this._clearLanguage();this._languageMessage=null;}
    if(!this._online() && this._languagePending)this._clearLanguage();
    if(this._bindings)for(const binding of this._bindings){let parent=binding.element;while(parent && parent!==this.shadowRoot)parent=parent.parentNode;if(parent===this.shadowRoot)binding.update();else this._bindings.delete(binding);}
    this._renderLanguage();
  }
  _renderLanguage() {const control=this.$('language');if(!control)return;const entity=this._hass?.states?.[LANGUAGE_ENTITY];control.value=['English','Español'].includes(entity?.state)?entity.state:this._language;control.disabled=!!this._languagePending || !this._active || !this._online() || this._hass?.user?.is_admin!==true || typeof this._hass?.callService!=='function' || !['English','Español'].includes(entity?.state) || !Array.isArray(entity?.attributes?.options) || !['English','Español'].every(v=>entity.attributes.options.includes(v));}
  _clearLanguage() {clearTimeout(this._languageTimeout);this._languageTimeout=null;this._languagePending=null;this._languageSerial++;this._renderLanguage();}
  async _changeLanguage(option) {
    this._renderLanguage();if(!this._active || !this.$('language') || this.$('language').disabled || !['English','Español'].includes(option) || option===this._language)return;
    const serial=++this._languageSerial;this._languagePending={option,serial};this._languageMessage=null;this._renderLanguage();
    this._languageTimeout=setTimeout(()=>{if(!this._active || serial!==this._languageSerial)return;this._clearLanguage();this._languageMessage=this._ui('Cambio de idioma sin confirmar. Se mantiene el idioma real.');this._renderStatus();},9000);
    try {await this._hass.callService('select','select_option',{entity_id:LANGUAGE_ENTITY,option});}
    catch(error) {if(!this._active || serial!==this._languageSerial)return;this._clearLanguage();this._languageMessage=this._ui('No se pudo cambiar el idioma. Se mantiene el idioma confirmado.');this._renderStatus();}
  }
  set hass(value) {
    const wasOnline=this._online();const oldConnection=this._hass?.connection;this._hass=value;this._syncLanguage();
    if(this._active){this._renderStatus();if(this._online() && (!wasOnline || oldConnection!==value?.connection || !this.snapshot))this.refresh();this._syncTimer();}
  }
  get hass() {return this._hass;}
  _renderDeviceInfo() {const gear=this.$('device-info');if(gear)gear.disabled=!this._active || !this._online() || this._hass?.user?.is_admin!==true || this._deviceBusy;}
  _navigateDevice(path) {window.location.assign(path);}
  async _openDeviceInfo() {
    this._renderDeviceInfo();if(!this.$('device-info') || this.$('device-info').disabled)return;
    const serial=++this._deviceSerial,connection=this._hass.connection;this._deviceBusy=true;this._renderDeviceInfo();
    try {
      const entry=await this._hass.callWS({type:'config/entity_registry/get',entity_id:LANGUAGE_ENTITY});
      if(!this._active || serial!==this._deviceSerial || connection!==this._hass.connection)return;
      if(entry?.entity_id!==LANGUAGE_ENTITY || typeof entry.device_id!=='string' || !/^[a-f0-9]{32}$/i.test(entry.device_id))throw new Error('Invalid device registry entry');
      this._navigateDevice('/config/devices/device/'+encodeURIComponent(entry.device_id));
    } catch(error) {
      if(this._active && serial===this._deviceSerial){this._message=this._ui('No se pudo abrir la información del dispositivo. Revisa su registro en Home Assistant.');this._renderStatus();}
    } finally {if(serial===this._deviceSerial){this._deviceBusy=false;this._renderDeviceInfo();}}
  }
  _online() {return !!this._hass?.callWS && this._hass.connection?.connected !== false && this._hass.user?.is_admin !== false;}
  connectedCallback() {
    if(this._active)return;this._active=true;this._panelVisible=true;this._build();this._syncLanguage();
    if(typeof IntersectionObserver!=='undefined'){
      this._observer=new IntersectionObserver(entries=>{const visible=entries.some(e=>e.isIntersecting);const changed=visible!==this._panelVisible;this._panelVisible=visible;this._syncTimer();if(changed && visible)this.refresh();});
      this._observer.observe(this);
    }
    document.addEventListener('visibilitychange',this._visibility);this._syncTimer();this.refresh();
  }
  disconnectedCallback() {
    this._active=false;this._clearLanguage();this._serial++;this._loading=false;this._busy=false;this._deviceSerial++;this._deviceBusy=false;this._renderDeviceInfo();
    this._observer?.disconnect();this._observer=null;this._freezeEditor(false);
    clearInterval(this._timer);this._timer=null;document.removeEventListener('visibilitychange',this._visibility);
  }
  _syncTimer() {
    const shouldPoll=this._active && document.visibilityState==='visible' && this._panelVisible!==false && this._online();
    if(!shouldPoll){clearInterval(this._timer);this._timer=null;}
    else if(this._timer===null)this._timer=setInterval(()=>this.refresh(),4500);
  }
  $(id) {return this.shadowRoot.querySelector(`#${id}`);}
  // List-backed exclusive group follows the visual HA → cron → proactive order.
  _accordion(id,sectionId,headingId,label,...children) {
    this._accordions ??= [];
    const content=node('div',{id:id+'-content',hidden:true,role:'region','aria-labelledby':headingId},...children);
    const toggle=button(label,()=>{
      const opening=content.hidden;
      for(const item of this._accordions){item.content.hidden=item.content!==content || !opening;item.toggle.setAttribute('aria-expanded',String(!item.content.hidden));}
    },{id:id+'-toggle','aria-expanded':'false','aria-controls':content.id,onkeydown:e=>{
      const index=this._accordions.findIndex(item=>item.toggle===e.currentTarget),length=this._accordions.length;
      const next=e.key==='ArrowDown'?(index+1)%length:e.key==='ArrowUp'?(index+length-1)%length:e.key==='Home'?0:e.key==='End'?length-1:null;
      if(next!==null){e.preventDefault();this._accordions[next].toggle.focus();}
    }});
    this._accordions.push({toggle,content});
    return node('section',{id:sectionId,class:'accordion','aria-labelledby':headingId},node('h2',{id:headingId},toggle),content);
  }
  _buildProactive() {
    const label=(es,en)=>this._both(()=>es,()=>en);
    this._proactiveNodes={};
    const field=(key,id,es,en,options)=>{
      const checkbox=['enabled','all_day'].includes(key);
      const change=e=>{if(!this._proactive)return;this._proactive.draft[key]=checkbox?e.target.checked:key==='interval_minutes'?Number(e.target.value):e.target.value;this._renderProactive();};
      const control=options?node('select',{id,onchange:change},...options.map(([value,text])=>node('option',{value:String(value)},text))):node('input',{id,type:checkbox?'checkbox':'time',oninput:change});
      if(key==='enabled'){control.role='switch';control.setAttribute('role','switch');}
      this._proactiveNodes[key]=control;
      return node('label',{class:checkbox?'check':'field',htmlFor:id},label(es,en),control,key==='enabled'?node('span',{id:'proactive-onoff'},'Off'):null);
    };
    const intervals=Array.from({length:48},(_,i)=>{const m=(i+1)*30;return [m,label(m<60?`${m} min`:`${Math.floor(m/60)} h${m%60?' 30 min':''}`,m<60?`${m} min`:`${Math.floor(m/60)} h${m%60?' 30 min':''}`)];});
    return this._accordion('proactive','proactive','proactive-heading',label('Modo Proactivo','Proactive mode'),
      node('p',{class:'muted'},label('Invitaciones para charlar con Hermes. El modo noche y la pausa global tienen prioridad. No se guardan como tarjetas; las conversaciones conservan su historial habitual.','Invitations to chat with Hermes. Night mode and global pause take priority. Not saved as cards; conversations retain their usual history.')),
      node('p',{id:'proactive-status',role:'status','aria-live':'polite'}),
      node('form',{id:'proactive-form',onsubmit:e=>{e.preventDefault();this._saveProactive();}},
        node('div',{class:'form-grid'},field('enabled','proactive-enabled','Activado','Enabled'),field('all_day','proactive-all-day','Todo el día','All day'),field('start','proactive-start','Desde','From'),field('end','proactive-end','Hasta','Until'),field('interval_minutes','proactive-interval','Intervalo orientativo','Approximate interval',intervals),field('mode','proactive-mode','Presentación','Presentation',[['cue',label('Texto + tres notas','Text + three notes')],['voice',label('Texto + locución','Text + speech')]])),
        node('p',{class:'muted'},label('La ejecución es aleatoria: por ejemplo, 45–75 minutos al elegir 1 hora; se omiten oportunidades fuera de horario, de noche o si la Ball está ocupada. Al terminar el mensaje, la Ball pasa a escucha nativa con los tiempos normales de la canalización, sin una duración fija de escucha.','Timing is random: for example, 45–75 minutes when selecting 1 hour; opportunities outside the window, at night or while the Ball is busy are skipped. Once the message ends, the Ball enters native listening using the pipeline’s normal timings, with no fixed listening duration.')),
        node('div',{class:'actions'},button(label('Guardar','Save'),()=>this._saveProactive(),{id:'proactive-save',class:'primary'}),button(label('Restablecer borrador','Reset draft'),()=>this._resetProactive(),{id:'proactive-reset'})),node('p',{id:'proactive-feedback',role:'status','aria-live':'polite'})));
  }
  _proactiveConfigValid(c) {
    const time=v=>typeof v==='string' && /^(?:[01]\d|2[0-3]):[0-5]\d$/.test(v);
    return c && typeBoolean(c.enabled) && typeBoolean(c.all_day) && time(c.start) && time(c.end) && (c.all_day || c.start!==c.end) && Number.isInteger(c.interval_minutes) && c.interval_minutes>=30 && c.interval_minutes<=1440 && c.interval_minutes%30===0 && ['cue','voice'].includes(c.mode);
    function typeBoolean(value){return typeof value==='boolean';}
  }
  _proactiveAllowed() {return this._active && this._online() && this._hass?.user?.is_admin===true && !this._busy && !!this.snapshot?.proactive;}
  _proactiveReady() {const c=this.snapshot?.proactive?.capabilities;return !!c && ['full_agent','session_binding','transcript_only','native_listen'].every(k=>c[k]===true);}
  _renderProactive() {
    if(!this.$('proactive-status'))return;
    const dto=this.snapshot?.proactive;
    if(dto && !this._proactive && Number.isInteger(dto.revision) && this._proactiveConfigValid(dto.config)){
      this._proactive={revision:dto.revision,draft:{...dto.config},message:null};
      for(const [key,control] of Object.entries(this._proactiveNodes)){if(['enabled','all_day'].includes(key))control.checked=this._proactive.draft[key];else control.value=String(this._proactive.draft[key]);}
    }
    const allowed=this._proactiveAllowed() && !!this._proactive;
    for(const control of Object.values(this._proactiveNodes || {}))control.disabled=!allowed;
    const draft=this._proactive?.draft;
    for(const key of ['start','end'])if(this._proactiveNodes?.[key])this._proactiveNodes[key].disabled=!allowed || draft?.all_day===true;
    this.$('proactive-save').disabled=!allowed;
    this.$('proactive-reset').disabled=!allowed;
    this.$('proactive-onoff').textContent=draft?.enabled?'On':'Off';
    const text=!dto?this._both(()=>'Configuración proactiva no disponible.',()=>'Proactive configuration unavailable.'):!this._proactiveReady()?this._both(()=>'Activación bloqueada: faltan comprobaciones de conversación, audio o escucha. Puedes preparar la configuración desactivada.',()=>'Activation blocked: conversation, audio or listening checks are incomplete. You can prepare disabled settings.'):dto.config?.enabled?this._both(()=>'Activado · se respetan el modo noche y la disponibilidad de la Ball.',()=>'Enabled · night mode and Ball availability are respected.'):this._both(()=>'Desactivado. Guardar opciones no envía ninguna prueba.',()=>'Disabled. Saving settings does not send a test.');
    this._setUI(this.$('proactive-status'),text);
    this._setUI(this.$('proactive-feedback'),this._proactive?.message || this._both(()=>' ',()=>' '));
  }
  _resetProactive() {
    if(!this._proactiveAllowed())return;
    this._proactive=null;this._renderProactive();
  }
  async _saveProactive() {
    if(!this._proactiveAllowed() || !this._proactive)return;
    const config={...this._proactive.draft};
    if(!this._proactiveConfigValid(config) || (config.enabled && !this._proactiveReady())){
      this._proactive.message=this._both(()=>'Revisa las horas, el intervalo y las comprobaciones de disponibilidad antes de activar.',()=>'Check the time window, interval and readiness checks before enabling.');this._renderProactive();return;
    }
    const serial=++this._serial,connection=this._hass.connection;this._loading=false;this._busy=true;this._proactive.message=null;this._freezeEditor(true);this._renderStatus();
    try {
      const reply=await this._hass.callWS({type:'ha2_notifications/proactive_config',expected_revision:this._proactive.revision,config});
      if(!this._active || serial!==this._serial || connection!==this._hass.connection)return;
      if(!Number.isInteger(reply?.proactive?.revision) || !this._proactiveConfigValid(reply.proactive.config))throw new Error('Invalid proactive snapshot');
      this.snapshot=reply;this._proactive.revision=reply.proactive.revision;this._proactive.draft={...reply.proactive.config};
      for(const [key,control] of Object.entries(this._proactiveNodes)){if(['enabled','all_day'].includes(key))control.checked=this._proactive.draft[key];else control.value=String(this._proactive.draft[key]);}
      this._proactive.message=this._both(()=>'Configuración guardada. No se ha enviado ningún mensaje de prueba.',()=>'Settings saved. No test message was sent.');
    }catch(error){
      if(!this._active || serial!==this._serial)return;
      this._proactive.message=error?.code==='conflict'?this._both(()=>'La configuración cambió en otra sesión. Borrador conservado; restablece explícitamente para recuperar la revisión actual.',()=>'Settings changed in another session. Draft preserved; explicitly reset to capture the current revision.'):this._both(()=>'No se pudo guardar. Se conserva el borrador; revisa la conexión y las opciones.',()=>'Could not save. Draft preserved; check the connection and options.');
    }finally{if(serial===this._serial){this._busy=false;this._freezeEditor(false);if(this._active)this._renderRuntime();}}
  }
  _build() {
    if(this.$('app'))return;
    const main=node('main',{id:'app',class:'app'},
      node('header',{class:'brand'},node('span',{class:'brandmark'},'HA²'),node('div',{},node('strong',{},'Home Hermes Agent Assitant'),node('small',{id:'panel-version'},this._both(()=>`Versión del panel: ${this.snapshot?.version || '—'}`,()=>`Panel version: ${this.snapshot?.version || '—'}`)),node('small',{},this._ui("RUYMANIA · NOTIFICACIONES"))),node('div',{class:'language-control'},node('label',{htmlFor:'language'},this._ui('Idioma')),node('select',{id:'language','aria-label':this._ui('Idioma'),onchange:e=>this._changeLanguage(e.target.value)},node('option',{value:'English'},'English'),node('option',{value:'Español'},'Español')),button(node('ha-icon',{icon:'mdi:cog'}),()=>this._openDeviceInfo(),{id:'device-info',title:this._ui('Información del dispositivo'),'aria-label':this._ui('Información del dispositivo')}))),
      node('h1',{},this._ui("Tu casa, en una Bola.")),node('p',{class:'muted'},this._ui("Elige qué quieres recibir, cuándo y cómo. Las reglas para tú Bola se coordinan aquí, en Home Assistant.")),
      node('div',{id:'system',class:'system'}),node('div',{id:'connection',class:'notice status',role:'status','aria-live':'polite'}),
      this._accordion('ha','ha-notifications','ha-heading',this._both(()=>'Avisos programados en Home Assistant',()=>'Scheduled notifications in Home Assistant'),
      node('div',{class:'toolbar'},node('div',{class:'actions'},node('label',{id:'filter-label',htmlFor:'filter'},this._ui("Mostrar los avisos de tipo:")),node('select',{id:'filter','aria-label':this._ui("Filtrar avisos"),onchange:e=>{this.filter=e.target.value;this._renderRules();}},...Object.entries({all:this._ui("Todos los avisos"),schedule:this._ui("Por horario"),state:this._ui("Por estado"),manual:this._ui("Bajo petición")}).map(([value,label])=>node('option',{value},label))),node('label',{class:'check'},this._ui("Pausar todos los avisos"),node('input',{id:'pause',type:'checkbox',role:'switch',onchange:e=>this.pause(e.target.checked)}),node('span',{id:'pause-value'},'Off'))),button(this._ui("+ Nuevo aviso"),()=>this.$('templates').showModal(),{class:'primary',id:'new'})),
      node('div',{id:'paused',class:'notice',hidden:true},this._ui("Pausa global: se bloquean también las pruebas reales.")),
      node('div',{class:'workspace'},node('section',{'aria-label':this._ui("Reglas de notificación")},node('div',{id:'rules',class:'rules'}),node('section',{id:'remember',class:'notice','aria-label':this._ui("RECUERDA:")},node('h2',{},this._ui("RECUERDA:")),node('ul',{},node('li',{},this._ui("-Durante el modo noche la Ball no mostrará por pantalla los avisos ni audio.")),node('li',{},this._ui("-El contenido de los avisos puede ser privado. Si la Ball es compartida, elija con cuidado qué se muestra o se lee."))))),node('aside',{class:'pane','aria-label':this._ui("Previsualización orientativa")},node('h2',{},this._ui("Así llegaría a la Ball")),node('small',{},this._ui("Aproximación visual · no envía ni reproduce audio")),node('div',{id:'preview'})))),
      this._accordion('cron','hermes-cron','cron-heading',this._both(()=>'Notificación de Tareas programadas en Hermes Agent',()=>'Hermes Agent scheduled task notifications'),node('p',{class:'muted'},this._both(()=>'Avisar en HA² no pausa ni activa la tarea original en Hermes. La pausa global también bloquea estos avisos.',()=>'Notifying in HA² does not pause or activate the original Hermes task. Global pause also blocks these notifications.')),node('div',{id:'cron-catalog'})),
      this._buildProactive(),
      node('section',{id:'real-activity',class:'activity','aria-labelledby':'activity-heading'},node('h2',{id:'activity-heading'},this._ui('Log de Actividad')),node('p',{class:'muted'},this._ui('Envíos y ejecuciones hacia la Ball · hasta 200 eventos recientes; no es un historial ilimitado.')),node('div',{id:'logs'}))
    );
    this.shadowRoot.append(node('style',{},CSS),main);
    this._buildDialogs();this._renderRuntime();this._renderLanguage();
  }
  _renderStatus() {
    this._renderDeviceInfo();this._renderCron();this._renderProactive();
    if(!this.$('connection'))return;
    const target=this.snapshot?.target;
    const text=this._hass?.user?.is_admin===false ? this._ui("Acceso reservado a administradores.") : !this._online() ? this._ui("Home Assistant desconectado. Los datos visibles pueden estar desactualizados.") : this._languageMessage || this._message || (!this.snapshot ? this._ui("Cargando configuración real…") : target?.available===true && target.name ? this._both(()=>`${target.name} está conectado a Home Assistant.`,()=>`${target.name} is connected to Home Assistant.`) : target?.available===false ? this._both(()=>`${target.name || 'La Ball'} no está disponible en Home Assistant.`,()=>`${target.name || 'The Ball'} is unavailable in Home Assistant.`) : this._ui("Disponibilidad de la Ball desconocida."));
    this.$('connection').replaceChildren(node('span',{},text));
    if(this._message || !this._online())this.$('connection').append(button(this._ui("Reintentar"),()=>this.refresh()));
    if(this.$('pause')){this.$('pause').disabled=this._busy || !this.snapshot || !this._online();this.$('pause').checked=this.snapshot?.paused===true;this.$('pause-value').textContent=this.snapshot?.paused?'On':'Off';}
    if(this.$('new'))this.$('new').disabled=this._busy || !this.snapshot || !this._online();
  }
  _renderRuntime() {
    this._renderStatus();const s=this.snapshot;
    this._setUI(this.$('panel-version'),this._both(()=>`Versión del panel: ${this.snapshot?.version || '—'}`,()=>`Panel version: ${this.snapshot?.version || '—'}`));
    this._setUI(this.$('system'),this._both(()=>s ? `${s.rules.filter(r=>r.enabled).length} habilitados · ${s.rules.length} avisos · Cola: ${s.queue_count} · Destino: ${s.target?.name || 'sin identificar'} · ${s.target?.available===true?'disponible':s.target?.available===false?'no disponible':'disponibilidad desconocida'} · Modo noche: ${s.target?.night_active===true?'activo':s.target?.night_active===false?'inactivo':'desconocido'} · Zona HA: ${s.timezone || 'sin informar'} · Tiempo: ${s.weather_entity || 'sin configurar'}` : 'Disponibilidad, destino y modo noche aún no consultados.',()=>s ? `${s.rules.filter(r=>r.enabled).length} enabled · ${s.rules.length} notifications · Queue: ${s.queue_count} · Target: ${s.target?.name || 'unidentified'} · ${s.target?.available===true?'available':s.target?.available===false?'unavailable':'availability unknown'} · Night mode: ${s.target?.night_active===true?'active':s.target?.night_active===false?'inactive':'unknown'} · HA timezone: ${s.timezone || 'not reported'} · Weather: ${s.weather_entity || 'not configured'}` : 'Availability, target and night mode not yet queried.'));
    this.$('paused').hidden=!s?.paused;
    this._renderRules();this._renderLogs();this._renderPreview();
  }
  _cronSource(job) {return this.snapshot?.hermes_cron?.sources?.find(s=>s.source_instance===job.source_instance && s.profile===job.profile);}
  _cronAllowed(row) {return this._active && this._online() && this._hass?.user?.is_admin===true && !this._busy && !!this.snapshot?.hermes_cron && row.job.present===true && this._cronSource(row.job)?.online===true;}
  _renderCron() {
    const region=this.$('cron-catalog');if(!region)return;
    this._cronRows ??= new Map();const dto=this.snapshot?.hermes_cron;
    if(!dto){region.replaceChildren(node('p',{class:'muted'},this._both(()=>'Sin catálogo de Hermes. Opciones no disponibles.',()=>'No Hermes catalog. Options unavailable.')));return;}
    const seen=new Set();
    for(const job of dto.jobs || []){
      seen.add(job.job_key);let row=this._cronRows.get(job.job_key);
      if(!row){
        row={job,draft:{...job.policy},revision:dto.revision,message:'',nodes:{}};this._cronRows.set(job.job_key,row);
        const id=name=>'cron-'+job.job_key+'-'+name;
        const label=(es,en)=>this._both(()=>es,()=>en);
        const control=(name,es,en,options)=>{
          const el=options?node('select',{id:id(name),onchange:e=>row.draft[name]=e.target.value},...options.map(([value,es,en])=>node('option',{value},label(es,en)))):node('input',{id:id(name),type:name==='enabled'?'checkbox':'text',oninput:e=>row.draft[name]=name==='enabled'?e.target.checked:e.target.value});
          if(name==='enabled')el.checked=row.draft[name]===true;else el.value=row.draft[name];row.nodes[name]=el;
          return node('label',{class:name==='enabled'?'check':'field'},label(es,en),el);
        };
        row.heading=node('h3',{});row.metadata=node('p',{class:'muted'});row.state=node('p',{id:id('state')});row.source=node('p',{});
        row.feedback=node('p',{id:id('feedback'),role:'status','aria-live':'polite'});
        row.save=button(this._ui('Guardar'),()=>this._saveCron(job.job_key),{id:id('save'),class:'primary'});
        row.reset=button(label('Restablecer desde catálogo (descarta cambios)','Reset from catalog (discard changes)'),()=>this._resetCron(job.job_key),{id:id('reset')});
        row.element=node('form',{class:'cron-job',id:id('form'),'aria-labelledby':id('name'),onsubmit:e=>{e.preventDefault();this._saveCron(job.job_key);}},row.heading,row.metadata,row.state,row.source,
          node('div',{class:'form-grid'},control('enabled','Avisar en HA²','Notify in HA²'),control('content','Contenido','Content',[['brief','Resumen breve','Brief summary'],['excerpt','Extracto del resultado','Result excerpt']]),control('mode','Presentación','Presentation',[['cue','Texto + tres notas','Text + three notes'],['voice','Texto + locución','Text + speech']]),control('title','Título corto opcional (32 caracteres / 128 bytes UTF-8)','Optional short title (32 characters / 128 UTF-8 bytes)')),node('div',{class:'actions'},row.save,row.reset),row.feedback);
        row.heading.id=id('name');
      }
      row.job=job;
    }
    for(const [key,row] of this._cronRows){
      if(!seen.has(key))row.job={...row.job,present:false};
      const job=row.job,source=this._cronSource(job);
      row.heading.textContent=job.name;row.metadata.textContent=job.profile+' · '+job.source_instance+' · '+job.schedule;
      this._setUI(row.state,this._both(()=>job.present===false?'Tarea ausente del catálogo':job.enabled?'Cron activo en Hermes':'Cron pausado en Hermes',()=>job.present===false?'Task missing from catalog':job.enabled?'Cron active in Hermes':'Cron paused in Hermes'));
      this._setUI(row.source,this._both(()=>`${source?.online===true?'Fuente en línea':source?.online===false?'Fuente sin conexión':'Conexión de fuente desconocida'} · Última señal: ${source?.last_seen || 'desconocida'}`,()=>`${source?.online===true?'Source online':source?.online===false?'Source offline':'Source connection unknown'} · Last seen: ${source?.last_seen || 'unknown'}`));
      const disabled=!this._cronAllowed(row);for(const control of Object.values(row.nodes))control.disabled=disabled;
      [...row.nodes.content.querySelectorAll('option')].find(o=>o.value==='excerpt').disabled=!job.excerpt_available;
      row.save.disabled=disabled;row.reset.disabled=disabled || !seen.has(key);
      this._setUI(row.feedback,this._ui(()=>row.message?this._language==='English'?row.message.en:row.message.es:''));
    }
    const elements=[...this._cronRows.values()].map(r=>r.element);
    // Reuse every form/control; no per-poll subtree replacement or focus loss.
    if(elements.length!==region.children.length || elements.some((el,i)=>region.children[i]!==el))region.replaceChildren(...elements);
    if(!elements.length)region.replaceChildren(node('p',{},this._both(()=>'Sin tareas en el catálogo de Hermes.',()=>'No tasks in the Hermes catalog.')));
  }
  _resetCron(key) {
    const row=this._cronRows?.get(key),dto=this.snapshot?.hermes_cron,job=dto?.jobs?.find(j=>j.job_key===key);
    if(!row || !job || !this._cronAllowed(row))return;
    row.draft={...job.policy};row.revision=dto.revision;row.message='';
    for(const [name,el] of Object.entries(row.nodes)){if(name==='enabled')el.checked=row.draft.enabled===true;else el.value=row.draft[name];}
    this._renderCron();
  }
  async _saveCron(key) {
    const row=this._cronRows?.get(key);if(!row || !this._cronAllowed(row))return;
    const {enabled,content,mode,title}=row.draft;
    if(typeof enabled!=='boolean' || !['brief','excerpt'].includes(content) || (content==='excerpt' && !row.job.excerpt_available) || !['cue','voice'].includes(mode) || typeof title!=='string' || [...title].length>32 || new TextEncoder().encode(title).length>128){
      row.message={es:'Revisa contenido, presentación y título (32 caracteres / 128 bytes UTF-8). No se recorta.',en:'Check content, presentation and title (32 characters / 128 UTF-8 bytes). Never truncated.'};this._renderCron();return;
    }
    const serial=++this._serial,connection=this._hass.connection;this._loading=false;this._busy=true;row.message='';this._freezeEditor(true);this._renderStatus();
    try {
      const snapshot=await this._hass.callWS({type:'ha2_notifications/cron_policy',job_key:key,expected_revision:row.revision,enabled,content,mode,title});
      if(!this._active || serial!==this._serial || connection!==this._hass.connection)return;
      this.snapshot=snapshot;row.message={es:'Preferencia guardada en Home Assistant. No cambia la tarea original. Restablece para capturar la nueva revisión.',en:'Preference saved in Home Assistant. The original task is unchanged. Reset to capture the new revision.'};
    } catch(error) {
      if(!this._active || serial!==this._serial)return;
      const messages={
        conflict:{es:'La configuración cambió en otro panel u otra sesión. Borrador conservado; restablece explícitamente antes de reintentar.',en:'Configuration changed in another panel or another session. Draft preserved; explicitly reset before retrying.'},
        not_found:{es:'La tarea ya no está disponible. Se conserva el borrador.',en:'The task is no longer available. Draft preserved.'},
        unauthorized:{es:'Acceso reservado a administradores. Se conserva el borrador.',en:'Administrator access only. Draft preserved.'},
        unavailable:{es:'Servicio no disponible. Se conserva el borrador; reintenta con conexión.',en:'Service unavailable. Draft preserved; retry when connected.'}
      };
      row.message=messages[error?.code] || {es:'No se pudo guardar. Se conserva el borrador; revisa la conexión y reintenta.',en:'Could not save. Draft preserved; check the connection and retry.'};
    } finally {
      if(serial===this._serial){this._busy=false;this._freezeEditor(false);if(this._active)this._renderRuntime();}
    }
  }
  _renderRules() {
    const {visible,selected}=selectRule(this.snapshot?.rules || [],this.selected,this.filter);this.selected=selected;
    const choose=id=>{this.selected=id;for(const card of this.$('rules').querySelectorAll('article')){card.classList.toggle('selected',card.getAttribute('data-rule-id')===id);card.setAttribute('aria-pressed',String(card.getAttribute('data-rule-id')===id));}this._renderPreview();};
    const action=fn=>e=>{e.stopPropagation();fn();};
    this.$('rules').replaceChildren(...visible.map(r=>node('article',{class:`card${r.id===selected?' selected':''}`,tabIndex:0,role:'button','aria-label':this._both(()=>`Previsualizar ${r.name}`,()=>`Preview ${r.name}`),'aria-pressed':String(r.id===selected),'data-rule-id':r.id,onclick:()=>choose(r.id),onkeydown:e=>{if(e.target===e.currentTarget && ['Enter',' '].includes(e.key)){e.preventDefault();choose(r.id);}}},
      node('h3',{},r.name),this.snapshot.paused?node('p',{class:'badge'},this._ui("Pausa global")):null,
      button(r.enabled?this._ui("Desactivar"):this._ui("Activar"),action(()=>this.toggle(r)),{disabled:this._busy || !this._online(),'aria-label':this._ui(()=>`${this._tr(r.enabled?'Desactivar':'Activar')} ${r.name}`)}),
      node('small',{class:'source'},r.kind==='weather'?this._both(()=>`Home Assistant · ${this.snapshot.weather_entity || 'tiempo no configurado'}`,()=>`Home Assistant · ${this.snapshot.weather_entity || 'weather not configured'}`):r.trigger==='state'?`Home Assistant · ${r.entity_id}`:this._ui(()=> 'Home Assistant · '+this._tr(KINDS[r.kind]))),
      node('p',{class:'schedule'},this._ui(()=>`${this._language==='English'?'Runs:':'Se ejecuta:'} ${whenRule(r,this.snapshot.timezone,this._language)}`)),node('p',{},this._ui(()=>this._tr(r.mode==='voice'?'Texto + locución':'Texto + tres notas'))),node('span',{class:'badge'},r.enabled?this._ui("Habilitado"):this._ui("Deshabilitado")),
      node('div',{class:'actions'},button(this._ui("Editar"),action(()=>this.openEditor(r)),{disabled:this._busy || !this._online()}),button(this._ui("Probar real…"),action(()=>this.testRule(r)),{disabled:this._busy || !this._online() || this.snapshot.paused})))));
    if(!visible.length)this.$('rules').append(node('div',{class:'empty'},node('h2',{},this.snapshot?.rules.length?this._ui("No hay avisos en este filtro."):this.snapshot?this._ui("Todavía no hay avisos."):this._ui("Esperando datos reales…")),this.snapshot?button(this._ui("Crear un aviso"),()=>this.$('templates').showModal(),{class:'primary'}):node('small',{},this._ui("No se cargan ejemplos."))));
  }
  _activityTime(at) {
    // Never interpret a legacy naive time in the browser's local timezone.
    const fallback=()=>`${at || (this._language==='English'?'Time unavailable':'Hora no disponible')} · ${this._language==='English'?'HA date/time or timezone unavailable':'Fecha/hora o zona HA no disponible'}`;
    if(typeof at!=='string' || !/(?:Z|[+-]\d{2}:\d{2})$/i.test(at) || !Number.isFinite(Date.parse(at)) || !this.snapshot?.timezone)return fallback();
    try {
      const value=new Intl.DateTimeFormat(this._language==='English'?'en-US':'es-ES',{timeZone:this.snapshot.timezone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23',timeZoneName:'longOffset'}).format(new Date(at));
      return `${value} · ${this.snapshot.timezone}`;
    }catch{return fallback();}
  }
  _renderLogs() {
    const region=this.$('logs');region.role='region';region.tabIndex=0;this._bind(region,'aria-label',()=>this._tr('Log de Actividad, eventos recientes primero'));
    const logs=[...(this.snapshot?.logs || [])].sort((a,b)=>(Date.parse(b.at)||0)-(Date.parse(a.at)||0));
    const key=JSON.stringify([this.snapshot?.timezone,logs]);if(key===this._logsKey)return;
    const top=region.scrollTop || 0;const cache=new Map();
    const children=logs.map((l,index)=>{const id=l.id ?? String(index),signature=JSON.stringify([this.snapshot?.timezone,l]),old=this._logNodes?.get(id);
      const element=old?.signature===signature?old.element:node('div',{class:'log'},node('strong',{class:'log-source'},this._ui(()=>this._tr(({home_assistant:'Home Assistant',hermes_cron:'Hermes cron',proactive:'Proactivo'})[l.source] || (['job_key','job_id'].some(key=>typeof l.origin?.[key]==='string' && l.origin[key].trim())?'Hermes cron':'Origen no disponible (registro anterior)')))),node('span',{class:'log-task'},this._ui(()=>`${this._tr(l.kind==='proactive'?'Invitación a conversar':KINDS[l.kind] || 'Tipo no disponible')} — ${l.name || this._tr('Nombre no disponible')}`)),node('span',{class:'log-result'},this._ui(()=>`${STATUS[l.status]?this._tr(STATUS[l.status]):l.status || this._tr('Resultado no disponible')}${l.reason?' · '+(l.reason==='not_completed'?this._tr('No completado'):l.reason==='unavailable'?this._tr('No disponible'):l.reason):''}`)),node('small',{class:'log-time'},this._ui(()=>this._activityTime(l.at))));
      cache.set(id,{signature,element});return element;});
    region.replaceChildren(...children);if(!logs.length)region.append(node('small',{},this._ui("Sin actividad registrada. No se ha inventado ninguna entrega.")));
    region.scrollTop=top;this._logNodes=cache;this._logsKey=key;
  }
  _renderPreview() {
    const r=this.snapshot?.rules.find(r=>r.id===this.selected);
    this.$('preview').replaceChildren(r?node('div',{},node('div',{class:'ball'},node('small',{},this._ui(()=>this._tr(KINDS[r.kind]))),node('b',{},r.title),node('p',{},r.kind==='weather'?this._ui("El resumen se generará con los datos meteorológicos HA al enviar."):r.body)),node('strong',{},r.name),node('p',{class:'muted'},this._ui(()=>this._tr(r.mode==='voice'?'Texto + locución':'Texto + tres notas'))),node('p',{class:'footnote'},this._ui("Pantalla aproximada: 30 s, independiente de la caducidad del envío. De noche puede recibirse sin pantalla ni audio."))):node('p',{class:'muted'},this._ui("Selecciona un aviso para ver su contenido. Esta vista no envía nada.")));
  }
  _buildDialogs() {
    const templates=node('dialog',{id:'templates','aria-label':this._ui("Nuevo aviso")},node('div',{class:'dialog-head'},node('h2',{},this._ui("¿Qué quieres recibir?")),button(this._ui("Cerrar"),()=>this.$('templates').close())),node('div',{class:'templates'},...Object.entries(KINDS).map(([kind,label])=>button('',()=>{this.$('templates').close();this.openEditor(newRule(kind),true);},{id:`template-${kind}`,class:'template'}))));
    for(const [kind,label] of Object.entries(KINDS))templates.querySelector(`#template-${kind}`).append(node('strong',{},this._ui(()=>this._tr(label))),node('small',{},kind==='weather'?this._ui("Resumen de los datos meteorológicos HA."):kind==='result'?this._ui("Bajo petición; no conecta tareas automáticamente."):kind==='notice'?this._ui("Transición concreta de una entidad HA."):this._ui("Una vez o ciertos días de la semana.")));
    templates.querySelector('#template-notice').append(node('span',{class:'beta-badge'},this._ui('MODO BETA')));
    templates.append(node('p',{class:'footnote'},this._ui("Los nuevos avisos se guardan deshabilitados. Actívalos después desde su tarjeta.")));
    this.shadowRoot.append(templates,node('dialog',{id:'editor','aria-label':this._ui("Editor de aviso")}),node('dialog',{id:'confirm','aria-label':this._ui("Confirmación de acción real")}));
  }
  openEditor(rule,isNew=false) {
    if(!this.snapshot)return;
    this.editing={rule:structuredClone(rule),revision:this.snapshot.revision,isNew};
    const r=this.editing.rule, grid=node('div',{class:'form-grid'});
    const field=(key,label,type='text',props={})=>{
      const input=node(type==='textarea'?'textarea':'input',{id:`edit-${key}`,type:type==='textarea'?undefined:type,value:r[key] ?? '',...props,oninput:e=>{
        r[key]=type==='number'?(e.target.value===''?NaN:Number(e.target.value)):e.target.value;
        if(key==='body' || key==='title')this._updateCounts();
      }});
      return node('label',{class:`field ${['name','title','body'].includes(key)?'wide':''}`},label,input);
    };
    const select=(key,label,options)=>{
      const control=node('select',{id:`edit-${key}`,onchange:e=>{r[key]=e.target.value;this._editorConditionals();}},...Object.entries(options).map(([value,text])=>node('option',{value,disabled:key==='mode' && value==='voice' && this.snapshot.capabilities?.voice===false},text)));
      control.value=r[key];return node('label',{class:'field'},label,control);
    };
    grid.append(field('name',this._ui("Nombre del aviso")),select('trigger',this._ui("Cuándo"),{weekly:this._ui("Semana"),once:this._ui("Una sola vez"),state:this._ui("Cambio de estado HA"),manual:this._ui("Bajo petición")}),select('mode',this._ui("Presentación"),{cue:this._ui("Texto + tres notas"),voice:this._ui("Texto + locución")}),select('busy',this._ui("Si la Ball está ocupada"),{wait:this._ui("Esperar hasta caducar"),drop:this._ui("Descartar si está ocupada")}));
    const time=field('time',this._both(()=>`Hora en ${this.snapshot.timezone || 'la zona HA (sin informar)'}`,()=>`Time in ${this.snapshot.timezone || 'the HA timezone (not reported)'}`),'time');time.id='time-field';
    const date=field('date',this._ui("Fecha puntual en la zona HA"),'date');date.id='date-field';
    const days=node('div',{id:'days-field',class:'field wide'},node('span',{},this._ui("Días de la semana")),node('div',{class:'days'},...DAY_NAMES.map((name,d)=>button(this._ui(()=>this._day(d).slice(0,2)),e=>{
      r.days=r.days.includes(d)?r.days.filter(v=>v!==d):[...r.days,d].sort();e.target.setAttribute('aria-pressed',String(r.days.includes(d)));
    },{'aria-label':this._ui(()=>this._day(d)),'aria-pressed':String(r.days.includes(d))}))));
    const entityChoices={'':this._ui("Elige una entidad…"),...Object.fromEntries((this.snapshot.entity_options || []).map(e=>[e.entity_id,`${e.name || e.entity_id} · ${e.entity_id}`]))};
    const state=node('div',{id:'state-fields',class:'wide form-grid'},select('entity_id',this._ui("Entidad HA (elige del catálogo)"),entityChoices),field('to_state',this._ui("Cuando pase al estado"),'text',{'aria-describedby':'state-help'}),node('datalist',{id:'state-options'}),node('div',{id:'state-suggestions',class:'wide row','aria-label':this._ui("Estados sugeridos")}),node('small',{id:'state-help',class:'wide'}),field('from_state',this._ui("Desde el estado (opcional)")),node('small',{class:'wide'},this._ui("Se comprueba una transición real; no se dispara por el estado inicial ni por unknown/unavailable. Escribe el valor exacto de estado, no una plantilla.")));
    state.querySelector('#edit-to_state').setAttribute('list','state-options');
    grid.append(time,date,days,state,node('p',{id:'manual-note',class:'wide notice'},this._ui("Bajo petición desde el panel o una acción HA. No hay un enlace automático a tareas Hermes.")),field('title',this._ui("Título de la tarjeta (32 caracteres / 128 bytes UTF-8)")),field('body',this._ui("Texto (4000 caracteres / 4096 bytes UTF-8)"),'textarea'),node('small',{id:'text-count',class:'wide'}),node('p',{id:'weather-note',class:'wide notice'},this._both(()=>`Texto automático: se genera al enviar con ${this.snapshot.weather_entity || 'la entidad meteorológica HA configurada'} y sus unidades reales. No se inventa un pronóstico.`,()=>`Automatic text: generated when sent using ${this.snapshot.weather_entity || 'the configured HA weather entity'} and its real units. No forecast is invented.`)),field('expiry_minutes',this._ui("Caducidad del envío (minutos)"),'number',{min:1,max:1440,step:1}),field('cooldown_seconds',this._ui("Evitar repeticiones (segundos)"),'number',{min:0,max:86400,step:1}),node('p',{class:'wide footnote'},this._ui("Caducidad = relevancia en cola, no tiempo en pantalla. La tarjeta permanece unos 30 segundos; el modo noche real puede impedir pantalla y audio. Los horarios se validan en HA, incluidos cambios de hora/DST.")),node('label',{class:'check wide'},node('input',{id:'edit-enabled',type:'checkbox',checked:r.enabled,disabled:isNew,onchange:e=>r.enabled=e.target.checked}),isNew?this._ui("Se creará deshabilitado; actívalo después en su tarjeta."):this._ui("Aviso habilitado")),node('p',{class:'wide footnote'},this._ui("Privacidad: la Ball es compartida. El texto puede aparecer en pantalla y la locución puede oírse.")));
    const form=node('form',{id:'edit-form',onsubmit:e=>{e.preventDefault();this.saveEditor();}},node('div',{class:'dialog-head'},node('h2',{id:'editor-heading'},this._ui(()=>this._tr(isNew?NEW_TITLES[r.kind]:'Editar aviso'))),button(this._ui("Cerrar editor"),()=>this.$('editor').close())),node('p',{id:'kind-description',class:'notice'},this._ui(()=>this._tr(DESCRIPTIONS[r.kind]))),node('span',{id:'editor-beta',class:'beta-badge'},this._ui('MODO BETA')),grid,node('div',{id:'edit-error',class:'notice error status',role:'alert',hidden:true}),node('div',{class:'dialog-actions'},!isNew?button(this._ui("Borrar…"),()=>this.deleteEditing(),{id:'delete'}):null,button(this._ui("Cancelar"),()=>this.$('editor').close()),node('button',{id:'save',class:'primary',type:'submit'},this._ui("Guardar"))));
    this.$('editor').replaceChildren(form);this._editorConditionals();this._updateCounts();this.$('editor').showModal();this.$('edit-name').focus();
  }
  _editorConditionals() {
    const r=this.editing?.rule;if(!r || !this.$('edit-form'))return;
    this._setUI(this.$('editor-heading'),this._ui(()=>this.editing.isNew?this._tr(NEW_TITLES[r.kind]):this._language==='English'?`Edit ${this._tr(KINDS[r.kind])} notification`:`Editar aviso de ${KINDS[r.kind]}`));
    this._setUI(this.$('kind-description'),this._ui(()=>this._tr(DESCRIPTIONS[r.kind])));
    this.$('editor-beta').hidden=r.trigger!=='state';
    this._stateSuggestions();
    this.$('time-field').hidden=!['weekly','once'].includes(r.trigger);this.$('date-field').hidden=r.trigger!=='once';this.$('days-field').hidden=r.trigger!=='weekly';this.$('state-fields').hidden=r.trigger!=='state';this.$('manual-note').hidden=r.trigger!=='manual';
    const weather=r.kind==='weather';this.$('edit-body').disabled=weather;this.$('weather-note').hidden=!weather;
    this._updateCounts();
  }
  _updateCounts() {
    const r=this.editing?.rule;if(!r || !this.$('text-count'))return;
    const bytes=v=>new TextEncoder().encode(v).length;
    this._setUI(this.$('text-count'),this._both(()=>`Título: ${[...r.title].length}/32 caracteres · ${bytes(r.title)}/128 bytes. Texto: ${[...r.body].length}/4000 caracteres · ${bytes(r.body)}/4096 bytes. No se recorta.`,()=>`Title: ${[...r.title].length}/32 characters · ${bytes(r.title)}/128 bytes. Text: ${[...r.body].length}/4000 characters · ${bytes(r.body)}/4096 bytes. Never truncated.`));
  }
  _stateSuggestions() {
    const r=this.editing?.rule,entity=this.snapshot?.entity_options?.find(e=>e.entity_id===r?.entity_id);
    const values=[...new Set((entity?.state_options || []).filter(v=>typeof v==='string' && v.trim() && !['unknown','unavailable'].includes(v.trim())))];
    this.$('state-options').replaceChildren(...values.map(value=>node('option',{value},value)));
    this.$('state-suggestions').replaceChildren(node('span',{},values.length?this._ui("Estados sugeridos:"):this._ui("Sin estados sugeridos; escribe el valor exacto.")),...values.map(value=>button(value,()=>{r.to_state=value;this.$('edit-to_state').value=value;this.$('edit-to_state').focus();})));
    const sources={declared:'opciones declaradas por la entidad',domain:'opciones del tipo de dispositivo',current:'solo el estado actual, no una enumeración completa'};
    this._setUI(this.$('state-help'),this._both(()=>entity?`Estado actual: ${entity.state ?? 'sin informar'}. Sugerencias: ${sources[entity.state_options_source] || 'sin fuente informada'}. Usa valores exactos como on y off, sin traducir ni cambiar mayúsculas. Para números u otros estados puedes escribir tu propio valor.`:'Elige una entidad del catálogo HA para ver su estado actual y sus sugerencias. El destino no se rellena automáticamente.',()=>entity?`Current state: ${entity.state ?? 'not reported'}. Suggestions: ${{declared:'options declared by the entity',domain:'device domain options',current:'only the current state, not a complete enumeration'}[entity.state_options_source] || 'source not reported'}. Use exact values such as on and off, without translating or changing case. For numbers or other states you can enter your own value.`:'Choose an entity from the HA catalog to see its current state and suggestions. The target state is not filled automatically.'));
  }
  _editorError(message,conflict=false) {
    if(!this.$('edit-error'))return;
    this.$('edit-error').hidden=false;this.$('edit-error').replaceChildren(node('span',{},message));
    if(conflict)this.$('edit-error').append(button(this._ui("Recargar aviso (descarta cambios)…"),()=>this._confirm(this._ui("Descartar edición"), this._ui("Se perderán los campos sin guardar. ¿Recargar la versión actual?"),async()=>{
      const refreshed=await this.refresh();if(!refreshed){this._editorError(this._ui("No se pudo recargar. Se conserva tu edición; reintenta cuando haya conexión."));return;}
      const current=refreshed.rules.find(r=>r.id===this.editing.rule.id);
      if(current)this.openEditor(current);else this._editorError(this._ui("El aviso ya no existe. Cierra este editor y crea uno nuevo si lo necesitas."));
    })));
  }
  async saveEditor() {
    if(!this.editing || this._busy)return;
    const {rule,revision,isNew}=this.editing;const payload=structuredClone(rule);
    if(isNew){delete payload.id;payload.enabled=false;}
    if(payload.kind==='weather')payload.body='';
    const errors=validateRule(payload,this.snapshot?.entity_options || []);
    if(errors.length){this._editorError(this._ui(()=>validateRule(payload,this.snapshot?.entity_options || [],this._language).join('\n')));return;}
    const s=await this._mutate('save',{rule:payload,expected_revision:revision});
    if(s){this.selected=s.saved_id || rule.id || this.selected;this.$('editor').close();this._renderRuntime();}
  }
  _confirm(title,message,action) {
    const dialog=this.$('confirm');
    dialog.replaceChildren(node('h2',{},title),node('p',{},message),node('div',{class:'dialog-actions'},button(this._ui("Cancelar acción"),()=>dialog.close()),button(this._ui("Confirmar"),()=>{dialog.close();action();},{id:'confirm-action',class:'primary'})));
    dialog.showModal();
  }
  deleteEditing() {
    const {rule,revision}=this.editing;
    this._confirm(this._ui("Borrar aviso"),this._both(()=>`Se borrará «${rule.name}» y se cancelarán sus pendientes. No detiene audio ajeno. ¿Continuar?`,()=>`«${rule.name}» will be deleted and its pending deliveries cancelled. This does not stop unrelated audio. Continue?`),async()=>{
      const s=await this._mutate('delete',{rule_id:rule.id,expected_revision:revision});if(s)this.$('editor').close();
    });
  }
  pause(paused=!this.snapshot?.paused) {if(this.snapshot)this._mutate('pause',{paused,expected_revision:this.snapshot.revision});this._renderStatus();}
  toggle(r) {if(this.snapshot)this._mutate('toggle',{rule_id:r.id,enabled:!r.enabled,expected_revision:this.snapshot.revision});}
  testRule(r) {
    if(this.snapshot?.paused){this._message=this._ui("Pausa global: las pruebas reales también están bloqueadas.");this._renderStatus();return;}
    this._confirm(this._ui("Probar real: envío a la Ball"),this._both(()=>`Esto enviará «${r.name}» a la Ball real, incluso si el aviso está deshabilitado. Puede mostrar texto y sonar según el modo y la noche reales. La Ball es compartida. ¿Enviar ahora?`,()=>`This will send «${r.name}» to the real Ball, even if the notification is disabled. It may display text and play audio depending on the actual mode and night settings. The Ball is shared. Send now?`),()=>this._mutate('test',{rule_id:r.id}));
  }
  _freezeEditor(frozen) {
    if(frozen && !this._frozen){
      this._frozen=new Map();const form=this.$('edit-form');
      if(form)for(const tag of ['input','select','textarea','button'])for(const control of form.querySelectorAll(tag)){this._frozen.set(control,control.disabled);control.disabled=true;}
    }else if(!frozen && this._frozen){for(const [control,disabled] of this._frozen)control.disabled=disabled;this._frozen=null;}
  }
  async _mutate(command,fields) {
    if(this._busy || !this._active)return null;
    if(command==='test' && this.snapshot?.paused){this._message=this._ui("Pausa global: las pruebas reales también están bloqueadas.");this._renderStatus();return null;}
    if(!this._online()){this._editorError(this._ui("Home Assistant desconectado. Se conserva la edición."));this._renderStatus();return null;}
    const serial=++this._serial;this._loading=false;this._busy=true;this._renderRuntime();
    this._freezeEditor(true);
    try {
      const s=await this._hass.callWS({type:`ha2_notifications/${command}`,...fields});
      if(!this._active || serial!==this._serial)return null;
      this.snapshot=s;this._message=command==='test'?this._both(()=>`Solicitud encolada${s.queued_request_id?' · '+s.queued_request_id:''}. No confirma entrega ni locución. Consulta la actividad real.`,()=>`Request queued${s.queued_request_id?' · '+s.queued_request_id:''}. Does not confirm delivery or speech. Check real activity.`):this._ui("Configuración guardada en Home Assistant.");
      return s;
    } catch(error) {
      if(!this._active || serial!==this._serial)return null;
      const code=error?.code;
      const messages={conflict:this._ui("La configuración cambió en otro panel u otra sesión. Se conserva tu edición. Recarga explícitamente antes de volver a guardar."),invalid_rule:this._ui("HA rechazó la regla: revisa límites, entidad, fecha y hora en la zona HA (incluido DST). Se conserva la edición."),not_found:this._ui("El aviso ya no existe. Se conserva la edición."),paused:this._ui("La pausa global bloquea también las pruebas reales."),queue_full:this._ui("La cola está llena. No se ha confirmado un nuevo envío."),unavailable:this._ui("La Ball o los servicios HA no están disponibles."),config_error:this._ui("Revisa la configuración real de la integración, destino y voz."),unauthorized:this._ui("Acceso reservado a administradores.")};
      this._message=messages[code] || this._ui("No se pudo confirmar la operación. Revisa la conexión y la actividad antes de repetir un envío.");
      if(this.$('editor')?.open)this._editorError(this._message,code==='conflict');return null;
    } finally {
      if(serial===this._serial){this._busy=false;this._freezeEditor(false);if(this._active)this._renderRuntime();}
    }
  }
  async refresh() {
    if(!this._active || !this._online() || document.visibilityState!=='visible' || this._panelVisible===false || this._loading || this._busy){this._renderStatus();return;}
    const serial=++this._serial;this._loading=true;
    try {const s=await this._hass.callWS({type:'ha2_notifications/get'});if(this._active && serial===this._serial){this.snapshot=s;this._message='';this._renderRuntime();return s;}}
    catch(error) {if(this._active && serial===this._serial){this._message=this._ui("No se pudo cargar la configuración. Revisa la conexión y reintenta.");this._renderStatus();}}
    finally {if(serial===this._serial)this._loading=false;}
  }
}
if(!customElements.get('ha2-notifications-panel'))customElements.define('ha2-notifications-panel',Ha2NotificationsPanel);
