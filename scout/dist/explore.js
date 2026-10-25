/* Geographic selection shared by the map and deterministic tests. */
(function(root){
 'use strict';
 const regions={seattle:[-123.6,46.8,-121.2,48.8],bay:[-123.6,36.8,-121.2,38.9]},us=[-125,24,-66,50];
 const wrap=x=>((x+180)%360+360)%360-180;
 function normalize(w,s,e,n){if(e-w>=360)return [-180,Math.max(-85,s),180,Math.min(85,n)];return [wrap(w),Math.max(-85,s),wrap(e),Math.min(85,n)]}
 function segments(b){return b[0]<b[2]?[b]:[[b[0],b[1],180,b[3]],[-180,b[1],b[2],b[3]]]}
 function intersects(a,b){return segments(a).some(x=>segments(b).some(y=>x[0]<=y[2]&&x[2]>=y[0]&&x[1]<=y[3]&&x[3]>=y[1]))}
 function contains(a,b){return segments(b).every(y=>segments(a).some(x=>x[0]<=y[0]&&x[2]>=y[2]&&x[1]<=y[1]&&x[3]>=y[3]))}
 function queryBounds(b){const span=b[2]>b[0]?b[2]-b[0]:360+b[2]-b[0];const step=span>30?5:span>6?1:.25;const w=Math.floor(b[0]/step)*step-step,e=Math.ceil((b[0]+span)/step)*step+step;return normalize(w,Math.floor(b[1]/step)*step-step,e,Math.ceil(b[3]/step)*step+step)}
 function applies(source,b){if(source.coverageBounds)return source.coverageBounds.some(bounds=>intersects(b,bounds));if(source.bounds)return intersects(b,source.bounds);if(source.region==='world')return !['world-radar','world-rivers','world-wildfire'].includes(source.id)||intersects(b,us);return Boolean(regions[source.region]&&intersects(b,regions[source.region]))}
 const api={regions,us,wrap,normalize,segments,intersects,contains,queryBounds,applies};
 if(typeof module!=='undefined')module.exports=api;else root.ScoutExplore=api;
})(typeof globalThis!=='undefined'?globalThis:this);
