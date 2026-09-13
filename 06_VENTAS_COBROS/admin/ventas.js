/* ----- ventas ----- */
function searchSaleProducts(){
  const q = $('sSearch').value.trim().toLowerCase();
  const box = $('sSearchResults');
  if (q.length < 2) { box.innerHTML=''; return; }
  const matches = biz.productos.filter(p => p.estado!=='inactivo' && (p.nombre+' '+(p.categoria||'')).toLowerCase().includes(q)).slice(0,8);
  box.innerHTML = '<div class="sr-list">' + (matches.length
    ? matches.map(p=>'<div class="sr-item" onclick="addSaleItem(\''+p.id+'\')"><span>'+esc(p.nombre)+'</span><span class="gold">'+fmtMoney(p.precio)+' '+esc(p.moneda||'MXN')+'</span></div>').join('')
    : '<div class="sr-item muted">Sin resultados</div>') + '</div>';
}
function addSaleItem(pid){
  const p = biz.productos.filter(x=>String(x.id)===String(pid))[0];
  if (!p) return;
  saleItems.push({producto_id:p.id, nombre:p.nombre, cantidad:1, precio:Number(p.precio)||0});
  $('sSearch').value=''; $('sSearchResults').innerHTML='';
  renderSaleItems();
}
function renderSaleItems(){
  $('sItems').innerHTML = saleItems.map((it,i)=>
    '<div class="item-row">' +
    '<input value="'+esc(it.nombre)+'" disabled>' +
    '<input type="number" min="1" value="'+it.cantidad+'" onchange="saleItems['+i+'].cantidad=parseFloat(this.value)||1; updateSaleTotal()">' +
    '<input type="number" min="0" step="0.01" value="'+it.precio+'" onchange="saleItems['+i+'].precio=parseFloat(this.value)||0; updateSaleTotal()">' +
    '<button class="del" onclick="saleItems.splice('+i+',1); renderSaleItems()">✕</button></div>'
  ).join('');
  updateSaleTotal();
}
function updateSaleTotal(){
  const t = saleItems.reduce((s,it)=>s+(Number(it.cantidad)||0)*(Number(it.precio)||0),0);
  $('sTotal').textContent = fmtMoney(t)+' '+$('sMoneda').value;
  return t;
}
function saveSale(){
  if (!$('sAlmacen').value) { notice('Selecciona un almacén.', false); return; }
  if (!saleItems.length) { notice('Agrega al menos un producto.', false); return; }
  apiPost({tipo:'venta', fecha:$('sFecha').value, cliente:$('sCliente').value.trim(),
    almacen_id:$('sAlmacen').value, moneda:$('sMoneda').value,
    cliente_id:$('sClienteSel').value, proyecto_id:$('sProyectoSel').value,
    items:saleItems, notas:$('sNotas').value.trim()})
    .then(d=>{
      notice(d&&d.ok?'Venta '+(d.folio?d.folio+' ':'')+'guardada. Stock descontado.':errMsg(d), !!(d&&d.ok));
      if(d&&d.ok){ saleItems=[]; renderSaleItems(); $('sCliente').value=''; $('sNotas').value=''; loadBiz(); }
    });
}
function renderSales(list){
  if (!list.length) { $('salesTable').innerHTML='<tr><td colspan="8" class="muted">Sin ventas registradas.</td></tr>'; return; }
  $('salesTable').innerHTML = list.slice().reverse().map(v=>{
    const ep = v.estado_pago || '—';
    const col = ep==='PAGADA'?'#7ce3a1':(ep==='PARCIAL'?'#e8b96a':(ep==='CANCELADA'?'#9a9a9a':'#e37c7c'));
    const acciones = v.id
      ? (ep!=='CANCELADA' && ep!=='PAGADA' ? '<button class="btn btn-sm" onclick="showTab(\'cobros\'); setTimeout(()=>showCobroForm(\''+v.id+'\'),400);">💰 Cobrar</button> ' : '') +
        (ep!=='CANCELADA' ? '<button class="btn btn-danger btn-sm" onclick="anularVenta(\''+v.id+'\')">Anular</button>' : '')
      : '<span class="muted">legacy</span>';
    return '<tr><td>'+esc(v.fecha)+'</td><td>'+esc(v.cliente)+(v.folio?' <span class="muted">'+esc(v.folio)+'</span>':'')+'</td><td>'+esc(v.almacen)+'</td><td>'+esc(v.items)+'</td>' +
      '<td class="gold">'+fmtMoney(v.total)+' '+esc(v.moneda)+'</td>' +
      '<td><span style="color:'+col+';font-weight:600;font-size:0.72rem;">'+esc(ep)+'</span></td>' +
      '<td style="color:#7ce3a1;">'+fmtMoney(v.utilidad_base)+' '+esc(biz.config.moneda_base||'')+'</td>' +
      '<td style="white-space:nowrap;">'+acciones+'</td></tr>';}).join('');
}

