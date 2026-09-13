/* ---------- COTIZADOR PROFESIONAL (formato propuesta ADIS) ---------- */
const TIPOS_PROYECTO = ['Centro de TV decorativo','Puerta oculta','Isla de cocina','Remodelación de cocina','Remodelación de baño','Muro decorativo','Barra decorativa','Plafón decorativo','Fachada / muro exterior','Revestimiento de columnas','Nichos decorativos','Área comercial'];
const GARANTIA_COBERTURA = ['7 meses de garantía en la instalación a partir de la entrega del proyecto.','Correcciones dentro de cobertura sin costo de mano de obra.','Materiales sujetos a la garantía y plazos de cada fabricante.','Toda solicitud se evalúa conforme a las condiciones de garantía.'];
const GARANTIA_NO_CUBRE = ['Golpes, accidentes o mal uso; desgaste normal de materiales.','Humedad, filtraciones o fugas ajenas a nuestra instalación.','Modificaciones o reparaciones realizadas por terceros.','Movimientos, asentamientos o problemas estructurales del inmueble.','Daños por condiciones externas al trabajo realizado por ADIS.'];
const LOGISTICA = [['PROTECCIÓN DEL ESPACIO','Barreras contra polvo y residuos; protección de pisos, muebles y superficies; delimitación del área de trabajo.'],['HORARIOS Y COORDINACIÓN','Programación previa de días y horarios, coordinación de cuadrilla y comunicación de avances relevantes.'],['ORDEN Y LIMPIEZA','Recolección de residuos y limpieza del área al final de cada jornada y al concluir el proyecto.'],['SUPERVISIÓN Y ENTREGA','Supervisión durante la instalación, inspección final y entrega del proyecto conforme a lo acordado.']];

function defaultProp(){
  return { folio:'', savedFolio:'', fecha:new Date().toISOString().slice(0,10), cliente:'', telefono:'', proyecto:'', ubicacion:'',
    elaboro:'Josías Espinoza · Gerente', vigencia:30,
    fotoProyecto:null, tipos:[], otroTipo:'', area:'', materiales:'', descripcion:'',
    moneda:'MXN', costo:'', precioFinal:'', items:[], incluirIva:true, tasaIva:16,
    fotos:[{data:null,desc:''},{data:null,desc:''},{data:null,desc:''}],
    especificaciones:'',
    formaPago:'50% al iniciar la instalación · 50% al finalizar el proyecto, contra entrega.',
    tiempoEntrega:'', alcanceExtra:'La propuesta contempla exclusivamente lo especificado. Modificaciones o trabajos adicionales se autorizan previamente y se cotizan por separado.',
    incluirGarantia:true, incluirLogistica:true, incluirAceptacion:true };
}
let prop = defaultProp();
let propTimer = null;

function initProposal(){
  try {
    const d = JSON.parse(localStorage.getItem('adis_prop_draft') || 'null');
    if (d && d.items) prop = Object.assign(defaultProp(), d);
  } catch (e) {}
  renderTiposChk(); applyPropToForm(); renderItemRows(); renderFotoProy(); renderFotosGrid(); renderProposal();
}
function scheduleProp(){ schedulePropDraft(); renderProposal(); }
function schedulePropDraft(){
  clearTimeout(propTimer);
  propTimer = setTimeout(()=>{ try { localStorage.setItem('adis_prop_draft', JSON.stringify(prop)); } catch (e) {} }, 400);
}

function applyPropToForm(){
  $('pCliente').value = prop.cliente; $('pTelefono').value = prop.telefono;
  $('pProyecto').value = prop.proyecto; $('pUbicacion').value = prop.ubicacion;
  $('pFecha').value = prop.fecha; $('pVigencia').value = prop.vigencia; $('pElaboro').value = prop.elaboro;
  $('pOtroTipo').value = prop.otroTipo; $('pArea').value = prop.area; $('pMateriales').value = prop.materiales;
  $('pDescripcion').value = prop.descripcion; $('pMoneda').value = prop.moneda;
  const pf = $('pPrecioFinal'); if (pf) pf.value = prop.precioFinal;
  const ct = $('pCosto'); if (ct && document.activeElement !== ct) ct.value = prop.costo;
  $('pEspec').value = prop.especificaciones; $('pFormaPago').value = prop.formaPago;
  $('pTiempoEntrega').value = prop.tiempoEntrega; $('pAlcanceExtra').value = prop.alcanceExtra;
  $('pIncluirGarantia').checked = prop.incluirGarantia; $('pIncluirLogistica').checked = prop.incluirLogistica;
  $('pIncluirAceptacion').checked = prop.incluirAceptacion;
}

