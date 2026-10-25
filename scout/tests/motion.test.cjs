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
