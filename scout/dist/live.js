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
 const p=ScoutMotion.sample(l.trails?.get(i.id)||[i],target,ScoutMotion.maxSpeed(l));
 if(pausedAt&&p)pausedSamples.set(key,p);
 return p;
}
function vehicleType(l){return l.id==='iss-orbit'?'satellite':l.id==='air'||l.id==='sea-air'||l.id==='world-air'?'air':l.id.includes('ferr')||l.id.includes('ships')?'ship':'transit'}
function vehicleSvg(type){
 const paths={satellite:'M9 8h6v10H9zM1 3h6v8H1zM17 15h6v8h-6zM6 9l4 3M14 15l4 3',air:'M12 1 14 9 22 15 22 18 14 15 14 20 17 22 17 24 12 22 7 24 7 22 10 20 10 15 2 18 2 15 10 9Z',ship:'M12 1 20 9 18 23 6 23 4 9Z',transit:'M12 1 19 8 19 22 5 22 5 8Z'};
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
  const el=marker.getElement();if(el){el.setAttribute('title',i.title);el.querySelector('.vehicle-label').textContent=vehicleType(l)==='satellite'?'ISS · modeled':vehicleType(l)==='air'?i.title:(i.routeLabel||'');el.classList.toggle('show-label',vehicleType(l)==='satellite'||map.getZoom()>=13||followed?.id===i.id)}
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
  for(const x of points){const prev=coordinates.at(-1);if(prev&&(x.time-prev.time>120000||ScoutMotion.distance(prev,x)/((x.time-prev.time)/1000)>(ScoutMotion.maxSpeed(l))))coordinates.length=0;coordinates.push(x)}
  if(p&&p.state!=='buffering')coordinates.push(p);
  const show=coordinates.length>1&&(['air','satellite'].includes(vehicleType(l))||map.getZoom()>=12||followed?.id===id);
  if(show){
   const latlngs=ScoutMotion.trailCoordinates(coordinates,map.getCenter().lng);let line=l.motionTrails.get(id);
   if(!line){line=L.polyline(latlngs,{renderer:trailRenderer,color:l.color,weight:followed?.id===id?3:1.5,opacity:.5,interactive:false}).addTo(l.groupLayer);l.motionTrails.set(id,line)}else line.setLatLngs(latlngs);
  }else if(l.motionTrails.has(id)){l.groupLayer.removeLayer(l.motionTrails.get(id));l.motionTrails.delete(id)}
 }
}
function stopFollowing(){followed=null;if($('follow-status'))$('follow-status').hidden=true}
function followVehicle(l,i){
 followed={layer:l.id,id:i.id};const p=ScoutMotion.sample(l.trails?.get(i.id)||[i],playbackTime(),ScoutMotion.maxSpeed(l))||i;
 map.setView([p.lat,displayLon(p.lon)],vehicleType(l)==='satellite'?4:vehicleType(l)==='air'?12:15,{animate:false});
 $('follow-status').hidden=false;$('follow-name').textContent=i.title;
}
function chooseFollow(type){
 const candidates=layers.filter(l=>l.on&&moving(l)&&vehicleType(l)===type).flatMap(l=>mapped(l).map(i=>({l,i,p:ScoutMotion.sample(l.trails?.get(i.id)||[i],playbackTime(),ScoutMotion.maxSpeed(l))})));
 candidates.sort((a,b)=>Number(b.p?.state==='moving')-Number(a.p?.state==='moving')||Number(inView(b.i))-Number(inView(a.i)));
 const pick=candidates.find(x=>x.i.id!==followed?.id)||candidates[0];
 if(!pick)return toast('No recent vehicles of this type are available. Enable a vehicle layer.');
 followVehicle(pick.l,pick.i);details(pick.l,pick.i);
}
function updateScenes(){
 const scenes=activeRegion==='seattle'?[
  ['City pulse',[47.607,-122.333],13],['Sea-Tac approaches',[47.45,-122.30],11],['Across the Sound',[47.66,-122.50],11]
 ]:activeRegion==='bay'?[['City pulse',[37.78,-122.42],13],['SFO approaches',[37.62,-122.38],11],['Across the Bay',[37.82,-122.25],10]]:[['Seattle',[47.61,-122.33],11],['San Francisco',[37.78,-122.42],12],...catalog.filter(s=>s.destination).map(s=>[s.destination.name,s.destination.center,s.destination.zoom])];
 $('scene-bar').innerHTML='<button id="world-view">◉ World view</button><button id="explore-world">◎ Explore the world</button>'+scenes.slice(0,4).map((s,n)=>`<button data-scene="${n}">${s[0]}</button>`).join('');
 $('explore-world').onclick=showExplorer;
 $('world-view').onclick=()=>{showWorld();toast('Choose a destination on the map, or zoom anywhere for available feeds.')};
 drawDiscovery();
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
 const tile=l.raster.type==='xyz'
  ?L.tileLayer(l.raster.frameUrls[index],{opacity:0,maxNativeZoom:7,maxZoom:19,attribution:'Weather data by <a href="https://www.rainviewer.com/" target="_blank" rel="noopener">RainViewer</a>'})
  :L.tileLayer.wms(l.raster.url,{layers:l.raster.layer,format:'image/png',transparent:true,opacity:0,time,bounds:L.latLngBounds([24,-125],[50,-66]),attribution:'Radar © NOAA / NWS'});
 let failed=false,settled=false;
 const finish=()=>{
  if(settled)return;settled=true;clearTimeout(timeout);
  l.radarPending=false;
  // Advance even on failure: an expired frame must not trap playback forever.
  l.radarIndex=index;
  if(failed||!l.on||!layers.includes(l)){
   tile.off('tileerror');l.groupLayer.removeLayer(tile);radarNextAt=Date.now()+5000;
   if(failed&&l.on&&layers.includes(l))$('radar-time').textContent=l.radarCurrent?'Radar frame unavailable · last frame held · retrying':'Radar tiles unavailable · retrying';
   return;
  }
  if(l.radarCurrent){l.radarCurrent.off('tileerror');l.groupLayer.removeLayer(l.radarCurrent)}
  l.radarCurrent=tile;tile.setOpacity(.5);
  $('radar-time').textContent=`RADAR ${new Date(time).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})} · ${index+1}/${frames.length} ${l.raster.type==='xyz'?'mosaics · coverage varies':'observed frames'}`;
  radarNextAt=Date.now()+1400;
 };
 const timeout=setTimeout(()=>{failed=true;finish()},20000);
 tile.on('tileerror',()=>{
  failed=true;
  if(l.on&&layers.includes(l)&&l.radarCurrent===tile)$('radar-time').textContent='Radar coverage incomplete · retrying';
 });
 // Leaflet still accesses the layer's map after emitting load. Never remove
 // this layer synchronously from that callback (including failed tiles).
 tile.once('load',()=>setTimeout(finish,0));
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
   if(followed?.layer===l.id&&followed.id===id&&now-lastFollow>250){lastFollow=now;$('follow-name').textContent=marker.record.title;map.panTo([p.lat,displayLon(p.lon)],{animate:false,noMoveStart:true})}
  }
  if(now-lastMetrics>1000)updateMotionTrails(l,target);
 }
 if(now-lastMetrics>1000){
  lastMetrics=now;$('moving-count').textContent=pausedAt?'0':inMotion;$('holding-count').textContent=holding+buffering;$('new-count').textContent=newReports;
  $('playback-clock').textContent=new Date(target).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'});
  $('motion-caption').textContent=pausedAt?'Playback paused · feeds continue updating':map.getZoom()<10&&!layers.some(l=>l.on&&l.id==='iss-orbit'&&l.vehicles?.size)?'Zoom in to see individual vehicles move':inMotion?'90s behind real time · interpolated between received positions':buffering?'Buffering observations · motion starts as the 90s buffer fills':'90s observation playback · vehicles hold when no new position is available';
  for(const l of layers.filter(l=>l.on&&l.id.endsWith('radar')))if(radarPlaying&&Date.now()>radarNextAt)advanceRadar(l);
 }
}
$('pause-motion').onclick=()=>{pausedAt=pausedAt?null:Date.now();pausedSamples.clear();if(pausedAt){for(const l of layers)for(const [id,m] of l.vehicles||[])if(m.playback)pausedSamples.set(l.id+':'+id,m.playback)}$('pause-motion').textContent=pausedAt?'▶ Resume':'Ⅱ Pause';$('pause-motion').setAttribute('aria-label',pausedAt?'Resume motion playback':'Pause motion playback')};
$('follow-iss').onclick=()=>chooseFollow('satellite');$('follow-ship').onclick=()=>chooseFollow('ship');$('follow-flight').onclick=()=>chooseFollow('air');$('follow-transit').onclick=()=>chooseFollow('transit');$('stop-follow').onclick=stopFollowing;
map.on('dragstart',stopFollowing);
$('radar-toggle').onclick=()=>{const l=layers.find(l=>l.id.endsWith('radar'));if(!l)return;l.on=!l.on;controls();sync();$('radar-toggle').classList.toggle('active',l.on);$('radar-status').hidden=!l.on;drawRadar(l)};
$('radar-pause').onclick=()=>{radarPlaying=!radarPlaying;$('radar-pause').textContent=radarPlaying?'Pause radar':'Play radar'};
if(matchMedia('(prefers-reduced-motion: reduce)').matches){pausedAt=Date.now();$('pause-motion').textContent='▶ Resume';$('pause-motion').setAttribute('aria-label','Resume motion playback');radarPlaying=false;$('radar-pause').textContent='Play radar'}
requestAnimationFrame(animationFrame);
boot();

