/* ----- otros ingresos (reembolsos, venta de activos...) ----- */
function addIngreso(){
  const concepto=$('ingConcepto').value.trim(), monto=parseFloat($('ingMonto').value)||0;
  if (!concepto || !monto) { notice('Falta el concepto o el monto.', false); return; }
  notice('⏳ Guardando ingreso…', true);
  apiPost({tipo:'ingreso', fecha:$('ingFecha').value, concepto,
    monto, moneda:$('ingMoneda').value, metodo:$('ingMetodo').value, notas:$('ingNotas').value.trim(),
    tipo_ingreso: $('ingTipo') ? $('ingTipo').value : 'venta'}).then(d=>{
    notice(d&&d.ok
      ? '✅ Ingreso correcto — folio '+(d.folio||'—')+' · '+fmtMoney(monto)+' '+$('ingMoneda').value+'. Ya está en tus Ventas del mes.'
      : errMsg(d,'No se pudo guardar.'), !!(d&&d.ok));
    if(d&&d.ok){ $('ingMonto').value=''; $('ingNotas').value=''; loadCXC(); }
  }).catch(()=>notice('Error de conexión. Revisa tu internet e intenta de nuevo.', false));
}

/* ----- catalogo de categorias (configurable desde INVENTARIO > Configuracion) ----- */
// Fallback local: si el backend aun no devuelve categorias (redeploy pendiente),
// la lista desplegable sigue teniendo las opciones que el dueño usa siempre.
const CAT_GASTOS_FALLBACK = ['Compra de material','Materiales','Compra de inventario','Publicidad','Inversión','Renta','Luz','Agua','Nómina','Gasolina','Alimentos','Mantenimiento','Envíos','Honorarios','Gastos personales','Equipos','Muestrario','Otro'];
const CAT_INGRESOS_FALLBACK = ['Venta','Reembolso','Otro ingreso','Otro'];
function poblarCategorias(){
  // Union: las de uso diario del dueño siempre presentes, mas las del catalogo
  // configurable (backend), sin duplicar. El campo sigue aceptando texto libre.
  const unir = (base, cfgList) => {
    const out = base.slice(), vistos = base.map(c=>c.toLowerCase());
    (cfgList||[]).forEach(c=>{ const x=String(c).trim(); if (x && vistos.indexOf(x.toLowerCase())===-1){ vistos.push(x.toLowerCase()); out.push(x); } });
    return out;
  };
  const cg = unir(CAT_GASTOS_FALLBACK, biz.config && biz.config.categorias_gastos);
  const ci = unir(CAT_INGRESOS_FALLBACK, biz.config && biz.config.categorias_ingresos);
  if ($('gCategoria')) { // select desplegable (el datalist no se abre igual en todos los navegadores)
    const prev = $('gCategoria').value;
    $('gCategoria').innerHTML = cg.map(c=>'<option value="'+esc(c)+'">'+esc(c)+'</option>').join('') +
      '<option value="__otra__">✏️ Otra (escribir...)</option>';
    if (prev && (cg.indexOf(prev)!==-1 || prev==='__otra__')) $('gCategoria').value = prev;
  }
  if ($('gCatList')) $('gCatList').innerHTML = cg.map(c=>'<option value="'+esc(c)+'"></option>').join('');
  if ($('ingCatList')) $('ingCatList').innerHTML = ci.map(c=>'<option value="'+esc(c)+'"></option>').join('');
}
// "Otra" en el select de categoria: muestra el campo para escribirla
function categoriaGastoCambiada(){
  const sel=$('gCategoria'), otra=$('gCategoriaOtra');
  if (!sel || !otra) return;
  const esOtra = sel.value==='__otra__';
  otra.style.display = esOtra ? '' : 'none';
  if (esOtra) otra.focus();
}
function pintarCategoriasConfig(){
  const box = (id, tipo, lista) => {
    if (!$(id)) return;
    $(id).innerHTML = '<p class="muted" style="margin:0.3rem 0;">'+(tipo==='gastos'?'Gastos':'Ingresos')+':</p><div>' +
      (lista.length ? lista.map(c=>
        '<span style="display:inline-block;border:1px solid #3a3428;border-radius:10px;padding:1px 8px;margin:2px;font-size:0.75rem;">'+esc(c)+
        ' <a href="javascript:void(0)" data-tipo="'+tipo+'" data-cat="'+esc(c)+'" onclick="quitarCategoria(this)" style="color:#e37c7c;text-decoration:none;">✕</a></span>'
      ).join('') : '<span class="muted">(sin categorías)</span>') + '</div>';
  };
  box('catGastosBox', 'gastos', (biz.config.categorias_gastos)||[]);
  box('catIngresosBox', 'ingresos', (biz.config.categorias_ingresos)||[]);
}
function agregarCategoria(){
  const nombre=$('catNombre').value.trim(), clase=$('catTipo').value;
  if (!nombre) { notice('Escribe el nombre de la categoría.', false); return; }
  apiPost({tipo:'categoria', accion:'agregar', clase, nombre}).then(d=>{
    notice(d&&d.ok?'Categoría agregada.':errMsg(d,'No se pudo agregar.'), !!(d&&d.ok));
    if(d&&d.ok){
      biz.config[clase==='ingresos'?'categorias_ingresos':'categorias_gastos'] = d.categorias;
      $('catNombre').value='';
      pintarCategoriasConfig(); poblarCategorias();
    }
  });
}
// doble paso sin confirm(): el ✕ pide confirmacion a si mismo
function quitarCategoria(el){
  const clase=el.dataset.tipo, nombre=el.dataset.cat;
  if (el.dataset.confirm!=='1') {
    el.dataset.confirm='1'; el.textContent='¿Seguro?';
    setTimeout(()=>{ if(el.isConnected){ el.dataset.confirm=''; el.textContent='✕'; } }, 3000);
    return;
  }
  apiPost({tipo:'categoria', accion:'quitar', clase, nombre}).then(d=>{
    notice(d&&d.ok?('Categoría "'+nombre+'" eliminada del catálogo.'):errMsg(d), !!(d&&d.ok));
    if(d&&d.ok){
      biz.config[clase==='ingresos'?'categorias_ingresos':'categorias_gastos'] = d.categorias;
      pintarCategoriasConfig(); poblarCategorias();
    }
  });
}

