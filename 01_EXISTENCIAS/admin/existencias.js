/* =====================================================================
   MINI-ERP: inventario, almacenes, ventas, gastos y estado de resultados
   ===================================================================== */
let biz = { productos: [], almacenes: [], stock: [], config: { moneda_base: 'MXN', tipo_cambio: '18.5' } };
let saleItems = [];
let pnlData = null;

function loadBiz(){
  apiGet('productos').then(d=>{ if(d&&d.ok){ biz.productos=d.productos; renderInventory(); if($('sSearch').value) searchSaleProducts(); if($('pItems')) renderItemRows(); } });
  apiGet('almacenes').then(d=>{ if(d&&d.ok){ biz.almacenes=d.almacenes; fillWarehouseSelects(); renderInventory(); } });
  apiGet('stock').then(d=>{ if(d&&d.ok){ biz.stock=d.stock; renderInventory(); renderSaleItems(); } });
  apiGet('movimientos').then(d=>{ if(d&&d.ok) renderMovs(d.movimientos); });
  apiGet('ventas').then(d=>{ if(d&&d.ok) renderSales(d.ventas); });
  apiGet('gastos').then(d=>{ if(d&&d.ok) renderExpenses(d.gastos); });
  apiGet('cxp').then(d=>{ if(d&&d.ok){ cxpCache = d.cxp || []; pagosCache = d.pagos || []; renderCXP(d); } });
  apiGet('config').then(d=>{ if(d&&d.ok) biz.config=d; });
}

function fillWarehouseSelects(){
  const opts = biz.almacenes.map(a=>'<option value="'+esc(a.id)+'">'+esc(a.nombre)+'</option>').join('');
  $('invAlmacen').innerHTML = '<option value="">Todos los almacenes</option>'+opts;
  $('sAlmacen').innerHTML = '<option value="">— Selecciona —</option>'+opts;
  if ($('movFAlmacen')) $('movFAlmacen').innerHTML = '<option value="">Todos los almacenes</option>'+opts;
}

function stockTotal(pid){
  return biz.stock.filter(s=>String(s.producto_id)===String(pid))
    .reduce((sum,s)=>sum+(Number(s.cantidad)||0), 0);
}
function stockEn(pid, aid){
  if (!aid) return stockTotal(pid);
  const s = biz.stock.filter(x=>String(x.producto_id)===String(pid)&&String(x.almacen_id)===String(aid))[0];
  return s ? Number(s.cantidad)||0 : 0;
}

let selectedProdId = null;

