'use strict';
(async()=>{
const data=window.MAP_DATA,$=id=>document.getElementById(id),canvas=$('map'),ctx=canvas.getContext('2d');
if(new URLSearchParams(location.search).get('embed')==='1')document.body.classList.add('embed');
const R=6378137,b=data.grid.bounds_3857,worldW=b[2]-b[0],worldH=b[3]-b[1],iw=data.grid.width,ih=data.grid.height;
let camera={x:0,y:0,scale:1,fit:1},ratio=.5,mode=new URLSearchParams(location.search).get('katman')==='su'&&data.kind==='uydu'?'mask':'rgb',ready=false,pan=null,width=0,height=0,renderCount=0;
const textures={};
const lonlat=(x,y)=>[x/R*180/Math.PI,(2*Math.atan(Math.exp(y/R))-Math.PI/2)*180/Math.PI];
const xy=(lon,lat)=>[R*lon*Math.PI/180,R*Math.log(Math.tan(Math.PI/4+lat*Math.PI/360))];
const screen=(x,y)=>[camera.x+(x-b[0])*camera.scale,camera.y+(b[3]-y)*camera.scale];
const world=(x,y)=>[b[0]+(x-camera.x)/camera.scale,b[3]-(y-camera.y)/camera.scale];
function image(path){return new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>reject(new Error('Görsel yüklenemedi: '+path));im.src='../'+path;});}
function surface(){const c=document.createElement('canvas');c.width=iw;c.height=ih;return c;}
function texture(photo,water,common,kind){const c=surface(),p=c.getContext('2d');if(kind==='mask'){p.fillStyle='#e7e5d7';p.fillRect(0,0,iw,ih);p.drawImage(water,0,0,iw,ih);}else{p.drawImage(photo,0,0,iw,ih);if(kind==='overlay'){p.globalAlpha=.70;p.drawImage(water,0,0,iw,ih);p.globalAlpha=1;}}p.globalCompositeOperation='destination-in';p.drawImage(common,0,0,iw,ih);return c;}
function reset(){camera.fit=Math.min(width/worldW,height/worldH);camera.scale=camera.fit;camera.x=(width-worldW*camera.scale)/2;camera.y=(height-worldH*camera.scale)/2;draw();}
function resize(){const rect=canvas.parentElement.getBoundingClientRect();width=rect.width;height=rect.height;const dpr=Math.min(window.devicePixelRatio||1,2);canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);reset();}
function setRatio(value){ratio=Math.min(.99,Math.max(.01,Number(value)));$('swipe').value=Math.round(ratio*100);$('percent').textContent=Math.round(ratio*100)+'%';$('divider').style.left=ratio*100+'%';$('handle').setAttribute('aria-valuenow',String(Math.round(ratio*100)));draw();}
function setMode(value){mode=data.kind==='uydu'?value:'rgb';for(const button of document.querySelectorAll('[data-mode]'))button.setAttribute('aria-pressed',String(button.dataset.mode===mode));draw();}
function zoom(factor,x=width/2,y=height/2){const point=world(x,y),next=Math.max(camera.fit,Math.min(camera.fit*12,camera.scale*factor));camera.scale=next;camera.x=x-(point[0]-b[0])*next;camera.y=y-(b[3]-point[1])*next;draw();}
function scaleBar(){const center=lonlat(...world(width/2,height/2));const mpp=Math.cos(center[1]*Math.PI/180)/camera.scale;const target=110*mpp,unit=10**Math.floor(Math.log10(target));let meters=unit;for(const v of [1,2,5,10])if(v*unit<=target)meters=v*unit;const length=meters/mpp,x=18,y=height-24;ctx.fillStyle='#ffffffeb';ctx.fillRect(x-8,y-22,length+18,35);ctx.strokeStyle='#193d33';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(x,y-4);ctx.lineTo(x,y+2);ctx.lineTo(x,y-1);ctx.lineTo(x+length,y-1);ctx.lineTo(x+length,y-4);ctx.lineTo(x+length,y+2);ctx.stroke();ctx.fillStyle='#193d33';ctx.font='11px system-ui';ctx.textAlign='center';ctx.fillText(meters>=1000?(meters/1000).toLocaleString('tr-TR')+' km':meters.toLocaleString('tr-TR')+' m',x+length/2,y-9);}
function points(){ctx.font='12px system-ui';for(const dam of data.dams){const p=screen(...xy(dam.lon,dam.lat));if(p[0]<0||p[0]>width||p[1]<0||p[1]>height)continue;ctx.beginPath();if(dam.project){ctx.moveTo(p[0],p[1]-6);ctx.lineTo(p[0]+6,p[1]);ctx.lineTo(p[0],p[1]+6);ctx.lineTo(p[0]-6,p[1]);ctx.closePath();ctx.fillStyle='#fff';}else{ctx.arc(p[0],p[1],5,0,Math.PI*2);ctx.fillStyle='#b95f3f';}ctx.fill();ctx.strokeStyle='white';ctx.lineWidth=2;ctx.stroke();if(data.dams.length===1){ctx.textAlign='left';const label=dam.name+(dam.project?' (proje)':'');const tw=ctx.measureText(label).width;let lx=p[0]+9;if(lx+tw+8>width)lx=p[0]-tw-14;let ly=p[1]-9;if(ly<65)ly=p[1]+23;ctx.fillStyle='#fffffff0';ctx.fillRect(lx-4,ly-14,tw+8,20);ctx.fillStyle='#173e32';ctx.fillText(label,lx,ly);}}}
function draw(){if(!ctx)return;ctx.clearRect(0,0,width,height);if(!ready)return;ctx.imageSmoothingEnabled=data.kind==='uydu'&&mode==='rgb';const target=textures[mode]||textures.rgb;const dx=camera.x,dy=camera.y,dw=worldW*camera.scale,dh=worldH*camera.scale;ctx.save();ctx.beginPath();ctx.rect(0,0,width*ratio,height);ctx.clip();ctx.drawImage(target[0],dx,dy,dw,dh);ctx.restore();ctx.save();ctx.beginPath();ctx.rect(width*ratio,0,width*(1-ratio),height);ctx.clip();ctx.drawImage(target[1],dx,dy,dw,dh);ctx.restore();points();scaleBar();renderCount++;}
function readout(event){const rect=canvas.getBoundingClientRect(),p=[event.clientX-rect.left,event.clientY-rect.top],ll=lonlat(...world(...p));let label=ll[1].toFixed(5)+'° K, '+ll[0].toFixed(5)+'° D';for(const dam of data.dams){const s=screen(...xy(dam.lon,dam.lat));if(Math.hypot(s[0]-p[0],s[1]-p[1])<13)label=dam.name+' · '+label;}$('coords').textContent=label;}
$('swipe').addEventListener('input',e=>setRatio(Number(e.target.value)/100));
const handle=$('handle');handle.addEventListener('pointerdown',e=>{e.preventDefault();e.stopPropagation();handle.setPointerCapture(e.pointerId);});handle.addEventListener('pointermove',e=>{if(handle.hasPointerCapture(e.pointerId)){const r=canvas.getBoundingClientRect();setRatio((e.clientX-r.left)/r.width);}});handle.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();setRatio(e.key==='Home'?.01:e.key==='End'?.99:ratio+(e.key==='ArrowLeft'?-.02:.02));}});
canvas.addEventListener('pointerdown',e=>{if(!ready)return;pan={id:e.pointerId,x:e.clientX,y:e.clientY,cx:camera.x,cy:camera.y};canvas.setPointerCapture(e.pointerId);canvas.classList.add('dragging');});
canvas.addEventListener('pointermove',e=>{if(pan&&pan.id===e.pointerId){camera.x=pan.cx+e.clientX-pan.x;camera.y=pan.cy+e.clientY-pan.y;draw();}readout(e);});
function endPan(){pan=null;canvas.classList.remove('dragging');}canvas.addEventListener('pointerup',endPan);canvas.addEventListener('pointercancel',endPan);
canvas.addEventListener('wheel',e=>{e.preventDefault();const r=canvas.getBoundingClientRect();zoom(Math.exp(-e.deltaY*.0013),e.clientX-r.left,e.clientY-r.top);},{passive:false});
$('plus').onclick=()=>zoom(1.5);$('minus').onclick=()=>zoom(1/1.5);$('reset').onclick=reset;
for(const button of document.querySelectorAll('[data-mode]'))button.onclick=()=>setMode(button.dataset.mode);
$('fullscreen').onclick=async()=>{try{const node=$('mapPanel');if(!document.fullscreenElement)await node.requestFullscreen();else await document.exitFullscreen();}catch(_){$('coords').textContent='Tam ekran bu görünümde kullanılamıyor.';}};
new ResizeObserver(resize).observe(canvas.parentElement);
try{
 const [before,after,va,vb,ma,mb]=await Promise.all([image(data.before.rgb),image(data.after.rgb),image(data.before.valid),image(data.after.valid),data.kind==='uydu'?image(data.before.water):Promise.resolve(null),data.kind==='uydu'?image(data.after.water):Promise.resolve(null)]);
 for(const im of [before,after,va,vb,ma,mb].filter(Boolean))if(im.naturalWidth!==iw||im.naturalHeight!==ih)throw new Error('Görsellerin ortak coğrafi ızgarası eşleşmiyor.');
 const common=surface(),cm=common.getContext('2d');cm.drawImage(va,0,0);cm.globalCompositeOperation='destination-in';cm.drawImage(vb,0,0);
 textures.rgb=[texture(before,null,common,'rgb'),texture(after,null,common,'rgb')];
 if(data.kind==='uydu'){textures.mask=[texture(before,ma,common,'mask'),texture(after,mb,common,'mask')];textures.overlay=[texture(before,ma,common,'overlay'),texture(after,mb,common,'overlay')];}
 ready=true;$('loading').hidden=true;resize();setRatio(.5);setMode(mode);
}catch(error){$('loading').textContent=error.message+' ZIP’in tamamını çıkarıp index.html dosyasından tekrar açın.';$('loading').classList.add('failed');}
window.swipeApp={ready:()=>ready,data,getView:()=>({...camera,ratio,mode,renderCount,width,height}),setRatio,setMode,zoom,reset,project:xy,unproject:lonlat,toScreen:screen,toWorld:world};
})();