function matchLead(){
  const q = prop.cliente.trim().toLowerCase();
  prop.clienteId = ''; // se reasigna solo si hay coincidencia exacta con un cliente
  if (q.length < 3) return;
  // FASE 3: autocompletar tambien desde clientes registrados (con prioridad)
  const c = clientesCache.find(x => String(x.nombre||'').toLowerCase() === q) || clientesCache.find(x => String(x.nombre||'').toLowerCase().indexOf(q) !== -1);
  if (c && document.activeElement === $('pCliente')) {
    prop.clienteId = c.id;
    if (c.telefono && !$('pTelefono').value) { prop.telefono = c.telefono; $('pTelefono').value = c.telefono; }
    if (c.ciudad && !$('pUbicacion').value) { prop.ubicacion = c.ciudad; $('pUbicacion').value = c.ciudad; }
    renderProposal();
    return;
  }
  apiGet('leads').then(d=>{
    if (!d || !d.ok) return;
    const l = d.leads.find(x => String(x.nombre||'').toLowerCase() === q) || d.leads.find(x => String(x.nombre||'').toLowerCase().indexOf(q) !== -1);
    if (l && document.activeElement === $('pCliente')) {
      if (l.telefono && !$('pTelefono').value) { prop.telefono = l.telefono; $('pTelefono').value = l.telefono; }
      if (l.ciudad && !$('pUbicacion').value) { prop.ubicacion = l.ciudad; $('pUbicacion').value = l.ciudad; }
      renderProposal();
    }
  }).catch(()=>{});
}

/* ----- alcance: tipos y foto ----- */
function renderTiposChk(){
  $('pTipos').innerHTML = TIPOS_PROYECTO.map((t,i)=>
    '<label><input type="checkbox" '+(prop.tipos.indexOf(t)!==-1?'checked':'')+' onchange="toggleTipo('+i+',this.checked)"> '+esc(t)+'</label>'
  ).join('');
}
function toggleTipo(i, on){
  const t = TIPOS_PROYECTO[i];
  const ix = prop.tipos.indexOf(t);
  if (on && ix === -1) prop.tipos.push(t);
  if (!on && ix !== -1) prop.tipos.splice(ix,1);
  scheduleProp();
}

function fileToDataURL(file, cb){
  const r = new FileReader();
  r.onload = e => {
    const img = new Image();
    img.onload = () => {
      const max = 1280; let w = img.width, h = img.height;
      if (Math.max(w,h) > max) { const s = max/Math.max(w,h); w = Math.round(w*s); h = Math.round(h*s); }
      const c = document.createElement('canvas'); c.width = w; c.height = h;
      c.getContext('2d').drawImage(img, 0, 0, w, h);
      cb(c.toDataURL('image/jpeg', 0.82));
    };
    img.src = e.target.result;
  };
  r.readAsDataURL(file);
}
function setFotoProyecto(input){
  const f = input.files && input.files[0];
  if (!f) return;
  fileToDataURL(f, url => { prop.fotoProyecto = url; renderFotoProy(); renderProposal(); schedulePropDraft(); });
  input.value = '';
}
function renderFotoProy(){
  $('pFotoProySlot').className = 'photo-slot' + (prop.fotoProyecto ? ' filled' : '');
  $('pFotoProySlot').innerHTML = prop.fotoProyecto
    ? '<img src="'+prop.fotoProyecto+'" alt="Foto del proyecto"><button class="del" onclick="prop.fotoProyecto=null;renderFotoProy();renderProposal();schedulePropDraft()">✕</button>'
    : '<label class="ph-add" for="pFotoProy">📷 Subir fotografía / render del proyecto<br><span class="muted" style="font-size:0.68rem;">JPG, PNG — se comprime automáticamente</span></label>' +
      '<input type="file" id="pFotoProy" accept="image/*" onchange="setFotoProyecto(this)">';
}

function setFotoProducto(idx, input){
  const f = input.files && input.files[0];
  if (!f) return;
  fileToDataURL(f, url => { prop.fotos[idx].data = url; renderFotosGrid(); renderProposal(); schedulePropDraft(); });
  input.value = '';
}
function renderFotosGrid(){
  $('pFotosGrid').innerHTML = prop.fotos.map((f,i)=>
    '<div class="photo-slot'+(f.data?' filled':'')+'">' +
    (f.data ? '<img src="'+f.data+'" alt="Foto de producto"><button class="del" onclick="prop.fotos['+i+'].data=null;renderFotosGrid();renderProposal();schedulePropDraft()">✕</button>'
            : '<label class="ph-add" for="pFoto'+i+'">📷 Foto '+(i+1)+'</label>') +
    '<input type="file" id="pFoto'+i+'" accept="image/*" onchange="setFotoProducto('+i+',this)">' +
    '<input placeholder="Descripción:" value="'+esc(f.desc)+'" oninput="prop.fotos['+i+'].desc=this.value;scheduleProp()" style="font-size:0.75rem; padding:0.4rem 0.5rem;">' +
    '</div>'
  ).join('');
}
function addFotoSlot(){ if (prop.fotos.length >= 6) { notice('Máximo 6 fotos de productos.', false); return; } prop.fotos.push({data:null,desc:''}); renderFotosGrid(); schedulePropDraft(); }

