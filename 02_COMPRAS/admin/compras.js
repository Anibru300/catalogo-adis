/* =====================================================================
   FASE 2 — COMPRAS: proveedores + ordenes de compra con recepcion parcial
   ===================================================================== */
let ocCache = [], provCache = [], ocItems = [];

function loadOC(){
  if (!biz.productos.length) loadBiz(); // almacenes/productos los reutiliza loadBiz
  apiGet('proveedores').then(d=>{ if(d&&d.ok){ provCache=d.proveedores||[]; renderProv(); } });
  apiGet('oc').then(d=>{ if(d&&d.ok){ ocCache=d.oc||[]; renderOC(); } });
}

function ocEstadoBadge(e){
  const colores = { BORRADOR:'#9a9a9a', AUTORIZADA:'#e8d5a3', ENVIADA:'#8fc7e8', PARCIAL:'#e8b96a', RECIBIDA:'#7ce3a1', CANCELADA:'#e37c7c' };
  return '<span style="display:inline-block;padding:0.12rem 0.5rem;border-radius:10px;font-size:0.68rem;border:1px solid '+(colores[e]||'#9a9a9a')+';color:'+(colores[e]||'#9a9a9a')+';font-weight:600;">'+esc(e||'—')+'</span>';
}

function renderOC(){
  const f = $('ocFiltro').value;
  let lista = ocCache.slice().reverse();
  if (f) lista = lista.filter(o=>o.estado===f);
  if (!lista.length) { $('ocTable').innerHTML='<tr><td colspan="7" class="muted">Sin órdenes de compra.</td></tr>'; return; }
  $('ocTable').innerHTML = lista.map(o=>{
    const puede = { BORRADOR:['AUTORIZADA','CANCELADA'], AUTORIZADA:['ENVIADA','CANCELADA'], ENVIADA:['CANCELADA'], PARCIAL:['CANCELADA'] };
    const verbo = { AUTORIZADA:'Autorizar', ENVIADA:'Enviar', CANCELADA:'Cancelar' };
    let acciones = '<button class="btn btn-sm" onclick="printOC(\''+o.id+'\')">🖨️</button> ';
    if ((puede[o.estado]||[]).length) {
      if (o.estado==='BORRADOR') acciones += '<button class="btn btn-sm" onclick="showOCForm(\''+o.id+'\')">✎</button> ';
      if (['AUTORIZADA','ENVIADA','PARCIAL'].indexOf(o.estado)>=0) acciones += '<button class="btn btn-sm" onclick="showRecepForm(\''+o.id+'\')">📥 Recibir</button> ';
      (puede[o.estado]||[]).forEach(est=>{
        acciones += est==='CANCELADA'
          ? '<button class="btn btn-danger btn-sm" onclick="cambiarEstadoOC(\''+o.id+'\',\'CANCELADA\')">Cancelar</button> '
          : '<button class="btn btn-sm" onclick="cambiarEstadoOC(\''+o.id+'\',\''+est+'\')">'+verbo[est]+'</button> ';
      });
    }
    return '<tr><td class="gold" style="white-space:nowrap;">'+esc(o.folio||'—')+'</td><td>'+esc(o.fecha)+'</td>' +
      '<td>'+esc(o.proveedor)+'</td><td>'+esc(o.almacen)+'</td>' +
      '<td class="gold" style="white-space:nowrap;">'+fmtMoney(o.total)+' '+esc(o.moneda)+'</td>' +
      '<td>'+ocEstadoBadge(o.estado)+'</td><td style="white-space:nowrap;">'+acciones+'</td></tr>';
  }).join('');
}

function renderProv(){
  if (!provCache.length) { $('provTable').innerHTML='<tr><td colspan="5" class="muted">Sin proveedores. Crea el primero.</td></tr>'; return; }
  $('provTable').innerHTML = provCache.map(p=>
    '<tr><td>'+esc(p.nombre)+'</td><td>'+esc(p.contacto||'—')+'</td><td>'+esc(p.telefono||'—')+'</td><td>'+esc(p.email||'—')+'</td>' +
    '<td><button class="btn btn-danger btn-sm" onclick="deleteProv(\''+p.id+'\')">✕</button></td></tr>').join('');
}

