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
/* Desglose de existencias por almacen (solo almacenes con cantidad <> 0). */
function stockPorAlmacen(pid){
  return biz.stock
    .filter(s=>String(s.producto_id)===String(pid)&&(Number(s.cantidad)||0)!==0)
    .map(s=>({almacen_id:s.almacen_id, cantidad:Number(s.cantidad)||0,
              nombre:(biz.almacenes.filter(a=>String(a.id)===String(s.almacen_id))[0]||{}).nombre||'Almacén'}));
}
/* Traslado de existencia entre almacenes: sale del origen y entra al destino
   con la misma referencia. Usa los endpoints existentes (sin cambio de backend). */
function transferForm(pid, fromAid){
  const p = biz.productos.filter(x=>String(x.id)===String(pid))[0];
  if (!p) return;
  const origen = biz.almacenes.filter(a=>String(a.id)===String(fromAid))[0];
  const destinos = biz.almacenes.filter(a=>String(a.id)!==String(fromAid));
  if (!destinos.length) { notice('Necesitas al menos otro almacén de destino. Crea uno con "＋ Almacén".', false); return; }
  const disp = stockEn(pid, fromAid);
  $('bizForms').innerHTML = '<div class="card-box"><p style="margin-bottom:0.5rem;"><strong>Trasladar: '+esc(p.nombre)+'</strong></p><div class="row">' +
    '<div><label>De (almacén origen)</label><input value="'+esc(origen?origen.nombre:'—')+'" disabled></div>' +
    '<div><label>A (almacén destino) *</label><select id="tDestino">'+destinos.map(a=>'<option value="'+esc(a.id)+'">'+esc(a.nombre)+'</option>').join('')+'</select></div>' +
    '<div><label>Cantidad *</label><input type="number" id="tCant" min="0.01" step="0.01" max="'+disp+'" value="'+disp+'"></div>' +
    '</div><p class="muted" style="margin-top:0.5rem;font-size:0.75rem;">Disponible en origen: '+disp+' pieza(s).</p><div class="toolbar" style="margin-top:0.8rem;">' +
    '<button class="btn btn-solid btn-sm" onclick="applyTransfer(\''+p.id+'\',\''+fromAid+'\')">Aplicar traslado</button> ' +
    '<button class="btn btn-sm" onclick="closeBizForms()">Cancelar</button></div></div>';
  $('bizForms').scrollIntoView({behavior:'smooth', block:'start'});
}
function applyTransfer(pid, fromAid){
  const p = biz.productos.filter(x=>String(x.id)===String(pid))[0];
  const destino = biz.almacenes.filter(a=>String(a.id)===String($('tDestino').value))[0];
  const origen = biz.almacenes.filter(a=>String(a.id)===String(fromAid))[0];
  const cant = parseFloat($('tCant').value)||0;
  if (!destino || !p) return;
  if (!(cant>0)) { notice('Escribe una cantidad mayor que cero.', false); return; }
  if (cant > stockEn(pid, fromAid)) { notice('No hay suficiente existencia en el almacén origen.', false); return; }
  const ref = 'Traslado: '+origen.nombre+' → '+destino.nombre;
  apiPost({tipo:'movimiento', tipo_mov:'salida', almacen_id:fromAid, fecha:fHoyLocal(),
    referencia:ref, notas:'Traslado entre almacenes', moneda:p.moneda||'MXN',
    items:[{producto_id:pid, cantidad:cant, costo_unit:''}]}).then(d=>{
    if (!d || !d.ok) { notice(errMsg(d,'No se pudo sacar del almacén origen.'), false); return; }
    apiPost({tipo:'movimiento', tipo_mov:'entrada', almacen_id:destino.id, fecha:fHoyLocal(),
      referencia:ref, notas:'Traslado entre almacenes', moneda:p.moneda||'MXN',
      items:[{producto_id:pid, cantidad:cant, costo_unit:Number(p.costo)||0}]}).then(d2=>{
      notice(d2&&d2.ok ? 'Traslado aplicado: '+cant+' pieza(s) de '+origen.nombre+' a '+destino.nombre+'.' : errMsg(d2,'Entró al origen pero falló la entrada al destino. Revisa y registra la entrada manualmente.'), !!(d2&&d2.ok));
      closeBizForms(); loadBiz();
    });
  });
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
    if (aid && stockEn(p.id, aid)===0) return false; // solo productos con existencia en ese almacén
    if (q && !(String(p.codigo||'').toLowerCase().includes(q) || String(p.nombre||'').toLowerCase().includes(q))) return false;
    return true;
  });
  if (!lista.length) { $('invTable').innerHTML='<tr><td colspan="11" class="muted">'+(aid?'Sin productos con existencia en este almacén.':'Sin productos. Dale a "＋ Producto" o importa tu lista.')+'</td></tr>'; return; }
  invListaCache = lista;
  $('invTable').innerHTML = lista.map(p=>{
    const costo=Number(p.costo)||0, precio=Number(p.precio)||0;
    const margen = precio ? ((precio-costo)/precio*100).toFixed(0)+'%' : '—';
    const st = stockEn(p.id, aid);
    const porAlmacen = stockPorAlmacen(p.id);
    const almacenTxt = porAlmacen.length
      ? porAlmacen.map(s=>'<button class="wh-chip" title="Trasladar desde '+esc(s.nombre)+'" onclick="event.stopPropagation();transferForm(\''+p.id+'\',\''+s.almacen_id+'\')">'+esc(s.nombre)+': '+s.cantidad+'</button>').join(' ')
      : '<span class="muted">—</span>';
    const min = Number(p.stock_minimo)||0;
    const alerta = min && st<=min ? ' stock-alert' : '';
    const mon = esc(p.moneda||'MXN');
    const inact = p.estado==='inactivo';
    const revision = String(p.notas||'').indexOf('REVISION')>=0;
    return '<tr data-pid="'+p.id+'" onclick="selectProduct(\''+p.id+'\')" class="'+(inact?'inv-inactive ':'')+(selectedProdId===p.id?'inv-selected':'')+'">' +
      '<td class="inv-thumb">'+(p.foto?'<img loading="lazy" src="'+esc(p.foto)+'" alt="">':'<span class="muted">—</span>')+'</td>' +
      '<td>'+esc(p.codigo||'—')+(revision?' <span class="badge-revision">REVISAR</span>':'')+'</td>' +
      '<td>'+esc(p.nombre)+'</td><td>'+esc(p.categoria)+(p.subcategoria?' <span class="muted">/'+esc(p.subcategoria)+'</span>':'')+'</td>' +
      '<td>'+fmtMoney(costo)+' '+mon+'</td><td>'+fmtMoney(precio)+' '+mon+'</td><td>'+margen+'</td>' +
      '<td class="'+alerta+'">'+st+'</td><td class="col-almacen">'+almacenTxt+'</td><td>'+(min||'—')+'</td>' +
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
  const fotosP = [p.foto, p.foto_2, p.foto_3, p.foto_4].filter(Boolean);
  $('invPhoto').innerHTML =
    (fotosP.length ? '<img id="phBig" src="'+esc(fotosP[0])+'" alt="'+esc(p.nombre)+'" onerror="this.style.display=\'none\'">'
            : '<div style="padding:2rem 0.5rem;color:var(--muted);font-size:0.75rem;">Sin fotografía</div>') +
    (fotosP.length > 1
            ? '<div class="ph-thumbs">' + fotosP.map(function (f, i) {
                return '<img src="' + esc(f) + '" onclick="document.getElementById(\'phBig\').src=this.src;this.parentNode.querySelectorAll(\'img\').forEach(function(x){x.classList.remove(\'on\')});this.classList.add(\'on\')" class="' + (i === 0 ? 'on' : '') + '" alt="">';
              }).join('') + '</div>'
            : '') +
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

/* ----- Exportar / imprimir el inventario filtrado (Excel + PDF) ----- */
/* ----- Exportar el inventario filtrado a Excel profesional (.xlsx) -----
   Hoja "Inventario": tabla con encabezado dorado, autofiltro, congelar
   encabezado, formato condicional (stock bajo en rojo, sin precio en ámbar).
   Hoja "Resumen": tabla tipo pivote por categoría + gráfica de barras.
   ExcelJS se carga bajo demanda desde CDN (mismo patron que jsPDF). */
function invExcel(){
  if (!invListaCache.length) { notice('No hay productos con estos filtros.', false); return; }
  notice('Generando Excel profesional…', true);
  cargarScriptCDN('https://cdnjs.cloudflare.com/ajax/libs/exceljs/4.4.0/exceljs.min.js').then(function(){
    const wb = new ExcelJS.Workbook();
    wb.creator = 'ADIS PANEL';
    const ws = wb.addWorksheet('Inventario');
    ws.columns = [
      { header: 'Código', key: 'codigo', width: 14 },
      { header: 'Producto', key: 'nombre', width: 38 },
      { header: 'Categoría', key: 'categoria', width: 22 },
      { header: 'Subcategoría', key: 'subcategoria', width: 22 },
      { header: 'Proveedor', key: 'proveedor', width: 18 },
      { header: 'Costo', key: 'costo', width: 12 },
      { header: 'Precio', key: 'precio', width: 12 },
      { header: 'Moneda', key: 'moneda', width: 8 },
      { header: 'Existencia', key: 'stock', width: 11 },
      { header: 'Por almacén', key: 'poralmacen', width: 26 },
      { header: 'Stock mínimo', key: 'min', width: 12 },
      { header: 'Estado', key: 'estado', width: 10 }
    ];
    const head = ws.getRow(1);
    head.font = { bold: true, color: { argb: 'FFFFFFFF' }, size: 11 };
    head.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFB08C3D' } };
    head.alignment = { vertical: 'middle' };
    head.height = 20;
    ws.views = [{ state: 'frozen', ySplit: 1 }];
    ws.autoFilter = { from: 'A1', to: 'L1' };
    invListaCache.forEach(p=>{
      ws.addRow({
        codigo: p.codigo || '', nombre: p.nombre || '', categoria: p.categoria || '',
        subcategoria: p.subcategoria || '', proveedor: p.proveedor || '',
        costo: Number(p.costo) || 0, precio: Number(p.precio) || 0, moneda: p.moneda || 'MXN',
        stock: stockTotal(p.id),
        poralmacen: stockPorAlmacen(p.id).map(s=>s.nombre + ': ' + s.cantidad).join(' | '),
        min: Number(p.stock_minimo) || 0,
        estado: p.estado === 'inactivo' ? 'Inactivo' : 'Activo'
      });
    });
    const n = invListaCache.length;
    for (let i = 2; i <= n + 1; i++) {
      ws.getCell('F' + i).numFmt = '#,##0.00';
      ws.getCell('G' + i).numFmt = '#,##0.00';
    }
    // Formato condicional: stock en/bajo el mínimo = rojo; activo sin precio = ámbar.
    ws.addConditionalFormatting({
      ref: 'A2:L' + (n + 1),
      rules: [
        { type: 'formula', formulae: ['AND($K2>0,$I2<=$K2)'],
          style: { fill: { type: 'pattern', pattern: 'solid', bgColor: { argb: 'FFF8CBAD' } },
                   font: { color: { argb: 'FF9C0006' }, bold: true } } },
        { type: 'formula', formulae: ['AND($G2=0,$L2="Activo")'],
          style: { fill: { type: 'pattern', pattern: 'solid', bgColor: { argb: 'FFFFEB9C' } },
                   font: { color: { argb: 'FF9C6500' } } } }
      ]
    });

    /* ----- Hoja Resumen: pivote por categoría (todo convertido a MXN) ----- */
    const tc = Number(biz.config.tipo_cambio) || 18.5;
    const agg = {};
    invListaCache.forEach(p=>{
      const c = p.categoria || 'Sin categoría';
      const st = stockTotal(p.id);
      const co = Number(p.costo) || 0;
      const valor = (p.moneda === 'USD' ? co * tc : co) * st;
      if (!agg[c]) agg[c] = { productos: 0, existencias: 0, valor: 0 };
      agg[c].productos++;
      agg[c].existencias += st;
      agg[c].valor += valor;
    });
    let items = Object.keys(agg).map(c=>({ label: c, ...agg[c] })).sort((a,b)=>b.valor - a.valor);
    let otros = null;
    if (items.length > 12) {
      const top = items.slice(0, 12), resto = items.slice(12);
      otros = resto.reduce((o, i)=>({ productos: o.productos + i.productos, existencias: o.existencias + i.existencias, valor: o.valor + i.valor }), { productos: 0, existencias: 0, valor: 0 });
      items = top;
    }
    const res = wb.addWorksheet('Resumen');
    res.getCell('A1').value = 'Resumen de inventario por categoría (valores en MXN)';
    res.getCell('A1').font = { bold: true, size: 14 };
    res.mergeCells('A1:D1');
    const rh = res.getRow(3);
    ['Categoría', 'Productos', 'Existencias', 'Valor inventario (MXN)'].forEach((t, i)=>{
      const cel = rh.getCell(i + 1);
      cel.value = t;
      cel.font = { bold: true, color: { argb: 'FFFFFFFF' } };
      cel.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFB08C3D' } };
    });
    res.columns = [{ width: 30 }, { width: 12 }, { width: 13 }, { width: 22 }];
    let filaR = 4;
    items.forEach(it=>{
      res.getCell('A' + filaR).value = it.label;
      res.getCell('B' + filaR).value = it.productos;
      res.getCell('C' + filaR).value = it.existencias;
      res.getCell('D' + filaR).value = Math.round(it.valor * 100) / 100;
      res.getCell('D' + filaR).numFmt = '$#,##0.00';
      filaR++;
    });
    if (otros) {
      res.getCell('A' + filaR).value = 'Otras categorías';
      res.getCell('B' + filaR).value = otros.productos;
      res.getCell('C' + filaR).value = otros.existencias;
      res.getCell('D' + filaR).value = Math.round(otros.valor * 100) / 100;
      res.getCell('D' + filaR).numFmt = '$#,##0.00';
      filaR++;
    }
    const tot = items.reduce((o, i)=>({ p: o.p + i.productos, e: o.e + i.existencias, v: o.v + i.valor }), { p: 0, e: 0, v: 0 });
    if (otros) { tot.p += otros.productos; tot.e += otros.existencias; tot.v += otros.valor; }
    const rt = res.getRow(filaR);
    rt.getCell(1).value = 'TOTAL';
    rt.getCell(2).value = tot.p;
    rt.getCell(3).value = tot.e;
    rt.getCell(4).value = Math.round(tot.v * 100) / 100;
    rt.getCell(4).numFmt = '$#,##0.00';
    rt.font = { bold: true };
    rt.eachCell(c=>{ c.border = { top: { style: 'thin' } }; });
    // Gráfica de barras dibujada en canvas e incrustada como imagen.
    const graf = dibujarGraficaBarras(items.map(it=>({ label: it.label, valor: it.valor })));
    if (graf) {
      const imgId = wb.addImage({ base64: graf, extension: 'png' });
      res.addImage(imgId, { tl: { col: 0, row: filaR + 2 }, ext: { width: 760, height: Math.max(160, items.length * 34 + 50) } });
    }
    return wb.xlsx.writeBuffer();
  }).then(function(buf){
    const blob = new Blob([buf], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'inventario_adis_' + fHoyLocal() + '.xlsx';
    document.body.appendChild(a); a.click(); a.remove();
    notice('Excel descargado: ' + invListaCache.length + ' productos (Inventario + Resumen con gráfica).', true);
  }).catch(function(e){
    notice('No se pudo generar el Excel: ' + (e && e.message ? e.message : e), false);
  });
}
/* Barra horizontal simple dibujada en canvas para incrustar en el .xlsx. */
function dibujarGraficaBarras(items){
  if (!items || !items.length) return null;
  try {
    const W = 780, rowH = 34, H = Math.max(140, items.length * rowH + 56);
    const c = document.createElement('canvas');
    c.width = W; c.height = H;
    const x = c.getContext('2d');
    x.fillStyle = '#FFFFFF'; x.fillRect(0, 0, W, H);
    x.fillStyle = '#231F18'; x.font = 'bold 17px Arial';
    x.fillText('Valor de inventario por categoría (MXN)', 16, 28);
    const max = Math.max.apply(null, items.map(i=>i.valor).concat([1]));
    const labelW = 210, barMax = W - labelW - 130;
    items.forEach((it, i)=>{
      const y = 48 + i * rowH;
      x.fillStyle = '#5F5748'; x.font = '12px Arial';
      x.fillText(it.label.length > 30 ? it.label.slice(0, 29) + '…' : it.label, 16, y + 16);
      x.fillStyle = '#EFE6CF'; x.fillRect(labelW, y, barMax, 22);
      const wBar = Math.max(2, barMax * it.valor / max);
      x.fillStyle = '#C5A059'; x.fillRect(labelW, y, wBar, 22);
      x.fillStyle = '#231F18'; x.font = 'bold 12px Arial';
      x.fillText('$' + Math.round(it.valor).toLocaleString('es-MX'), labelW + wBar + 8, y + 16);
    });
    return c.toDataURL('image/png').split(',')[1];
  } catch (e) { return null; }
}
function printInventory(){
  if (!invListaCache.length) { notice('No hay productos con estos filtros.', false); return; }
  const w = window.open('', '_blank');
  if (!w) { notice('El navegador bloqueó la ventana de impresión.', false); return; }
  w.document.write('<!doctype html><html><head><meta charset="utf-8"><title>Inventario ADIS</title>' +
    '<style>body{font-family:Arial,sans-serif;font-size:11px;padding:20px;}h1{font-size:16px;margin:0 0 4px;}p{margin:0 0 12px;color:#555;}table{width:100%;border-collapse:collapse;}th,td{border:1px solid #bbb;padding:4px 6px;text-align:left;vertical-align:top;}th{background:#eee;}td.num{text-align:right;white-space:nowrap;}</style></head><body>' +
    '<h1>ADIS — Inventario ('+invListaCache.length+' productos)</h1><p>Generado: '+new Date().toLocaleString()+'</p>' +
    '<table><thead><tr><th>Código</th><th>Producto</th><th>Categoría</th><th class="num">Costo</th><th class="num">Precio</th><th class="num">Existencia</th><th class="num">Mín</th></tr></thead><tbody>' +
    invListaCache.map(p=>{
      const min = Number(p.stock_minimo)||0, st = stockTotal(p.id);
      const bajo = min>0 && st<=min;
      return '<tr><td>'+esc(p.codigo||'')+'</td><td>'+esc(p.nombre)+'</td><td>'+esc(p.categoria||'')+'</td>' +
        '<td class="num">'+fmtMoney(Number(p.costo)||0)+' '+esc(p.moneda||'MXN')+'</td>' +
        '<td class="num">'+fmtMoney(Number(p.precio)||0)+' '+esc(p.moneda||'MXN')+'</td>' +
        '<td class="num"'+(bajo?' style="color:#c0392b;font-weight:bold;"':'')+'>'+st+'</td>' +
        '<td class="num">'+(min||'—')+'</td></tr>';
    }).join('') +
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
    '<label>Fotografías (la 1ª es la principal; hasta 4 ángulos)</label>' +
    '<div class="gal-grid" id="galSlots"></div>' +
    '<div class="foto-uprow" style="margin-top:0.6rem;">' +
    '<label class="btn btn-sm foto-pick">📁 Examinar<input type="file" id="pFotoFile" accept="image/*" multiple style="display:none" onchange="subirFotosGaleria(this.files);this.value=\'\';"></label>' +
    '<div class="gal-drop" id="galDrop" ondragover="event.preventDefault();this.classList.add(\'over\')" ondragleave="this.classList.remove(\'over\')" ondrop="event.preventDefault();this.classList.remove(\'over\');if(event.dataTransfer.files.length)subirFotosGaleria(event.dataTransfer.files)">Arrastra las fotos aquí</div>' +
    '</div>' +
    '<label>Descripción</label><textarea id="pDesc" rows="2">'+esc(p?p.descripcion:'')+'</textarea>' +
    '<label>Notas internas</label><input id="pNotas" value="'+esc(p?p.notas:'')+'">' +
    '<div class="toolbar" style="margin-top:1rem;">' +
    '<button class="btn btn-solid btn-sm" onclick="saveProduct(\''+(p?p.id:'')+'\')">💾 Guardar</button> ' +
    '<button class="btn btn-sm" onclick="closeBizForms()">Cancelar</button></div></div>';
  galeriaInit(p);
  (p ? $('pCodigo') : $('pCodigo')).focus();
}

/* ----- Galeria de fotos del producto (principal + 3 angulos) -----
   Las fotos se suben una a una a la carpeta de Drive del negocio
   (endpoint upload_foto) y se guardan en foto, foto_2, foto_3, foto_4. */
let galeriaFotos = ['','','',''];
let invListaCache = [];
function galeriaInit(p){
  galeriaFotos = [(p&&p.foto)||'', (p&&p.foto_2)||'', (p&&p.foto_3)||'', (p&&p.foto_4)||''];
  renderGaleriaSlots();
}
function renderGaleriaSlots(){
  if (!$('galSlots')) return;
  $('galSlots').innerHTML = galeriaFotos.map((f,i)=>
    '<div class="gal-slot">' +
    (f ? '<img src="'+esc(f)+'" alt="">' +
         '<button type="button" class="gal-x" onclick="quitarFotoSlot('+i+')" title="Quitar foto">✕</button>'
       : '<span class="muted">'+(i===0?'Principal':'Ángulo '+(i+1))+'<br>sin foto</span>') +
    '</div>').join('');
}
function quitarFotoSlot(i){ galeriaFotos[i]=''; renderGaleriaSlots(); }
function subirFotosGaleria(files){
  const imgs = Array.from(files||[]).filter(f=>/^image\//.test(f.type));
  if (!imgs.length) { notice('Solo se aceptan imágenes (JPG, PNG, WebP...).', false); return; }
  let k = 0;
  function siguiente(){
    const slot = galeriaFotos.indexOf('');
    if (slot === -1) { notice('Máximo 4 fotos por producto. Quita una para subir otra.', false); return; }
    if (k >= imgs.length) { notice('Fotos listas. Pulsa «Guardar» para asignarlas al producto.', true); return; }
    const f = imgs[k++];
    const drop = $('galDrop'); const previo = drop.textContent;
    drop.textContent = '⏳ Subiendo ' + f.name + '…';
    fileToDataURL(f, function(dataUrl){
      apiPost({tipo:'upload_foto', foto_base64:dataUrl, nombre:($('pCodigo').value||'producto')}).then(d=>{
        drop.textContent = previo;
        if (d && d.ok && d.foto) { galeriaFotos[slot] = d.foto; renderGaleriaSlots(); }
        else {
          const err = d && d.error;
          notice('Falló la subida de ' + f.name + ': ' + (err ? (err.message || err) : 'error de conexión') +
            ' (si el backend no está actualizado, falta el redeploy).', false);
        }
        siguiente();
      });
    });
  }
  siguiente();
}

function saveProduct(id){
  const codigo=$('pCodigo').value.trim().toUpperCase(), nombre=$('pNombre').value.trim();
  if (!codigo) { notice('El código es obligatorio.', false); return; }
  if (!nombre) { notice('El producto necesita nombre.', false); return; }
  apiPost({tipo:'save_product', id:id||undefined, codigo, nombre, categoria:$('pCat').value.trim(),
    subcategoria:$('pSubcat').value.trim(), proveedor:$('pProv').value.trim(),
    costo:parseFloat($('pCosto').value)||0, precio:parseFloat($('pPrecio').value)||0,
    unidad:$('pUnidad').value.trim()||'pieza', stock_minimo:parseFloat($('pMin').value)||0,
    moneda:$('pMoneda').value, foto: galeriaFotos[0]||'', foto_2: galeriaFotos[1]||'',
    foto_3: galeriaFotos[2]||'', foto_4: galeriaFotos[3]||'', estado:$('pEstado').value,
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

/* Aviso en el panel cuando el backend reporta productos en/bajo su mínimo. */
function avisoAlertasStock(d){
  if (d && d.alertas && d.alertas.length) {
    notice('⚠️ Stock bajo: ' + d.alertas.slice(0,4).map(a=>a.codigo+' '+a.producto+' ('+a.stock+')').join(' · ') +
      (d.alertas.length>4 ? ' +'+(d.alertas.length-4)+' más' : ''), false);
  }
}

function saveAdjust(pid){
  apiPost({tipo:'movimiento', tipo_mov:$('mTipo').value, producto_id:pid, almacen_id:$('mAlmacen').value,
    cantidad:parseFloat($('mCant').value)||0, notas:$('mNotas').value.trim()}).then(d=>{
    notice(d&&d.ok?'Movimiento aplicado. Stock nuevo: '+(d.stock_nuevo!==undefined?d.stock_nuevo:'?'):errMsg(d), !!(d&&d.ok));
    if(d&&d.ok){ avisoAlertasStock(d); closeBizForms(); loadBiz(); }
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
  const hoy = fHoyLocal();
  apiGet('proveedores').then(d=>{ if(d&&d.ok){ provCache=d.proveedores||[]; movPoblarVars(); } });
  apiGet('proyectos').then(d=>{ if(d&&d.ok){ proyCache=d.proyectos||[]; movPoblarVars(); } });
  $('bizForms').innerHTML = '<div class="card-box">' +
    '<div class="toolbar" style="margin-bottom:0.5rem;"><strong id="mTitulo">Movimiento de material</strong>' +
    '<span class="muted">Puedes incluir varios productos en una sola operación</span></div>' +
    '<div class="row">' +
    '<div><label>Tipo de movimiento *</label><select id="mTipoMov" onchange="movTipoCambio()">' +
    '<option value="entrada">Entrada (compra / mercancía que llega)</option>' +
    '<option value="salida">Salida (merma / material que se usa)</option>' +
    '<option value="ajuste">Ajuste (fijar la cantidad exacta)</option></select></div>' +
    '<div><label>Fecha</label><input type="date" id="mFecha" value="'+hoy+'" max="'+hoy+'"></div>' +
    '<div><label>Almacén *</label><select id="mAlmacen">'+biz.almacenes.map(a=>'<option value="'+esc(a.id)+'">'+esc(a.nombre)+'</option>').join('')+'</select></div>' +
    '</div>' +
    '<div class="row" id="mVars"></div>' +
    '<label>Agregar producto (del inventario)</label>' +
    '<div class="search-results"><input id="mSearch" placeholder="Escribe el nombre o código del producto..." autocomplete="off" oninput="searchMovProducts()"><div id="mSearchResults"></div></div>' +
    '<div class="items" id="mItems"></div>' +
    '<div class="total-line"><span class="muted" id="mTotalTxt">Piezas: 0</span></div>' +
    '<label>Notas</label><input id="mNotas" placeholder="Observaciones...">' +
    '<div class="toolbar" style="margin-top:1rem;">' +
    '<button class="btn btn-solid btn-sm" id="mApplyBtn" onclick="saveMovLote()">Aplicar movimiento</button> ' +
    '<button class="btn btn-sm" onclick="closeBizForms()">Cancelar</button></div></div>';
  if (tipo) $('mTipoMov').value = tipo;
  movTipoCambio();
  setTimeout(()=>{ const el=$('bizForms'); if (el) el.scrollIntoView({behavior:'smooth', block:'start'}); }, 100);
}
/* Recambia los campos variables (proveedor/documento/moneda vs proyecto/motivo)
   segun el tipo elegido. Asi un solo formulario sirve para entrada, salida y ajuste. */
function movTipoCambio(){
  const t = $('mTipoMov').value;
  $('mTitulo').textContent = t==='entrada' ? 'Entrada de material' : t==='salida' ? 'Salida de material' : 'Ajuste de existencia';
  $('mApplyBtn').textContent = 'Aplicar ' + t;
  const vars = $('mVars');
  if (t==='entrada') vars.innerHTML =
    '<div><label>Proveedor</label><select id="mProv"><option value="">— Ninguno —</option></select></div>' +
    '<div><label>Documento (factura/remisión)</label><input id="mRef" placeholder="Ej. FAC-1234"></div>' +
    '<div><label>Moneda</label><select id="mMoneda"><option value="MXN">MXN</option><option value="USD">USD</option></select></div>';
  else if (t==='salida') vars.innerHTML =
    '<div><label>Proyecto / obra</label><select id="mProy"><option value="">— Ninguna (uso general) —</option></select></div>' +
    '<div><label>Motivo / referencia</label><input id="mRef" placeholder="Ej. Merma, uso en obra..."></div>';
  else vars.innerHTML =
    '<div><label>En el ajuste</label><p class="muted" style="margin:0.3rem 0 0;font-size:0.78rem;">La cantidad de cada producto será la existencia <b>exacta</b> que quede registrada (no se suma ni se resta). Úsalo para corregir diferencias tras un conteo físico.</p></div>';
  movPoblarVars();
  renderMovItems();
}
function movPoblarVars(){
  if (typeof provCache!=='undefined' && provCache.length && $('mProv')) $('mProv').innerHTML = '<option value="">— Ninguno —</option>'+provCache.filter(p=>String(p.activo)!=='no').map(p=>'<option value="'+esc(p.nombre)+'">'+esc(p.nombre)+'</option>').join('');
  if (typeof proyCache!=='undefined' && proyCache.length && $('mProy')) $('mProy').innerHTML = '<option value="">— Ninguna (uso general) —</option>'+proyCache.filter(p=>p.estado==='ACTIVO').map(p=>'<option value="'+esc(p.id)+'">'+esc(p.folio)+' · '+esc(p.nombre)+'</option>').join('');
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
  const ajuste = $('mTipoMov') && $('mTipoMov').value==='ajuste';
  box.innerHTML = (movItems.length ? '<div class="item-row" style="opacity:.65;"><input value="Producto" disabled>' +
    '<input type="text" value="'+(ajuste?'Cantidad exacta':'Cantidad')+'" disabled>' +
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
  if (movEsEntrada() && n>0 && $('mMoneda')) txt += ' · Costo total: '+fmtMoney(movItems.reduce((s,it)=>s+(Number(it.cantidad)||0)*(Number(it.costo_unit)||0),0))+' '+$('mMoneda').value;
  el.textContent = txt;
}
function saveMovLote(){
  const tipo = $('mTipoMov').value;
  if (!$('mAlmacen').value) { notice('Selecciona un almacén.', false); return; }
  if (!movItems.length) { notice('Agrega al menos un producto.', false); return; }
  const items = movItems.map(it=>({producto_id:it.producto_id, cantidad:it.cantidad,
    costo_unit: tipo==='entrada' ? (it.costo_unit||0) : ''}));
  apiPost({tipo:'movimiento', tipo_mov:tipo, almacen_id:$('mAlmacen').value, fecha:$('mFecha').value,
    referencia:$('mRef').value.trim(), notas:$('mNotas').value.trim(), moneda:$('mMoneda')?$('mMoneda').value:'MXN',
    proveedor: (tipo==='entrada' && $('mProv')) ? $('mProv').value : '',
    proyecto_id: (tipo==='salida' && $('mProy')) ? $('mProy').value : '',
    items}).then(d=>{
    notice(d&&d.ok?((d.lote?('Lote '+d.lote+' aplicado ('+items.length+' producto(s)). '):'Movimiento aplicado. ')+'Stock actualizado.'):errMsg(d), !!(d&&d.ok));
    if(d&&d.ok){ avisoAlertasStock(d); closeBizForms(); loadBiz(); }
  });
}

