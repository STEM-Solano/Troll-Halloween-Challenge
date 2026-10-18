/* Resize CSS presentation only; retain Pygame's 800x600 input/render coordinates. */
(() => {
 let scheduled=false,lastLayout='';
 function fit(){
  scheduled=false;
  const viewport=window.visualViewport;
  const width=viewport?viewport.width:innerWidth;
  const height=viewport?viewport.height:innerHeight;
  const probe=document.getElementById('safe-area-probe');
  if(!probe)return;
  const inset=getComputedStyle(probe);
  const left=parseFloat(inset.paddingLeft)||0,right=parseFloat(inset.paddingRight)||0;
  const top=parseFloat(inset.paddingTop)||0,bottom=parseFloat(inset.paddingBottom)||0;
  const availableWidth=Math.max(1,width-left-right),availableHeight=Math.max(1,height-top-bottom);
  const gameWidth=Math.min(availableWidth,availableHeight*4/3),gameHeight=gameWidth*3/4;
  const values={
   '--game-width':gameWidth+'px','--game-height':gameHeight+'px',
   '--game-left':((viewport?viewport.offsetLeft:0)+left+(availableWidth-gameWidth)/2)+'px',
   '--game-top':((viewport?viewport.offsetTop:0)+top+(availableHeight-gameHeight)/2)+'px'
  };
  for(const [name,value] of Object.entries(values))document.documentElement.style.setProperty(name,value);
  const layout=Math.round(width)+'×'+Math.round(height)+' → '+Math.round(gameWidth)+'×'+Math.round(gameHeight);
  if(layout!==lastLayout){lastLayout=layout;window.trollDiag?.mark('layout','Screen '+layout);}
 }
 function schedule(){if(!scheduled){scheduled=true;requestAnimationFrame(fit);}}
 addEventListener('DOMContentLoaded',()=>{
  const probe=document.createElement('div');probe.id='safe-area-probe';
  probe.style.cssText='position:fixed;visibility:hidden;pointer-events:none;padding:env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left)';
  document.body.append(probe);fit();
  new MutationObserver(schedule).observe(document.getElementById('canvas'),{attributes:true,attributeFilter:['width','height']});
 });
 addEventListener('resize',schedule);addEventListener('orientationchange',schedule);
 window.visualViewport?.addEventListener('resize',schedule);
 window.visualViewport?.addEventListener('scroll',schedule);
})();
