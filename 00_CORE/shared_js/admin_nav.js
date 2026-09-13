/* ---------- FASE 7: navegación rápida Ctrl+K ---------- */
const CMDK_TABS = [
  ['dash','🏠 Resumen'], ['leads','📥 Leads'], ['clientes','👥 Clientes'], ['quotes','🧾 Cotizaciones'],
  ['proposal','📝 Cotizador'], ['inventory','📦 Inventario'], ['oc','🛒 Compras'], ['sales','💵 Ventas'],
  ['proyectos','🏗️ Proyectos'], ['cobros','💰 Cobros'], ['flujocaja','🧮 Caja'], ['expenses','📉 Gastos'],
  ['pnl','📊 Resultados'], ['reviews','⭐ Reseñas'], ['analytics','📊 Estadísticas'], ['flow','🌊 Flujo'], ['ayuda','❓ Ayuda'],
];
let cmdkSel = 0;
function abrirCmdk(){
  if ($('cmdkOverlay')) return;
  const ov = document.createElement('div');
  ov.id = 'cmdkOverlay'; ov.className = 'cmdk-overlay';
  ov.innerHTML = '<div class="cmdk-box"><input id="cmdkInput" placeholder="Ir a... (escribe el nombre de la sección)" autocomplete="off"><div id="cmdkList"></div><div class="cmdk-hint">↑↓ seleccionar · Enter ir · Esc cerrar</div></div>';
  document.body.appendChild(ov);
  const inp = $('cmdkInput');
  inp.addEventListener('input', pintarCmdk);
  inp.addEventListener('keydown', e=>{
    const items = CMDK_TABS.filter(t=>t[1].toLowerCase().includes(inp.value.toLowerCase()));
    if (e.key === 'ArrowDown') { e.preventDefault(); cmdkSel = Math.min(cmdkSel + 1, items.length - 1); pintarCmdk(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); cmdkSel = Math.max(cmdkSel - 1, 0); pintarCmdk(); }
    else if (e.key === 'Enter') { e.preventDefault(); if (items[cmdkSel]) { irCmdk(items[cmdkSel][0]); } }
  });
  pintarCmdk();
  inp.focus();
  ov.addEventListener('mousedown', e=>{ if (e.target === ov) cerrarCmdk(); });
}
function pintarCmdk(){
  const q = $('cmdkInput').value.toLowerCase();
  const items = CMDK_TABS.filter(t=>t[1].toLowerCase().includes(q));
  if (cmdkSel >= items.length) cmdkSel = 0;
  $('cmdkList').innerHTML = items.map((t, i)=>'<div class="cmdk-item'+(i===cmdkSel?' sel':'')+'" onclick="irCmdk(\''+t[0]+'\')">'+esc(t[1])+'</div>').join('') || '<div class="cmdk-item muted">Sin coincidencias</div>';
}
function irCmdk(tab){ cerrarCmdk(); showTab(tab); }
function cerrarCmdk(){ const ov = $('cmdkOverlay'); if (ov) ov.remove(); }
document.addEventListener('keydown', e=>{
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); abrirCmdk(); }
  else if (e.key === 'Escape') cerrarCmdk();
});

function showTab(name){
  document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active', t.dataset.tab===name));
  document.querySelectorAll('.mgroup').forEach(g=>{ g.removeAttribute('open'); g.classList.toggle('active', (g.dataset.group||'').split(' ').indexOf(name)!==-1); });
  const nav = $('mainMenu'); if (nav) nav.classList.remove('open');
  ['dash','leads','clientes','quotes','proposal','inventory','oc','sales','proyectos','cobros','expenses','pnl','reviews','analytics','flujocaja','flow','ayuda'].forEach(n=>$('tab-'+n).classList.toggle('hidden', n!==name));
  if (name==='dash') loadDash();
  if (name==='pnl' && !$('pnlCards').innerHTML) generarPNL();
  if (name==='flow') loadFlow();
  if (name==='oc') loadOC();
  if (name==='clientes') loadClientes();
  if (name==='proyectos') loadProyectos();
  if (name==='cobros') loadCXC();
  if (name==='flujocaja') loadFlujoCaja();
  if (name==='pnl') loadAlertas();
}

/* ---------- selector de producto (para movimientos y edicion desde el menu) ---------- */
function elegirProducto(cb){
  const prods = (biz.productos||[]).filter(p=>p.estado!=='inactivo');
  if (!prods.length) { notice('No hay productos activos. Crea uno primero en Inventario.', false); return; }
  const ov = document.createElement('div');
  ov.className = 'cmdk-overlay';
  ov.innerHTML = '<div class="cmdk-box"><input id="pickInput" placeholder="Buscar producto (código o nombre)..." autocomplete="off"><div id="pickList"></div><div class="cmdk-hint">↑↓ seleccionar · Enter elegir · Esc cerrar</div></div>';
  document.body.appendChild(ov);
  const inp = $('pickInput');
  let items = [], sel = 0;
  const render = ()=>{
    const q = inp.value.toLowerCase();
    items = prods.filter(p=>!q || (String(p.codigo)+' '+String(p.nombre)).toLowerCase().indexOf(q)!==-1).slice(0,30);
    if (sel >= items.length) sel = 0;
    $('pickList').innerHTML = items.map((p,i)=>'<div class="cmdk-item'+(i===sel?' sel':'')+'" data-id="'+esc(p.id)+'"><span>'+esc(p.codigo)+' · '+esc(p.nombre)+'</span></div>').join('') || '<div class="cmdk-item muted">Sin coincidencias</div>';
  };
  const cerrar = ()=>ov.remove();
  const elegir = (id)=>{ const p = prods.filter(x=>String(x.id)===String(id))[0]; cerrar(); if (p) cb(p.id); };
  inp.addEventListener('input', ()=>{ sel=0; render(); });
  inp.addEventListener('keydown', e=>{
    if (e.key==='ArrowDown') { e.preventDefault(); sel=Math.min(sel+1, items.length-1); render(); }
    else if (e.key==='ArrowUp') { e.preventDefault(); sel=Math.max(sel-1,0); render(); }
    else if (e.key==='Enter') { e.preventDefault(); if (items[sel]) elegir(items[sel].id); }
    else if (e.key==='Escape') { cerrar(); }
  });
  $('pickList').addEventListener('click', e=>{ const it = e.target.closest('[data-id]'); if (it) elegir(it.dataset.id); });
  ov.addEventListener('click', e=>{ if (e.target===ov) cerrar(); });
  render(); inp.focus();
}
function invMov(tipo){
  if (tipo==='ajuste'){ elegirProducto(pid=>showAdjustForm(pid)); return; }
  showMovForm(tipo);
}
function invEditar(){ elegirProducto(pid=>showProductForm(pid)); }
function provScroll(){ setTimeout(()=>{ const el=$('provAnchor'); if (el) el.scrollIntoView({behavior:'smooth', block:'start'}); }, 400); }