/* ----- partidas ----- */
function parseNum(v){ return parseFloat(String(v==null?'':v).replace(/[^0-9.]/g,'')) || 0; }
function productOptionsHTML(sel){
  const cats = [];
  biz.productos.forEach(p => { const c = p.categoria || 'General'; if (cats.indexOf(c) === -1) cats.push(c); });
  let h = '<option value="">— Partida manual —</option>';
  cats.forEach(c => {
    h += '<optgroup label="'+esc(c)+'">';
    biz.productos.filter(p => (p.categoria||'General') === c).forEach(p => {
      const id = p.id || '';
      h += '<option value="'+esc(id)+'"'+(sel===id?' selected':'')+'>'+esc((p.codigo||'')+' · '+(p.nombre||''))+'</option>';
    });
    h += '</optgroup>';
  });
  return h;
}
function renderItemRows(){
  const body = $('pItems'); if (!body) return; // la tabla de partidas se elimino del formulario
  body.innerHTML = prop.items.map((it,i)=>
    '<tr>' +
    '<td><select onchange="itemProduct('+i+',this.value)">'+productOptionsHTML(it.pid)+'</select></td>' +
    '<td><input value="'+esc(it.descripcion)+'" placeholder="Descripción / especificaciones" oninput="prop.items['+i+'].descripcion=this.value;updItem('+i+');scheduleProp()"></td>' +
    '<td><input type="number" min="0" step="any" value="'+it.cantidad+'" oninput="prop.items['+i+'].cantidad=parseFloat(this.value)||0;updItem('+i+');scheduleProp()"></td>' +
    '<td><input value="'+esc(it.unidad)+'" oninput="prop.items['+i+'].unidad=this.value;updItem('+i+');scheduleProp()"></td>' +
    '<td><input type="number" min="0" step="any" value="'+it.precio+'" oninput="prop.items['+i+'].precio=parseFloat(this.value)||0;updItem('+i+');scheduleProp()"></td>' +
    '<td class="imp" id="pImp'+i+'"></td>' +
    '<td><button class="del" onclick="prop.items.splice('+i+',1);renderItemRows();scheduleProp()">✕</button></td>' +
    '</tr>'
  ).join('');
  updateTotalsUI();
}
function itemProduct(i, pid){
  const it = prop.items[i];
  it.pid = pid;
  const p = biz.productos.find(x => String(x.id||'') === String(pid));
  if (p) {
    it.codigo = p.codigo || ''; it.descripcion = p.nombre || '';
    it.unidad = (p.unidad || 'PZS').toUpperCase(); it.precio = parseNum(p.precio);
  }
  renderItemRows(); scheduleProp();
}
function updItem(i){ const it = prop.items[i]; $('pImp'+i).textContent = fmtMoney((Number(it.cantidad)||0)*(Number(it.precio)||0)); updateTotalsUI(); }
function addPropItem(){ prop.items.push({pid:'',codigo:'',descripcion:'',cantidad:1,unidad:'PZS',precio:0}); renderItemRows(); schedulePropDraft(); }
function calcTotals(){
  // Precio final manual: un solo cuadro; si esta vacio, compat con borradores viejos que tengan partidas
  const manual = parseFloat(prop.precioFinal);
  if (isFinite(manual) && manual > 0) return { subtotal: manual, iva: 0, total: manual };
  const sub = prop.items.reduce((s,it)=> s + (String(it.descripcion).trim() ? (Number(it.cantidad)||0)*(Number(it.precio)||0) : 0), 0);
  const iva = prop.incluirIva ? sub * (Number(prop.tasaIva)||0) / 100 : 0;
  return { subtotal: sub, iva: iva, total: sub + iva };
}
function updateTotalsUI(){
  // Solo actualiza textos: NUNCA re-renderiza inputs (destruiria el foco al teclear)
  const t = calcTotals();
  const el = $('pTotalTxt'); if (el) el.textContent = fmtMoney(t.total) + ' ' + prop.moneda;
  renderUtilidad();
}
function renderUtilidad(){
  const el = $('pUtil'); if (!el) return;
  const c = parseFloat(prop.costo);
  if (!isFinite(c) || c <= 0) { el.textContent = ''; el.className = ''; return; }
  const t = calcTotals();
  const u = t.total - c;
  el.textContent = 'Utilidad estimada: ' + fmtMoney(u) + ' ' + prop.moneda + ' (' + (t.total ? Math.round(u / t.total * 100) : 0) + '%)';
  el.className = u >= 0 ? 'gold' : 'stock-alert';
}

