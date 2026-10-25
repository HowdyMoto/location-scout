/* Timestamped observation playback. Never extrapolates beyond received reports. */
(function(root){
 'use strict';
 const radians=d=>d*Math.PI/180;
 function distance(a,b){const p=radians(b.lat-a.lat),q=radians(b.lon-a.lon);return 6371000*2*Math.asin(Math.min(1,Math.sqrt(Math.sin(p/2)**2+Math.cos(radians(a.lat))*Math.cos(radians(b.lat))*Math.sin(q/2)**2)))}
 function bearing(a,b){const p=radians(a.lat),q=radians(b.lat),d=radians(b.lon-a.lon);return (Math.atan2(Math.sin(d)*Math.cos(q),Math.cos(p)*Math.sin(q)-Math.sin(p)*Math.cos(q)*Math.cos(d))*180/Math.PI+360)%360}
 function merge(previous,incoming,now=Date.now()){
  const by=new Map();
  for(const p of [...previous,...incoming])if(Number.isFinite(p.lat)&&Number.isFinite(p.lon)&&Number.isFinite(p.time)&&p.time>now-600000&&p.time<=now+60000)by.set(p.time,p);
  return [...by.values()].sort((a,b)=>a.time-b.time).slice(-40);
 }
 function sample(points,target,maxSpeed=400){
  if(!points.length)return null;
  if(target<points[0].time)return {...points[0],state:'buffering'};
  for(let n=1;n<points.length;n++){
   const a=points[n-1],b=points[n];if(target>=b.time)continue;
   const dt=b.time-a.time,d=distance(a,b);
   if(dt>120000||d/(dt/1000)>maxSpeed)return {...a,state:'gap'};
   const t=(target-a.time)/dt;
   return {...a,lat:a.lat+(b.lat-a.lat)*t,lon:a.lon+(b.lon-a.lon)*t,time:target,heading:d>2?bearing(a,b):(a.heading??b.heading),state:d>2?'moving':'stationary',from:a.time,to:b.time};
  }
  return {...points.at(-1),state:'holding'};
 }
 function balanced(groups,limit=20){
  const out=[];for(let n=0;out.length<limit;n++){
   let added=false;for(const group of groups){if(group[n]){out.push(group[n]);added=true;if(out.length===limit)break}}
   if(!added)break;
  }return out;
 }
 const api={distance,bearing,merge,sample,balanced};
 if(typeof module!=='undefined')module.exports=api;else root.ScoutMotion=api;
})(typeof globalThis!=='undefined'?globalThis:this);