function renderInventory(){
  const aid = $('invAlmacen').value;
  const q = ($('invSearch').value || '').trim().toLowerCase();
  const verInactivos = $('invVerInactivos').checked;
  // mini dashboard de estado
  const total = biz.productos.length;
  const activos = biz.productos.filter(p=>p.estado!=='inactivo').length;
  const sinFoto = biz.productos.filter(p=>p.estado!=='inactivo' && !p.foto).length;
  const revision = biz.productos.filter(p=>p.estado!=='inactivo' && String(p.notas||'').indexOf('REVISION')>=0).length;
  // FASE 1: dashboard completo de salud del inventario
  const vivos = biz.productos.filter(p=>p.estado!=='inactivo');
  const sinPrecio = vivos.filter(p=>!(Number(p.precio)>0)).length;
  const sinCosto = vivos.filter(p=>!(Number(p.costo)>0)).length;
  const sinStock = vivos.filter(p=>stockTotal(p.id)<=0).length;
  const stockBajo = vivos.filter(p=>{const min=Number(p.stock_minimo)||0; return min>0 && stockTotal(p.id)<=min;}).length;
  const tc = Number(biz.config.tipo_cambio)||18.5, base = biz.config.moneda_base||'MXN';
  const valorInv = vivos.reduce((s,p)=>{
    const co=Number(p.costo)||0, m=p.moneda||'MXN';
    const cob = m===base ? co : (base==='MXN'&&m==='USD' ? co*tc : (base==='USD'&&m==='MXN' ? co/tc : co));
    return s + stockTotal(p.id)*cob;
  },0);
  $('invDash').innerHTML =
    '<div class="pnl-card"><div class="k">Productos</div><div class="v">'+total+'</div></div>' +
    '<div class="pnl-card good"><div class="k">Activos</div><div class="v">'+activos+'</div></div>' +
    '<div class="pnl-card '+(sinPrecio?'bad':'')+'"><div class="k">Sin precio</div><div class="v">'+sinPrecio+'</div></div>' +
    '<div class="pnl-card '+(sinCosto?'bad':'')+'"><div class="k">Sin costo</div><div class="v">'+sinCosto+'</div></div>' +
    '<div class="pnl-card"><div class="k">Sin foto</div><div class="v">'+sinFoto+'</div></div>' +
    '<div class="pnl-card"><div class="k">Sin stock</div><div class="v">'+sinStock+'</div></div>' +
    '<div class="pnl-card '+(stockBajo?'bad':'')+'"><div class="k">Stock bajo</div><div class="v">'+stockBajo+'</div></div>' +
    '<div class="pnl-card"><div class="k">Valor inventario</div><div class="v" style="font-size:0.95rem;">'+fmtMoney(valorInv)+' '+esc(base)+'</div></div>' +
    '<div class="pnl-card '+(revision?'bad':'')+'"><div class="k">Revisión manual</div><div class="v">'+revision+'</div></div>';
  let lista = biz.productos.filter(p=>{
    if (!verInactivos && p.estado==='inactivo') return false;
    if (q && !(String(p.codigo||'').toLowerCase().includes(q) || String(p.nombre||'').toLowerCase().includes(q))) return false;
    return true;
  });
  if (!lista.length) { $('invTable').innerHTML='<tr><td colspan="9" class="muted">Sin productos. Dale a "＋ Producto" o importa tu lista.</td></tr>'; return; }
  $('invTable').innerHTML = lista.map(p=>{
    const costo=Number(p.costo)||0, precio=Number(p.precio)||0;
    const margen = precio ? ((precio-costo)/precio*100).toFixed(0)+'%' : '—';
    const st = stockEn(p.id, aid);
    const min = Number(p.stock_minimo)||0;
    const alerta = min && st<=min ? ' stock-alert' : '';
    const mon = esc(p.moneda||'MXN');
    const inact = p.estado==='inactivo';
    const revision = String(p.notas||'').indexOf('REVISION')>=0;
    return '<tr data-pid="'+p.id+'" onclick="selectProduct(\''+p.id+'\')" class="'+(inact?'inv-inactive ':'')+(selectedProdId===p.id?'inv-selected':'')+'">' +
      '<td style="white-space:nowrap;">'+esc(p.codigo||'—')+(revision?' <span class="badge-revision">REVISAR</span>':'')+'</td>' +
      '<td>'+esc(p.nombre)+'</td><td>'+esc(p.categoria)+(p.subcategoria?' <span class="muted">/'+esc(p.subcategoria)+'</span>':'')+'</td>' +
      '<td>'+fmtMoney(costo)+' '+mon+'</td><td>'+fmtMoney(precio)+' '+mon+'</td><td>'+margen+'</td>' +
      '<td class="'+alerta+'">'+st+'</td><td>'+(min||'—')+'</td>' +
      '<td style="white-space:nowrap;">' +
      '<button class="btn btn-sm" onclick="event.stopPropagation();showProductForm(\''+p.id+'\')">✎</button> ' +
      '<button class="btn btn-sm" onclick="event.stopPropagation();showAdjustForm(\''+p.id+'\')">±</button> ' +
      (inact
        ? '<button class="btn btn-sm" onclick="event.stopPropagation();restoreProduct(\''+p.id+'\')">↩</button>'
        : '<button class="btn btn-danger btn-sm" onclick="event.stopPropagation();deleteProduct(\''+p.id+'\')">✕</button>') +
      '</td></tr>';
  }).join('');
}

function selectProduct(id){
  selectedProdId = id;
  const p = biz.productos.filter(x=>String(x.id)===String(id))[0];
  if (!p) return;
  renderInventory();
  const st = stockTotal(p.id);
  $('invPhoto').innerHTML =
    (p.foto ? '<img src="'+esc(p.foto)+'" alt="'+esc(p.nombre)+'" onerror="this.style.display=\'none\'">'
            : '<div style="padding:2rem 0.5rem;color:var(--muted);font-size:0.75rem;">Sin fotografía<br>(Fase 2: podrás subirla aquí)</div>') +
    '<div class="ph-code">'+esc(p.codigo||'')+'</div>' +
    '<div class="ph-name">'+esc(p.nombre)+'</div>' +
    '<div class="ph-meta">'+esc(p.categoria)+(p.subcategoria?' · '+esc(p.subcategoria):'')+'<br>' +
    (p.proveedor?'Proveedor: '+esc(p.proveedor)+'<br>':'') +
    'Stock total: <strong>'+st+'</strong> '+(p.unidad||'')+'<br>' +
    (Number(p.precio)?'Precio: <strong class="gold">'+fmtMoney(p.precio)+' '+esc(p.moneda||'MXN')+'</strong>':'Precio: pendiente') +
    '</div>' +
    '<div style="margin-top:0.8rem;"><button class="btn btn-sm" onclick="showProductForm(\''+p.id+'\')">✎ Editar producto</button></div>' +
    '<div id="invHist" style="margin-top:0.8rem;"></div>';
  loadProductHistory(p.id);
}