/* ----- vista previa / documento ----- */
function qpFecha(f){ if(!f) return '__ / __ / ______'; const d = new Date(f+'T12:00:00'); if(isNaN(d)) return esc(f); return String(d.getDate()).padStart(2,'0')+' / '+String(d.getMonth()+1).padStart(2,'0')+' / '+d.getFullYear(); }
function qpFolio(){ return prop.savedFolio || 'ADIS-'+(prop.fecha?String(new Date(prop.fecha+'T12:00:00').getFullYear()):new Date().getFullYear())+'-_______'; }

function buildProposalHTML(){
  const t = calcTotals();
  const checks = TIPOS_PROYECTO.map(tp => '<span class="'+(prop.tipos.indexOf(tp)!==-1?'on':'')+'">'+esc(tp)+'</span>').join('');
  const fotosLlenas = prop.fotos.filter(f => f.data);
  let h = '<div class="qp">';
  h += '<div class="qp-header"><div>' +
    '<img src="LOGO%20ADIS.webp" onerror="this.onerror=null;this.src=\'LOGO%20ADIS.png\'" alt="ADIS">' +
    '<div class="qp-brand" style="margin-top:0.3rem;">ADIS | DISEÑOS &amp; REMODELACIONES</div>' +
    '<div class="qp-slogan">Creando espacios, reinventando hogares.</div></div>' +
    '<div class="qp-doc"><b>PROPUESTA DE REMODELACIÓN</b><br>COTIZACIÓN N.º <b>'+esc(qpFolio())+'</b><br>FECHA: <b>'+qpFecha(prop.fecha)+'</b></div></div>';

  h += '<div class="qp-sec"><div class="qp-sec-t">01 · DATOS DEL CLIENTE Y DEL PROYECTO</div>' +
    '<table class="qp-table qp-kv"><tbody>' +
    '<tr><td>CLIENTE</td><td>'+esc(prop.cliente)+'</td></tr>' +
    '<tr><td>PROYECTO</td><td>'+esc(prop.proyecto)+'</td></tr>' +
    '<tr><td>UBICACIÓN</td><td>'+esc(prop.ubicacion)+'</td></tr>' +
    '<tr><td>VIGENCIA</td><td>'+esc(String(prop.vigencia||30))+' días naturales</td></tr>' +
    '<tr><td>ELABORÓ</td><td>'+esc(prop.elaboro)+'</td></tr>' +
    '</tbody></table></div>';

  h += '<div class="qp-sec"><div class="qp-sec-t">02 · ALCANCE DEL PROYECTO</div>' +
    (prop.fotoProyecto ? '<div class="qp-photo-box" style="border-style:solid; padding:0.25rem;"><img src="'+prop.fotoProyecto+'" alt="Proyecto"></div>'
                       : '<div class="qp-photo-box">FOTOGRAFÍA / RENDER DEL PROYECTO<br><span style="font-size:0.55rem;">(se mostrará aquí la imagen que subas en la sección 02 del formulario)</span></div>') +
    '<div class="qp-checks">'+checks+'</div>' +
    (prop.otroTipo ? '<div style="font-size:0.64rem; color:#333; margin:0.15rem 0;">Otro: <b>'+esc(prop.otroTipo)+'</b></div>' : '') +
    '<table class="qp-table qp-kv"><tbody>' +
    '<tr><td>ÁREA A TRANSFORMAR</td><td>'+esc(prop.area)+'</td></tr>' +
    '<tr><td>MATERIALES PRINCIPALES</td><td>'+esc(prop.materiales)+'</td></tr>' +
    '<tr><td>DESCRIPCIÓN BREVE DEL PROYECTO</td><td>'+esc(prop.descripcion)+'</td></tr>' +
    '</tbody></table></div>';

  h += '<div class="qp-sec"><div class="qp-sec-t">03 · INVERSIÓN TOTAL DEL PROYECTO</div>' +
    '<table class="qp-table qp-kv"><tbody>' +
    '<tr><td style="width:22%;">USD</td><td>'+(prop.moneda==='USD' && t.total ? '<b>'+fmtMoney(t.total)+' USD</b>' : '—')+'</td></tr>' +
    '<tr><td>MXN</td><td>'+(prop.moneda==='MXN' && t.total ? '<b>'+fmtMoney(t.total)+' MXN</b>' : '—')+'</td></tr>' +
    '</tbody></table>' +
    '<div class="qp-moneda">La inversión contempla los materiales, insumos, preparación, instalación y servicios especificados en esta propuesta.</div></div>';

  h += '<div class="qp-sec"><div class="qp-sec-t">04 · FOTOGRAFÍAS DE PRODUCTOS Y MATERIALES</div>' +
    (fotosLlenas.length
      ? '<div class="qp-fotos">' + fotosLlenas.map(f => '<div class="qp-foto"><img src="'+f.data+'" alt=""><p>'+esc(f.desc)+'</p></div>').join('') + '</div>'
      : '<div class="qp-photo-box">Aquí se mostrarán las fotos de productos que subas en la sección 04 del formulario.</div>') + '</div>';

  h += '<div class="qp-sec"><div class="qp-sec-t">05 · ESPECIFICACIONES TÉCNICAS Y NOTAS</div>' +
    '<div class="qp-notes">'+(prop.especificaciones ? esc(prop.especificaciones) : '<span style="color:#999;">Acabados, medidas, marcas, colores u observaciones relevantes para el cliente.</span>')+'</div></div>';

  h += '<div class="qp-sec"><div class="qp-sec-t">06 · CONDICIONES COMERCIALES</div><div class="qp-cond">' +
    '<div><b>FORMA DE PAGO</b>'+esc(prop.formaPago)+'</div>' +
    '<div><b>TIEMPO DE ENTREGA</b>Duración estimada: '+esc(prop.tiempoEntrega||'____')+' días de trabajo. Puede variar por condiciones del área o modificaciones autorizadas.</div>' +
    '<div><b>VIGENCIA DE LA COTIZACIÓN</b>Vigente por '+esc(String(prop.vigencia||30))+' días naturales a partir de la fecha de emisión; después de ese plazo, precios y condiciones se confirman por escrito.</div>' +
    '<div><b>ALCANCE Y TRABAJOS ADICIONALES</b>'+esc(prop.alcanceExtra)+'</div>' +
    '</div></div>';

  if (prop.incluirGarantia) {
    h += '<div class="qp-sec"><div class="qp-sec-t">07 · GARANTÍA ADIS</div><div class="qp-cond">' +
      '<div><b>COBERTURA</b>'+GARANTIA_COBERTURA.map(x=>esc(x)).join('<br>')+'</div>' +
      '<div><b>LA GARANTÍA NO CUBRE</b>'+GARANTIA_NO_CUBRE.map(x=>esc(x)).join('<br>')+'</div>' +
      '</div></div>';
  }
  if (prop.incluirLogistica) {
    h += '<div class="qp-sec"><div class="qp-sec-t">08 · LOGÍSTICA PREMIUM ADIS</div><div class="qp-qp-4 qp-4col">' +
      LOGISTICA.map(x => '<div style="border:1px solid #e2d3ac; border-left:3px solid #C5A059; padding:0.45rem 0.55rem; font-size:0.62rem; color:#333;"><b style="color:#8a6d2f; display:block; margin-bottom:0.2rem;">'+esc(x[0])+'</b>'+esc(x[1])+'</div>').join('') +
      '</div></div>';
  }
  if (prop.incluirAceptacion) {
    h += '<div class="qp-sec"><div class="qp-sec-t">09 · ACEPTACIÓN DE LA PROPUESTA</div>' +
      '<div class="qp-acepta">Con la firma de este documento, el cliente acepta el alcance, la inversión y las condiciones descritas en la presente cotización.</div>' +
      '<div class="qp-firmas">' +
      '<div class="qp-firma"><b>CLIENTE</b><br>NOMBRE: '+esc(prop.cliente)+'<br>FIRMA: ______________________________<br>FECHA: ____ / ____ / ______</div>' +
      '<div class="qp-firma"><b>ADIS DISEÑOS &amp; REMODELACIONES</b><br>NOMBRE: '+esc(prop.elaboro)+'<br>FIRMA: ______________________________<br>FECHA: ____ / ____ / ______</div>' +
      '</div></div>';
  }

  h += '<div class="qp-foot"><b>GRACIAS POR CONFIAR EN ADIS</b><br>' +
    'México: +52 631 120 4943 &nbsp;&nbsp;|&nbsp;&nbsp; USA: +1 520 839 2877 &nbsp;&nbsp;|&nbsp;&nbsp; adis-diseño.com &nbsp;&nbsp;|&nbsp;&nbsp; adis.remodelacion@gmail.com<br>' +
    'Nogales, Sonora &nbsp;·&nbsp; Rio Rico, AZ &nbsp;—&nbsp; Creando espacios, reinventando hogares.</div>';
  h += '</div>';
  return h;
}
function renderProposal(){ const el = $('propPreview'); if (el) el.innerHTML = buildProposalHTML(); updateTotalsUI(); }

