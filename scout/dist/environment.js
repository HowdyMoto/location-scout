'use strict';
// Particle paths are visualizations of aggregate/model fields, never tracked objects.
let environmentCanvas=null,environmentParticles=[],environmentLast=0;
function windVector(field,lat,lon){
 const [w,s,e,n]=field.bounds,span=e>w?e-w:360+e-w,dx=(lon-w+360)%360;
 if(dx>span||lat<s||lat>n)return null;
 const x=dx/span*(field.size-1),y=(lat-s)/(n-s)*(field.size-1),ix=Math.min(field.size-2,Math.floor(x)),iy=Math.min(field.size-2,Math.floor(y));
 const tx=x-ix,ty=y-iy,at=(a,b)=>field.vectors[b*field.size+a];
 return [0,1].map(k=>at(ix,iy)[k]*(1-tx)*(1-ty)+at(ix+1,iy)[k]*tx*(1-ty)+at(ix,iy+1)[k]*(1-tx)*ty+at(ix+1,iy+1)[k]*tx*ty);
}
function environmentFrame(now){
 if(!environmentCanvas){
  environmentCanvas=document.createElement('canvas');environmentCanvas.className='environment-canvas';environmentCanvas.style.cssText='position:absolute;inset:0;pointer-events:none;z-index:450';map.getContainer().append(environmentCanvas);
  map.on('movestart zoomstart',()=>{environmentParticles=[];environmentCanvas.getContext('2d').clearRect(0,0,environmentCanvas.width,environmentCanvas.height)});
 }
 const size=map.getSize(),ctx=environmentCanvas.getContext('2d'),ratio=Math.min(2,devicePixelRatio||1);
 if(environmentCanvas.width!==Math.round(size.x*ratio)||environmentCanvas.height!==Math.round(size.y*ratio)){
  environmentCanvas.width=Math.round(size.x*ratio);environmentCanvas.height=Math.round(size.y*ratio);environmentCanvas.style.width=size.x+'px';environmentCanvas.style.height=size.y+'px';environmentParticles=[];
 }
 ctx.setTransform(ratio,0,0,ratio,0,0);ctx.clearRect(0,0,size.x,size.y);
 const dt=Math.min(.1,(now-environmentLast)/1000||.033);environmentLast=now;
 const wind=layers.find(l=>l.on&&l.field&&Date.now()-l.field.time<7200000);
 if(wind){
  while(environmentParticles.length<220)environmentParticles.push({x:Math.random()*size.x,y:Math.random()*size.y,age:Math.random()*120});
  ctx.strokeStyle='rgba(70,135,170,.65)';ctx.lineWidth=1;
  for(const p of environmentParticles){
   const ll=map.containerPointToLatLng([p.x,p.y]),v=windVector(wind.field,ll.lat,ScoutExplore.wrap(ll.lng));
   if(!v||p.age>180||p.x<0||p.x>size.x||p.y<0||p.y>size.y){p.x=Math.random()*size.x;p.y=Math.random()*size.y;p.age=0;continue}
   const dx=v[0]*dt*1.5,dy=-v[1]*dt*1.5;
   ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(p.x+dx*5,p.y+dy*5);ctx.stroke();
   if(!pausedAt){p.x+=dx;p.y+=dy;p.age++}
  }
 }else environmentParticles=[];
 for(const l of layers.filter(l=>l.on&&l.id==='world-traffic'&&l.status==='ok'))for(const i of l.items){
  if(!i.flow||Date.now()-i.time>600000||i.flow.speed<=0)continue;
  const path=i.flow.coordinates.map(p=>map.latLngToContainerPoint([p[1],displayLon(p[0])])),lengths=[0];
  for(let j=1;j<path.length;j++)lengths.push(lengths[j-1]+path[j].distanceTo(path[j-1]));
  const total=lengths.at(-1);if(!total)continue;
  ctx.fillStyle='#ed9854';const phase=((pausedAt??Date.now())/1000*i.flow.speed*.15)%35;
  for(let d=phase;d<total;d+=35){const j=lengths.findIndex(x=>x>d);if(j<1)continue;const t=(d-lengths[j-1])/(lengths[j]-lengths[j-1]);const a=path[j-1],b=path[j];ctx.beginPath();ctx.arc(a.x+(b.x-a.x)*t,a.y+(b.y-a.y)*t,2,0,Math.PI*2);ctx.fill()}
 }
}
function drawWeather(l){
 if(!l.on||!l.weatherRaster||l.weatherPending||Date.now()<(l.weatherNext||0))return;
 const frames=l.weatherRaster.frames;const index=((l.weatherIndex??-1)+1)%frames.length,time=frames[index];
 const tile=L.tileLayer.wms(l.weatherRaster.url,{layers:l.weatherRaster.layer,format:'image/png',transparent:true,time:new Date(time).toISOString(),opacity:0,attribution:l.id==='world-lightning'?'NOAA nowCOAST / Vaisala lightning density':'NOAA nowCOAST satellite imagery'});
 l.weatherPending=true;let failed=false,done=false;
 const finish=()=>{if(done)return;done=true;clearTimeout(timer);l.weatherPending=false;l.weatherNext=Date.now()+(failed?15000:2000);l.weatherIndex=index;
  if(failed||!l.on||!layers.includes(l)){l.groupLayer.removeLayer(tile);return}
  if(l.weatherCurrent)l.groupLayer.removeLayer(l.weatherCurrent);l.weatherCurrent=tile;tile.setOpacity(l.id==='world-clouds'?.22:.5);
  l.weatherShown=time;const el=$('status-'+l.id);if(el)el.textContent=(l.id==='world-lightning'?'15-min density · ':'Infrared · ')+new Date(time).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
 };
 const timer=setTimeout(()=>{failed=true;finish()},20000);
 tile.on('tileerror',()=>{failed=true});tile.once('load',()=>setTimeout(finish,0));l.groupLayer.addLayer(tile);
}