// FASE 1: historial de movimientos del producto seleccionado (trazabilidad completa)
function loadProductHistory(pid){
  const box = $('invHist');
  if (!box) return;
  box.innerHTML = '<p class="muted" style="font-size:0.72rem;">Cargando historial…</p>';
  apiGet('movimientos&producto_id='+encodeURIComponent(pid)).then(d=>{
    let movs = (d && d.movimientos) || [];
    // filtro cliente ademas del server: compatible con backend viejo (sin filtro)
    movs = movs.filter(m=>String(m.producto_id)===String(pid));
    if (!movs.length) { box.innerHTML='<p class="muted" style="font-size:0.72rem;">Sin movimientos registrados.</p>'; return; }
    box.innerHTML = '<table class="hist-table"><thead><tr><th>Fecha</th><th>Tipo</th><th>Cant.</th><th>Existencia</th><th>Documento</th></tr></thead><tbody>' +
      movs.slice().reverse().slice(0,30).map(m=>
        '<tr><td>'+esc(String(m.fecha||'').slice(0,16))+'</td><td>'+esc(m.tipo)+'</td><td>'+esc(m.cantidad)+'</td>' +
        '<td>'+(m.existencia_anterior!==undefined && m.existencia_anterior!=='' ? esc(m.existencia_anterior)+' → '+esc(m.existencia_posterior) : '—')+'</td>' +
        '<td>'+movDocTxt(m)+(m.referencia?' <span class="muted">'+esc(m.referencia)+'</span>':'')+(m.id?' <span class="muted">'+esc(m.id)+'</span>':'')+'</td></tr>').join('') +
      '</tbody></table>' +
      (movs.length>30 ? '<p class="muted" style="font-size:0.7rem;margin-top:0.3rem;">Mostrando los últimos 30 de '+movs.length+' movimientos.</p>' : '');
  }).catch(()=>{ box.innerHTML='<p class="muted" style="font-size:0.72rem;">No se pudo cargar el historial.</p>'; });
}

function restoreProduct(id){
  apiPost({tipo:'restore_product', id}).then(d=>{
    notice(d&&d.ok?'Producto recuperado.':(d&&d.error)||'Error', !!(d&&d.ok));
    if(d&&d.ok) loadBiz();
  });
}

