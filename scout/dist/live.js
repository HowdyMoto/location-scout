'use strict';
let followed=null,pausedAt=null,newReports=0,lastFrame=0,lastMetrics=0,lastFollow=0;
let radarPlaying=true,radarNextAt=0;
const BUFFER_MS=90000;
const pausedSamples=new Map();
const trailRenderer=L.canvas({padding:.3});
function playbackTime(){return (pausedAt??Date.now())-BUFFER_MS}
function positionFor(l,i,target=playbackTime()){
 const key=l.id+':'+i.id;
 if(pausedAt&&pausedSamples.has(key))return pausedSamples.get(key);
 const p=ScoutMotion.sample(l.trails?.get(i.id)||[i],target,vehicleType(l)==='air'?400:65);
 if(pausedAt&&p)pausedSamples.set(key,p);
 return p;
}
function vehicleType(l){return l.id==='air'||l.id==='sea-air'||l.id==='world-air'?'air':l.id.includes('ferr')||l.id.includes('ships')?'ship':'transit'}
function vehicleSvg(type){
 const paths={air:'M12 1 14 9 22 15 22 18 14 15 14 20 17 22 17 24 12 22 7 24 7 22 10 20 10 15 2 18 2 15 10 9Z',ship:'M12 1 20 9 18 23 6 23 4 9Z',transit:'M12 1 19 8 19 22 5 22 5 8Z'};
 return `<svg viewBox="0 0 24 26" aria-hidden="true"><path d="${paths[type]}"/><path class="vehicle-window" d="M9 11h6v4H9z"/></svg>`;
}
function drawVehicles(l){
 if(!l.on)return;
 if(!l.vehicleMode){l.groupLayer.clearLayers();l.vehicles=new Map();l.motionTrails=new Map();l.vehicleMode=true}
 const visible=map.getBounds().pad(.3),keep=new Set(),target=playbackTime();
 for(const i of mapped(l)){
  const p=positionFor(l,i,target);
  if(!p||(!visible.contains([p.lat,displayLon(p.lon)])&&followed?.id!==i.id))continue;
  keep.add(i.id);let marker=l.vehicles.get(i.id);
  if(!marker){
   const icon=L.divIcon({className:'vehicle-marker',html:`<div class="vehicle-shell ${vehicleType(l)}" style="--vehicle-color:${l.color}"><span class="vehicle-direction">${vehicleSvg(vehicleType(l))}</span><span class="vehicle-label"></span></div>`,iconSize:[28,28],iconAnchor:[14,14]});
   marker=L.marker([p.lat,displayLon(p.lon)],{icon,title:i.title,zIndexOffset:vehicleType(l)==='air'?200:100}).on('click',()=>{const latest=l.items.find(x=>x.id===i.id);if(latest)details(l,latest)}).addTo(l.groupLayer);
   marker.bindTooltip(esc(i.title),{direction:'top',offset:[0,-15],className:'vehicle-tooltip'});l.vehicles.set(i.id,marker);
  }
  marker.record=i;marker.playback=p;marker.setTooltipContent(esc(i.title));marker.options.title=i.title;
  const el=marker.getElement();if(el){el.setAttribute('title',i.title);el.querySelector('.vehicle-label').textContent=vehicleType(l)==='air'?i.title:(i.routeLabel||'');el.classList.toggle('show-label',map.getZoom()>=13||followed?.id===i.id)}
 }
 for(const [id,marker] of l.vehicles)if(!keep.has(id)){l.groupLayer.removeLayer(marker);l.vehicles.delete(id);if(l.motionTrails.has(id)){l.groupLayer.removeLayer(l.motionTrails.get(id));l.motionTrails.delete(id)}}
 if(followed?.layer===l.id&&!l.vehicles.has(followed.id)){stopFollowing();toast('Tracking ended: no recent position is available.')}
}
function updateMotionTrails(l,target){
 if(!l.vehicles)return;
 for(const [id,marker] of l.vehicles){
  const p=marker.playback,points=(l.trails?.get(id)||[]).filter(x=>x.time<=target&&x.time>target-180000);
  const coordinates=[];
  // Break at long gaps or impossible jumps instead of drawing a misleading track.
  for(const x of points){const prev=coordinates.at(-1);if(prev&&(x.time-prev.time>120000||ScoutMotion.distance(prev,x)/((x.time-prev.time)/1000)>(vehicleType(l)==='air'?400:65)))coordinates.length=0;coordinates.push(x)}
  if(p&&p.state!=='buffering')coordinates.push(p);
  const show=coordinates.length>1&&(vehicleType(l)==='air'||map.getZoom()>=12||followed?.id===id);
  if(show){
   const latlngs=coordinates.map(x=>[x.lat,displayLon(x.lon)]);let line=l.motionTrails.get(id);
   if(!line){line=L.polyline(latlngs,{renderer:trailRenderer,color:l.color,weight:followed?.id===id?3:1.5,opacity:.5,interactive:false}).addTo(l.groupLayer);l.motionTrails.set(id,line)}else line.setLatLngs(latlngs);
  }else if(l.motionTrails.has(id)){l.groupLayer.removeLayer(l.motionTrails.get(id));l.motionTrails.delete(id)}
 }
}
function stopFollowing(){followed=null;if($('follow-status'))$('follow-status').hidden=true}
function followVehicle(l,i){
 followed={layer:l.id,id:i.id};const p=ScoutMotion.sample(l.trails?.get(i.id)||[i],playbackTime(),vehicleType(l)==='air'?400:65)||i;
 map.setView([p.lat,p.lon],vehicleType(l)==='air'?12:15,{animate:false});
 $('follow-status').hidden=false;$('follow-name').textContent=i.title;
}
function chooseFollow(type){
 const candidates=layers.filter(l=>l.on&&moving(l)&&vehicleType(l)===type).flatMap(l=>mapped(l).map(i=>({l,i,p:ScoutMotion.sample(l.trails?.get(i.id)||[i],playbackTime(),type==='air'?400:65)})));
 candidates.sort((a,b)=>Number(b.p?.state==='moving')-Number(a.p?.state==='moving')||Number(inView(b.i))-Number(inView(a.i)));
 const pick=candidates.find(x=>x.i.id!==followed?.id)||candidates[0];
 if(!pick)return toast('No recent vehicles of this type are available. Enable a vehicle layer.');
 followVehicle(pick.l,pick.i);details(pick.l,pick.i);
}
function updateScenes(){
 const scenes=activeRegion==='seattle'?[
  ['City pulse',[47.607,-122.333],13],['Sea-Tac approaches',[47.45,-122.30],11],['Across the Sound',[47.66,-122.50],11]
 ]:activeRegion==='bay'?[['City pulse',[37.78,-122.42],13],['SFO approaches',[37.62,-122.38],11],['Across the Bay',[37.82,-122.25],10]]:[['Seattle',[47.61,-122.33],11],['San Francisco',[37.78,-122.42],12],...catalog.filter(s=>s.destination).map(s=>[s.destination.name,s.destination.center,s.destination.zoom])];
 $('scene-bar').innerHTML=scenes.map((s,n)=>`<button data-scene="${n}">${s[0]}</button>`).join('');
 document.querySelectorAll('[data-scene]').forEach(b=>b.onclick=()=>{stopFollowing();const s=scenes[+b.dataset.scene];map.flyTo(s[1],s[2],{duration:1});$('place').textContent=s[0]});
}
function drawRadar(l){
 const active=l.on&&layers.includes(l);$('radar-status').hidden=!layers.some(x=>x.on&&x.id.endsWith('radar'));
 if(!active||!l.raster)return;
 if(!l.radarCurrent&&!l.radarPending)advanceRadar(l);
}
function advanceRadar(l){
 const frames=l.raster?.frames?.length?l.raster.frames:[l.raster?.time];
 if(!frames[0]||l.radarPending)return;
 const next=(l.radarIndex??-1)+1,index=next%frames.length,time=frames[index];
 l.radarPending=true;
 const tile=L.tileLayer.wms(l.raster.url,{layers:l.raster.layer,format:'image/png',transparent:true,opacity:0,time,bounds:L.latLngBounds([24,-125],[50,-66]),attribution:'Radar © NOAA / NWS'});
 let failed=false;
 tile.on('tileerror',()=>{failed=true;$('radar-time').textContent='Radar tiles unavailable · last frame held'});
 tile.once('load',()=>{
  l.radarPending=false;
  if(failed||!l.on||!layers.includes(l)){l.groupLayer.removeLayer(tile);radarNextAt=Date.now()+5000;return}
  if(l.radarCurrent)l.groupLayer.removeLayer(l.radarCurrent);
  l.radarCurrent=tile;l.radarIndex=index;tile.setOpacity(.5);
  $('radar-time').textContent=`RADAR ${new Date(time).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})} · ${index+1}/${frames.length} observed frames`;
  radarNextAt=Date.now()+1400;
 });
 l.groupLayer.addLayer(tile);
}
function animationFrame(now){
 requestAnimationFrame(animationFrame);
 if(document.hidden||now-lastFrame<33)return;lastFrame=now;
 const target=playbackTime();let inMotion=0,holding=0,buffering=0;
 for(const l of layers.filter(l=>l.on&&moving(l)&&l.vehicleMode)){
  for(const [id,marker] of l.vehicles){
   const p=positionFor(l,marker.record,target);if(!p)continue;
   marker.playback=p;marker.setLatLng([p.lat,displayLon(p.lon)]);
   const el=marker.getElement();
   if(el){const h=Number.isFinite(p.heading)?p.heading:0;el.querySelector('.vehicle-direction').style.transform=`rotate(${h}deg)`;el.classList.toggle('vehicle-held',p.state==='gap'||staleItem(l,marker.record));el.classList.toggle('vehicle-followed',followed?.layer===l.id&&followed.id===id)}
   if(map.getBounds().contains([p.lat,displayLon(p.lon)])){if(p.state==='moving')inMotion++;else if(p.state==='buffering')buffering++;else holding++}
   if(followed?.layer===l.id&&followed.id===id&&now-lastFollow>250){lastFollow=now;$('follow-name').textContent=marker.record.title;map.panTo([p.lat,p.lon],{animate:false,noMoveStart:true})}
  }
  if(now-lastMetrics>1000)updateMotionTrails(l,target);
 }
 if(now-lastMetrics>1000){
  lastMetrics=now;$('moving-count').textContent=pausedAt?'0':inMotion;$('holding-count').textContent=holding+buffering;$('new-count').textContent=newReports;
  $('playback-clock').textContent=new Date(target).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'});
  $('motion-caption').textContent=pausedAt?'Playback paused · feeds continue updating':map.getZoom()<10?'Zoom in to see individual vehicles move':inMotion?'90s behind real time · interpolated between received positions':buffering?'Buffering observations · motion starts as the 90s buffer fills':'90s observation playback · vehicles hold when no new position is available';
  for(const l of layers.filter(l=>l.on&&l.id.endsWith('radar')))if(radarPlaying&&Date.now()>radarNextAt)advanceRadar(l);
 }
}
$('pause-motion').onclick=()=>{pausedAt=pausedAt?null:Date.now();pausedSamples.clear();if(pausedAt){for(const l of layers)for(const [id,m] of l.vehicles||[])if(m.playback)pausedSamples.set(l.id+':'+id,m.playback)}$('pause-motion').textContent=pausedAt?'▶ Resume':'Ⅱ Pause';$('pause-motion').setAttribute('aria-label',pausedAt?'Resume motion playback':'Pause motion playback')};
$('follow-flight').onclick=()=>chooseFollow('air');$('follow-transit').onclick=()=>chooseFollow('transit');$('stop-follow').onclick=stopFollowing;
map.on('dragstart',stopFollowing);
$('radar-toggle').onclick=()=>{const l=layers.find(l=>l.id.endsWith('radar'));if(!l)return;l.on=!l.on;controls();sync();$('radar-toggle').classList.toggle('active',l.on);$('radar-status').hidden=!l.on;drawRadar(l)};
$('radar-pause').onclick=()=>{radarPlaying=!radarPlaying;$('radar-pause').textContent=radarPlaying?'Pause radar':'Play radar'};
if(matchMedia('(prefers-reduced-motion: reduce)').matches){pausedAt=Date.now();$('pause-motion').textContent='▶ Resume';$('pause-motion').setAttribute('aria-label','Resume motion playback');radarPlaying=false;$('radar-pause').textContent='Play radar'}
requestAnimationFrame(animationFrame);
boot();
