/* =====================================================================
   CONFIGURACION — Completa estos valores (ver admin/GUIA_CONFIGURACION.md)
   ===================================================================== */
const CONFIG = {
  API_URL: 'https://script.google.com/macros/s/AKfycbxq47t5I3eSqPmJ7zCnk47_RlHGfIwov8mcI1tJ92yNVvSsUXHU5Pe7DQ2Nx_h1wPP2/exec',   // URL de la app web de Apps Script
  LOOKER_STUDIO_URL: '',                    // Enlace de inserción del informe de Looker Studio
  WHATSAPP: '15208392877'
};

let token = sessionStorage.getItem('adis_admin_token') || null;
let usuario = sessionStorage.getItem('adis_admin_user') || '';
let products = [];
let quoteItems = [];
let starRating = 5;

/* ---------- helpers ---------- */
function $(id){ return document.getElementById(id); }
function notice(text, ok=true){
  $('notice').innerHTML = '<div class="msg ' + (ok?'ok':'err') + '">' + text + '</div>';
  setTimeout(()=>{ $('notice').innerHTML=''; }, 5000);
}
function fmtMoney(n){ return '$' + (Number(n)||0).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}); }
function esc(s){ return String(s==null?'':s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
// FASE 0: mensaje de error utilizable venga como string (backend viejo) o como
// objeto {code, message} (backend nuevo). Centraliza el formato para el usuario.
function errMsg(d, fallback){
  if (d && d.error) {
    if (typeof d.error === 'string') return d.error;
    if (d.error.message) return d.error.message;
  }
  return fallback || 'Error. Intenta de nuevo.';
}
// FASE 0: si el backend rechaza el token, avisar y volver al login.
function manejarSesion(d){
  if (d && d.error && typeof d.error === 'object' && d.error.code === 'TOKEN_INVALIDO'){
    notice('Tu sesión expiró. Entra de nuevo.', false);
    setTimeout(logout, 1200);
  }
  return d;
}
function apiGet(action){
  return fetch(CONFIG.API_URL + '?action=' + action + '&token=' + encodeURIComponent(token)).then(r=>r.json()).then(manejarSesion);
}
function apiPost(payload){
  payload.token = token;
  return fetch(CONFIG.API_URL, {method:'POST', headers:{'Content-Type':'text/plain;charset=utf-8'}, body:JSON.stringify(payload)})
    .then(r=>r.json()).then(manejarSesion);
}

/* ---------- autenticacion (usuario/contraseña, validada en el servidor) ---------- */
function login(){
  const u = $('loginUser').value.trim(), p = $('loginPass').value;
  if (!u || !p) { $('loginStatus').textContent = 'Escribe usuario y contraseña.'; return; }
  $('loginStatus').textContent = 'Verificando…';
  fetch(CONFIG.API_URL, {method:'POST', headers:{'Content-Type':'text/plain;charset=utf-8'},
    body: JSON.stringify({tipo:'login', usuario:u, clave:p})})
    .then(r=>r.json())
    .then(d=>{
      if (d && d.ok) {
        token = d.token; usuario = u;
        sessionStorage.setItem('adis_admin_token', token);
        sessionStorage.setItem('adis_admin_user', u);
        enterApp(u);
      } else {
        $('loginStatus').textContent = errMsg(d, 'Usuario o contraseña incorrectos.');
        $('loginPass').value = '';
      }
    })
    .catch(()=>{ $('loginStatus').textContent = 'No se pudo conectar con el servidor.'; });
}
function enterApp(u){
  $('loginView').classList.add('hidden');
  $('appView').classList.remove('hidden');
  $('userEmail').textContent = 'Sesión: ' + u;
  if (CONFIG.LOOKER_STUDIO_URL) {
    $('analyticsBox').innerHTML = '<iframe id="analyticsFrame" src="' + esc(CONFIG.LOOKER_STUDIO_URL) + '" frameborder="0" allowfullscreen></iframe>';
  }
  loadLeads(); loadQuotes(); loadReviewsAdmin(); loadProducts(); loadBiz(); loadClientes();
  initProposal();
  $('sFecha').value = new Date().toISOString().slice(0,10);
  $('gFecha').value = new Date().toISOString().slice(0,10);
  $('pnlMes').value = new Date().toISOString().slice(0,7);
  showTab('dash');
}
function logout(){
  try { apiPost({tipo:'logout'}); } catch(e) {} // FASE 0: revocar token en el servidor (best-effort)
  token = null; usuario = '';
  sessionStorage.removeItem('adis_admin_token');
  sessionStorage.removeItem('adis_admin_user');
  $('appView').classList.add('hidden');
  $('loginView').classList.remove('hidden');
  $('loginPass').value = '';
}

/* ---------- tabs ---------- */
/* ---------- FASE 7: confirmación en dos pasos (sin confirm()) ---------- */
const _confPend = new Set();
function confirma(key, msg){
  if (_confPend.has(key)) { _confPend.delete(key); return true; }
  _confPend.add(key);
  notice(msg + ' — vuelve a hacer clic para CONFIRMAR.', true);
  setTimeout(()=>_confPend.delete(key), 5000);
  return false;
}

