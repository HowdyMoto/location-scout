/* Timestamped observation playback. Never extrapolates beyond received reports. */
(function(root){
 'use strict';
 const maxSpeed=layer=>layer.maxSpeed|| (layer.id==='iss-orbit'||layer.vehicleType==='satellite'?9000:(layer.id||'').includes('air')?400:65);
 function bufferDelay(layer,now=Date.now()){
  const gaps=[],ages=[];
  for(const track of layer.trails?.values()||[]){
   const last=track.at(-1);if(!last||now-last.time>300000)continue;
   ages.push(Math.max(0,now-last.time));
   for(let n=Math.max(1,track.length-5);n<track.length;n++){const d=track[n].time-track[n-1].time;if(d>0&&d<=120000)gaps.push(d)}
   if(ages.length>=150)break;
  }
  const percentile=(a,p,fallback)=>a.length?a.sort((x,y)=>x-y)[Math.floor((a.length-1)*p)]:fallback;
  const cadence=percentile(gaps,.75,(layer.refresh||30)*1000);
  return Math.min(180000,Math.max(10000,percentile(ages,.75,0)+Math.max(cadence,(layer.refresh||5)*1000)+5000));
 }
 const radians=d=>d*Math.PI/180;
 const wrapLongitude=lon=>((lon+180)%360+360)%360-180;
 function trailCoordinates(points,centerLongitude){
  let previous=centerLongitude;
  return points.map(p=>{const lon=p.lon+360*Math.round((previous-p.lon)/360);previous=lon;return [p.lat,lon]});
 }
 function distance(a,b){const p=radians(b.lat-a.lat),q=radians(b.lon-a.lon);return 6371000*2*Math.asin(Math.min(1,Math.sqrt(Math.sin(p/2)**2+Math.cos(radians(a.lat))*Math.cos(radians(b.lat))*Math.sin(q/2)**2)))}
 function bearing(a,b){const p=radians(a.lat),q=radians(b.lat),d=radians(b.lon-a.lon);return (Math.atan2(Math.sin(d)*Math.cos(q),Math.cos(p)*Math.sin(q)-Math.sin(p)*Math.cos(q)*Math.cos(d))*180/Math.PI+360)%360}
 function merge(previous,incoming,now=Date.now()){
  const by=new Map();
  for(const p of [...previous,...incoming])if(Number.isFinite(p.lat)&&Number.isFinite(p.lon)&&Number.isFinite(p.time)&&p.time>now-600000&&p.time<=now+60000)by.set(p.time,p);
  return [...by.values()].sort((a,b)=>a.time-b.time).slice(-600);
 }
 function alongRoute(path,distance){
  if(!path||path.length<2||distance<path[0][2]||distance>path.at(-1)[2])return null;
  let lo=1,hi=path.length-1;while(lo<hi){const m=(lo+hi)>>1;if(path[m][2]<distance)lo=m+1;else hi=m}
  const a=path[lo-1],b=path[lo],t=(distance-a[2])/(b[2]-a[2]||1);
  return {lat:a[0]+(b[0]-a[0])*t,lon:wrapLongitude(a[1]+wrapLongitude(b[1]-a[1])*t),heading:bearing({lat:a[0],lon:a[1]},{lat:b[0],lon:b[1]})};
 }
 function sample(points,target,maxSpeed=400,shapes={}){
  if(!points.length)return null;
  if(target<points[0].time)return {...points[0],state:'buffering'};
  if(points.length>1&&target<points.at(-1).time){
   let lo=1,hi=points.length-1;while(lo<hi){const mid=(lo+hi)>>1;if(points[mid].time<=target)lo=mid+1;else hi=mid}
   const n=lo,a=points[n-1],b=points[n];
   const dt=b.time-a.time,d=distance(a,b);
   if(dt>120000||d/(dt/1000)>maxSpeed)return {...a,state:'gap'};
   const t=(target-a.time)/dt;
   if(a.shapeId&&a.shapeId===b.shapeId&&a.tripId&&a.tripId===b.tripId&&Number.isFinite(a.routeDistance)&&Number.isFinite(b.routeDistance)){
    const length=b.routeDistance-a.routeDistance;
    // Reject reverse matches, loop shortcuts, and ambiguous large detours.
    if(length>=0&&length<=d*2+100&&length/(dt/1000)<=maxSpeed){
     const matched=alongRoute(shapes[a.shapeId],a.routeDistance+length*t);
     if(matched)return {...a,...matched,time:target,state:length>2?'moving':'stationary',routeMatched:true,from:a.time,to:b.time};
    }
   }
   return {...a,lat:a.lat+(b.lat-a.lat)*t,lon:wrapLongitude(a.lon+wrapLongitude(b.lon-a.lon)*t),time:target,heading:d>2?bearing(a,b):(a.heading??b.heading),state:d>2?'moving':'stationary',from:a.time,to:b.time};
  }
  return {...points.at(-1),state:'holding'};
 }
 function balanced(groups,limit=20){
  const out=[];for(let n=0;out.length<limit;n++){
   let added=false;for(const group of groups){if(group[n]){out.push(group[n]);added=true;if(out.length===limit)break}}
   if(!added)break;
  }return out;
 }
 function availabilityChanged(old,item){
  if(!old?.availability||!item.availability||!Number.isFinite(old.time)||!Number.isFinite(item.time)||item.time<=old.time)return false;
  return ['bikes','docks','renting','returning'].some(key=>old.availability[key]!==item.availability[key]);
 }
 function activity(layers,center,now=Date.now()){
  const result={vehicles:0,moving:0,stations:0,checked:false,unavailable:false};
  if(!center)return result;
  for(const l of layers){
   if(!l.motion&&l.adapter!=='gbfs'&&l.id!=='bikes')continue;
   if(l.zoomRequired||l.coverageUnavailable||l.configurationRequired)continue;
   if(['stale','unavailable'].includes(l.status)){result.unavailable=true;continue}
   if(!['ok','partial'].includes(l.status)||!Number.isFinite(l.fetchedAt)||now-l.fetchedAt>300000)continue;
   result.checked=true;
   for(const i of l.items||[]){
    if(!Number.isFinite(i.time)||now-i.time>Math.min(l.maxAge||300,300)*1000||i.time>now+60000||!Number.isFinite(i.lat)||!Number.isFinite(i.lon))continue;
    if(distance({lat:center[0],lon:center[1]},i)>50000)continue;
    if(l.motion){result.vehicles++;if(sample(l.trails?.get(i.id)||[i],now-(l.playbackDelayMs??90000),maxSpeed(l))?.state==='moving')result.moving++}
    else if(i.availability||l.id==='bikes')result.stations++;
   }
  }
  return result;
 }
 function activeDestinations(places,lastId){
  const candidates=places.filter(p=>p.id!==lastId);
  for(const field of ['moving','vehicles','stations']){const active=candidates.filter(p=>p.activity?.[field]>0);if(active.length)return active}
  return candidates;
 }
 const api={maxSpeed,bufferDelay,alongRoute,distance,bearing,merge,sample,balanced,availabilityChanged,wrapLongitude,trailCoordinates,activity,activeDestinations};
 if(typeof module!=='undefined')module.exports=api;else root.ScoutMotion=api;
})(typeof globalThis!=='undefined'?globalThis:this);
