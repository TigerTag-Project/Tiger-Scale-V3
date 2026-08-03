// live_page.h — the browser side of §LIVE, served from flash by the scale.
//
// A separate file rather than a raw string literal inside the .ino, and not by
// preference: the Arduino prototype generator scans raw string literals as if
// they were code, so every `function` in this script became a generated C++
// prototype at the top of TigerTagSplashESP32.ino and nothing compiled. Headers
// are not scanned. Same reason logo_tigertag.h and icon_bolt.h are separate.
//
// ASCII only, no emoji, per the repository rule.
//
// Protocol, decoder and the single-commit rule are documented in §LIVE.
#pragma once

static const char LIVE_PAGE[] PROGMEM = R"HTML(<!doctype html>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TigerScale live</title>
<style>
 :root{color-scheme:dark}
 body{margin:0;background:#0B0E14;color:#8A93A6;font:13px/1.5 ui-monospace,Menlo,Consolas,monospace;
      display:flex;flex-direction:column;align-items:center;gap:12px;padding:16px}
 #wrap{position:relative;line-height:0}
 canvas{width:min(96vw,960px);aspect-ratio:3/2;image-rendering:pixelated;
        border:1px solid #2E3646;border-radius:8px;cursor:crosshair;background:#000}
 #bar{display:flex;gap:16px;flex-wrap:wrap;justify-content:center}
 b{color:#FFF;font-weight:600}
 #gate{display:flex;gap:8px}
 input{background:#141821;border:1px solid #2E3646;color:#FFF;border-radius:6px;padding:7px 10px;font:inherit}
 button{background:#2F7FFF;border:0;color:#FFF;border-radius:6px;padding:7px 14px;font:inherit;cursor:pointer}
 .off{color:#E24B4A}
</style>
<div id=gate><input id=code placeholder="access code" size=8 autocapitalize=off spellcheck=false><button id=go>connect</button></div>
<div id=wrap><canvas id=c width=480 height=320></canvas></div>
<div id=bar><span id=st>idle</span><span>page <b id=pt>-</b></span><span>frame <b id=ft>-</b></span><span><b id=kb>0</b> KB/s</span></div>
<script>
const W=480,H=320,BC=16,NB=W/BC;
const cv=document.getElementById('c'),cx=cv.getContext('2d');
const img=cx.createImageData(W,H);
// Destination byte offset for pixel i of band 0. Band n is the same plus n*BC*4:
// within a band, memory runs down a column and columns run right to left.
const OFF=new Int32Array(BC*H);
for(let r=0;r<BC;r++)for(let y=0;y<H;y++)OFF[r*H+y]=(y*W+(BC-1-r))*4;
const R5=new Uint8Array(32),G6=new Uint8Array(64);
for(let i=0;i<32;i++)R5[i]=Math.round(i*255/31);
for(let i=0;i<64;i++)G6[i]=Math.round(i*255/63);
for(let i=0;i<W*H;i++)img.data[i*4+3]=255;

const $=i=>document.getElementById(i);
let bytes=0,lastPaint=0,pageStart=0,pending=0;
setInterval(()=>{$('kb').textContent=(bytes/1024).toFixed(1);bytes=0},1000);

function band(idx,buf,len){
  const D=img.data,sh=idx*BC*4;let p=0,i=0;
  while(p<len){
    const t=buf[p++];let n,lit=false;
    if(t<0x80){n=t+1;lit=true}
    else if(t<0xFF){n=t-0x80+2}
    else{n=buf[p]|(buf[p+1]<<8);p+=2}
    if(lit){for(let k=0;k<n;k++){const v=buf[p]|(buf[p+1]<<8);p+=2;
      const o=OFF[i++]+sh;D[o]=R5[(v>>11)&31];D[o+1]=G6[(v>>5)&63];D[o+2]=R5[v&31]}}
    else{const v=buf[p]|(buf[p+1]<<8);p+=2;
      const r=R5[(v>>11)&31],g=G6[(v>>5)&63],b=R5[v&31];
      for(let k=0;k<n;k++){const o=OFF[i++]+sh;D[o]=r;D[o+1]=g;D[o+2]=b}}
  }
}

async function stream(code){
  const res=await fetch('/stream?c='+encodeURIComponent(code));
  if(res.status===403){fail('wrong code');$('gate').style.display='flex';return'stop'}
  if(!res.ok)return'retry';
  localStorage.tsLive=code;$('gate').style.display='none';
  $('st').textContent='live';$('st').className='';
  const rd=res.body.getReader();let buf=new Uint8Array(0),n=0,t0=0;
  const need=k=>buf.length>=k;
  const eat=k=>{buf=buf.subarray(k)};
  for(;;){
    const{done,value}=await rd.read();
    if(done)return'retry';
    bytes+=value.length;
    const nb=new Uint8Array(buf.length+value.length);nb.set(buf);nb.set(value,buf.length);buf=nb;
    // Decode whole messages only. Bands land in an off-screen ImageData as they
    // arrive; the visible canvas is written once, on FRAME_END, so a frame that
    // is still arriving is never on screen.
    for(;;){
      if(!need(1))break;
      const k=buf[0];
      if(k===3){eat(1);continue}                       // ping
      if(k===1){if(!need(7))break;eat(7);continue}     // hello
      if(k===2){eat(1);n=0;t0=performance.now();continue}
      if(k===5){                                       // band
        if(!need(4))break;
        const l=buf[2]|(buf[3]<<8);
        if(!need(4+l))break;
        band(buf[1],buf.subarray(4,4+l),l);eat(4+l);n++;continue;
      }
      if(k===4){                                       // frame end: commit
        eat(1);
        cx.putImageData(img,0,0);
        const now=performance.now();
        // Bounded ring of what actually landed, for measuring. A page change
        // shows as ONE entry carrying most of the bands; several small entries
        // in a row would be exactly the progressive fill to avoid.
        (window.tsFrames=window.tsFrames||[]).push({t:now,bands:n});
        if(window.tsFrames.length>500)window.tsFrames.shift();
        $('ft').textContent=n+' bands, '+(now-t0).toFixed(0)+' ms';
        if(pending&&n>NB/2){$('pt').textContent=(now-pending).toFixed(0)+' ms';pending=0}
        continue;
      }
      return'retry';                                   // out of step: start over
    }
  }
}

// Reconnect on its own. A stream can end for reasons that have nothing to do
// with the viewer -- the scale hands up briefly when its heap runs short -- and
// a page that just froze on its last frame would be showing something stale
// while looking perfectly fine, which is the worst failure this tool can have.
async function run(code){
  for(let backoff=300;;){
    let r='retry';
    try{r=await stream(code)}catch(e){}
    if(r==='stop')return;
    fail('reconnecting');
    await new Promise(s=>setTimeout(s,backoff));
    backoff=Math.min(backoff*2,3000);
  }
}
function fail(m){$('st').textContent=m;$('st').className='off'}

cv.onpointerdown=async e=>{
  const r=cv.getBoundingClientRect();
  const x=Math.round((e.clientX-r.left)/r.width*W),y=Math.round((e.clientY-r.top)/r.height*H);
  pending=performance.now();
  const u='/tap?c='+encodeURIComponent(localStorage.tsLive||'')+'&x='+x+'&y='+y;
  // Once more on failure. The browser reuses a keep-alive connection for this,
  // and if the scale closed that one in the meantime the POST simply fails --
  // a POST is not retried automatically, so the click would just vanish.
  try{await fetch(u,{method:'POST'})}
  catch(_){try{await fetch(u,{method:'POST'})}catch(_){}}
};
$('go').onclick=()=>run($('code').value.trim());
$('code').onkeydown=e=>{if(e.key==='Enter')$('go').click()};
const q=new URLSearchParams(location.search).get('c')||localStorage.tsLive;
if(q){$('code').value=q;run(q)}
</script>
)HTML";
