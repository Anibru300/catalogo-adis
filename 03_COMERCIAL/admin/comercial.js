/* ---------- leads ---------- */
let leadsCache = [];
function loadLeads(){
  apiGet('leads').then(data=>{
    if (!data || !data.ok) { $('leadsTable').innerHTML='<tr><td colspan="9" class="muted">Sin acceso o error de conexión.</td></tr>'; return; }
    leadsCache = data.leads || [];
    $('leadsCount').textContent = leadsCache.length + ' registro(s)';
    if (!leadsCache.length) { $('leadsTable').innerHTML='<tr><td colspan="9" class="muted">Aún no hay contactos del formulario.</td></tr>'; return; }
    $('leadsTable').innerHTML = leadsCache.slice().reverse().map((l,i)=>{
      const rev = leadsCache.length - 1 - i;
      return '<tr><td>'+esc(l.fecha)+'</td><td>'+esc(l.nombre)+'</td><td>'+esc(l.telefono)+'</td><td>'+esc(l.email)+'</td>' +
      '<td>'+esc(l.ciudad)+'</td><td>'+esc(l.metros)+'</td><td>'+esc(l.producto)+'</td><td>'+esc(l.mensaje)+'</td>' +
      '<td style="white-space:nowrap;"><a class="btn btn-sm" target="_blank" href="https://wa.me/'+esc(waNum(l.telefono))+'">WA</a> ' +
      '<button class="btn btn-sm" title="Convertir en cliente" onclick="convertLead('+rev+')">→ Cliente</button></td></tr>';
    }).join('');
  }).catch(()=>{ $('leadsTable').innerHTML='<tr><td colspan="9" class="muted">Error de conexión.</td></tr>'; });
}

/* ---------- clientes (FASE 3) ---------- */
let clientesCache = [];
function loadClientes(){
  apiGet('clientes').then(d=>{
    if (!d || !d.ok) { $('cliTable').innerHTML='<tr><td colspan="6" class="muted">Sin acceso.</td></tr>'; return; }
    clientesCache = d.clientes || [];
    $('cliCount').textContent = clientesCache.length + ' cliente(s)';
    fillSaleLinks();
    if (!clientesCache.length) { $('cliTable').innerHTML='<tr><td colspan="6" class="muted">Sin clientes todavía. Convierte un contacto o crea uno.</td></tr>'; return; }
    $('cliTable').innerHTML = clientesCache.map(c=>
      '<tr><td>'+esc(c.nombre)+'</td><td>'+esc(c.telefono||'—')+'</td><td>'+esc(c.email||'—')+'</td>' +
      '<td>'+esc(c.ciudad||'—')+'</td><td>'+(c.origen==='lead'?'Formulario':'Manual')+'</td>' +
      '<td><button class="btn btn-danger btn-sm" onclick="deleteCliente(\''+c.id+'\')">✕</button></td></tr>').join('');
  }).catch(()=>{ $('cliTable').innerHTML='<tr><td colspan="6" class="muted">Error de conexión.</td></tr>'; });
}
function showClienteForm(){
  $('cliForms').innerHTML = '<div class="card-box"><div class="row">' +
    '<div><label>Nombre *</label><input id="cNombre"></div>' +
    '<div><label>Teléfono</label><input id="cTel"></div>' +
    '<div><label>Email</label><input id="cEmail"></div>' +
    '<div><label>Ciudad</label><input id="cCiudad"></div>' +
    '</div><label>Notas / dirección</label><input id="cNotas">' +
    '<div class="toolbar" style="margin-top:1rem;"><button class="btn btn-solid btn-sm" onclick="saveCliente()">💾 Guardar</button> ' +
    '<button class="btn btn-sm" onclick="$(\'cliForms\').innerHTML=\'\'">Cancelar</button></div></div>';
}
function saveCliente(datos){
  const d = datos || { nombre:$('cNombre').value.trim(), telefono:$('cTel').value.trim(),
    email:$('cEmail').value.trim(), ciudad:$('cCiudad').value.trim(), notas:$('cNotas').value.trim(), origen:'manual' };
  if (!d.nombre) { notice('El cliente necesita nombre.', false); return; }
  apiPost({tipo:'save_cliente', nombre:d.nombre, telefono:d.telefono||'', email:d.email||'',
    ciudad:d.ciudad||'', notas:d.notas||'', origen:d.origen||'manual'}).then(r=>{
    notice(r&&r.ok?'Cliente guardado.':errMsg(r,'No se pudo guardar.'), !!(r&&r.ok));
    if(r&&r.ok){ $('cliForms').innerHTML=''; loadClientes(); }
  }).catch(()=>notice('Error de conexión.', false));
}
function convertLead(idx){
  const l = leadsCache[idx];
  if (!l) return;
  if (!confirma('lead-'+idx, 'Convertir a '+l.nombre+' en cliente (se crea en el directorio; el contacto se conserva como histórico).')) return;
  saveCliente({ nombre:l.nombre, telefono:l.telefono, email:l.email, ciudad:l.ciudad, notas:'Convertido desde lead: '+(l.producto||''), origen:'lead' });
}
function deleteCliente(id){
  if (!confirma('cli-'+id, 'Desactivar este cliente (su historial de cotizaciones no se toca).')) return;
  apiPost({tipo:'delete_cliente', id}).then(d=>{
    notice(d&&d.ok?'Cliente desactivado.':errMsg(d), !!(d&&d.ok));
    if(d&&d.ok) loadClientes();
  });
}

