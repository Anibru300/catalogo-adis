/* ---------- FASE 7: dashboard ejecutivo (Resumen) ---------- */
function loadDash(){
  const hoy = fLocal();
  const mes = hoy.slice(0, 7);
  const desdeMes = hoy.slice(0, 8) + '01';
  $('dashFecha').textContent = hoy;
  $('dashKpis').innerHTML = '<div class="pnl-card"><div class="k">Cargando…</div><div class="v">—</div></div>';
  const getj = url => fetch(url).then(r=>r.json()).catch(()=>null);
  const base = CONFIG.API_URL + '?token=' + encodeURIComponent(token);
  Promise.all([
    getj(base + '&action=estado_resultados&mes=' + mes),
    getj(base + '&action=cxc'),
    getj(base + '&action=cxp'),
    getj(base + '&action=flujo_caja&desde=' + desdeMes + '&hasta=' + hoy),
    getj(base + '&action=alertas'),
    getj(base + '&action=proyectos'),
  ]).then(([pnl, cxc, cxp, flujo, alertas, proys])=>{
    const f = n => fmtMoney(n||0);
    const moneda = (pnl && pnl.moneda_base) || 'MXN';
    const porCobrar = cxc ? Number(cxc.por_cobrar_base)||0 : 0;
    const porPagar = cxp ? Number(cxp.por_pagar_base)||0 : 0;
    const neto = flujo ? Number(flujo.neto)||0 : 0;
    const ventasMes = pnl ? Number(pnl.ingresos)||0 : 0;
    const utilOp = pnl ? Number(pnl.utilidad_operativa != null ? pnl.utilidad_operativa : pnl.utilidad_neta)||0 : 0;
    const margen = pnl ? Number(pnl.margen_operativo != null ? pnl.margen_operativo : pnl.margen_neto)||0 : 0;
    const als = (alertas && alertas.alertas) || [];
    const nCrit = als.filter(a=>a.prioridad==='CRITICA').length;
    const nAlta = als.filter(a=>a.prioridad==='ALTA').length;
    const nProy = proys ? (proys.proyectos||[]).filter(p=>p.estado==='ACTIVO').length : 0;
    $('dashKpis').innerHTML =
      '<div class="pnl-card"><div class="k">Ventas del mes ('+(pnl?pnl.num_ventas:0)+')</div><div class="v">'+f(ventasMes)+' '+moneda+'</div></div>' +
      '<div class="pnl-card '+(utilOp>=0?'good':'bad')+'"><div class="k">Utilidad operativa</div><div class="v">'+f(utilOp)+' <small style="font-size:0.7rem;">'+margen.toFixed(1)+'%</small></div></div>' +
      '<div class="pnl-card '+(porCobrar?'bad':'good')+'"><div class="k">Por cobrar</div><div class="v">'+f(porCobrar)+' '+moneda+'</div></div>' +
      '<div class="pnl-card '+(porPagar?'bad':'good')+'"><div class="k">Por pagar</div><div class="v">'+f(porPagar)+' '+moneda+'</div></div>' +
      '<div class="pnl-card '+(neto>=0?'good':'bad')+'"><div class="k">Flujo neto del mes</div><div class="v">'+f(neto)+' '+moneda+'</div></div>' +
      '<div class="pnl-card '+(nCrit||nAlta?'bad':'good')+'"><div class="k">Alertas</div><div class="v">'+als.length+' <small style="font-size:0.7rem;">'+(nCrit?nCrit+' crítica(s), ':'')+(nAlta?nAlta+' alta(s)':'')+'</small></div></div>' +
      '<div class="pnl-card"><div class="k">Proyectos activos</div><div class="v">'+nProy+'</div></div>';
    const colorP = { CRITICA: '#e37c7c', ALTA: '#e8b96a', MEDIA: '#8ab4e8' };
    $('dashAlertas').innerHTML = als.length
      ? '<strong>Alertas que necesitan atención:</strong><table style="margin-top:0.5rem;"><tbody>' +
        als.slice(0, 8).map(a=>'<tr><td style="white-space:nowrap;"><span style="color:'+(colorP[a.prioridad]||'#e8b96a')+';font-weight:700;font-size:0.7rem;">'+esc(a.prioridad)+'</span></td><td style="font-size:0.85rem;">'+esc(a.detalle)+'</td></tr>').join('') +
        (als.length > 8 ? '<tr><td colspan="2" class="muted">… y '+(als.length-8)+' más. <a href="#" onclick="showTab(\'pnl\'); return false;" style="color:var(--gold);">Ver todas en Resultados</a></td></tr>' : '') +
        '</tbody></table>'
      : '<strong style="color:#7ce3a1;">Todo bajo control.</strong> <span class="muted">Sin alertas de inventario, cobros, pagos ni compras.</span>';
  });
}