function showProvForm(){
  $('ocForms').innerHTML = '<div class="card-box"><div class="row">' +
    '<div><label>Nombre *</label><input id="pvNombre"></div>' +
    '<div><label>Contacto</label><input id="pvContacto"></div>' +
    '<div><label>Teléfono</label><input id="pvTel"></div>' +
    '<div><label>Email</label><input id="pvEmail"></div>' +
    '</div><label>Dirección / notas</label><input id="pvNotas">' +
    '<div class="toolbar" style="margin-top:1rem;"><button class="btn btn-solid btn-sm" onclick="saveProv()">💾 Guardar</button> ' +
    '<button class="btn btn-sm" onclick="$(\'ocForms\').innerHTML=\'\'">Cancelar</button></div></div>';
}
function saveProv(){
  const nombre = $('pvNombre').value.trim();
  if (!nombre) { notice('El proveedor necesita nombre.', false); return; }
  apiPost({tipo:'save_proveedor', nombre, contacto:$('pvContacto').value.trim(), telefono:$('pvTel').value.trim(),
    email:$('pvEmail').value.trim(), notas:$('pvNotas').value.trim()}).then(d=>{
    notice(d&&d.ok?'Proveedor guardado.':errMsg(d,'No se pudo guardar.'), !!(d&&d.ok));
    if(d&&d.ok){ $('ocForms').innerHTML=''; loadOC(); }
  }).catch(()=>notice('Error de conexión.', false));
}
function deleteProv(id){
  if (!confirma('prov-'+id, 'Desactivar este proveedor.')) return;
  apiPost({tipo:'delete_proveedor', id}).then(d=>{
    notice(d&&d.ok?'Proveedor desactivado.':errMsg(d), !!(d&&d.ok));
    if(d&&d.ok) loadOC();
  });
}