/* ----- gastos ----- */
function limpiarFormGasto(){
  $('gMonto').value=''; $('gDesc').value=''; $('gCategoriaOtra').value='';
  if ($('gCategoria')) $('gCategoria').selectedIndex = 0;
  categoriaGastoCambiada();
}
function addExpense(){
  let cat = $('gCategoria') ? $('gCategoria').value : '';
  if (cat==='__otra__') cat = $('gCategoriaOtra').value.trim();
  const monto=parseFloat($('gMonto').value)||0;
  if (!cat || !monto) { notice(cat?'Falta el monto.':'Elige la categoría (o escribe la nueva).', false); return; }
  // categoría nueva escrita a mano: agregarla a la lista de la sesión para no repetir
  if (cat && CAT_GASTOS_FALLBACK.map(c=>c.toLowerCase()).indexOf(cat.toLowerCase())===-1) {
    CAT_GASTOS_FALLBACK.push(cat);
    poblarCategorias();
  }
  notice('⏳ Guardando gasto…', true);
  const yaPagado = $('gPagado') && $('gPagado').value==='si';
  const monedaG = $('gMoneda').value;
  apiPost({tipo:'gasto', fecha:$('gFecha').value, categoria:cat, descripcion:$('gDesc').value.trim(),
    monto, moneda:monedaG}).then(d=>{
    if (!(d&&d.ok)) { notice(errMsg(d,'No se pudo guardar.'), false); logCliente('error','gasto', errMsg(d,'respuesta sin ok')+' | categoria='+cat+' monto='+monto); return; }
    if (!yaPagado) {
      notice('✅ Gasto correcto — folio '+(d.folio||'—')+' · '+fmtMoney(monto)+' '+monedaG+'. Quedó POR PAGAR: cuando lo cubras, ve a "Cuentas por pagar" y dale clic en Pagar.', true);
      limpiarFormGasto(); loadBiz();
      return;
    }
    // "Ya lo pagué": gasto y pago registrados en un solo paso
    notice('⏳ Registrando el pago…', true);
    apiPost({tipo:'gasto_pago', gasto_id:d.id, fecha:fLocal(), monto, moneda:monedaG,
      metodo:$('gMetodo')?$('gMetodo').value:'Transferencia', notas:''}).then(p=>{
      if (!(p&&p.ok)) logCliente('error','gasto_pago_auto', 'gasto '+(d.folio||'—')+' (id='+d.id+') sin pago: '+errMsg(p,'respuesta sin ok'));
      notice(p&&p.ok
        ? '✅ Gasto y pago registrados — '+(d.folio||'—')+' · '+(p.folio||'—')+' · '+fmtMoney(monto)+' '+monedaG+'. Gasto PAGADA.'
        : '⚠️ El gasto '+(d.folio||'—')+' se guardó, pero el PAGO falló: ve a "Cuentas por pagar" y dale clic en Pagar.',
        !!(p&&p.ok));
      limpiarFormGasto(); if ($('gPagado')) $('gPagado').value='no'; loadBiz();
    }).catch(()=>{
      notice('⚠️ El gasto '+(d.folio||'—')+' se guardó, pero el PAGO no pudo registrarse (conexión). Ve a "Cuentas por pagar" y dale clic en Pagar.', false);
      logCliente('error','gasto_pago_auto', 'gasto '+(d.folio||'—')+' (id='+d.id+') sin pago: error de conexion');
      limpiarFormGasto(); if ($('gPagado')) $('gPagado').value='no'; loadBiz();
    });
  }).catch(()=>{ notice('Error de conexión. Revisa tu internet e intenta de nuevo.', false); logCliente('error','gasto_red', 'sin respuesta del servidor | categoria='+cat+' monto='+monto); });
}
// FASE 5: gasto != pago. Cada gasto lleva folio GAS-, estado (ACTIVA/CANCELADA) y pagos parciales.
function renderExpenses(list){
  if (!list.length) { $('expTable').innerHTML='<tr><td colspan="9" class="muted">Sin gastos registrados.</td></tr>'; return; }
  $('expTable').innerHTML = list.slice().reverse().map(g=>{
    const est = g.estado || 'ACTIVA';
    const cancelada = est==='CANCELADA';
    const pagado = Number(g.pagado)||0;
    const saldo = Math.max(0, (Number(g.monto)||0) - pagado);
    const colE = cancelada ? '#9a9a9a' : '#e8b96a';
    const acciones = g.id && !cancelada
      ? (saldo>0.001 ? '<button class="btn btn-sm" onclick="showPagoForm(\''+g.id+'\')">Pagar</button> ' : '') +
        '<button class="btn btn-danger btn-sm" onclick="cancelarGasto(\''+g.id+'\', this)">Cancelar</button>'
      : (cancelada ? '<span class="muted">cancelado</span>' : '');
    return '<tr><td class="gold">'+esc(g.folio||'—')+'</td><td>'+esc(g.fecha)+'</td><td>'+esc(g.categoria)+'</td><td>'+esc(g.descripcion)+'</td>' +
      '<td class="gold">'+fmtMoney(g.monto)+' '+esc(g.moneda)+'</td>' +
      '<td style="color:#7ce3a1;">'+fmtMoney(pagado)+'</td>' +
      '<td>'+(saldo>0.001&&!cancelada?'<span class="gold">'+fmtMoney(saldo)+'</span>':'—')+'</td>' +
      '<td><span style="color:'+colE+';font-weight:600;font-size:0.72rem;">'+esc(est)+'</span></td>' +
      '<td style="white-space:nowrap;">'+acciones+'</td></tr>';}).join('');
}
function renderCXP(d){
  const porPagar = Number(d && d.por_pagar_base)||0;
  const conSaldo = cxpCache.filter(x=>x.saldo_base>0.001).length;
  const pagadas = cxpCache.filter(x=>x.estado_pago==='PAGADA').length;
  if ($('cxpDash')) $('cxpDash').innerHTML =
    '<div class="pnl-card '+(porPagar?'bad':'good')+'"><div class="k">Por pagar ('+esc((d&&d.moneda_base)||'MXN')+')</div><div class="v">'+fmtMoney(porPagar)+'</div></div>' +
    '<div class="pnl-card"><div class="k">Gastos con saldo</div><div class="v">'+conSaldo+'</div></div>' +
    '<div class="pnl-card good"><div class="k">Gastos pagados</div><div class="v">'+pagadas+'</div></div>';
  if (!$('cxpTable')) return;
  const orden = cxpCache.slice().sort((a,b)=>(Number(b.saldo_base>0.001))-(Number(a.saldo_base>0.001)));
  $('cxpTable').innerHTML = orden.length ? orden.map(x=>{
    const col = x.estado_pago==='PAGADA'?'#7ce3a1':(x.estado_pago==='PARCIAL'?'#e8b96a':'#e37c7c');
    return '<tr><td class="gold">'+esc(x.folio||'—')+'</td><td>'+esc(x.fecha)+'</td><td>'+esc(x.categoria)+'</td>' +
      '<td>'+fmtMoney(x.total)+' '+esc(x.moneda)+'</td><td style="color:#7ce3a1;">'+fmtMoney(x.pagado)+'</td>' +
      '<td class="gold">'+fmtMoney(x.saldo)+'</td>' +
      '<td><span style="color:'+col+';font-weight:600;font-size:0.72rem;">'+esc(x.estado_pago)+'</span></td>' +
      '<td style="white-space:nowrap;">'+(x.saldo>0.001?'<button class="btn btn-sm" onclick="showPagoForm(\''+x.gasto_id+'\')">Pagar</button>':'')+'</td></tr>';
  }).join('') : '<tr><td colspan="8" class="muted">Sin gastos pendientes de pago.</td></tr>';
  $('pagosTable').innerHTML = pagosCache.length ? pagosCache.map(p=>
    '<tr><td class="gold">'+esc(p.folio||'—')+'</td><td>'+esc(p.fecha)+'</td><td>'+esc(p.gasto_folio||'—')+'</td>' +
    '<td>'+esc(p.categoria||'—')+'</td><td class="gold">'+fmtMoney(p.monto)+' '+esc(p.moneda)+'</td><td>'+esc(p.metodo||'—')+'</td></tr>').join('')
    : '<tr><td colspan="6" class="muted">Sin pagos registrados.</td></tr>';
}
function showPagoForm(gastoId){
  const x = cxpCache.filter(g=>String(g.gasto_id)===String(gastoId))[0];
  if (!x) { notice('Recarga la pestaña para ver el saldo actualizado.', false); return; }
  $('pagoForms').innerHTML = '<div class="card-box"><p style="margin-bottom:0.5rem;"><strong>Registrar pago — '+esc(x.folio)+'</strong> <span class="muted">'+esc(x.categoria)+' · saldo '+fmtMoney(x.saldo)+' '+esc(x.moneda)+'</span></p><div class="row">' +
    '<div><label>Fecha</label><input type="date" id="pgFecha" value="'+fLocal()+'"></div>' +
    '<div><label>Monto *</label><input type="number" id="pgMonto" min="0" step="0.01" value="'+x.saldo+'"></div>' +
    '<div><label>Moneda</label><select id="pgMoneda"><option value="'+esc(x.moneda)+'">'+esc(x.moneda)+'</option><option value="MXN">MXN</option><option value="USD">USD</option></select></div>' +
    '<div><label>Método</label><select id="pgMetodo"><option>Efectivo</option><option>Transferencia</option><option>Tarjeta</option><option>Depósito</option><option>Otro</option></select></div>' +
    '</div><label>Notas</label><input id="pgNotas">' +
    '<div class="toolbar" style="margin-top:1rem;"><button class="btn btn-solid btn-sm" onclick="savePago(\''+x.gasto_id+'\')">Guardar pago</button> ' +
    '<button class="btn btn-sm" onclick="$(\'pagoForms\').innerHTML=\'\'">Cerrar</button></div></div>';
  $('pagoForms').scrollIntoView({behavior:'smooth', block:'nearest'});
}
function savePago(gastoId){
  const monto = parseFloat($('pgMonto').value)||0;
  if (monto <= 0) { notice('El monto debe ser mayor que cero.', false); return; }
  notice('⏳ Registrando pago…', true);
  apiPost({tipo:'gasto_pago', gasto_id:gastoId, fecha:$('pgFecha').value, monto,
    moneda:$('pgMoneda').value, metodo:$('pgMetodo').value, notas:$('pgNotas').value.trim()}).then(d=>{
    notice(d&&d.ok?('Pago '+(d.folio||'')+' registrado. Gasto ahora: '+d.estado_pago+'.'):errMsg(d), !!(d&&d.ok));
    if(d&&d.ok){ $('pagoForms').innerHTML=''; loadBiz(); }
  }).catch(()=>notice('Error de conexión.', false));
}
// doble paso sin confirm(): el boton pide confirmacion a si mismo
function cancelarGasto(id, btn){
  if (btn.dataset.confirm !== '1') {
    btn.dataset.confirm = '1'; btn.textContent = '¿Seguro?';
    setTimeout(()=>{ if (btn.isConnected){ btn.dataset.confirm=''; btn.textContent='Cancelar'; } }, 3000);
    return;
  }
  apiPost({tipo:'gasto_cancelar', id}).then(d=>{
    notice(d&&d.ok?'Gasto cancelado (baja lógica; queda en el historial).':errMsg(d), !!(d&&d.ok));
    if(d&&d.ok) loadBiz();
  });
}