/* ---------- Movimientos recientes: cache + filtros + CSV + imprimir ---------- */
let movsCache = [];
function renderMovs(list){ movsCache = list || []; renderMovFiltered(); }
function movFiltered(){
  const desde = $('movFDesde').value, hasta = $('movFHasta').value, tipo = $('movFTipo').value,
    alm = $('movFAlmacen').value, q = ($('movFBuscar').value||'').trim().toLowerCase();
  return movsCache.filter(m=>{
    const f = String(m.fecha||'').slice(0,10);
    if (desde && f < desde) return false;
    if (hasta && f > hasta) return false;
    if (tipo && String(m.tipo)!==tipo) return false;
    if (alm && String(m.almacen_id)!==String(alm)) return false;
    if (q){
      const hay = (String(m.producto||'')+' '+String(m.notas||'')+' '+String(m.referencia||'')+' '+String(m.proveedor||'')+' '+String(m.id||'')).toLowerCase();
      if (hay.indexOf(q)===-1) return false;
    }
    return true;
  });
}
function movDocTxt(m){
  const dt = String(m.documento_tipo||''), did = String(m.documento_id||'');
  let txt;
  if (dt==='PROYECTO' && did) {
    const p = (typeof proyCache!=='undefined' ? proyCache : []).filter(x=>String(x.id)===did)[0];
    txt = '🏗 '+(p ? esc(p.folio)+' · '+esc(p.nombre) : 'Proyecto '+esc(did));
  }
  else if (dt==='LOTE' && did) txt = 'Lote '+esc(did);
  else if (dt==='ORDEN_COMPRA' && did) txt = 'OC '+esc(did);
  else txt = dt ? esc(dt) : '—';
  if (m.lote && dt!=='LOTE') txt += ' <span class="muted">· Lote '+esc(m.lote)+'</span>';
  return txt;
}
function renderMovFiltered(){
  const list = movFiltered().slice().reverse();
  if (!list.length) { $('movTable').innerHTML='<tr><td colspan="9" class="muted">Sin movimientos'+(movsCache.length?' con estos filtros.':'.')+'</td></tr>'; return; }
  $('movTable').innerHTML = list.map(m=>
    '<tr><td>'+esc(String(m.fecha||'').slice(0,16))+'</td><td>'+esc(m.tipo)+'</td><td>'+esc(m.producto)+'</td><td>'+esc(m.almacen)+'</td>' +
    '<td>'+esc(m.cantidad)+'</td>' +
    '<td>'+(m.existencia_anterior!==undefined && m.existencia_anterior!=='' ? esc(m.existencia_anterior)+' → '+esc(m.existencia_posterior) : '—')+'</td>' +
    '<td>'+movDocTxt(m)+(m.id?' <span class="muted">'+esc(m.id)+'</span>':'')+'</td>' +
    '<td>'+(m.referencia?esc(m.referencia)+' ':'')+(m.proveedor?'<span class="muted">'+esc(m.proveedor)+'</span>':'—')+'</td>' +
    '<td>'+esc(m.notas||'')+'</td></tr>').join('');
}
function movCSVEsc(v){ v=String(v===undefined||v===null?'':v); return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v; }
function movCSV(){
  const rows = movFiltered();
  if (!rows.length) { notice('No hay movimientos con estos filtros.', false); return; }
  const docTxt = m=>{ const dt=String(m.documento_tipo||''),did=String(m.documento_id||'');
    return dt==='LOTE'?'Lote '+did: dt==='PROYECTO'?'Proyecto '+did: dt==='ORDEN_COMPRA'?'OC '+did: dt; };
  const cab = ['Fecha','Tipo','Producto','Almacen','Cantidad','Exist. anterior','Exist. posterior','Documento','Lote','Referencia','Proveedor','Folio mov.','Usuario','Notas'];
  const txt = '\ufeff'+cab.join(',')+'\n'+rows.map(m=>
    [m.fecha,m.tipo,m.producto,m.almacen,m.cantidad,m.existencia_anterior,m.existencia_posterior,
     docTxt(m),m.lote||'',m.referencia,m.proveedor,m.id,m.usuario,m.notas].map(movCSVEsc).join(',')).join('\n');
  const blob = new Blob([txt],{type:'text/csv;charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'movimientos_'+fHoyLocal()+'.csv';
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=>URL.revokeObjectURL(a.href), 5000);
}
function printMovs(){
  const rows = movFiltered().slice().reverse();
  if (!rows.length) { notice('No hay movimientos con estos filtros.', false); return; }
  const w = window.open('', '_blank');
  if (!w) { notice('El navegador bloqueó la ventana de impresión.', false); return; }
  w.document.write('<!doctype html><html><head><meta charset="utf-8"><title>Movimientos de inventario</title>' +
    '<style>body{font-family:Arial,sans-serif;font-size:11px;padding:20px;}h1{font-size:16px;margin:0 0 4px;}p{margin:0 0 12px;color:#555;}table{width:100%;border-collapse:collapse;}th,td{border:1px solid #bbb;padding:4px 6px;text-align:left;vertical-align:top;}th{background:#eee;}</style></head><body>' +
    '<h1>ADIS — Movimientos de inventario ('+rows.length+')</h1><p>Generado: '+new Date().toLocaleString()+'</p>' +
    '<table><thead><tr><th>Fecha</th><th>Tipo</th><th>Producto</th><th>Almacén</th><th>Cant.</th><th>Existencia</th><th>Documento</th><th>Referencia</th><th>Proveedor</th><th>Notas</th></tr></thead><tbody>' +
    rows.map(m=>'<tr><td>'+esc(String(m.fecha||'').slice(0,16))+'</td><td>'+esc(m.tipo)+'</td><td>'+esc(m.producto)+'</td><td>'+esc(m.almacen)+'</td><td>'+esc(m.cantidad)+'</td><td>'+esc(m.existencia_anterior)+' → '+esc(m.existencia_posterior)+'</td><td>'+movDocTxt(m)+'</td><td>'+esc(m.referencia||'')+'</td><td>'+esc(m.proveedor||'')+'</td><td>'+esc(m.notas||'')+'</td></tr>').join('') +
    '</tbody></table></body></html>');
  w.document.close();
  w.focus(); setTimeout(()=>{ w.print(); }, 400);
}

/* ----- formularios dinamicos (producto / almacen / config / ajuste) ----- */
function closeBizForms(){ $('bizForms').innerHTML=''; }

/* ----- FASE 1: captura rapida de precios por lote ----- */
let priceRowsCache = [];
function showPricesForm(){
  priceRowsCache = biz.productos.filter(p=>p.estado!=='inactivo').map(p=>({
    id:p.id, codigo:p.codigo, nombre:p.nombre, costo:Number(p.costo)||0, precio:Number(p.precio)||0, moneda:p.moneda||'MXN'}));
  $('bizForms').innerHTML = '<div class="card-box"><div class="toolbar" style="margin-bottom:0.5rem;">' +
    '<strong>Captura rápida de precios</strong>' +
    '<input id="prSearch" placeholder="Filtrar por código o nombre..." oninput="renderPricesRows(this.value)" style="width:220px;">' +
    '<button class="btn btn-solid btn-sm" onclick="savePrices()">💾 Guardar cambios</button> ' +
    '<button class="btn btn-sm" onclick="closeBizForms()">Cerrar</button></div>' +
    '<div id="prRows"></div></div>';
  renderPricesRows('');
}
function priceMargenTxt(r){
  if (!r.precio) return '—';
  const neg = r.costo > r.precio;
  return '<span style="color:'+(neg?'#e37c7c':'#7ce3a1')+';">'+( ((r.precio-r.costo)/r.precio*100).toFixed(1)+'%'+(neg?' ⚠':'') )+'</span>';
}
function renderPricesRows(q){
  q = (q||'').trim().toLowerCase();
  const rows = priceRowsCache
    .map((r,i)=>({r,i}))
    .filter(o=>!q || String(o.r.codigo||'').toLowerCase().includes(q) || String(o.r.nombre||'').toLowerCase().includes(q))
    .slice(0,100);
  $('prRows').innerHTML = '<div class="table-scroll"><table><thead><tr><th>Código</th><th>Producto</th><th>Costo</th><th>Precio</th><th>Margen</th></tr></thead><tbody>' +
    rows.map(o=>
      '<tr><td style="white-space:nowrap;">'+esc(o.r.codigo||'—')+'</td><td>'+esc(o.r.nombre)+'</td>' +
      '<td><input type="number" min="0" step="0.01" value="'+(o.r.costo||'')+'" onchange="priceRowsCache['+o.i+'].costo=parseFloat(this.value)||0; updPriceMargen('+o.i+')"></td>' +
      '<td><input type="number" min="0" step="0.01" value="'+(o.r.precio||'')+'" onchange="priceRowsCache['+o.i+'].precio=parseFloat(this.value)||0; updPriceMargen('+o.i+')"></td>' +
      '<td id="prM'+o.i+'">'+priceMargenTxt(o.r)+'</td></tr>').join('') +
    '</tbody></table></div>' +
    (priceRowsCache.length>100 && !q ? '<p class="muted" style="font-size:0.72rem;margin-top:0.4rem;">Mostrando 100 de '+priceRowsCache.length+' productos — usa el filtro para ver los demás.</p>' : '');
}
function updPriceMargen(i){ const el=$('prM'+i); if(el) el.innerHTML=priceMargenTxt(priceRowsCache[i]); }
function savePrices(){
  const items = priceRowsCache.map(r=>({id:r.id, costo:r.costo, precio:r.precio}));
  apiPost({tipo:'update_precios', items})
    .then(d=>{
      notice(d&&d.ok?('Precios actualizados en '+(d.actualizados||0)+' productos.'):errMsg(d,'No se pudo guardar.'), !!(d&&d.ok));
      if(d&&d.ok) loadBiz();
    })
    .catch(()=>notice('Error de conexión al guardar precios.', false));
}

function showProductForm(id){
  const p = id ? biz.productos.filter(x=>String(x.id)===String(id))[0] : null;
  $('bizForms').innerHTML = '<div class="card-box"><div class="row">' +
    '<div><label>Código *</label><input id="pCodigo" value="'+esc(p?p.codigo:'')+'" placeholder="HJPVC-001" style="text-transform:uppercase;"></div>' +
    '<div><label>Nombre *</label><input id="pNombre" value="'+esc(p?p.nombre:'')+'"></div>' +
    '<div><label>Categoría</label><input id="pCat" value="'+esc(p?p.categoria:'')+'"></div>' +
    '<div><label>Subcategoría</label><input id="pSubcat" value="'+esc(p?p.subcategoria:'')+'"></div>' +
    '<div><label>Proveedor</label><input id="pProv" value="'+esc(p?p.proveedor:'')+'"></div>' +
    '<div><label>Costo</label><input type="number" id="pCosto" min="0" step="0.01" value="'+(p?p.costo:'')+'"></div>' +
    '<div><label>Precio venta</label><input type="number" id="pPrecio" min="0" step="0.01" value="'+(p?p.precio:'')+'"></div>' +
    '<div><label>Unidad</label><input id="pUnidad" value="'+esc(p?p.unidad:'pieza')+'"></div>' +
    '<div><label>Stock mínimo</label><input type="number" id="pMin" min="0" value="'+(p?p.stock_minimo:'')+'"></div>' +
    '<div><label>Moneda</label><select id="pMoneda"><option value="MXN"'+((!p||p.moneda==='MXN')?' selected':'')+'>MXN</option><option value="USD"'+(p&&p.moneda==='USD'?' selected':'')+'>USD</option></select></div>' +
    '<div><label>Estado</label><select id="pEstado"><option value="activo"'+((!p||p.estado!=='inactivo')?' selected':'')+'>Activo</option><option value="inactivo"'+(p&&p.estado==='inactivo'?' selected':'')+'>Inactivo</option></select></div>' +
    '</div>' +
    '<label>Fotografía (ruta en la web, ej: img/1-placas-pvc/.../foto.jpg)</label>' +
    '<input id="pFoto" value="'+esc(p?p.foto:'')+'" placeholder="img/...">' +
    '<label>Descripción</label><textarea id="pDesc" rows="2">'+esc(p?p.descripcion:'')+'</textarea>' +
    '<label>Notas internas</label><input id="pNotas" value="'+esc(p?p.notas:'')+'">' +
    '<div class="toolbar" style="margin-top:1rem;">' +
    '<button class="btn btn-solid btn-sm" onclick="saveProduct(\''+(p?p.id:'')+'\')">💾 Guardar</button> ' +
    '<button class="btn btn-sm" onclick="closeBizForms()">Cancelar</button></div></div>';
  (p ? $('pCodigo') : $('pCodigo')).focus();
}

function saveProduct(id){
  const codigo=$('pCodigo').value.trim().toUpperCase(), nombre=$('pNombre').value.trim();
  if (!codigo) { notice('El código es obligatorio.', false); return; }
  if (!nombre) { notice('El producto necesita nombre.', false); return; }
  apiPost({tipo:'save_product', id:id||undefined, codigo, nombre, categoria:$('pCat').value.trim(),
    subcategoria:$('pSubcat').value.trim(), proveedor:$('pProv').value.trim(),
    costo:parseFloat($('pCosto').value)||0, precio:parseFloat($('pPrecio').value)||0,
    unidad:$('pUnidad').value.trim()||'pieza', stock_minimo:parseFloat($('pMin').value)||0,
    moneda:$('pMoneda').value, foto:$('pFoto').value.trim(), estado:$('pEstado').value,
    descripcion:$('pDesc').value.trim(), notas:$('pNotas').value.trim()}).then(d=>{
    notice(d&&d.ok?'Producto guardado.':(d&&d.error)||'No se pudo guardar.', !!(d&&d.ok));
    if(d&&d.ok){ closeBizForms(); loadBiz(); }
  });
}

function deleteProduct(id){
  if (!confirma('prod-'+id, 'Desactivar este producto (no se borra de la hoja).')) return;
  apiPost({tipo:'delete_product', id}).then(d=>{ if(d&&d.ok) loadBiz(); });
}

function showWarehouseForm(){
  const lista = biz.almacenes.map(a=>
    '<tr><td>'+esc(a.nombre)+'</td><td>'+esc(a.ubicacion)+'</td>' +
    '<td><button class="btn btn-danger btn-sm" onclick="deleteWarehouse(\''+a.id+'\')">✕</button></td></tr>').join('');
  $('bizForms').innerHTML = '<div class="card-box"><div class="row">' +
    '<div><label>Nombre del almacén *</label><input id="wNombre" placeholder="Ej. Nogales, Rio Rico..."></div>' +
    '<div><label>Ubicación</label><input id="wUbi" placeholder="Dirección / ciudad"></div>' +
    '</div><div class="toolbar" style="margin-top:1rem;">' +
    '<button class="btn btn-solid btn-sm" onclick="saveWarehouse()">💾 Guardar almacén</button> ' +
    '<button class="btn btn-sm" onclick="closeBizForms()">Cerrar</button></div>' +
    '<div class="table-scroll"><table><thead><tr><th>Almacén</th><th>Ubicación</th><th></th></tr></thead><tbody>' +
    (lista || '<tr><td colspan="3" class="muted">Sin almacenes todavía.</td></tr>') + '</tbody></table></div></div>';
}

function saveWarehouse(){
  const nombre=$('wNombre').value.trim();
  if (!nombre) { notice('Escribe el nombre del almacén.', false); return; }
  apiPost({tipo:'save_almacen', nombre, ubicacion:$('wUbi').value.trim()}).then(d=>{
    notice(d&&d.ok?'Almacén guardado.':'No se pudo guardar.', !!(d&&d.ok));
    if(d&&d.ok){ closeBizForms(); loadBiz(); }
  });
}

function deleteWarehouse(id){
  if (!confirma('alm-'+id, 'Desactivar este almacén.')) return;
  apiPost({tipo:'delete_almacen', id}).then(d=>{ if(d&&d.ok){ closeBizForms(); loadBiz(); } });
}

function showConfigForm(){
  $('bizForms').innerHTML = '<div class="card-box"><div class="row">' +
    '<div><label>Moneda base (para resultados)</label><select id="cBase"><option value="MXN"'+(biz.config.moneda_base==='MXN'?' selected':'')+'>MXN — Pesos</option><option value="USD"'+(biz.config.moneda_base==='USD'?' selected':'')+'>USD — Dólares</option></select></div>' +
    '<div><label>Tipo de cambio (1 USD = ? en moneda base)</label><input type="number" id="cTC" min="0" step="0.01" value="'+esc(biz.config.tipo_cambio)+'"></div>' +
    '</div><div class="toolbar" style="margin-top:1rem;">' +
    '<button class="btn btn-solid btn-sm" onclick="saveConfig()">💾 Guardar</button> ' +
    '<button class="btn btn-sm" onclick="closeBizForms()">Cerrar</button></div>' +
    '<p class="muted">Ejemplo: si la moneda base es MXN y 1 dólar = $18.50 pesos, escribe 18.50. Las ventas y gastos en USD se convertirán automáticamente.</p></div>';
}

function saveConfig(){
  apiPost({tipo:'config', moneda_base:$('cBase').value, tipo_cambio:parseFloat($('cTC').value)||1}).then(d=>{
    notice(d&&d.ok?'Configuración guardada.':'No se pudo guardar.', !!(d&&d.ok));
    if(d&&d.ok){ biz.config=d; closeBizForms(); }
  });
}

function showAdjustForm(pid){
  const p = biz.productos.filter(x=>String(x.id)===String(pid))[0];
  if (!biz.almacenes.length) { notice('Primero crea un almacén.', false); return; }
  $('bizForms').innerHTML = '<div class="card-box"><p style="margin-bottom:0.5rem;"><strong>'+esc(p.nombre)+'</strong></p><div class="row">' +
    '<div><label>Almacén *</label><select id="mAlmacen">'+biz.almacenes.map(a=>'<option value="'+esc(a.id)+'">'+esc(a.nombre)+'</option>').join('')+'</select></div>' +
    '<div><label>Tipo *</label><select id="mTipo"><option value="entrada">Entrada (compra/mercancía)</option><option value="salida">Salida (merma/uso)</option><option value="ajuste">Ajuste (fijar cantidad exacta)</option></select></div>' +
    '<div><label>Cantidad *</label><input type="number" id="mCant" min="0" step="0.01"></div>' +
    '</div><label>Notas</label><input id="mNotas" placeholder="Ej. Compra a proveedor X, merma..."><div class="toolbar" style="margin-top:1rem;">' +
    '<button class="btn btn-solid btn-sm" onclick="saveAdjust(\''+p.id+'\')">💾 Aplicar</button> ' +
    '<button class="btn btn-sm" onclick="closeBizForms()">Cancelar</button></div></div>';
}

function saveAdjust(pid){
  apiPost({tipo:'movimiento', tipo_mov:$('mTipo').value, producto_id:pid, almacen_id:$('mAlmacen').value,
    cantidad:parseFloat($('mCant').value)||0, notas:$('mNotas').value.trim()}).then(d=>{
    notice(d&&d.ok?'Movimiento aplicado. Stock nuevo: '+(d.stock_nuevo!==undefined?d.stock_nuevo:'?'):errMsg(d), !!(d&&d.ok));
    if(d&&d.ok){ closeBizForms(); loadBiz(); }
  });
}

/* ---------- Entrada / salida multi-producto (LOTE trazable) ----------
   Una sola operacion con N productos. El backend aplica todo bajo un lock
   con folio LOTE-AAAA-NNNN compartido; si algo falla no se mueve nada. */
let movItems = [];
function fHoyLocal(){ const d=new Date(); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); }
function showMovForm(tipo){
  if (!biz.almacenes.length) { notice('Primero crea un almacén.', false); return; }
  movItems = [];
  const esEntrada = tipo==='entrada';
  const hoy = fHoyLocal();
  apiGet('proveedores').then(d=>{ if(d&&d.ok){ provCache=d.proveedores||[]; const s=$('mProv'); if(s) s.innerHTML='<option value="">— Ninguno —</option>'+provCache.filter(p=>String(p.activo)!=='no').map(p=>'<option value="'+esc(p.nombre)+'">'+esc(p.nombre)+'</option>').join(''); } });
  apiGet('proyectos').then(d=>{ if(d&&d.ok){ proyCache=d.proyectos||[]; const s=$('mProy'); if(s) s.innerHTML='<option value="">— Ninguna (uso general) —</option>'+proyCache.filter(p=>p.estado==='ACTIVO').map(p=>'<option value="'+esc(p.id)+'">'+esc(p.folio)+' · '+esc(p.nombre)+'</option>').join(''); } });
  $('bizForms').innerHTML = '<div class="card-box">' +
    '<div class="toolbar" style="margin-bottom:0.5rem;"><strong>'+(esEntrada?'📥 Entrada de material':'📤 Salida de material')+'</strong>' +
    '<span class="muted">Puedes incluir varios productos en una sola operación</span></div>' +
    '<div class="row">' +
    '<div><label>Fecha</label><input type="date" id="mFecha" value="'+hoy+'" max="'+hoy+'"></div>' +
    '<div><label>Almacén *</label><select id="mAlmacen">'+biz.almacenes.map(a=>'<option value="'+esc(a.id)+'">'+esc(a.nombre)+'</option>').join('')+'</select></div>' +
    (esEntrada
      ? '<div><label>Proveedor</label><select id="mProv"><option value="">— Ninguno —</option></select></div>' +
        '<div><label>Documento (factura/remisión)</label><input id="mRef" placeholder="Ej. FAC-1234"></div>'
      : '<div><label>Proyecto / obra</label><select id="mProy"><option value="">— Ninguna (uso general) —</option></select></div>' +
        '<div><label>Motivo / referencia</label><input id="mRef" placeholder="Ej. Merma, uso en obra..."></div>') +
    '<div><label>Moneda</label><select id="mMoneda"><option value="MXN">MXN</option><option value="USD">USD</option></select></div>' +
    '</div>' +
    '<label>Agregar producto (del inventario)</label>' +
    '<div class="search-results"><input id="mSearch" placeholder="Escribe el nombre o código del producto..." autocomplete="off" oninput="searchMovProducts()"><div id="mSearchResults"></div></div>' +
    '<div class="items" id="mItems"></div>' +
    '<div class="total-line"><span class="muted" id="mTotalTxt">Piezas: 0</span></div>' +
    '<label>Notas</label><input id="mNotas" placeholder="Observaciones...">' +
    '<div class="toolbar" style="margin-top:1rem;">' +
    '<button class="btn btn-solid btn-sm" onclick="saveMovLote(\''+tipo+'\')">💾 Aplicar '+(esEntrada?'entrada':'salida')+'</button> ' +
    '<button class="btn btn-sm" onclick="closeBizForms()">Cancelar</button></div></div>';
  renderMovItems();
  setTimeout(()=>{ const el=$('bizForms'); if (el) el.scrollIntoView({behavior:'smooth', block:'start'}); }, 100);
}
function movEsEntrada(){ return !!document.getElementById('mProv'); }
function searchMovProducts(){
  const q = $('mSearch').value.trim().toLowerCase();
  const box = $('mSearchResults');
  if (q.length < 2) { box.innerHTML=''; return; }
  const matches = biz.productos.filter(p => p.estado!=='inactivo' && ((p.nombre||'')+' '+(p.codigo||'')+' '+(p.categoria||'')).toLowerCase().includes(q)).slice(0,8);
  box.innerHTML = '<div class="sr-list">' + (matches.length
    ? matches.map(p=>'<div class="sr-item" onclick="movAddProduct(\''+p.id+'\')"><span>'+esc(p.codigo||'')+' · '+esc(p.nombre)+'</span><span class="gold">stock: '+stockTotal(p.id)+'</span></div>').join('')
    : '<div class="sr-item muted">Sin resultados</div>') + '</div>';
}
function movAddProduct(pid){
  const p = biz.productos.filter(x=>String(x.id)===String(pid))[0];
  if (!p) return;
  if (movItems.some(it=>String(it.producto_id)===String(pid))) { notice('Ese producto ya está en la lista.', false); return; }
  movItems.push({producto_id:p.id, codigo:p.codigo||'', nombre:p.nombre, cantidad:1, costo_unit:(Number(p.costo)||0)});
  $('mSearch').value=''; $('mSearchResults').innerHTML='';
  renderMovItems();
}
function renderMovItems(){
  const box = $('mItems');
  if (!box) return;
  const conCosto = movEsEntrada();
  box.innerHTML = (movItems.length ? '<div class="item-row" style="opacity:.65;"><input value="Producto" disabled>' +
    '<input type="text" value="Cantidad" disabled>' +
    (conCosto?'<input type="text" value="Costo unit." disabled>':'') +
    '<input type="text" value="" disabled></div>' : '<p class="muted" style="font-size:0.75rem;">Sin productos todavía. Búscalos arriba para agregarlos.</p>') +
    movItems.map((it,i)=>'<div class="item-row">' +
      '<input value="'+esc(it.codigo?it.codigo+' · ':'')+esc(it.nombre)+'" disabled>' +
      '<input type="number" min="0.01" step="0.01" value="'+it.cantidad+'" onchange="movItems['+i+'].cantidad=parseFloat(this.value)||1; renderMovTotals()">' +
      (conCosto?'<input type="number" min="0" step="0.01" value="'+it.costo_unit+'" onchange="movItems['+i+'].costo_unit=parseFloat(this.value)||0; renderMovTotals()">':'') +
      '<button class="del" onclick="movItems.splice('+i+',1); renderMovItems()">✕</button></div>').join('');
  renderMovTotals();
}
function renderMovTotals(){
  const n = movItems.reduce((s,it)=>s+(Number(it.cantidad)||0),0);
  const el = $('mTotalTxt');
  if (!el) return;
  let txt = 'Piezas: '+n;
  if (movEsEntrada() && n>0) txt += ' · Costo total: '+fmtMoney(movItems.reduce((s,it)=>s+(Number(it.cantidad)||0)*(Number(it.costo_unit)||0),0))+' '+$('mMoneda').value;
  el.textContent = txt;
}
function saveMovLote(tipo){
  if (!$('mAlmacen').value) { notice('Selecciona un almacén.', false); return; }
  if (!movItems.length) { notice('Agrega al menos un producto.', false); return; }
  const items = movItems.map(it=>({producto_id:it.producto_id, cantidad:it.cantidad,
    costo_unit: tipo==='entrada' ? (it.costo_unit||0) : ''}));
  apiPost({tipo:'movimiento', tipo_mov:tipo, almacen_id:$('mAlmacen').value, fecha:$('mFecha').value,
    referencia:$('mRef').value.trim(), notas:$('mNotas').value.trim(), moneda:$('mMoneda').value,
    proveedor: tipo==='entrada' ? $('mProv').value : '',
    proyecto_id: tipo==='salida' ? $('mProy').value : '',
    items}).then(d=>{
    notice(d&&d.ok?((d.lote?('Lote '+d.lote+' aplicado ('+items.length+' producto(s)). '):'Movimiento aplicado. ')+'Stock actualizado.'):errMsg(d), !!(d&&d.ok));
    if(d&&d.ok){ closeBizForms(); loadBiz(); }
  });
}