/* ----- acciones ----- */
function saveProposal(){
  syncFormToProp();
  if (!prop.cliente.trim()) { notice('Falta el nombre del cliente (sección 01).', false); return; }
  if (!(parseFloat(prop.precioFinal) > 0) && !prop.items.some(it => String(it.descripcion).trim())) { notice('Escribe el precio final de la cotización (sección 03).', false); return; }
  const t = calcTotals();
  const datos = Object.assign({}, prop, {
    fotoProyecto: prop.fotoProyecto ? '(foto guardada en el borrador local del navegador)' : '',
    fotos: prop.fotos.map(f => ({ data: f.data ? '(foto en borrador local)' : '', desc: f.desc }))
  });
  apiPost({ tipo:'quote', folio: prop.savedFolio || '', cliente: prop.cliente, telefono: prop.telefono,
    ciudad: prop.ubicacion, proyecto: prop.proyecto, ubicacion: prop.ubicacion, moneda: prop.moneda,
    cliente_id: prop.clienteId || '',
    items: prop.items.map(it => ({ codigo: it.codigo, descripcion: it.descripcion, cantidad: it.cantidad, unidad: it.unidad, precio: it.precio })),
    subtotal: t.subtotal, iva: t.iva, total: t.total, notas: prop.especificaciones.slice(0, 500), datos: datos })
    .then(d => {
      if (d && d.ok) {
        prop.savedFolio = d.folio || prop.savedFolio;
        notice('Cotización <b>' + esc(prop.savedFolio) + '</b> guardada en Google Sheets.');
        loadQuotes(); renderProposal(); schedulePropDraft();
      } else notice(errMsg(d, 'No se pudo guardar.'), false);
    }).catch(()=>notice('Error de conexión al guardar.', false));
}
/* Blindaje: vuelca el formulario visible en prop, para que el documento / PDF /
   WhatsApp SIEMPRE reflejen lo que hay en pantalla (nunca datos de una
   cotizacion anterior quedados en el borrador del navegador). */
