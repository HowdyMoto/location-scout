const test=require('node:test'),assert=require('node:assert/strict'),E=require('../dist/explore.js');
test('SF sources activate from bounds without a region selection',()=>{const b=[-122.6,37.6,-122.2,37.9];assert.ok(E.applies({region:'bay'},b));assert.ok(!E.applies({region:'seattle'},b));assert.ok(E.applies({region:'world',id:'world-air'},b))});
test('a wide view activates both regional catalogs',()=>{const b=[-130,30,-115,50];assert.ok(E.applies({region:'bay'},b));assert.ok(E.applies({region:'seattle'},b))});
test('global sources follow London while US-only sources do not',()=>{const b=[-1,51,1,52];assert.ok(E.applies({region:'world',id:'world-air'},b));assert.ok(E.applies({region:'world',id:'world-radar'},b));assert.ok(!E.applies({region:'world',id:'world-rivers'},b));assert.ok(!E.applies({region:'bay'},b))});
test('antimeridian views and wrapped worlds normalize correctly',()=>{assert.deepEqual(E.normalize(170,-10,190,10),[170,-10,-170,10]);assert.ok(E.intersects([170,-10,-170,10],[-179,-2,-175,2]));assert.ok(!E.intersects([170,-10,-170,10],[-1,-2,1,2]));assert.deepEqual(E.normalize(-300,-90,300,90),[-180,-85,180,85])});
test('padded query contains the viewport, including dateline',()=>{for(const b of [[-122.5,37.7,-122.3,37.9],[179,-5,-179,5],[-180,-85,180,85]])assert.ok(E.contains(E.queryBounds(b),b))});
test('small movements reuse query coverage',()=>{const q=E.queryBounds([-122.5,37.7,-122.3,37.9]);assert.ok(E.contains(q,[-122.49,37.71,-122.29,37.91]))});
test('catalog footprints activate worldwide transit without hardcoded regions',()=>{
 const sources=require('../dist/sources.json').filter(s=>s.adapter==='gtfs-rt');
 assert.ok(sources.length>=4);
 for(const s of sources){const [lat,lon]=s.destination.center;assert.ok(E.applies(s,[lon-.01,lat-.01,lon+.01,lat+.01]));assert.ok(!E.applies(s,[-122.5,37.7,-122.4,37.8]));assert.ok(E.applies(s,[-180,-85,180,85]));}
});
test('Norway regional footprints do not activate over Helsinki',()=>{
 const source=require('../dist/sources.json').find(s=>s.id==='entur-vehicles');
 assert.ok(!E.applies(source,[24.8,60.1,25.1,60.3]));
 assert.ok(E.applies(source,[10.2,63.3,10.6,63.5]));
});