/* ----- gastos fijos (programados) ----- */
let fijosCache = [];
let fijosAvisados = false; // el aviso global de vencimientos se muestra 1 vez por sesion

function loadFijos(){
  if (!$('fijosTable')) return;
  apiGet('gastos_fijos').then(d=>{
    fijosCache = (d && d.fijos) || [];
    renderFijos();
    avisarVencimientosFijos();
  }).catch(()=>{ $('fijosTable').innerHTML='<tr><td colspan="8" class="muted">No se pudo cargar. Intenta de nuevo.</td></tr>'; });
}

// dias desde hoy hasta la fecha (negativo = vencido). Base local, sin sorpasas de horario.
function diasHasta_(fecha){
  if (!fecha || !/^\d{4}-\d{2}-\d{2}$/.test(String(fecha))) return null;
  const hoy = new Date(); hoy.setHours(0,0,0,0);
  const d = new Date(String(fecha)+'T00:00:00');
  return Math.round((d - hoy) / 86400000);
}

function alertaFijo_(f){
  const dias = diasHasta_(f.proxima_fecha);
  if (dias === null) return {txt:'<span class="muted">sin fecha</span>', nivel:0, dias};
  if (dias < 0)  return {txt:'🔴 Vencido hace '+(-dias)+' día'+(-dias===1?'':'s'), nivel:2, dias};
  if (dias === 0) return {txt:'🔴 Vence HOY', nivel:2, dias};
  if (dias <= 3) return {txt:'🟠 Por vencer en '+dias+' día'+(dias===1?'':'s'), nivel:1, dias};
  return {txt:'🟢 En '+dias+' días', nivel:0, dias};
}

