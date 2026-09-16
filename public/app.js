const deck = document.querySelector('#deck');
const stage = document.querySelector('#stage');
let rx = 58, rz = -24, zoom = 1, dragging = false, x = 0, y = 0;

function draw(){ deck.style.transform = `scale(${zoom}) rotateX(${rx}deg) rotateZ(${rz}deg)`; }
stage.addEventListener('pointerdown', e => { dragging = true; x=e.clientX; y=e.clientY; stage.setPointerCapture(e.pointerId); });
stage.addEventListener('pointermove', e => {
  if(!dragging) return;
  rz += (e.clientX-x)*.28; rx -= (e.clientY-y)*.28; x=e.clientX; y=e.clientY; draw();
});
stage.addEventListener('pointerup', () => dragging=false);
stage.addEventListener('pointercancel', () => dragging=false);
stage.addEventListener('wheel', e => { e.preventDefault(); zoom=Math.max(.55,Math.min(1.5,zoom-e.deltaY*.0007)); draw(); }, {passive:false});
stage.addEventListener('dblclick', () => { rx=58;rz=-24;zoom=1;draw(); });

document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('[data-view]').forEach(b => b.classList.toggle('active', b===button));
  document.querySelectorAll('.viewer').forEach(v => v.classList.remove('active'));
  document.querySelector(`#${button.dataset.view}View`).classList.add('active');
}));
