'use strict';
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const homes={bay:{center:[37.82,-122.25],zoom:10,name:'San Francisco Bay Area'},seattle:{center:[47.61,-122.33],zoom:11,name:'Seattle / Puget Sound'}};
let activeRegion='seattle',home=homes.seattle,allLayers=[];
let viewportTimer,selectedPreset='all';
const map = L.map('map',{zoomControl:false,worldCopyJump:true,preferCanvas:true}).setView(home.center,home.zoom);
L.control.zoom({position:'topright'}).addTo(map);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',maxZoom:19}).addTo(map).on('tileerror',()=>toast('Some basemap tiles are unavailable.'));
let layers=[],catalog=[],selected=null,dark=false,toastTimer,activeLoads=0;
const moving=l=>Boolean(l.motion);
const groups=['Safety','Motion','Roads','Earth','Water','City'];
function toast(s){$('toast').textContent=s;$('toast').style.display='block';clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').style.display='none',5000)}
function ago(t){if(!t)return 'Time not supplied';const mins=Math.floor((Date.now()-t)/60000);return mins<0?'Future timestamp':mins<1?'Just now':mins<60?`${mins}m ago`:mins<1440?`${Math.floor(mins/60)}h ago`:`${Math.floor(mins/1440)}d ago`}
function date(t){return t?new Date(t).toLocaleString(): 'Not supplied'}
function staleItem(l,i){return Boolean(l.maxAge&&i.time&&Date.now()-i.time>l.maxAge*1000)}
function mapped(l){return l.items.filter(i=>!moving(l)||!staleItem(l,i))}
function status(l){if(l.zoomRequired)return 'Zoom in for this layer';if(l.coverageUnavailable)return 'Outside provider coverage';if(l.configurationRequired)return 'Access code needed';if(l.loading&&!l.fetchedAt)return 'Connecting…';if(l.status==='unavailable')return 'Unavailable · retrying';if(l.status==='stale')return 'Feed unavailable · cached data';if(!l.fetchedAt)return 'Not loaded';if(l.id.endsWith('radar')&&l.raster)return `Radar frame · ${ago(Date.parse(l.raster.time))}`;return `${mapped(l).length} mapped · ${l.kind.toLowerCase()}${l.status==='partial'?' · partial':''}`}
function controls(){
  $('layers').innerHTML=groups.filter(g=>layers.some(l=>l.group===g)).map(g=>`<div class="layer-group"><h3>${g}</h3>${layers.filter(l=>l.group===g).map(l=>`<div class="layer"><span class="layer-icon" style="--color:${l.color}">${l.icon}</span><div class="layer-info"><strong>${esc(l.name)}</strong><small id="status-${l.id}">${esc(status(l))}</small></div><label class="switch"><input type="checkbox" data-layer="${l.id}" aria-label="${esc(l.name)}" ${l.on?'checked':''}><span></span></label></div>`).join('')}</div>`).join('');
  document.querySelectorAll('[data-layer]').forEach(e=>e.onchange=()=>{selectedPreset='custom';layers.find(l=>l.id===e.dataset.layer).on=e.checked;document.querySelectorAll('[data-preset]').forEach(b=>b.classList.remove('active'));sync()});
}
function details(l,i){
  selected={layer:l.id,id:i.id};$('detail').hidden=false;
  const stale=l.status==='stale'||staleItem(l,i);
  const playback=moving(l)?ScoutMotion.sample(l.trails?.get(i.id)||[],playbackTime(),ScoutMotion.maxSpeed(l)):null;
  $('detail').innerHTML=`<button class="close" aria-label="Close details">×</button><div class="detail-status">${stale?'STALE / LAST KNOWN · ':''}${esc(l.kind.toUpperCase())}</div><h3>${esc(i.title)}</h3>${moving(l)?`<button id="follow-vehicle" class="follow-button">${followed?.layer===l.id&&followed.id===i.id?'Stop following':'◎ Follow this vehicle'}</button><div class="playback-note">Map: ${esc(playback?date(playback.time):'latest report')} · ${esc(playback?.state||'buffering')}<br>${l.id==='iss-orbit'?'90-second orbital-model playback. Trail joins received estimates.':'90-second observation playback. Lines connect reports, not road geometry.'}</div>`:''}<p>${esc(i.description)}</p><p><strong>${l.id==='iss-orbit'?'Orbital estimate':i.timestampKind?'Reception':'Observation / report'}:</strong> ${esc(date(i.time))}<br><strong>Fetched:</strong> ${esc(date(l.fetchedAt))}</p>${i.eventUrl?`<a href="${esc(i.eventUrl)}" target="_blank" rel="noopener">Open NASA event record ↗</a>`:''}${i.link?`<a href="${esc(i.link)}" target="_blank" rel="noopener">Open official camera viewer ↗</a>`:''}${i.image?`<a class="snapshot-link" href="${esc(i.image)}" target="_blank" rel="noopener">Open current camera snapshot ↗</a><p>Image capture time is not verified. Check the timestamp in the image.</p>`:''}${moving(l)?'<p>Direction and movement come from received observations. When reports stop, the marker holds; no future position is invented.</p>':''}<p>${esc(l.source)}<br>${esc(l.coverage)}<br>${i.lat.toFixed(4)}°, ${i.lon.toFixed(4)}°</p><p class="source-note">${esc(l.note||l.notes)}</p><a href="${esc(l.url)}" target="_blank" rel="noopener">Source documentation ↗</a>`;
  $('detail').querySelector('.close').onclick=()=>{stopFollowing();selected=null;$('detail').hidden=true};
  if(moving(l))$('follow-vehicle').onclick=()=>{if(followed?.layer===l.id&&followed.id===i.id)stopFollowing();else followVehicle(l,i);details(l,i)};
}
function draw(l){
  if(l.id.endsWith('radar')){drawRadar(l);return}
  if(moving(l)&&(map.getZoom()>=10||l.id==='iss-orbit')){drawVehicles(l);return}
  if(l.vehicles){l.vehicles.clear();l.motionTrails?.clear();l.vehicleMode=false}
  l.groupLayer.clearLayers();if(!l.on)return;
  if(moving(l)&&l.trails&&map.getZoom()>=12){for(const trail of l.trails.values()){const recent=trail.filter(i=>Date.now()-i.time<180000);if(recent.length>1)L.polyline(ScoutMotion.trailCoordinates(recent,map.getCenter().lng),{color:l.color,weight:2,opacity:.4,interactive:false}).addTo(l.groupLayer)}}
  const buckets=new Map();
  for(const i of mapped(l).filter(inView)){
    const p=map.project([i.lat,displayLon(i.lon)],map.getZoom());
    const key=map.getZoom()>=15?i.id:`${Math.floor(p.x/45)}:${Math.floor(p.y/45)}`;
    if(!buckets.has(key))buckets.set(key,[]);buckets.get(key).push(i);
  }
  for(const bucket of buckets.values()){
    const i=bucket[0],isCluster=bucket.length>1;
    const lat=isCluster?bucket.reduce((s,i)=>s+i.lat,0)/bucket.length:i.lat;
    const lon=isCluster?bucket.reduce((s,i)=>s+displayLon(i.lon),0)/bucket.length:displayLon(i.lon);
    const icon=L.divIcon({className:'signal',html:`<span class="marker ${isCluster?'cluster':i.availability?'bike-station':''} ${l.status==='stale'||staleItem(l,i)?'stale':''} ${(i.newAt&&Date.now()-i.newAt<60000)||(i.changedAt&&Date.now()-i.changedAt<60000)?'new-event':''}" style="--color:${l.color}">${isCluster?bucket.length:(i.availability&&map.getZoom()>=15?`<small>🚲</small> ${i.availability.bikes??'?'}`:l.icon)}</span>`,iconSize:[30,30],iconAnchor:[15,15]});
    L.marker([lat,displayLon(lon)],{icon,title:isCluster?`${bucket.length} ${l.name} · zoom to expand`:i.availability?`${i.title} · ${i.summary}`:i.title}).on('click',()=>{if(isCluster)map.fitBounds(bucket.map(i=>[i.lat,displayLon(i.lon)]),{padding:[60,60],maxZoom:16});else details(l,i)}).addTo(l.groupLayer);
  }
  for(const i of mapped(l).filter(i=>i.geometry))L.geoJSON(i.geometry,{style:{color:l.color,weight:1.5,fillOpacity:.10}}).on('click',()=>details(l,i)).addTo(l.groupLayer);
}
function displayLon(lon){return lon+360*Math.round((map.getCenter().lng-lon)/360)}
function inView(i){if(map.getBounds().contains([i.lat,displayLon(i.lon)]))return true;if(i.geometry){try{const b=L.geoJSON(i.geometry).getBounds();return b.isValid()&&map.getBounds().intersects(b)}catch{return false}}return false}
function feed(){
  updateExplorerActivity();
  const items=layers.filter(l=>l.on).flatMap(l=>mapped(l).filter(inView).map(i=>({l,i}))).sort((a,b)=>(b.i.time||0)-(a.i.time||0));
  $('signal-count').textContent=items.length.toLocaleString();$('visible-count').textContent=`${items.length.toLocaleString()} signals in view`;$('layer-count').textContent=layers.filter(l=>l.on).length;
  const groups=layers.filter(l=>l.on).sort((a,b)=>(moving(a)?1:0)-(moving(b)?1:0)).map(l=>items.filter(x=>x.l.id===l.id));
  const highlights=ScoutMotion.balanced(groups);
  $('feed').innerHTML=highlights.length?highlights.map(({l,i},n)=>`<button class="feed-item" data-index="${n}"><span class="layer-icon" style="--color:${l.color}">${l.icon}</span><span><strong>${esc(i.title)}</strong><small>${esc(i.summary||l.name)}</small><span class="badge">${i.changedAt&&Date.now()-i.changedAt<60000?'AVAILABILITY CHANGED · ':i.newAt&&Date.now()-i.newAt<60000?'NEW TO FEED · ':''}${l.status==='stale'||staleItem(l,i)?'STALE · ':''}${esc(l.kind)} · ${esc(ago(i.time))}</span></span></button>`).join(''):'<p class="empty">No mapped records in this view. Enable a layer or zoom out. A blank map does not establish that no activity exists.</p>';
  document.querySelectorAll('[data-index]').forEach(b=>b.onclick=()=>{const {l,i}=highlights[+b.dataset.index];map.panTo([i.lat,i.lon]);details(l,i)});
}
function sync(){$('radar-toggle').disabled=!layers.some(l=>l.id.endsWith('radar'));$('radar-status').hidden=!layers.some(l=>l.on&&l.id.endsWith('radar'));$('radar-toggle').classList.toggle('active',layers.some(l=>l.on&&l.id.endsWith('radar')));if(followed&&!layers.find(l=>l.id===followed.layer)?.on)stopFollowing();for(const l of layers){if(l.on){l.groupLayer.addTo(map);draw(l)}else map.removeLayer(l.groupLayer)}if(selected&&!layers.find(l=>l.id===selected.layer)?.on){selected=null;$('detail').hidden=true}feed()}
function health(){
  const connected=layers.filter(l=>['ok','partial'].includes(l.status)&&!l.configurationRequired&&!l.zoomRequired&&!l.coverageUnavailable).length;
  const issues=layers.filter(l=>['unavailable','stale','partial'].includes(l.status)).length;
  $('refresh-status').textContent=`${connected} sources responding${layers.some(l=>l.configurationRequired)?` · ${layers.filter(l=>l.configurationRequired).length} need access`:''}${issues?` · ${issues} need attention`:''} · source-specific refresh`;
  $('catalog-summary').textContent=`${layers.length} integrated sources · ${catalog.filter(s=>!s.supersededBy&&ScoutExplore.applies(s,currentBounds())).length-layers.length} additional sources cataloged`;
}
async function load(l){
  l.loading=true;const request=l.request=new AbortController(),requestedKey=l.queryKey;
  try{
    const r=await fetch(`/api/${l.id}${l.viewport?'?bbox='+encodeURIComponent(requestedKey):''}`,{signal:AbortSignal.any([request.signal,AbortSignal.timeout(70000)])});
    if(!r.ok)throw Error('Backend unavailable');const d=await r.json();if(!Array.isArray(d.items))throw Error('Invalid response');if(request.signal.aborted||(l.viewport&&requestedKey!==l.queryKey))return;
    if(moving(l)){
      l.trails??=new Map();
      for(const i of d.items){l.trails.set(i.id,ScoutMotion.merge(l.trails.get(i.id)||[],[...(d.history?.[i.id]||[]),i]))}
      for(const [id,trail] of l.trails)if(!trail.length||Date.now()-trail.at(-1).time>600000)l.trails.delete(id);
    }else if(l.fetchedAt){
      const previous=new Map(l.items.map(i=>[i.id,i]));
      for(const i of d.items){const old=previous.get(i.id);if(ScoutMotion.availabilityChanged(old,i))i.changedAt=Date.now();else if(old?.changedAt)i.changedAt=old.changedAt;if(old?.newAt)i.newAt=old.newAt;else if(!old&&l.group==='Safety'&&i.time&&Date.now()-i.time<86400000){i.newAt=Date.now();if(l.on&&layers.includes(l))newReports++}}
    }
    Object.assign(l,{zoomRequired:false,coverageUnavailable:false},d);l.next=Date.now()+(['ok','partial'].includes(l.status)?l.refresh:Math.max(60,l.retryAfter||0))*1000;
  }catch{
    if(request.signal.aborted||(l.viewport&&requestedKey!==l.queryKey))return;
    l.status=l.fetchedAt?'stale':'unavailable';l.error='Cannot reach the Scout data server. Start python scout/server.py and retry.';l.next=Date.now()+60000;
  }finally{
    l.loading=false;const el=$(`status-${l.id}`);if(el)el.textContent=status(l);if(l.on&&layers.includes(l))draw(l);feed();health();
    if(selected?.layer===l.id){const item=l.items.find(i=>i.id===selected.id);if(item)details(l,item);else{selected=null;$('detail').hidden=true;toast('That record is no longer in the latest source response.')}}
  }
}
function refresh(force=false){
  // Rebuild the queue from the current view whenever a slot opens. A slow
  // request must not hold the next region behind an entire previous batch.
  if(force)layers.filter(l=>!l.loading).forEach(l=>l.next=0);
  const queue=layers.filter(l=>!l.loading&&Date.now()>=l.next)
    .sort((a,b)=>Number(moving(b))-Number(moving(a)));
  while(activeLoads<4&&queue.length){
    const l=queue.shift();activeLoads++;
    load(l).finally(()=>{activeLoads--;refresh();health()});
  }
  $('refresh').disabled=activeLoads>0;
}
function cancelLoad(l){
  if(l.loading){l.request?.abort();l.next=0}
}

function preset(p){selectedPreset=p;allLayers.forEach(l=>l.on=p==='all'?true:p==='default'?(moving(l)||l.kind==='Live'&&l.group==='Safety'):p==='move'?moving(l):['Earth','Water'].includes(l.group));document.querySelectorAll('[data-preset]').forEach(b=>b.classList.toggle('active',b.dataset.preset===p));controls();sync()}
document.querySelectorAll('[data-preset]').forEach(b=>b.onclick=()=>preset(b.dataset.preset));$('reset').onclick=()=>preset('all');$('refresh').onclick=()=>refresh(true);
function centerLon(){return ScoutExplore.wrap(map.getCenter().lng)}
function currentBounds(){const b=map.getBounds();return ScoutExplore.normalize(b.getWest(),b.getSouth(),b.getEast(),b.getNorth())}
function applyViewport(){
 if(!allLayers.length)return;
 const bounds=currentBounds(),next=allLayers.filter(l=>ScoutExplore.applies(l,bounds));
 const destinations=next.filter(l=>l.destination&&ScoutExplore.applies(l,[centerLon(),map.getCenter().lat,centerLon()+.000001,map.getCenter().lat+.000001]));
 const regions=Object.keys(ScoutExplore.regions).filter(k=>ScoutExplore.intersects(bounds,ScoutExplore.regions[k]));
 const center=map.getCenter();activeRegion=regions.length===1?regions[0]:'world';home=homes[activeRegion]||homes.seattle;
 document.querySelector('.brand small').textContent='EXPLORE';
 $('place').textContent=map.getZoom()<=4?'World explorer':destinations.length===1?(destinations[0].areaName||destinations[0].destination.name):regions.length===1?homes[regions[0]].name:regions.length>1?'West Coast & beyond':`${center.lat.toFixed(2)}°, ${ScoutExplore.wrap(center.lng).toFixed(2)}°`;
 $('transit-credit').hidden=!regions.includes('seattle');
 document.querySelector('.coverage p').textContent='Feeds follow your map automatically. Global reception varies; local sources connect automatically where available. Transit coverage varies by operator and service hours. Delayed and modeled data stay labeled.';
 let changed=layers.map(l=>l.id).join()!==next.map(l=>l.id).join();
 for(const l of layers)if(!next.includes(l)){cancelLoad(l);map.removeLayer(l.groupLayer)}
 layers=next;
 for(const l of layers.filter(l=>l.viewport)){
  if(!l.queryBounds||!ScoutExplore.contains(l.queryBounds,bounds)||Math.abs((l.queryZoom??map.getZoom())-map.getZoom())>=2){
   l.queryBounds=ScoutExplore.queryBounds(bounds);const key=l.queryBounds.join(',');l.queryZoom=map.getZoom();
   if(key!==l.queryKey){cancelLoad(l);l.queryKey=key;l.next=0;l.items=[];l.fetchedAt=null;l.status='loading';l.zoomRequired=false;l.coverageUnavailable=false;l.error=null;changed=true}
  }
 }
 if(changed){controls();sync();health();refresh()}
 if(!changed)layers.filter(l=>l.on&&!moving(l)).forEach(draw);
 updateScenes();feed();
}
function scheduleViewport(){if(!viewportTimer)viewportTimer=setTimeout(()=>{viewportTimer=null;applyViewport()},450)}
function setRegion(region){stopFollowing();selected=null;$('detail').hidden=true;const v=homes[region];if(v){map.setView(v.center,v.zoom);applyViewport()}}
function goHome(){setRegion('seattle')}$('home').onclick=goHome;
$('region').onchange=()=>{const key=$('region').value;if(key==='world'){stopFollowing();map.setView([24,0],3);applyViewport()}else if(key==='london'){stopFollowing();map.setView([51.5,-.12],11);applyViewport()}else if(key==='tokyo'){stopFollowing();map.setView([35.68,139.76],11);applyViewport()}else setRegion(key);$('region').value='explore'};
$('mobile-layers').onclick=()=>$('sidebar').classList.toggle('open');map.on('click',()=>$('sidebar').classList.remove('open'));map.on('moveend',()=>{scheduleViewport();feed();layers.filter(l=>l.on&&moving(l)).forEach(draw)});map.on('zoomend',()=>{layers.filter(l=>l.on).forEach(draw);feed()});
$('theme').onclick=()=>{dark=!dark;$('map').classList.toggle('dark-map',dark)};
$('locate').onclick=()=>{if(!navigator.geolocation)return toast('Location is not supported.');navigator.geolocation.getCurrentPosition(p=>{map.setView([p.coords.latitude,p.coords.longitude],12);$('place').textContent='Around you';toast('Feeds update automatically for this map view.')},()=>toast('Location unavailable. Search for a city instead.'),{timeout:10000})};
$('save').onclick=()=>{try{localStorage.setItem('scout-regional-view',JSON.stringify({region:activeRegion,center:map.getCenter(),zoom:map.getZoom(),place:$('place').textContent,layers:allLayers.filter(l=>l.on).map(l=>l.id)}));toast('View saved on this device.')}catch{toast('Your browser could not save this view.')}};
$('restore').onclick=()=>{try{const v=JSON.parse(localStorage.getItem('scout-regional-view'));if(!v)return toast('Save a view first using ☆ Save view.');setRegion(v.region in homes?v.region:'seattle');map.setView(v.center,v.zoom);$('place').textContent=v.place;selectedPreset='custom';const saved=new Set(v.layers.map(id=>catalog.find(s=>s.id===id)?.supersededBy||id));allLayers.forEach(l=>l.on=saved.has(l.id));applyViewport();controls();sync();toast('Saved view restored.')}catch{toast('Saved view unavailable.')}};
let searching=false;
$('search').onsubmit=async e=>{
 e.preventDefault();const q=$('query').value.trim();if(!q||searching)return;
 const c=q.match(/^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/);
 if(c){if(Math.abs(+c[1])>90||Math.abs(+c[2])>180){$('search-result').textContent='Coordinates are out of range.';return}map.setView([+c[1],+c[2]],12);$('place').textContent=q;$('search-result').textContent='';return}
 searching=true;$('search-result').textContent='Finding your place…';
 try{const r=await fetch('https://geocoding-api.open-meteo.com/v1/search?count=1&language=en&format=json&name='+encodeURIComponent(q),{signal:AbortSignal.timeout(15000)});if(!r.ok)throw Error();const d=await r.json();if(!d.results?.length)throw Error();const p=d.results[0];map.setView([p.latitude,p.longitude],12);$('place').textContent=`${p.name}, ${p.admin1||p.country}`;$('search-result').textContent='Feeds update automatically for this map view.';$('sidebar').classList.remove('open')}catch{$('search-result').textContent='Search unavailable or no match. Try coordinates.'}finally{searching=false}
};
function showSources(){
 const q=$('source-query').value.toLowerCase();
 $('source-list').innerHTML=catalog.filter(s=>!s.supersededBy&&ScoutExplore.applies(s,currentBounds())).filter(s=>`${s.name} ${s.source} ${s.group} ${s.notes}`.toLowerCase().includes(q)).map(s=>{const l=layers.find(l=>l.id===s.id);return `<div class="source-row"><div><strong>${esc(s.name)}</strong><span class="source-chip">${esc(s.access==='integrated'?`${s.kind} · ${status(l)}`:s.access)}</span><small>${esc(s.source)}${s.coverage?' · '+esc(s.coverage):''}</small><p>${esc(s.notes)}</p>${l?`<small>Fetch interval: ${s.refresh}s · fetched ${esc(date(l.fetchedAt))}</small><p>${esc(l.error||l.note||'Waiting for first response.')}</p>`:''}</div><a href="${esc(s.url)}" target="_blank" rel="noopener">Source ↗</a></div>`}).join('');
}
$('sources').onclick=()=>{showSources();$('source-dialog').showModal()};$('source-query').oninput=showSources;$('source-dialog').querySelector('.close').onclick=()=>$('source-dialog').close();$('open-catalog').onclick=$('sources').onclick;
function clock(){$('clock').textContent=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',timeZoneName:'short'})}clock();setInterval(clock,1000);
async function boot(){try{const r=await fetch('sources.json');if(!r.ok)throw Error();catalog=await r.json();for(const s of catalog.filter(s=>s.destination)){homes[s.id]={...s.destination};const option=document.createElement('option');option.value=s.id;option.textContent=s.destination.name+(s.adapter==='gbfs'?' · live bikes':s.id.includes('ships')?' · live ships':' · live transit');$('region').append(option)}allLayers=catalog.filter(s=>s.access==='integrated'&&!s.supersededBy).map(s=>({...s,on:true,items:[],status:'loading',next:0,groupLayer:L.layerGroup([],{attribution:s.id==='iss-orbit'?'<a href="https://wheretheiss.at" target="_blank" rel="noopener">ISS orbital model: Where the ISS at?</a>':s.id==='world-air'?'<a href="https://adsb.fi" target="_blank" rel="noopener">Aircraft: adsb.fi</a>':s.id==='canberra-rail'?'<a href="https://www.data.act.gov.au/Transport/Canberra-Metro-Light-Rail-Transit-Feed-Vehicle-Upd/4f7h-bvpk" target="_blank" rel="noopener">Canberra Metro / ACT Government</a> · <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener">CC BY-SA 4.0</a> · filtered &amp; interpolated':s.id==='fi-ships'?'<a href="https://www.digitraffic.fi/en/marine-traffic/" target="_blank" rel="noopener">Fintraffic / Digitraffic</a> · <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener">CC BY 4.0</a> · filtered &amp; interpolated':undefined})}));showWorld();setInterval(()=>{refresh();layers.filter(l=>l.on&&moving(l)).forEach(draw);feed()},5000)}catch{toast('Source catalog failed to load. Start the Scout server and refresh.')}}
