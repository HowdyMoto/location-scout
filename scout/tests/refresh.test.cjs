const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const code = fs.readFileSync('scout/dist/app.js', 'utf8');
function harness() {
  const requests = [], button = {};
  const context = vm.createContext({AbortController, AbortSignal, Date,
    fetch: (url, {signal}) => new Promise((resolve, reject) => {
      requests.push({url, resolve: () => resolve({ok:true,json:async()=>({items:[],status:'ok',fetchedAt:Date.now()})})});
      signal.addEventListener('abort', () => reject(new Error('aborted')), {once:true});
    }), $:()=>button, moving:()=>false, draw(){}, feed(){}, health(){}, status:()=>'',
  });
  vm.runInContext('let layers=[], activeLoads=0,selected=null;'+code.slice(code.indexOf('async function load(l)'),code.indexOf('\nfunction preset('))+
    ';this.api={refresh,cancelLoad,setLayers:v=>layers=v};',context);
  return {...context.api, requests};
}
const layer=id=>({id,items:[],next:0,refresh:60});
const settle=()=>new Promise(resolve=>setImmediate(resolve));
test('disabled layers do not keep demanding upstream snapshots',()=>{
 const h=harness();h.setLayers([{...layer('off'),on:false}]);h.refresh();assert.equal(h.requests.length,0);
});
test('a completed slot immediately fetches the new region while another old request is slow',async()=>{
  const h=harness(), old=Array.from({length:4},(_,i)=>layer('bay-'+i));
  h.setLayers(old);h.refresh();assert.equal(h.requests.length,4);
  h.setLayers([layer('seattle')]);h.refresh();
  h.requests[0].resolve();await settle();
  assert.equal(h.requests[4].url,'/api/seattle');
  h.requests.slice(1).forEach(r=>r.resolve());await settle();
});
test('leaving and returning to an aborted region does not impose an error cooldown',async()=>{
  const h=harness(), sf=layer('sf');h.setLayers([sf]);h.refresh();
  h.setLayers([]);h.cancelLoad(sf);await settle();
  assert.equal(sf.next,0);assert.notEqual(sf.status,'unavailable');
  h.setLayers([sf]);h.refresh();assert.equal(h.requests.length,2);
  h.requests[1].resolve();await settle();
});
test('rapid viewport changes discard canceled responses and fetch the latest bounds',async()=>{
  const h=harness(), air={...layer('world-air'),viewport:true,queryKey:'sf'};
  h.setLayers([air]);h.refresh();h.cancelLoad(air);air.queryKey='seattle';
  await settle();assert.equal(h.requests[1].url,'/api/world-air?bbox=seattle');
  h.requests[1].resolve();await settle();assert.equal(air.status,'ok');
});