function showOCForm(id){
  const o = id ? ocCache.filter(x=>String(x.id)===String(id))[0] : null;
  ocItems = o ? o.partidas.map(p=>({producto_id:p.producto_id, nombre:p.producto, cantidad:p.cantidad, costo_unit:p.costo_unit})) : [];
  const provOpts = '<option value="">— Selecciona —</option>' + provCache.map(p=>'<option value="'+esc(p.id)+'"'+(o&&String(o.proveedor_id)===String(p.id)?' selected':'')+'>'+esc(p.nombre)+'</option>').join('');
  const almOpts = '<option value="">— Selecciona —</option>' + biz.almacenes.map(a=>'<option value="'+esc(a.id)+'"'+(o&&String(o.almacen_id)===String(a.id)?' selected':'')+'>'+esc(a.nombre)+'</option>').join('');
  $('ocForms').innerHTML = '<div class="card-box"><p style="margin-bottom:0.5rem;"><strong>'+(o?'Editar ':'Nueva ')+'orden de compra</strong> <span class="muted">(se guarda como BORRADOR)</span></p>' +
    '<div class="row">' +
    '<div><label>Proveedor *</label><select id="ocProv">'+provOpts+'</select></div>' +
    '<div><label>Fecha</label><input type="date" id="ocFecha" value="'+(o?o.fecha:fLocal())+'"></div>' +
    '<div><label>Fecha esperada</label><input type="date" id="ocEsperada" value="'+(o&&o.fecha_esperada?o.fecha_esperada:'')+'"></div>' +
    '<div><label>Almacén destino *</label><select id="ocAlmacen">'+almOpts+'</select></div>' +
    '<div><label>Moneda</label><select id="ocMoneda"><option value="MXN"'+(!o||o.moneda!=='USD'?' selected':'')+'>MXN</option><option value="USD"'+(o&&o.moneda==='USD'?' selected':'')+'>USD</option></select></div>' +
    '<div><label>IVA %</label><input type="number" id="ocIva" min="0" max="100" step="0.01" value="'+(o?Math.round((o.iva/(o.subtotal||1))*1000)/10:16)+'" oninput="updateOCTotals()"></div>' +
    '<div><label>Descuento</label><input type="number" id="ocDesc" min="0" step="0.01" value="'+(o?o.descuento:0)+'" oninput="updateOCTotals()"></div>' +
    '</div>' +
    '<label>Agregar producto</label><input id="ocSearch" placeholder="Buscar por nombre..." oninput="searchOCProducts()" autocomplete="off"><div id="ocSearchResults"></div>' +
    '<div id="ocItems" style="margin-top:0.5rem;"></div>' +
    '<div id="ocTotales" style="text-align:right;margin-top:0.5rem;"></div>' +
    '<label>Notas</label><input id="ocNotas" value="'+(o?esc(o.notas||''):'')+'">' +
    '<div class="toolbar" style="margin-top:1rem;"><button class="btn btn-solid btn-sm" onclick="saveOC(\''+(o?o.id:'')+'\')">💾 Guardar OC</button> ' +
    '<button class="btn btn-sm" onclick="$(\'ocForms\').innerHTML=\'\'">Cancelar</button></div></div>';
  renderOCItems();
}
function searchOCProducts(){
  const q = $('ocSearch').value.trim().toLowerCase();
  const box = $('ocSearchResults');
  if (q.length < 2) { box.innerHTML=''; return; }
  const matches = biz.productos.filter(p=>p.estado!=='inactivo' && (p.nombre+' '+(p.codigo||'')).toLowerCase().includes(q)).slice(0,8);
  box.innerHTML = '<div class="sr-list">' + (matches.length
    ? matches.map(p=>'<div class="sr-item" onclick="addOCItem(\''+p.id+'\')"><span>'+esc(p.nombre)+'</span><span class="muted">'+esc(p.codigo||'')+'</span></div>').join('')
    : '<div class="sr-item muted">Sin resultados</div>') + '</div>';
}
function addOCItem(pid){
  const p = biz.productos.filter(x=>String(x.id)===String(pid))[0];
  if (!p) return;
  if (ocItems.some(it=>String(it.producto_id)===String(pid))) { notice('Ese producto ya está en la orden.', false); return; }
  ocItems.push({producto_id:p.id, nombre:p.nombre, cantidad:1, costo_unit:Number(p.costo)||0});
  $('ocSearch').value=''; $('ocSearchResults').innerHTML='';
  renderOCItems();
}
function renderOCItems(){
  $('ocItems').innerHTML = ocItems.length ? '<table style="width:100%;"><thead><tr><th>Producto</th><th style="width:90px;">Cantidad</th><th style="width:110px;">Costo unit.</th><th style="width:80px;">Importe</th><th></th></tr></thead><tbody>' +
    ocItems.map((it,i)=>'<tr><td>'+esc(it.nombre)+'</td>' +
      '<td><input type="number" min="1" value="'+it.cantidad+'" onchange="ocItems['+i+'].cantidad=parseFloat(this.value)||1; renderOCItems()"></td>' +
      '<td><input type="number" min="0" step="0.01" value="'+it.costo_unit+'" onchange="ocItems['+i+'].costo_unit=parseFloat(this.value)||0; renderOCItems()"></td>' +
      '<td>'+fmtMoney(it.cantidad*it.costo_unit)+'</td>' +
      '<td><button class="del" onclick="ocItems.splice('+i+',1); renderOCItems()">✕</button></td></tr>').join('') +
    '</tbody></table>' : '<p class="muted" style="font-size:0.75rem;">Sin productos todavía.</p>';
  updateOCTotals();
}
function ocTotalsCalc(){
  const sub = ocItems.reduce((s,it)=>s+(Number(it.cantidad)||0)*(Number(it.costo_unit)||0),0);
  const ivaPct = parseFloat(($('ocIva')||{}).value)||0;
  const desc = parseFloat(($('ocDesc')||{}).value)||0;
  return { sub:sub, iva:sub*ivaPct/100, desc:desc, total:sub+sub*ivaPct/100-desc, moneda:($('ocMoneda')||{}).value||'MXN' };
}
function updateOCTotals(){
  const t = ocTotalsCalc();
  const el = $('ocTotales');
  if (el) el.innerHTML = '<span class="muted">Subtotal: '+fmtMoney(t.sub)+' · IVA: '+fmtMoney(t.iva)+' · Desc: '+fmtMoney(t.desc)+'</span><br><strong class="gold" style="font-size:1.1rem;">Total: '+fmtMoney(t.total)+' '+esc(t.moneda)+'</strong>';
}
function saveOC(id){
  if (!$('ocProv').value) { notice('Selecciona un proveedor.', false); return; }
  if (!$('ocAlmacen').value) { notice('Selecciona un almacén destino.', false); return; }
  if (!ocItems.length) { notice('Agrega al menos un producto.', false); return; }
  const t = ocTotalsCalc();
  apiPost({tipo:'save_oc', id:id||undefined, proveedor_id:$('ocProv').value, almacen_id:$('ocAlmacen').value,
    fecha:$('ocFecha').value, fecha_esperada:$('ocEsperada').value, moneda:$('ocMoneda').value,
    iva_pct:parseFloat($('ocIva').value)||0, descuento:t.desc,
    items:ocItems.map(it=>({producto_id:it.producto_id, cantidad:it.cantidad, costo_unit:it.costo_unit})),
    notas:$('ocNotas').value.trim()})
    .then(d=>{
      notice(d&&d.ok?('Orden '+(d.folio||'')+' guardada como BORRADOR.'):errMsg(d,'No se pudo guardar.'), !!(d&&d.ok));
      if(d&&d.ok){ $('ocForms').innerHTML=''; loadOC(); }
    }).catch(()=>notice('Error de conexión al guardar.', false));
}
function cambiarEstadoOC(id, estado){
  const msg = { AUTORIZADA:'Autorizar esta orden', ENVIADA:'Marcar como enviada al proveedor', CANCELADA:'Cancelar esta orden (no afecta el inventario)' };
  if (!confirma('oc-'+id+'-'+estado, (msg[estado]||('Cambiar estado a '+estado))+'.')) return;
  apiPost({tipo:'cambiar_estado_oc', id, estado}).then(d=>{
    notice(d&&d.ok?('Orden ahora está '+estado+'.'):errMsg(d), !!(d&&d.ok));
    if(d&&d.ok) loadOC();
  });
}
function showRecepForm(id){
  const o = ocCache.filter(x=>String(x.id)===String(id))[0];
  if (!o) return;
  $('ocForms').innerHTML = '<div class="card-box"><p style="margin-bottom:0.5rem;"><strong>Recibir mercancía — '+esc(o.folio)+'</strong> <span class="muted">'+esc(o.proveedor)+' · almacén '+esc(o.almacen)+'</span></p>' +
    '<table style="width:100%;"><thead><tr><th>Producto</th><th>Pedido</th><th>Recibido</th><th>Pendiente</th><th style="width:110px;">A recibir</th></tr></thead><tbody>' +
    o.partidas.map((p,i)=>'<tr><td>'+esc(p.producto)+'</td><td>'+esc(p.cantidad)+'</td><td>'+esc(p.recibido)+'</td><td>'+esc(p.pendiente)+'</td>' +
      '<td><input type="number" id="rec'+i+'" min="0" max="'+p.pendiente+'" step="0.01" value="'+(p.pendiente||0)+'"'+(p.pendiente?'':' disabled')+'></td></tr>').join('') +
    '</tbody></table>' +
    '<p class="muted" style="font-size:0.72rem;margin-top:0.4rem;">Al guardar, cada recepción genera una ENTRADA de inventario trazable vinculada a esta OC, y se actualiza el último costo del producto.</p>' +
    '<div class="toolbar" style="margin-top:0.8rem;"><button class="btn btn-solid btn-sm" onclick="saveRecepcion(\''+o.id+'\')">💾 Registrar recepción</button> ' +
    '<button class="btn btn-sm" onclick="$(\'ocForms\').innerHTML=\'\'">Cancelar</button></div></div>';
}
function saveRecepcion(ocId){
  const o = ocCache.filter(x=>String(x.id)===String(ocId))[0];
  const items = [];
  o.partidas.forEach((p,i)=>{
    const v = parseFloat($('rec'+i).value)||0;
    if (v > 0) items.push({producto_id:p.producto_id, cantidad:v});
  });
  if (!items.length) { notice('Indica al menos una cantidad a recibir.', false); return; }
  apiPost({tipo:'recibir_oc', oc_id:ocId, items}).then(d=>{
    notice(d&&d.ok?('Recepción registrada. Orden ahora: '+d.estado+'.'):errMsg(d), !!(d&&d.ok));
    if(d&&d.ok){ $('ocForms').innerHTML=''; loadOC(); loadBiz(); }
  }).catch(()=>notice('Error de conexión al recibir.', false));
}
function printOC(id){
  const o = ocCache.filter(x=>String(x.id)===String(id))[0];
  if (!o) return;
  $('printArea').innerHTML =
    '<h1>ADIS Diseño & Remodelación</h1><div class="pq-meta">Orden de compra '+esc(o.folio)+' · '+esc(o.fecha)+(o.fecha_esperada?' · Esperada: '+esc(o.fecha_esperada):'')+'</div>' +
    '<p><strong>Proveedor:</strong> '+esc(o.proveedor)+' &nbsp; <strong>Almacén destino:</strong> '+esc(o.almacen)+'</p>' +
    '<table><thead><tr><th>Producto</th><th>Cant.</th><th>Costo unit.</th><th>Importe</th><th>Recibido</th></tr></thead><tbody>' +
    o.partidas.map(p=>'<tr><td>'+esc(p.producto)+'</td><td>'+esc(p.cantidad)+'</td><td>'+fmtMoney(p.costo_unit)+'</td><td>'+fmtMoney(p.cantidad*p.costo_unit)+'</td><td>'+esc(p.recibido)+'</td></tr>').join('') +
    '</tbody></table>' +
    '<div class="pq-total">Subtotal: '+fmtMoney(o.subtotal)+' · IVA: '+fmtMoney(o.iva)+' · Descuento: '+fmtMoney(o.descuento)+' &nbsp; <strong>Total: '+fmtMoney(o.total)+' '+esc(o.moneda)+'</strong></div>' +
    (o.notas?'<p style="margin-top:1rem;font-size:0.85rem;">'+esc(o.notas)+'</p>':'') +
    '<div class="pq-foot">Estado: '+esc(o.estado)+' · Generado desde el panel administrativo ADIS</div>';
  window.print();
}

