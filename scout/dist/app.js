'use strict';
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const homes={bay:{center:[37.82,-122.25],zoom:10,name:'San Francisco Bay Area'},seattle:{center:[47.61,-122.33],zoom:11,name:'Seattle / Puget Sound'}};
let activeRegion='seattle',home=homes.seattle,allLayers=[];
const map = L.map('map',{zoomControl:false}).setView(home.center,home.zoom);
L.control.zoom({position:'topright'}).addTo(map);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',maxZoom:19}).addTo(map).on('tileerror',()=>toast('Some basemap tiles are unavailable.'));
let layers=[],catalog=[],selected=null,dark=false,toastTimer,loading=false;
const moving=l=>l.group==='Motion'&&l.maxAge>0;
const groups=['Safety','Motion','Roads','Earth','Water','City'];
function toast(s){$('toast').textContent=s;$('toast').style.display='block';clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').style.display='none',5000)}
function ago(t){if(!t)return 'Time not supplied';const mins=Math.floor((Date.now()-t)/60000);return mins<0?'Future timestamp':mins<1?'Just now':mins<60?`${mins}m ago`:mins<1440?`${Math.floor(mins/60)}h ago`:`${Math.floor(mins/1440)}d ago`}
function date(t){return t?new Date(t).toLocaleString(): 'Not supplied'}
function staleItem(l,i){return Boolean(l.maxAge&&i.time&&Date.now()-i.time>l.maxAge*1000)}
function mapped(l){return l.items.filter(i=>!(['air','sea-air','sea-metro','sea-sound','sea-community','sea-everett','sea-kitsap','sea-ferries'].includes(l.id))||!staleItem(l,i))}
function status(l){if(l.configurationRequired)return 'Access code needed';if(l.loading&&!l.fetchedAt)return 'Connecting…';if(l.status==='unavailable')return 'Unavailable · retrying';if(l.status==='stale')return 'Feed unavailable · cached data';if(!l.fetchedAt)return 'Not loaded';if(l.id.endsWith('radar')&&l.raster)return `Radar frame · ${ago(Date.parse(l.raster.time))}`;return `${mapped(l).length} mapped · ${l.kind.toLowerCase()}${l.status==='partial'?' · partial':''}`}
function controls(){
  $('layers').innerHTML=groups.map(g=>`<div class="layer-group"><h3>${g}</h3>${layers.filter(l=>l.group===g).map(l=>`<div class="layer"><span class="layer-icon" style="--color:${l.color}">${l.icon}</span><div class="layer-info"><strong>${esc(l.name)}</strong><small id="status-${l.id}">${esc(status(l))}</small></div><label class="switch"><input type="checkbox" data-layer="${l.id}" aria-label="${esc(l.name)}" ${l.on?'checked':''}><span></span></label></div>`).join('')}</div>`).join('');
  document.querySelectorAll('[data-layer]').forEach(e=>e.onchange=()=>{layers.find(l=>l.id===e.dataset.layer).on=e.checked;document.querySelectorAll('[data-preset]').forEach(b=>b.classList.remove('active'));sync()});
}
function details(l,i){
  selected={layer:l.id,id:i.id};$('detail').hidden=false;
  const stale=l.status==='stale'||staleItem(l,i);
  $('detail').innerHTML=`<button class="close" aria-label="Close details">×</button><div class="detail-status">${stale?'STALE / LAST KNOWN · ':''}${esc(l.kind.toUpperCase())}</div><h3>${esc(i.title)}</h3><p>${esc(i.description)}</p><p><strong>Observation / report:</strong> ${esc(date(i.time))}<br><strong>Fetched:</strong> ${esc(date(l.fetchedAt))}</p>${i.link?`<a href="${esc(i.link)}" target="_blank" rel="noopener">Open official camera viewer ↗</a>`:''}${i.image?`<a class="snapshot-link" href="${esc(i.image)}" target="_blank" rel="noopener">Open current camera snapshot ↗</a><p>Image capture time is not verified. Check the timestamp in the image.</p>`:''}${moving(l)?'<p>Faint trails connect recent reported positions when zoomed in; they are not road routes or predicted movement.</p>':''}<p>${esc(l.source)}<br>${esc(l.coverage)}<br>${i.lat.toFixed(4)}°, ${i.lon.toFixed(4)}°</p><p class="source-note">${esc(l.note||l.notes)}</p><a href="${esc(l.url)}" target="_blank" rel="noopener">Source documentation ↗</a>`;
  $('detail').querySelector('.close').onclick=()=>{selected=null;$('detail').hidden=true};
}
function draw(l){
  if(l.id.endsWith('radar')){
    if(!l.on||!l.raster)return;
    if(!l.wms){l.wms=L.tileLayer.wms(l.raster.url,{layers:l.raster.layer,format:'image/png',transparent:true,opacity:.55,time:l.raster.time,attribution:'Radar © NOAA / NWS'}).on('tileerror',()=>{l.status='partial';l.error='Some radar tiles failed. A blank tile is not proof of clear weather.';health();const el=$(`status-${l.id}`);if(el)el.textContent='Radar imagery partially unavailable';});l.groupLayer.addLayer(l.wms)}
    else if(l.wms.wmsParams.time!==l.raster.time)l.wms.setParams({time:l.raster.time});
    return;
  }
  l.groupLayer.clearLayers();if(!l.on)return;
  if(moving(l)&&l.trails&&map.getZoom()>=12){for(const trail of l.trails.values()){const recent=trail.filter(i=>Date.now()-i.time<180000);if(recent.length>1)L.polyline(recent.map(i=>[i.lat,i.lon]),{color:l.color,weight:2,opacity:.4,interactive:false}).addTo(l.groupLayer)}}
  const buckets=new Map();
  for(const i of mapped(l)){
    const p=map.project([i.lat,i.lon],map.getZoom());
    const key=map.getZoom()>=15?i.id:`${Math.floor(p.x/45)}:${Math.floor(p.y/45)}`;
    if(!buckets.has(key))buckets.set(key,[]);buckets.get(key).push(i);
  }
  for(const bucket of buckets.values()){
    const i=bucket[0],isCluster=bucket.length>1;
    const lat=isCluster?bucket.reduce((s,i)=>s+i.lat,0)/bucket.length:i.lat;
    const lon=isCluster?bucket.reduce((s,i)=>s+i.lon,0)/bucket.length:i.lon;
    const icon=L.divIcon({className:'signal',html:`<span class="marker ${isCluster?'cluster':''} ${l.status==='stale'||staleItem(l,i)?'stale':''}" style="--color:${l.color}">${isCluster?bucket.length:l.icon}</span>`,iconSize:[30,30],iconAnchor:[15,15]});
    L.marker([lat,lon],{icon,title:isCluster?`${bucket.length} ${l.name} · zoom to expand`:i.title}).on('click',()=>{if(isCluster)map.fitBounds(bucket.map(i=>[i.lat,i.lon]),{padding:[60,60],maxZoom:16});else details(l,i)}).addTo(l.groupLayer);
  }
  for(const i of mapped(l).filter(i=>i.geometry))L.geoJSON(i.geometry,{style:{color:l.color,weight:1.5,fillOpacity:.10}}).on('click',()=>details(l,i)).addTo(l.groupLayer);
}
function inView(i){if(map.getBounds().contains([i.lat,i.lon]))return true;if(i.geometry){try{const b=L.geoJSON(i.geometry).getBounds();return b.isValid()&&map.getBounds().intersects(b)}catch{return false}}return false}
function feed(){
  const items=layers.filter(l=>l.on).flatMap(l=>mapped(l).filter(inView).map(i=>({l,i}))).sort((a,b)=>(b.i.time||0)-(a.i.time||0));
  $('signal-count').textContent=items.length.toLocaleString();$('visible-count').textContent=`${items.length.toLocaleString()} signals in view`;$('layer-count').textContent=layers.filter(l=>l.on).length;
  $('feed').innerHTML=items.length?items.slice(0,25).map(({l,i},n)=>`<button class="feed-item" data-index="${n}"><span class="layer-icon" style="--color:${l.color}">${l.icon}</span><span><strong>${esc(i.title)}</strong><small>${esc(i.summary||l.name)}</small><span class="badge">${l.status==='stale'||staleItem(l,i)?'STALE · ':''}${esc(l.kind)} · ${esc(ago(i.time))}</span></span></button>`).join(''):'<p class="empty">No mapped records in this view. Enable a layer or zoom out. A blank map does not establish that no activity exists.</p>';
  document.querySelectorAll('[data-index]').forEach(b=>b.onclick=()=>{const {l,i}=items[+b.dataset.index];map.panTo([i.lat,i.lon]);details(l,i)});
}
function sync(){for(const l of layers){if(l.on){l.groupLayer.addTo(map);draw(l)}else map.removeLayer(l.groupLayer)}if(selected&&!layers.find(l=>l.id===selected.layer)?.on){selected=null;$('detail').hidden=true}feed()}
function health(){
  const connected=layers.filter(l=>['ok','partial'].includes(l.status)&&!l.configurationRequired).length;
  const issues=layers.filter(l=>['unavailable','stale','partial'].includes(l.status)).length;
  $('refresh-status').textContent=`${connected} sources responding${layers.some(l=>l.configurationRequired)?' · 1 needs an access code':''}${issues?` · ${issues} need attention`:''} · source-specific refresh`;
  $('catalog-summary').textContent=`${layers.length} integrated sources · ${catalog.filter(s=>s.region===activeRegion).length-layers.length} additional sources cataloged`;
}
async function load(l){
  l.loading=true;
  try{
    const r=await fetch(`/api/${l.id}`,{signal:AbortSignal.timeout(70000)});
    if(!r.ok)throw Error('Backend unavailable');const d=await r.json();if(!Array.isArray(d.items))throw Error('Invalid response');
    if(moving(l)){l.trails??=new Map();for(const i of d.items){if(!i.time)continue;const trail=l.trails.get(i.id)||[];if(!trail.length||i.time>trail.at(-1).time){trail.push(i);l.trails.set(i.id,trail.slice(-6))}}for(const [id,trail] of l.trails){if(Date.now()-trail.at(-1).time>180000)l.trails.delete(id)}}
    Object.assign(l,d);l.next=Date.now()+(['ok','partial'].includes(l.status)?l.refresh:60)*1000;
  }catch{
    l.status=l.fetchedAt?'stale':'unavailable';l.error='Cannot reach the Scout data server. Start python scout/server.py and retry.';l.next=Date.now()+60000;
  }finally{
    l.loading=false;const el=$(`status-${l.id}`);if(el)el.textContent=status(l);if(l.on&&layers.includes(l))draw(l);feed();health();
    if(selected?.layer===l.id){const item=l.items.find(i=>i.id===selected.id);if(item)details(l,item);else{selected=null;$('detail').hidden=true;toast('That record is no longer in the latest source response.')}}
  }
}
async function refresh(force=false){
  if(loading)return;loading=true;$('refresh').disabled=true;
  const startedRegion=activeRegion;
  const queue=layers.filter(l=>!l.loading&&(force||Date.now()>=l.next));
  async function worker(){while(queue.length)await load(queue.shift())}
  try{await Promise.all(Array.from({length:Math.min(4,queue.length)},worker))}finally{loading=false;$('refresh').disabled=false;health();if(startedRegion!==activeRegion)refresh()}
}
function preset(p){layers.forEach(l=>l.on=p==='all'?true:p==='default'?l.defaultOn:p==='move'?['Motion','Roads'].includes(l.group):['Earth','Water'].includes(l.group));document.querySelectorAll('[data-preset]').forEach(b=>b.classList.toggle('active',b.dataset.preset===p));controls();sync()}
document.querySelectorAll('[data-preset]').forEach(b=>b.onclick=()=>preset(b.dataset.preset));$('reset').onclick=()=>preset('default');$('refresh').onclick=()=>refresh(true);
function setRegion(region){
 for(const l of layers)map.removeLayer(l.groupLayer);
 activeRegion=region;home=homes[region];layers=allLayers.filter(l=>l.region===region);
 selected=null;$('detail').hidden=true;$('region').value=region;
 document.querySelector('.brand small').textContent=region==='seattle'?'PUGET SOUND':'BAY AREA';
 document.querySelector('.demo-label').textContent='Live / delayed / daily / modeled · No simulated events';
 document.querySelector('.coverage p').textContent=region==='seattle'?'Transit markers use actual GPS reports. Fire calls cover Seattle; regional coverage varies. Police and parking are delayed history.':'SF dispatch and 311 cover San Francisco only. Regional coverage varies.';
 $('transit-credit').hidden=region!=='seattle';
 map.setView(home.center,home.zoom);$('place').textContent=home.name;
 controls();sync();health();refresh();
}
function goHome(){map.setView(home.center,home.zoom);$('place').textContent=home.name}$('home').onclick=goHome;
$('region').onchange=()=>setRegion($('region').value);
$('mobile-layers').onclick=()=>$('sidebar').classList.toggle('open');map.on('click',()=>$('sidebar').classList.remove('open'));map.on('moveend',feed);map.on('zoomend',()=>{layers.filter(l=>l.on).forEach(draw);feed()});
$('theme').onclick=()=>{dark=!dark;$('map').classList.toggle('dark-map',dark)};
$('locate').onclick=()=>{if(!navigator.geolocation)return toast('Location is not supported.');navigator.geolocation.getCurrentPosition(p=>{map.setView([p.coords.latitude,p.coords.longitude],12);$('place').textContent='Around you';toast('Feed coverage remains in the selected region.')},()=>toast('Location unavailable. Search for a city instead.'),{timeout:10000})};
$('save').onclick=()=>{try{localStorage.setItem('scout-regional-view',JSON.stringify({region:activeRegion,center:map.getCenter(),zoom:map.getZoom(),place:$('place').textContent,layers:layers.filter(l=>l.on).map(l=>l.id)}));toast('View saved on this device.')}catch{toast('Your browser could not save this view.')}};
$('restore').onclick=()=>{try{const v=JSON.parse(localStorage.getItem('scout-regional-view'));if(!v)return toast('Save a view first using ☆ Save view.');setRegion(v.region in homes?v.region:'seattle');map.setView(v.center,v.zoom);$('place').textContent=v.place;layers.forEach(l=>l.on=v.layers.includes(l.id));controls();sync();toast('Saved view restored.')}catch{toast('Saved view unavailable.')}};
let searching=false;
$('search').onsubmit=async e=>{
 e.preventDefault();const q=$('query').value.trim();if(!q||searching)return;
 const c=q.match(/^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/);
 if(c){if(Math.abs(+c[1])>90||Math.abs(+c[2])>180){$('search-result').textContent='Coordinates are out of range.';return}map.setView([+c[1],+c[2]],12);$('place').textContent=q;$('search-result').textContent='';return}
 searching=true;$('search-result').textContent='Finding your place…';
 try{const r=await fetch('https://geocoding-api.open-meteo.com/v1/search?count=1&language=en&format=json&name='+encodeURIComponent(q),{signal:AbortSignal.timeout(15000)});if(!r.ok)throw Error();const d=await r.json();if(!d.results?.length)throw Error();const p=d.results[0];map.setView([p.latitude,p.longitude],12);$('place').textContent=`${p.name}, ${p.admin1||p.country}`;$('search-result').textContent='Feed coverage remains in the selected region.';$('sidebar').classList.remove('open')}catch{$('search-result').textContent='Search unavailable or no match. Try coordinates.'}finally{searching=false}
};
function showSources(){
 const q=$('source-query').value.toLowerCase();
 $('source-list').innerHTML=catalog.filter(s=>s.region===activeRegion).filter(s=>`${s.name} ${s.source} ${s.group} ${s.notes}`.toLowerCase().includes(q)).map(s=>{const l=layers.find(l=>l.id===s.id);return `<div class="source-row"><div><strong>${esc(s.name)}</strong><span class="source-chip">${esc(s.access==='integrated'?`${s.kind} · ${status(l)}`:s.access)}</span><small>${esc(s.source)}${s.coverage?' · '+esc(s.coverage):''}</small><p>${esc(s.notes)}</p>${l?`<small>Fetch interval: ${s.refresh}s · fetched ${esc(date(l.fetchedAt))}</small><p>${esc(l.error||l.note||'Waiting for first response.')}</p>`:''}</div><a href="${esc(s.url)}" target="_blank" rel="noopener">Source ↗</a></div>`}).join('');
}
$('sources').onclick=()=>{showSources();$('source-dialog').showModal()};$('source-query').oninput=showSources;$('source-dialog').querySelector('.close').onclick=()=>$('source-dialog').close();$('open-catalog').onclick=$('sources').onclick;
function clock(){$('clock').textContent=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',timeZoneName:'short'})}clock();setInterval(clock,1000);
async function boot(){try{const r=await fetch('sources.json');if(!r.ok)throw Error();catalog=await r.json();allLayers=catalog.filter(s=>s.access==='integrated').map(s=>({...s,on:s.defaultOn,items:[],status:'loading',next:0,groupLayer:L.layerGroup()}));setRegion('seattle');setInterval(()=>{refresh();layers.filter(l=>l.on&&moving(l)).forEach(draw);feed()},15000)}catch{toast('Source catalog failed to load. Start the Scout server and refresh.')}}boot();
