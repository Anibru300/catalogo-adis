window.addEventListener('load', ()=>{
  if (CONFIG.API_URL.indexOf('PEGAR') === 0) {
    $('loginStatus').innerHTML = 'Falta configurar API_URL. Sigue admin/GUIA_CONFIGURACION.md.';
    return;
  }
  if (token) {
    $('loginUser').value = usuario;
    apiGet('me').then(d=>{ if (d && d.ok) enterApp(usuario); else logout(); }).catch(()=>logout());
  }
});