function renderFijos(){
  if (!$('fijosTable')) return;
  const orden = fijosCache.slice().sort((a,b)=>{
    const ea = String(a.estado)==='CANCELADA' ? 1 : 0, eb = String(b.estado)==='CANCELADA' ? 1 : 0;
    if (ea !== eb) return ea - eb;
    return String(a.proxima_fecha||'').localeCompare(String(b.proxima_fecha||''));
  });
  const activos = orden.filter(f=>String(f.estado)!=='CANCELADA');
  const vencidos = activos.filter(f=>alertaFijo_(f).nivel===2).length;
  const porVencer = activos.filter(f=>alertaFijo_(f).nivel===1).length;
  if ($('fijosDash')) $('fijosDash').innerHTML =
    '<div class="pnl-card '+(vencidos?'bad':'good')+'"><div class="k">🔴 Vencidos</div><div class="v">'+vencidos+'</div></div>' +
    '<div class="pnl-card '+(porVencer?'bad':'')+'"><div class="k">🟠 Por vencer (≤3 días)</div><div class="v">'+porVencer+'</div></div>' +
    '<div class="pnl-card"><div class="k">Gastos fijos activos</div><div class="v">'+activos.length+'</div></div>';
  if (!orden.length) { $('fijosTable').innerHTML='<tr><td colspan="8" class="muted">Sin gastos fijos. Programa el primero arriba (renta, internet, nómina...).</td></tr>'; return; }
  const FREC_TXT = {semanal:'Cada semana', quincenal:'Cada 2 semanas', mensual:'Cada mes', anual:'Cada año'};
  $('fijosTable').innerHTML = orden.map(f=>{
    const cancelado = String(f.estado)==='CANCELADA';
    const al = alertaFijo_(f);
    const acciones = cancelado ? '<span class="muted">cancelado</span>'
      : '<button class="btn btn-sm" onclick="generarFijo(\''+f.id+'\', this)">Generar gasto</button> ' +
        '<button class="btn btn-danger btn-sm" onclick="quitarFijo(\''+f.id+'\', this)">Cancelar</button>';
    return '<tr'+(cancelado?' style="opacity:0.5;"':'')+'><td><strong>'+esc(f.concepto)+'</strong>'+(f.notas?'<br><span class="muted">'+esc(f.notas)+'</span>':'')+'</td>' +
      '<td>'+esc(f.categoria)+'</td>' +
      '<td class="gold">'+fmtMoney(f.monto)+' '+esc(f.moneda)+'</td>' +
      '<td>'+esc(FREC_TXT[f.frecuencia]||f.frecuencia)+'</td>' +
      '<td>'+esc(f.proxima_fecha||'—')+'</td>' +
      '<td style="font-weight:600;font-size:0.78rem;white-space:nowrap;">'+al.txt+'</td>' +
      '<td>'+(f.gasto_folio_ultimo?'<span class="muted">'+esc(f.gasto_folio_ultimo)+'</span>':'—')+'</td>' +
      '<td style="white-space:nowrap;">'+acciones+'</td></tr>';
  }).join('');
}