function syncFormToProp(){
  const v = id => { const el = document.getElementById(id); return el ? el.value : ''; };
  prop.cliente = v('pCliente'); prop.telefono = v('pTelefono');
  prop.proyecto = v('pProyecto'); prop.ubicacion = v('pUbicacion');
  prop.fecha = v('pFecha') || prop.fecha; prop.vigencia = parseInt(v('pVigencia')) || 30;
  prop.elaboro = v('pElaboro'); prop.otroTipo = v('pOtroTipo');
  prop.area = v('pArea'); prop.materiales = v('pMateriales');
  prop.descripcion = v('pDescripcion'); prop.moneda = v('pMoneda') || 'MXN';
  prop.precioFinal = v('pPrecioFinal'); prop.costo = v('pCosto');
  prop.especificaciones = v('pEspec'); prop.formaPago = v('pFormaPago');
  prop.tiempoEntrega = v('pTiempoEntrega'); prop.alcanceExtra = v('pAlcanceExtra');
  const chk = id => { const el = document.getElementById(id); return el ? el.checked : true; };
  prop.incluirGarantia = chk('pIncluirGarantia'); prop.incluirLogistica = chk('pIncluirLogistica');
  prop.incluirAceptacion = chk('pIncluirAceptacion');
  const grid = document.getElementById('pTipos');
  if (grid) {
    const boxes = grid.querySelectorAll('input[type=checkbox]');
    prop.tipos = [];
    boxes.forEach((b, i) => { if (b.checked && TIPOS_PROYECTO[i]) prop.tipos.push(TIPOS_PROYECTO[i]); });
  }
}
async function descargarPDF(){
  syncFormToProp();
  if (!(parseFloat(prop.precioFinal) > 0) && !calcTotals().total) { notice('Escribe el precio final de la cotización (sección 03) antes de descargar.', false); return; }
  try {
    notice('Generando PDF…');
    await cargarPdfLibs();
    const doc = await buildProposalPDF();
    const folio = prop.savedFolio || qpFolio();
    doc.save('Propuesta-ADIS-' + String(folio).replace(/[^A-Za-z0-9-]/g, '') + '.pdf');
    notice('PDF descargado.', true);
  } catch (e) { notice('No se pudo generar el PDF (revisa tu conexión).', false); }
}
function printProposal(){
  syncFormToProp();
  $('printArea').innerHTML = buildProposalHTML();
  document.body.classList.add('imprimiendo');
  const limpiar = ()=>document.body.classList.remove('imprimiendo');
  window.onafterprint = limpiar;
  setTimeout(()=>{ window.print(); setTimeout(limpiar, 2000); }, 80);
}

/* Normaliza un telefono a formato internacional para que funcione wa.me:
   10 digitos = Mexico (+52) · 11 empezando en 1 = EEUU · ya con lada = igual */
