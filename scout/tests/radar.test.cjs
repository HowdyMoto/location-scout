const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const source=fs.readFileSync(require.resolve('../dist/live.js'),'utf8');
const fn=source.slice(source.indexOf('function advanceRadar('),source.indexOf('function animationFrame('));
function setup(){
 const timers=new Map(),tiles=[],removed=[];let seq=0;
 const label={textContent:''};
 const layer={on:true,raster:{type:'xyz',frames:['2026-10-25T10:00:00Z','2026-10-25T10:10:00Z'],frameUrls:['first','second']},groupLayer:{addLayer(){},removeLayer(t){removed.push(t)}}};
 const context=vm.createContext({layers:[layer],radarNextAt:0,Date,$:()=>label,
  setTimeout:(fn,ms)=>{timers.set(++seq,{fn,ms});return seq},clearTimeout:id=>timers.delete(id),
  L:{tileLayer:url=>{const handlers={};const t={url,handlers,on(name,fn){handlers[name]=fn},once(name,fn){handlers[name]=fn},off(name){delete handlers[name]},setOpacity(value){this.opacity=value}};tiles.push(t);return t}}
 });
 vm.runInContext(fn,context);
 const run=ms=>{for(const [id,t] of [...timers])if(t.ms===ms){timers.delete(id);t.fn()}};
 return {layer,tiles,removed,label,run,start:()=>context.advanceRadar(layer)};
}
test('failed frame removal waits until Leaflet finishes its load callback and advances past failure',()=>{
 const h=setup();h.start();h.tiles[0].handlers.tileerror();h.tiles[0].handlers.load();
 assert.equal(h.removed.length,0);assert.equal(h.layer.radarPending,true);
 h.run(0);assert.equal(h.removed.length,1);assert.equal(h.layer.radarPending,false);
 h.start();assert.equal(h.tiles[1].url,'second');
 h.tiles[1].handlers.load();h.run(0);assert.equal(h.layer.radarCurrent,h.tiles[1]);assert.equal(h.tiles[1].opacity,.5);
});
test('stalled load times out, holds last frame and ignores a late completion',()=>{
 const h=setup();const old={off(){}};h.layer.radarCurrent=old;
 h.start();h.run(20000);assert.equal(h.layer.radarCurrent,old);assert.equal(h.layer.radarPending,false);
 h.tiles[0].handlers.load();h.run(0);assert.equal(h.removed.length,1);assert.match(h.label.textContent,/last frame held/);
});
test('disabling radar during a load removes the pending frame without publishing it',()=>{
 const h=setup();h.start();h.layer.on=false;h.tiles[0].handlers.load();h.run(0);
 assert.equal(h.layer.radarCurrent,undefined);assert.equal(h.layer.radarPending,false);assert.equal(h.removed.length,1);
});
