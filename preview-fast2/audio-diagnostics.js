/* Preview-only audio and timing instrumentation. No telemetry is sent. */
(() => {
 'use strict';
 const lines=['Preview audio1 · timings since navigation'];
 let output, player, soundButton, desired=0, enabled=false, fadeTimer;
 const seconds=()=> (performance.now()/1000).toFixed(2)+'s';
 const report=text=>{ lines.push(seconds()+' '+text);if(lines.length>40)lines.splice(1,1);if(output)output.textContent=lines.join('\n'); };
 const mark=(key,label)=>{report(label);if(key==='game')document.documentElement.dataset.previewReady='true';};
 window.trollDiag={mark};
 function initAudio(){
  if(player)return;
  player=document.createElement('audio');player.controls=true;player.preload='none';player.loop=true;player.volume=.5;
  player.id='preview-audio';player.setAttribute('playsinline','');
  player.src='music/1.mp3';
  ['playing','pause','waiting','stalled','loadedmetadata','ended'].forEach(event=>player.addEventListener(event,()=>{
   report('Audio '+event+' · '+player.currentTime.toFixed(1)+'s · readyState '+player.readyState);
   if(event==='playing'){enabled=true;if(soundButton)soundButton.textContent='Sound playing · test again';}
  }));
  player.addEventListener('error',()=>report('Audio ERROR '+(player.error?.code||'unknown')+' '+(player.error?.message||'')));
 }
 function attempt(fromGesture){
  initAudio();clearInterval(fadeTimer);player.volume=.5;
  // play() is called synchronously here when invoked by the button's click handler.
  try { const p=player.play();if(p)p.then(()=>{enabled=true;report('play accepted'+(fromGesture?' after direct tap':''));}).catch(e=>{enabled=false;report('play blocked: '+e.name+' '+e.message);if(soundButton)soundButton.textContent='Tap to enable sound';}); }
  catch(e){report('play failed: '+e.name+' '+e.message);}
 }
 window.trollAudio={
  play(number){
   initAudio();const n=Math.max(0,Math.min(5,Number(number)));const changed=n!==desired;desired=n;
   if(changed){player.pause();player.src='music/'+(n+1)+'.mp3';}
   report('Game requested track '+(n+1));
   if(enabled)attempt(false);else report('Waiting for Enable / test sound tap');
  },
  stop(){if(player){clearInterval(fadeTimer);player.pause();player.currentTime=0;}},
  fadeOut(){if(!player)return;clearInterval(fadeTimer);const start=performance.now(),v=player.volume;fadeTimer=setInterval(()=>{const p=Math.min(1,(performance.now()-start)/1200);player.volume=v*(1-p);if(p>=1){clearInterval(fadeTimer);player.pause();}},50);}
 };
 addEventListener('DOMContentLoaded',()=>{
  initAudio();const panel=document.createElement('div');panel.id='preview-controls';
  panel.style.cssText='position:fixed;top:6px;right:6px;z-index:1000000;max-width:90vw;font:13px system-ui;color:white;background:#17243aed;padding:6px;border-radius:8px';
  soundButton=document.createElement('button');soundButton.id='enable-preview-sound';soundButton.textContent='Enable / test sound';soundButton.style.cssText='font:15px system-ui;padding:8px;touch-action:manipulation';
  soundButton.addEventListener('click',()=>{report('Direct sound button tap');attempt(true);});
  const details=document.createElement('details');const summary=document.createElement('summary');summary.textContent='Startup / sound details';
  output=document.createElement('pre');output.id='preview-diagnostics';output.style.cssText='white-space:pre-wrap;max-height:36vh;overflow:auto;max-width:85vw';
  details.append(summary,player,output);panel.append(soundButton,details);document.body.append(panel);output.textContent=lines.join('\n');report('Page controls ready');
  new PerformanceObserver(list=>{for(const e of list.getEntries()){if(e.name.includes('.tar.gz'))report('Archive '+(e.duration/1000).toFixed(2)+'s, '+e.transferSize+' network bytes');if(e.name.includes('/cpython312/')&&e.name.endsWith('.wasm'))report('Python runtime download '+(e.duration/1000).toFixed(2)+'s');}}).observe({type:'resource',buffered:true});
 });
 addEventListener('error',e=>report('Page error: '+e.message));
 document.addEventListener('visibilitychange',()=>{if(document.hidden&&player)player.pause();else if(enabled)report('Returned to page; tap sound button if needed');});
})();