// Aviso una sola vez por sesion si hay vencidos o proximos a vencer
function avisarVencimientosFijos(){
  if (fijosAvisados) return;
  fijosAvisados = true;
  const activos = fijosCache.filter(f=>String(f.estado)!=='CANCELADA');
  const vencidos = activos.filter(f=>alertaFijo_(f).nivel===2);
  const proximos = activos.filter(f=>alertaFijo_(f).nivel===1);
  if (vencidos.length) {
    notice('🔴 Gastos fijos VENCIDOS: '+vencidos.map(f=>esc(f.concepto)).join(', ')+'. Ve a Dinero → Gastos fijos.', false);
  } else if (proximos.length) {
    notice('🟠 Pronto vence(n): '+proximos.map(f=>esc(f.concepto)+' ('+esc(f.proxima_fecha)+')').join(', ')+'.', true);
  }
}

function addFijo(){
  const concepto=$('fConcepto').value.trim(), monto=parseFloat($('fMonto').value)||0;
  if (!concepto || !monto) { notice('Falta el concepto o el monto.', false); return; }
  if (!$('fProxima').value) { notice('Elige la fecha del próximo pago.', false); return; }
  notice('⏳ Guardando gasto fijo…', true);
  apiPost({tipo:'gasto_fijo', accion:'agregar', concepto, categoria:$('fCategoria').value.trim(),
    monto, moneda:$('fMoneda').value, frecuencia:$('fFrecuencia').value,
    proxima_fecha:$('fProxima').value, notas:$('fNotas').value.trim()}).then(d=>{
    notice(d&&d.ok
      ? '✅ Gasto fijo correcto — '+esc(concepto)+'. Próximo pago: '+(d.proxima_fecha||$('fProxima').value)+'.'
      : errMsg(d,'No se pudo guardar.'), !!(d&&d.ok));
    if(d&&d.ok){ $('fConcepto').value=''; $('fMonto').value=''; $('fNotas').value=''; $('fCategoria').value=''; loadFijos(); }
  }).catch(()=>notice('Error de conexión. Revisa tu internet e intenta de nuevo.', false));
}

