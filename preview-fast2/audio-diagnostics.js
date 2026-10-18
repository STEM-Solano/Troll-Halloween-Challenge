/* Preview-only audio and timing instrumentation. No telemetry is sent. */
(() => {
 'use strict';
 const lines=['Preview audio1 · timings since navigation'];
 let output, player, soundButton, desired=0, enabled=false, fadeTimer, playGeneration=0, compactButton, controls, details;
 const updateButton=()=>{
  if(soundButton){soundButton.textContent=enabled?'Sound ON — Disable':'Sound OFF — Enable';soundButton.setAttribute('aria-pressed',String(enabled));}
  if(compactButton){compactButton.textContent=(enabled?'🔊':'🔇')+' '+(controls.hidden?'▾':'▴');compactButton.setAttribute('aria-label','Sound '+(enabled?'on':'off')+' — '+(controls.hidden?'expand':'collapse')+' controls');}
 };
 const setExpanded=expanded=>{if(!controls)return;controls.hidden=!expanded;compactButton.setAttribute('aria-expanded',String(expanded));if(!expanded&&details)details.open=false;updateButton();};
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
   if(event==='playing'){if(!enabled){player.muted=true;player.pause();}updateButton();}
  }));
  player.addEventListener('error',()=>report('Audio ERROR '+(player.error?.code||'unknown')+' '+(player.error?.message||'')));
 }
 function attempt(fromGesture){
  if(!enabled)return;
  initAudio();clearInterval(fadeTimer);player.muted=false;player.volume=.5;
  const generation=++playGeneration;
  const failed=e=>{if(generation!==playGeneration)return;enabled=false;player.muted=true;player.pause();updateButton();report('play blocked: '+e.name+' '+e.message);};
  // Keep play() synchronous inside the enabling button's click handler.
  try {const p=player.play();if(p)p.then(()=>{if(generation!==playGeneration||!enabled)return;updateButton();report('play accepted'+(fromGesture?' after direct tap':''));}).catch(failed);}
  catch(e){failed(e);}
 }
 window.trollAudio={
  play(number){
   initAudio();const n=Math.max(0,Math.min(5,Number(number)));const changed=n!==desired;desired=n;
   if(changed){player.pause();player.src='music/'+(n+1)+'.mp3';}
   report('Game requested track '+(n+1));
   if(enabled)attempt(false);else report('Sound disabled; track queued');
  },
  stop(){if(player){clearInterval(fadeTimer);player.pause();player.currentTime=0;}},
  fadeOut(){if(!player)return;clearInterval(fadeTimer);const start=performance.now(),v=player.volume;fadeTimer=setInterval(()=>{const p=Math.min(1,(performance.now()-start)/1200);player.volume=v*(1-p);if(p>=1){clearInterval(fadeTimer);player.pause();}},50);}
 };
 addEventListener('DOMContentLoaded',()=>{
  initAudio();const panel=document.createElement('div');panel.id='preview-controls';
  panel.style.cssText='position:fixed;top:6px;right:6px;z-index:1000000;max-width:90vw;font:13px system-ui;color:white;background:#17243aed;padding:6px;border-radius:8px';
  soundButton=document.createElement('button');soundButton.id='enable-preview-sound';updateButton();soundButton.style.cssText='font:15px system-ui;padding:8px;touch-action:manipulation';
  soundButton.addEventListener('click',()=>{
   enabled=!enabled;++playGeneration;updateButton();
   if(enabled){report('Sound enabled by tap');attempt(true);}
   else{clearInterval(fadeTimer);player.muted=true;player.pause();report('Sound disabled by tap');}
   setExpanded(false);compactButton.focus();
  });
  details=document.createElement('details');const summary=document.createElement('summary');summary.textContent='Startup / sound details';
  output=document.createElement('pre');output.id='preview-diagnostics';output.style.cssText='white-space:pre-wrap;max-height:36vh;overflow:auto;max-width:85vw';
  controls=document.createElement('div');controls.id='sound-options';controls.hidden=true;
  compactButton=document.createElement('button');compactButton.id='sound-panel-toggle';compactButton.setAttribute('aria-controls','sound-options');compactButton.setAttribute('aria-expanded','false');
  compactButton.style.cssText='font:18px system-ui;padding:6px 10px;touch-action:manipulation';
  compactButton.addEventListener('click',()=>setExpanded(controls.hidden));
  details.append(summary,player,output);controls.append(soundButton,details);panel.append(compactButton,controls);document.body.append(panel);updateButton();output.textContent=lines.join('\n');report('Page controls ready');
  new PerformanceObserver(list=>{for(const e of list.getEntries()){if(e.name.includes('.tar.gz'))report('Archive '+(e.duration/1000).toFixed(2)+'s, '+e.transferSize+' network bytes');if(e.name.includes('/cpython312/')&&e.name.endsWith('.wasm'))report('Python runtime download '+(e.duration/1000).toFixed(2)+'s');}}).observe({type:'resource',buffered:true});
 });
 addEventListener('error',e=>report('Page error: '+e.message));
 document.addEventListener('visibilitychange',()=>{if(document.hidden&&player)player.pause();else if(enabled)report('Returned to page; toggle sound off/on if playback is interrupted');});
})();
