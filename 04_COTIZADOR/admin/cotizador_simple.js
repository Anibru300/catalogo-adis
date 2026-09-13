/* ---------- cotizaciones ---------- */
function loadProducts(){
  fetch('products.json').then(r=>r.json()).then(d=>{ products = d.products || []; }).catch(()=>{});
}
function searchProducts(){
  const q = $('qSearch').value.trim().toLowerCase();
  const box = $('qSearchResults');
  if (q.length < 2) { box.innerHTML=''; return; }
  const matches = products.filter(p => (p.name+' '+p.category+' '+(p.subcategory||'')).toLowerCase().includes(q)).slice(0,8);
  box.innerHTML = '<div class="sr-list">' + (matches.length
    ? matches.map(p=>'<div class="sr-item" onclick="addItem('+products.indexOf(p)+')"><span>'+esc(p.name)+' <span class="muted">· '+esc(p.category)+'</span></span><span class="gold">'+esc(p.price)+'</span></div>').join('')
    : '<div class="sr-item muted">Sin resultados</div>') + '</div>';
}
function addItem(idx){
  const p = products[idx];
  const price = parseFloat(String(p.price).replace(/[^0-9.]/g,'')) || 0;
  quoteItems.push({nombre:p.name, categoria:p.category, cantidad:1, precio:price});
  $('qSearch').value=''; $('qSearchResults').innerHTML='';
  renderItems();
}
function renderItems(){
  $('qItems').innerHTML = quoteItems.map((it,i)=>
    '<div class="item-row">' +
    '<input value="'+esc(it.nombre)+'" onchange="quoteItems['+i+'].nombre=this.value">' +
    '<input type="number" min="1" value="'+it.cantidad+'" onchange="quoteItems['+i+'].cantidad=parseFloat(this.value)||1; updateTotal()">' +
    '<input type="number" min="0" step="0.01" value="'+it.precio+'" onchange="quoteItems['+i+'].precio=parseFloat(this.value)||0; updateTotal()">' +
    '<button class="del" onclick="quoteItems.splice('+i+',1); renderItems()">✕</button></div>'
  ).join('');
  updateTotal();
}
function updateTotal(){
  const t = quoteItems.reduce((s,it)=>s + (Number(it.cantidad)||0)*(Number(it.precio)||0), 0);
  $('qTotal').textContent = fmtMoney(t);
  return t;
}
function quoteData(){
  return { tipo:'quote', cliente:$('qNombre').value.trim(), telefono:$('qTelefono').value.trim(),
    ciudad:$('qCiudad').value.trim(), items:quoteItems, total:updateTotal(), notas:$('qNotas').value.trim() };
}
function saveQuote(){
  if (!$('qNombre').value.trim() || !$('qTelefono').value.trim()) { notice('Falta el nombre o teléfono del cliente.', false); return; }
  if (!quoteItems.length) { notice('Agrega al menos un producto a la cotización.', false); return; }
  apiPost(quoteData()).then(d=>{ notice(d && d.ok ? 'Cotización guardada en Google Sheets.' : 'No se pudo guardar.', !!(d&&d.ok)); if(d&&d.ok) loadQuotes(); });
}
function quoteText(){
  const d = quoteData();
  let t = 'Cotización ADIS — ' + d.cliente + '\n';
  t += 'Tel: ' + d.telefono + (d.ciudad ? ' · ' + d.ciudad : '') + '\n\n';
  d.items.forEach(it=>{ t += '• ' + it.nombre + ' × ' + it.cantidad + ' — ' + fmtMoney(it.cantidad*it.precio) + '\n'; });
  t += '\nTotal: ' + fmtMoney(d.total);
  if (d.notas) t += '\n\nNotas: ' + d.notas;
  return t;
}
function sendQuoteWhatsApp(){ window.open('https://wa.me/'+CONFIG.WHATSAPP+'?text='+encodeURIComponent(quoteText()),'_blank'); }
function printQuote(){
  const d = quoteData();
  $('printArea').innerHTML =
    '<h1>ADIS Diseño & Remodelación</h1><div class="pq-meta">Cotización · ' + new Date().toLocaleDateString('es-MX') +
    ' · Cliente: ' + esc(d.cliente) + ' · Tel: ' + esc(d.telefono) + (d.ciudad?' · '+esc(d.ciudad):'') + '</div>' +
    '<table><thead><tr><th>Producto</th><th>Cant.</th><th>P. unitario</th><th>Importe</th></tr></thead><tbody>' +
    d.items.map(it=>'<tr><td>'+esc(it.nombre)+'</td><td>'+it.cantidad+'</td><td>'+fmtMoney(it.precio)+'</td><td>'+fmtMoney(it.cantidad*it.precio)+'</td></tr>').join('') +
    '</tbody></table><div class="pq-total">Total: ' + fmtMoney(d.total) + '</div>' +
    (d.notas?'<p style="margin-top:1rem;font-size:0.85rem;">'+esc(d.notas)+'</p>':'') +
    '<div class="pq-foot">ADIS Diseño & Remodelación · Nogales, Sonora · Rio Rico, AZ · +1 (520) 839-2877 · adis.remodelacion@gmail.com</div>';
  window.print();
}
let quotesCache = [];
function loadQuotes(){
  apiGet('quotes').then(data=>{
    if (!data || !data.ok) { $('quotesTable').innerHTML='<tr><td colspan="6" class="muted">Sin acceso.</td></tr>'; return; }
    quotesCache = data.quotes || [];
    if (!quotesCache.length) { $('quotesTable').innerHTML='<tr><td colspan="6" class="muted">Aún no hay cotizaciones guardadas.</td></tr>'; return; }
    $('quotesTable').innerHTML = quotesCache.slice().reverse().map((q,i)=>{
      const rev = quotesCache.length - 1 - i;
      const estado = q.estado || 'Activa';
      const puedeAprobar = q.id && estado === 'Activa';
      const puedeProyecto = q.id && estado === 'Aprobada' && q.datos;
      return '<tr><td>'+esc(String(q.fecha||'').slice(0,10))+'</td><td class="gold">'+esc(q.folio||'—')+'</td><td>'+esc(q.cliente)+'</td>' +
        '<td>'+esc(q.telefono)+'</td><td class="gold">'+esc(q.total)+'</td>' +
        '<td>'+(q.id ? '<span class="muted">'+esc(estado)+'</span>' : '<span class="muted">'+(q.datos?'Activa':'simple')+'</span>')+'</td>' +
        '<td style="white-space:nowrap;">'+(q.datos ? '<button class="btn btn-sm" onclick="loadProposalFromQuote('+rev+')">📂 Cargar</button> ' : '')+
        (puedeAprobar ? '<button class="btn btn-sm" onclick="aprobarQuote(\''+q.id+'\')">✔ Aprobar</button> ' : '')+
        (puedeProyecto ? '<button class="btn btn-sm" onclick="crearProyectoDesdeQuote(\''+q.id+'\')">🏗️ Proyecto</button>' : '')+'</td></tr>';
    }).join('');
  }).catch(()=>{});
}
function aprobarQuote(id){
  if (!confirma('quote-'+id, 'Marcar esta cotización como APROBADA.')) return;
  apiPost({tipo:'set_estado_quote', id, estado:'Aprobada'}).then(d=>{
    notice(d&&d.ok?'Cotización aprobada.':errMsg(d), !!(d&&d.ok));
    if(d&&d.ok) loadQuotes();
  });
}