function waNum(tel){
  let d = String(tel || '').replace(/\D/g, '');
  if (d.indexOf('00') === 0) d = d.slice(2);
  if (d.length === 12 && d.indexOf('521') === 0) return '52' + d.slice(3);
  if (d.length === 12 && d.indexOf('52') === 0) return d;
  if (d.length === 11 && d.charAt(0) === '1') return d;
  if (d.length === 10) return '52' + d;
  return d;
}

/* Carga perezosa de jsPDF + html2canvas (solo cuando se va a generar PDF) */
function cargarScriptCDN(src){
  return new Promise(function(res, rej){
    const s = document.createElement('script');
    s.src = src;
    s.onload = function(){ res(); };
    s.onerror = function(){ rej(new Error('Sin conexion al CDN: ' + src)); };
    document.head.appendChild(s);
  });
}
function cargarJsPDF(){
  if (window.jspdf && window.jspdf.jsPDF) return Promise.resolve(window.jspdf.jsPDF);
  return cargarScriptCDN('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js')
    .then(function(){ if (window.jspdf && window.jspdf.jsPDF) return window.jspdf.jsPDF; throw new Error('jsPDF no cargo'); });
}
let __pdfLibs = null;
function cargarPdfLibs(){
  if (!__pdfLibs) __pdfLibs = Promise.all([
    cargarJsPDF(),
    window.html2canvas ? Promise.resolve() : cargarScriptCDN('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js')
  ]);
  return __pdfLibs;
}

/* Busca cortes de pagina en filas casi en blanco (para no partir texto/fotos).
   protegidos: rangos Y que NO se pueden cortar (bloques que deben quedar juntos). */
function cortesDePaginaPDF(canvas, pagePx, protegidos){
  try {
    const ctx = canvas.getContext('2d');
    const cortes = [];
    let y = 0;
    while (y + pagePx < canvas.height) {
      const limite = y + pagePx;
      const margen = Math.floor(pagePx * 0.12);
      const datos = ctx.getImageData(0, limite - margen, canvas.width, margen).data;
      let mejor = limite, mejorScore = -1;
      for (let fila = margen - 1; fila >= 0; fila--) {
        let blancos = 0, total = 0;
        for (let x = 0; x < canvas.width; x += 4) {
          const k = (fila * canvas.width + x) * 4;
          total++;
          if (datos[k] > 238 && datos[k+1] > 238 && datos[k+2] > 238) blancos++;
        }
        const score = blancos / total;
        if (score > mejorScore) { mejorScore = score; mejor = limite - margen + fila; }
        if (score > 0.995) break;
      }
      // Keep-together: jamas cortar dentro de un bloque protegido (fotos, firmas)
      for (let p = 0; p < protegidos.length; p++) {
        const r = protegidos[p];
        if (mejor > r.y0 && mejor < r.y1) {
          if (r.y0 > y + pagePx * 0.3) mejor = r.y0; // cortar justo antes del bloque
          else mejor = r.y1;                          // o justo despues
        }
      }
      if (mejor <= y) mejor = limite; // seguridad anti-bucle
      cortes.push(mejor);
      y = mejor;
    }
    return cortes;
  } catch (e) { return []; }
}

/* Genera el PDF desde el MISMO documento completo de la vista previa / impresion
   (secciones 01-09, fotos, garantia, logistica, firmas) — nunca un resumen. */
