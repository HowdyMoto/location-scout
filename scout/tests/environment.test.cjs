const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
test('wind interpolation crosses the date line and does not invent vectors outside the grid',()=>{
 const code=fs.readFileSync('scout/dist/environment.js','utf8'),ctx=vm.createContext({});
 vm.runInContext(code.slice(code.indexOf('function windVector'),code.indexOf('function environmentFrame'))+';this.vector=windVector',ctx);
 const field={bounds:[170,-10,-170,10],size:2,vectors:[[1,0],[3,0],[1,2],[3,2]]};
 assert.deepEqual(Array.from(ctx.vector(field,0,180)),[2,1]);
 assert.equal(ctx.vector(field,0,0),null);
 assert.equal(ctx.vector(field,40,180),null);
});
test('regional vehicles render with Canvas and switch to detailed markers at street zoom',()=>{
 const code=fs.readFileSync('scout/dist/live.js','utf8');let zoom=6,canvas=0,dom=0;
 const marker=()=>({on(){return this},addTo(){return this},bindTooltip(){},setTooltipContent(){},getElement(){return null},options:{}});
 const ctx=vm.createContext({map:{getZoom:()=>zoom,getBounds:()=>({pad:()=>({contains:()=>true})})},L:{circleMarker(){canvas++;return marker()},marker(){dom++;return marker()},divIcon:()=>({})},trailRenderer:{},mapped:l=>l.items,playbackTime:()=>0,positionFor:(l,i)=>i,displayLon:x=>x,vehicleType:()=> 'transit',vehicleSvg:()=>'',esc:x=>x,followed:null,stopFollowing(){},toast(){}});
 vm.runInContext(code.slice(code.indexOf('function drawVehicles'),code.indexOf('function updateMotionTrails'))+';this.draw=drawVehicles',ctx);
 const l={id:'bus',on:true,items:[{id:'a',lat:0,lon:0,title:'bus'}],groupLayer:{clearLayers(){},removeLayer(){}}};
 ctx.draw(l);assert.equal(canvas,1);assert.equal(dom,0);assert.equal(l.vehicles.size,1);
 zoom=14;ctx.draw(l);assert.equal(dom,1);assert.equal(l.vehicles.size,1);
});