// doble paso sin confirm(): el boton pide confirmacion a si mismo
function generarFijo(id, btn){
  if (btn.dataset.confirm!=='1') {
    btn.dataset.confirm='1'; btn.textContent='¿Seguro? Genera el gasto';
    setTimeout(()=>{ if (btn.isConnected){ btn.dataset.confirm=''; btn.textContent='Generar gasto'; } }, 3000);
    return;
  }
  notice('⏳ Generando gasto…', true);
  apiPost({tipo:'gasto_fijo', accion:'generar', id}).then(d=>{
    notice(d&&d.ok
      ? '✅ Gasto '+(d.folio||'—')+' generado (quedó POR PAGAR). Próximo pago programado: '+d.proxima_fecha+'.'
      : errMsg(d,'No se pudo generar.'), !!(d&&d.ok));
    if(d&&d.ok) loadFijos();
  }).catch(()=>notice('Error de conexión. Intenta de nuevo.', false));
}

// doble paso sin confirm(): el boton pide confirmacion a si mismo
function quitarFijo(id, btn){
  if (btn.dataset.confirm!=='1') {
    btn.dataset.confirm='1'; btn.textContent='¿Seguro?';
    setTimeout(()=>{ if (btn.isConnected){ btn.dataset.confirm=''; btn.textContent='Cancelar'; } }, 3000);
    return;
  }
  apiPost({tipo:'gasto_fijo', accion:'quitar', id}).then(d=>{
    notice(d&&d.ok?'Gasto fijo cancelado (se conserva en el historial).':errMsg(d), !!(d&&d.ok));
    if(d&&d.ok) loadFijos();
  }).catch(()=>notice('Error de conexión. Intenta de nuevo.', false));
}
