const test=require('node:test');const assert=require('node:assert/strict');const M=require('../dist/motion.js');
const t=1_000_000;
const a={lat:47.6,lon:-122.3,time:t},b={lat:47.61,lon:-122.3,time:t+30000};
test('interpolates only between timestamped reports',()=>{const p=M.sample([a,b],t+15000);assert.equal(p.state,'moving');assert.ok(Math.abs(p.lat-47.605)<1e-9);assert.equal(p.heading,0)});
test('holds last position and never extrapolates',()=>{const p=M.sample([a,b],t+120000);assert.equal(p.lat,b.lat);assert.equal(p.time,b.time);assert.equal(p.state,'holding')});
test('initial playback is explicitly buffering',()=>{assert.equal(M.sample([a],t-1).state,'buffering')});
test('long report gaps are not animated',()=>{const p=M.sample([a,{...b,time:t+180000}],t+15000);assert.equal(p.lat,a.lat);assert.equal(p.state,'gap')});
test('teleports are not interpolated',()=>{const p=M.sample([a,{...b,lat:48.6}],t+15000,65);assert.equal(p.state,'gap')});
test('stationary observations do not count as movement',()=>{assert.equal(M.sample([a,{...a,time:t+30000}],t+15000).state,'stationary')});
test('history sorts, deduplicates, prunes and rejects future timestamps',()=>{const result=M.merge([b,a],[a,{...a,time:t-700000},{...a,time:t+1000000}],t+30000);assert.deepEqual(result,[a,b])});
test('activity is balanced across sources instead of dominated by aircraft',()=>{assert.deepEqual(M.balanced([['fire1','fire2'],['air1','air2','air3'],['bus1']],5),['fire1','air1','bus1','fire2','air2'])});
test('empty history is safe',()=>{assert.equal(M.sample([],t),null)});
test('availability changes require a newer station report and never count initial stations as changes',()=>{
 const a={time:100,availability:{bikes:2,docks:8,renting:true,returning:true}};
 assert.equal(M.availabilityChanged(undefined,a),false);
 assert.equal(M.availabilityChanged(a,{...a,time:101}),false);
 assert.equal(M.availabilityChanged(a,{time:101,availability:{...a.availability,bikes:1,docks:9}}),true);
 assert.equal(M.availabilityChanged(a,{time:99,availability:{bikes:1}}),false);
});
test('eastbound date-line crossing stays near the Pacific instead of crossing Greenwich',()=>{
 const points=[{lat:0,lon:179.99,time:t},{lat:0,lon:-179.99,time:t+30000}];
 const p=M.sample(points,t+15000);assert.equal(p.state,'moving');assert.ok(Math.abs(Math.abs(p.lon)-180)<1e-9);assert.ok(Math.abs(p.heading-90)<1e-9);
 assert.ok(M.sample(points,t+22500).lon<-179.99);
});
test('westbound date-line crossing takes the short path and retains speed rejection',()=>{
 const points=[{lat:0,lon:-179.99,time:t},{lat:0,lon:179.99,time:t+30000}];
 const p=M.sample(points,t+15000);assert.equal(p.state,'moving');assert.ok(Math.abs(Math.abs(p.lon)-180)<1e-9);assert.ok(Math.abs(p.heading-270)<1e-9);
 assert.equal(M.sample(points,t+15000,10).state,'gap');
});
test('trails remain continuous across the date line in either displayed world copy',()=>{
 const points=[{lat:1,lon:179.99},{lat:2,lon:-179.99},{lat:3,lon:-179.98}];
 for(const center of [0,180,-180,540]){
  const trail=M.trailCoordinates(points,center);
  assert.ok(Math.abs(trail[0][1]-center)<=180);
  for(let n=1;n<trail.length;n++)assert.ok(Math.abs(trail[n][1]-trail[n-1][1])<.1);
 }
 assert.deepEqual(M.trailCoordinates([],0),[]);
});