let lastDestination=null;
const discoveryLayer=L.layerGroup().addTo(map);
map.on('moveend',drawDiscovery);
function showWorld(){
 stopFollowing();map.closePopup();map.fitBounds([[-55,-175],[72,180]],{animate:false});applyViewport();drawDiscovery();
}
function drawDiscovery(){
 discoveryLayer.clearLayers();
 if(map.getZoom()>7||!catalog.length)return;
 const places=explorationPlaces().map(p=>({...p,center:p.center||homes[p.id]?.center})).filter(p=>p.center);
 const buckets=ScoutExplore.discoveryBuckets(places,center=>map.project([center[0],displayLon(center[1])],map.getZoom()));
 for(const bucket of buckets){
  const first=bucket[0],point=first.center,label=bucket.length>1?`${bucket.length} places to explore`:first.name;
  const icon=L.divIcon({className:'discovery-marker',html:`<span class="discovery-dot">${bucket.length>1?bucket.length:'↗'}</span><span class="discovery-name">${esc(label)}</span>`,iconSize:[150,32],iconAnchor:[16,16]});
  const marker=L.marker([point[0],displayLon(point[1])],{icon,title:label,zIndexOffset:1000}).addTo(discoveryLayer);
  marker.on('click',()=>{
   if(bucket.length===1){visitDestination(first);return}
   const list=document.createElement('div');list.className='discovery-options';
   for(const p of bucket){const button=document.createElement('button');button.textContent=p.name+' ↗';button.title=p.description;button.onclick=()=>visitDestination(p);list.append(button)}
   marker.bindPopup(list,{maxWidth:260}).openPopup();
  });
 }
}
function explorationPlaces(){
 return [{id:'seattle',name:'Seattle',country:'United States',timeZone:'America/Los_Angeles',description:'Buses, light rail, fire dispatch & coastal weather'},
 {id:'bay',name:'San Francisco',country:'United States',timeZone:'America/Los_Angeles',description:'Bike availability, traffic, tides & public reports'},
 ...catalog.filter(s=>s.destination).map(s=>({id:s.id,...s.destination,description:s.name})),
 {id:'london-sky',name:'London skies',country:'United Kingdom',timeZone:'Europe/London',center:[51.5,-.12],zoom:10,description:'Aircraft across the London airport approaches'},
 {id:'singapore-sky',name:'Singapore skies',country:'Singapore',timeZone:'Asia/Singapore',center:[1.35,103.82],zoom:10,description:'Aircraft around the Strait of Singapore'},
 {id:'cape-sky',name:'Cape Town skies',country:'South Africa',timeZone:'Africa/Johannesburg',center:[-33.93,18.42],zoom:10,description:'Aircraft over the Cape; receiver coverage varies'}];
}
function visitDestination(p){
 lastDestination=p.id;if(homes[p.id])setRegion(p.id);else{stopFollowing();map.setView(p.center,p.zoom);applyViewport()}$('region').value='explore';
 $('explore-dialog')?.close();map.closePopup();toast('Exploring '+p.name+' · feeds follow your view.');
}
function destinationActivity(p){
 const center=p.center||homes[p.id]?.center;
 const sources=allLayers.filter(l=>l.id===p.id||l.region===p.id||(p.id.endsWith('-sky')&&l.id==='world-air'&&l.queryKey&&center&&ScoutExplore.contains(l.queryKey.split(',').map(Number),[center[1],center[0],center[1]+.000001,center[0]+.000001])));
 return ScoutMotion.activity(sources,center);
}
function activityLabel(a){
 if(a.vehicles)return `${a.vehicles.toLocaleString()} recent vehicles · ${a.moving.toLocaleString()} moving in playback`;
 if(a.stations)return `${a.stations.toLocaleString()} stations reporting availability`;
 if(a.unavailable)return 'Feed unavailable · try another place';
 return a.checked?'No fresh local reports in the last check':'Explore coverage · activity not checked yet';
}
function updateExplorerActivity(){
 const dialog=$('explore-dialog');if(!dialog?.open)return;
 for(const p of explorationPlaces()){
  const badge=dialog.querySelector(`[data-activity="${p.id}"]`);if(!badge)continue;
  const a=destinationActivity(p);badge.textContent=activityLabel(a);badge.classList.toggle('has-activity',a.vehicles+a.stations>0);
 }
}
function showExplorer(){
 let dialog=$('explore-dialog');
 if(!dialog){dialog=document.createElement('dialog');dialog.id='explore-dialog';dialog.setAttribute('aria-labelledby','explorer-title');document.body.append(dialog)}
 const places=explorationPlaces();
 dialog.innerHTML=`<div class="explore-heading"><div><div class="eyebrow">FOLLOW YOUR CURIOSITY</div><h2 id="explorer-title">A different place. A different rhythm.</h2><p>Find fresh reports near each destination. Surprise me favors places with observed movement.</p></div><button id="close-explorer" aria-label="Close world explorer">×</button></div><button id="surprise-place" class="surprise-place">↗ Surprise me</button><div class="explore-grid">${places.map(p=>{
 const localTime=new Intl.DateTimeFormat([],{hour:'numeric',minute:'2-digit',timeZone:p.timeZone}).format(new Date());
 return `<button class="explore-place" data-destination="${esc(p.id)}"><small>${esc(p.country)} · ${esc(localTime)} local</small><strong>${esc(p.name)} ↗</strong><span>${esc(p.description)}</span><span class="explore-activity" data-activity="${esc(p.id)}"></span></button>`;
 }).join('')}</div><p class="explore-note">Counts cover fresh reports within 50 km of each destination, from feeds already checked. Movement uses 90-second observation playback. Unchecked or quiet places are still explorable; pan anywhere for global layers.</p>`;
 $('close-explorer').onclick=()=>dialog.close();
 dialog.querySelectorAll('[data-destination]').forEach(b=>b.onclick=()=>visitDestination(places.find(p=>p.id===b.dataset.destination)));
 $('surprise-place').onclick=()=>{const candidates=ScoutMotion.activeDestinations(places.map(p=>({...p,activity:destinationActivity(p)})),lastDestination);if(candidates.length)visitDestination(candidates[Math.floor(Math.random()*candidates.length)])};
 dialog.showModal();updateExplorerActivity();
}