async function buildProposalPDF(){
  const jsPDF = window.jspdf.jsPDF;
  let holder = document.getElementById('pdfRenderHolder');
  if (!holder) {
    holder = document.createElement('div');
    holder.id = 'pdfRenderHolder';
    holder.style.cssText = 'position:fixed;left:-10000px;top:0;width:820px;background:#fff;z-index:-1;';
    document.body.appendChild(holder);
  }
  holder.innerHTML = buildProposalHTML();
  await new Promise(function(r){ setTimeout(r, 250); }); // deja cargar fuentes e imagenes
  const canvas = await window.html2canvas(holder.firstElementChild, { scale: 2, backgroundColor: '#ffffff', useCORS: true, logging: false });
  const rootEl = holder.firstElementChild;
  const M = 10, PW = 215.9, PH = 279.4, W = PW - 2 * M, H = PH - 2 * M;
  const doc = new jsPDF({ unit: 'mm', format: 'letter' });
  const pagePx = Math.max(1, Math.floor(canvas.width * H / W));
  // Bloques que deben quedar JUNTOS en una pagina: fotos de productos y firmas.
  // Se miden ANTES de limpiar el holder (fuera del DOM los rects dan 0).
  const escala = canvas.width / rootEl.offsetWidth;
  const rootTop = rootEl.getBoundingClientRect().top;
  const protegidos = [];
  rootEl.querySelectorAll('.qp-fotos, .qp-firmas').forEach(function (el) {
    const r = el.getBoundingClientRect();
    const y0 = (r.top - rootTop) * escala;
    const y1 = (r.bottom - rootTop) * escala;
    if (y1 - y0 < pagePx * 0.85) protegidos.push({ y0: y0, y1: y1 });
  });
  holder.innerHTML = '';
  const cortes = cortesDePaginaPDF(canvas, pagePx, protegidos);
  const trozos = cortes.concat([canvas.height]);
  let y0 = 0, first = true;
  for (let i = 0; i < trozos.length; i++) {
    const sliceH = trozos[i] - y0;
    if (sliceH <= 0) continue;
    const c2 = document.createElement('canvas');
    c2.width = canvas.width; c2.height = sliceH;
    c2.getContext('2d').drawImage(canvas, 0, y0, canvas.width, sliceH, 0, 0, canvas.width, sliceH);
    if (!first) doc.addPage();
    doc.addImage(c2.toDataURL('image/jpeg', 0.92), 'JPEG', M, M, W, sliceH * W / canvas.width);
    y0 = trozos[i];
    first = false;
  }
  return doc;
}
async function sendProposalWhatsApp(){
  syncFormToProp();
  const t = calcTotals();
  const dest = waNum(prop.telefono) || CONFIG.WHATSAPP;
  const folio = prop.savedFolio || qpFolio();
  let txt = '*PROPUESTA ADIS ' + folio + '*\n';
  txt += 'Cliente: ' + (prop.cliente || '-') + '\n';
  if (prop.proyecto) txt += 'Proyecto: ' + prop.proyecto + '\n';
  if (prop.ubicacion) txt += 'Ubicacion: ' + prop.ubicacion + '\n';
  txt += 'Inversion total: ' + fmtMoney(t.total) + ' ' + prop.moneda + (t.iva > 0 ? ' (IVA incluido)' : '') + '\n';
  txt += 'Vigencia: ' + (prop.vigencia || 30) + ' dias\n\n';
  txt += 'Te adjunto la propuesta completa en PDF con el detalle, fotos y condiciones. Quedo atento(a) a tus comentarios!';
  // Hibrido: en movil el PDF va ADJUNTO en el menu Compartir (eliges WhatsApp -> contacto);
  // en computadora se descarga el PDF y se abre el chat directo al numero con el mensaje.
  const esMovil = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
  try {
    await cargarPdfLibs();
    const doc = await buildProposalPDF();
    const nombre = 'Propuesta-ADIS-' + String(folio).replace(/[^A-Za-z0-9-]/g, '') + '.pdf';
    if (esMovil && navigator.canShare) {
      const blob = doc.output('blob');
      const file = new File([blob], nombre, { type: 'application/pdf' });
      if (navigator.canShare({ files: [file] })) {
        await navigator.share({ files: [file], text: txt, title: 'Propuesta ADIS ' + folio });
        return;
      }
    }
    doc.save(nombre);
    notice('PDF descargado. Adjuntalo en el chat de WhatsApp que se abre ahora.', true);
  } catch (e) {
    if (e && e.name === 'AbortError') return; // el usuario cancelo el menu Compartir
    notice('No se pudo generar el PDF; se abre WhatsApp con el mensaje de todos modos.', false);
  }
  window.open('https://wa.me/' + dest + '?text=' + encodeURIComponent(txt), '_blank');
}
function loadProposalFromQuote(idx){
  const q = quotesCache[idx];
  if (!q || !q.datos) { notice('Esta cotización no tiene datos completos para cargar (guárdala de nuevo con el Cotizador).', false); return; }
  try {
    const d = JSON.parse(q.datos);
    if (!d || !d.items) throw 0;
    prop = Object.assign(defaultProp(), d);
    prop.savedFolio = q.folio || prop.savedFolio;
    prop.clienteId = q.cliente_id || prop.clienteId || '';
    renderTiposChk(); applyPropToForm(); renderItemRows(); renderFotoProy(); renderFotosGrid(); renderProposal(); schedulePropDraft();
    showTab('proposal');
    notice('Cotización ' + (q.folio || '') + ' cargada en el editor. Las fotos se conservan en el borrador local.');
  } catch (e) { notice('No se pudo leer la cotización guardada.', false); }
}
function newProposal(){
  if (!confirma('newprop', 'Empezar una cotización nueva (se limpia el formulario; lo guardado en Sheets no se toca).')) return;
  prop = defaultProp();
  try { localStorage.removeItem('adis_prop_draft'); } catch (e) {}
  renderTiposChk(); applyPropToForm(); renderItemRows(); renderFotoProy(); renderFotosGrid(); renderProposal();
}