test('discovery activity counts only fresh nearby vehicles and verified playback motion',()=>{
 const now=t+120000,one={id:'v',...b,time:t+60000},far={...one,id:'far',lat:0,lon:0};
 const layer={id:'bus',motion:true,status:'ok',fetchedAt:now,maxAge:300,items:[one,far,{...one,id:'old',time:now-301000},{...one,id:'future',time:now+61000},{...one,id:'missing',time:null}],trails:new Map([['v',[a,one]]])};
 assert.deepEqual(M.activity([layer],[a.lat,a.lon],now),{vehicles:1,moving:1,stations:0,checked:true,unavailable:false});
 layer.trails.set('v',[{...one,time:t},one]);assert.equal(M.activity([layer],[a.lat,a.lon],now).moving,0);
 layer.trails.set('v',[{...a,lat:49},one]);assert.equal(M.activity([layer],[a.lat,a.lon],now).moving,0);
});
test('discovery never promotes failed or expired feeds, and station counts are not vehicles',()=>{
 const layer={id:'bikes',adapter:'gbfs',status:'ok',fetchedAt:t,maxAge:300,items:[{...a,availability:{bikes:3}}]};
 assert.deepEqual(M.activity([layer],[a.lat,a.lon],t),{vehicles:0,moving:0,stations:1,checked:true,unavailable:false});
 for(const status of ['stale','unavailable']){const result=M.activity([{...layer,status}],[a.lat,a.lon],t);assert.equal(result.stations,0);assert.equal(result.unavailable,true)}
 assert.equal(M.activity([layer],[a.lat,a.lon],t+301000).checked,false);
 assert.equal(M.activity([{...layer,status:'loading'}],[a.lat,a.lon],t).stations,0);
});
test('activity near the date line uses geographic distance',()=>{
 const layer={motion:true,status:'ok',fetchedAt:t,items:[{id:'v',lat:0,lon:-179.9,time:t}]};
 assert.equal(M.activity([layer],[0,179.9],t).vehicles,1);
});
test('surprise prioritizes movement, then fresh reports, and always allows unchecked destinations',()=>{
 const places=[{id:'unknown'},{id:'bikes',activity:{stations:10}},{id:'bus',activity:{vehicles:2}},{id:'moving',activity:{vehicles:1,moving:1}}];
 assert.deepEqual(M.activeDestinations(places,null).map(p=>p.id),['moving']);
 assert.deepEqual(M.activeDestinations(places,'moving').map(p=>p.id),['bus']);
 assert.deepEqual(M.activeDestinations(places.slice(0,2),null).map(p=>p.id),['bikes']);
 assert.deepEqual(M.activeDestinations(places.slice(0,1),null).map(p=>p.id),['unknown']);
 assert.deepEqual(M.activeDestinations(places.slice(0,1),'unknown'),[]);
});

test('unqueried aircraft, coverage gaps and missing access never imply a quiet destination',()=>{
 const layer={motion:true,status:'ok',fetchedAt:t,items:[]};
 for(const flag of ['zoomRequired','coverageUnavailable','configurationRequired'])assert.equal(M.activity([{...layer,[flag]:true}],[0,0],t).checked,false);
 assert.equal(M.activity([{id:'bikes',status:'ok',fetchedAt:t,items:[a]}],[a.lat,a.lon],t).stations,1);
});

test('orbital playback accepts satellite speeds without weakening aircraft or ground limits',()=>{
 const points=[{lat:0,lon:0,time:t},{lat:0,lon:1,time:t+15000}];
 assert.equal(M.sample(points,t+7500,M.maxSpeed({id:'iss-orbit'})).state,'moving');
 assert.equal(M.sample(points,t+7500,M.maxSpeed({id:'world-air'})).state,'gap');
 assert.equal(M.sample(points,t+7500,M.maxSpeed({id:'bus'})).state,'gap');
 assert.equal(M.sample(points,t+30000,M.maxSpeed({id:'iss-orbit'})).state,'holding');
});
