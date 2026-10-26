/* Minimal DOM boundary, NOT a browser/rendering engine. Exercises real UI nodes/listeners.
   No parsing/asserting HTML strings; no backend implementation. See frontend.md limits. */
class Classes {
  constructor(node) { this.node = node; }
  toggle(name, force) { const s = new Set(this.node.className.split(' ').filter(Boolean)); const add = force ?? !s.has(name); add ? s.add(name) : s.delete(name); this.node.className = [...s].join(' '); return add; }
  add(n) { this.toggle(n,true); } remove(n) { this.toggle(n,false); }
  contains(n) { return this.node.className.split(' ').includes(n); }
}
export class NodeFixture {
  constructor(tag = '') { if(tag==='textarea')Object.defineProperty(this,'type',{get:()=> 'textarea'}); this.tagName = tag.toUpperCase(); this.children=[]; this.attributes={}; this.listeners=new Map(); this.className=''; this.classList = new Classes(this); this.value=''; this.checked=false; this.hidden=false; this.disabled=false; this.parentNode=null; this._text=''; }
  set textContent(s) { this._text=String(s); this.children=[]; }
  get textContent() { return this._text + this.children.map(c=>c.textContent).join(''); }
  append(...items) { for (const item of items) { const child=typeof item==='string' ? Object.assign(new NodeFixture('#text'),{textContent:item}) : item; if(child) {child.parentNode=this;this.children.push(child);} } }
  replaceChildren(...items) {this.children=[];this._text='';this.append(...items);}
  setAttribute(k,v) {this.attributes[k]=String(v); if(k==='id')this.id=String(v);if(k==='class')this.className=String(v);}
  getAttribute(k) { return this.attributes[k] ?? null; }
  addEventListener(k,fn) { if(!this.listeners.has(k))this.listeners.set(k,new Set());this.listeners.get(k).add(fn); }
  removeEventListener(k,fn) {this.listeners.get(k)?.delete(fn);}
  dispatchEvent(e) {if(!e.target)Object.defineProperty(e,'target',{value:this});Object.defineProperty(e,'currentTarget',{value:this,configurable:true}); for(const fn of this.listeners.get(e.type) || [])fn(e);if(e.bubbles && !e.cancelBubble)this.parentNode?.dispatchEvent(e);return !e.defaultPrevented;}
  click() { if(!this.disabled)this.dispatchEvent(new Event('click',{bubbles:true,cancelable:true})); }
  focus() { document.activeElement=this; }
  showModal() {this.open=true;} close() {this.open=false;}
  matches(s) {if(s.startsWith('#'))return this.id===s.slice(1);if(s.startsWith('.'))return this.classList.contains(s.slice(1));const a=s.match(/^\[([^=]+)(?:="?([^"\]]+)"?)?\]$/);if(a)return this.attributes[a[1]]!==undefined && (a[2]===undefined||this.attributes[a[1]]===a[2]);return this.tagName===s.toUpperCase();}
  querySelectorAll(s) {return this.children.flatMap(c=>[...(c.matches(s)?[c]:[]),...c.querySelectorAll(s)]);}
  querySelector(s) {return this.querySelectorAll(s)[0]||null;}
  attachShadow() {this.shadowRoot=new NodeFixture('#shadow-root');return this.shadowRoot;}
}
export function installDOM() {
  globalThis.HTMLElement = NodeFixture;
  globalThis.document = Object.assign(new NodeFixture('document'), {visibilityState:'visible', createElement:t=>new NodeFixture(t), createTextNode:t=>Object.assign(new NodeFixture('#text'),{textContent:t})});
  const registry=new Map();globalThis.customElements={define:(n,c)=>registry.set(n,c),get:n=>registry.get(n)};
  const intervals = new Map(),timeouts=new Map();let id=0;
  globalThis.setTimeout=(fn,ms)=>{timeouts.set(++id,{fn,ms});return id;};
  globalThis.clearTimeout=id=>timeouts.delete(id);
  globalThis.setInterval=(fn,ms)=>{intervals.set(++id,{fn,ms});return id;};
  globalThis.clearInterval=id=>intervals.delete(id);
  return {intervals,timeouts, registry};
}
export const flush = async () => {for(let i=0;i<8;i++)await Promise.resolve();};
export function input(node,value) {if(node.type==='checkbox')node.checked=value;else node.value=value;node.dispatchEvent(new Event('input',{bubbles:true}));node.dispatchEvent(new Event('change',{bubbles:true}));}
