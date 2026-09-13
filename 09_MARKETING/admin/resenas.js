/* ---------- reseñas ---------- */
function renderStars(){
  $('rStars').innerHTML = [1,2,3,4,5].map(n=>'<button class="'+(n<=starRating?'on':'')+'" onclick="starRating='+n+'; renderStars()">⭐</button>').join('');
}
function addReview(){
  const nombre=$('rNombre').value.trim(), texto=$('rTexto').value.trim();
  if (!nombre || !texto) { notice('Faltan el nombre o el texto de la reseña.', false); return; }
  apiPost({tipo:'review', nombre, estrellas:starRating, texto}).then(d=>{
    notice(d && d.ok ? 'Reseña publicada en el sitio.' : 'No se pudo publicar.', !!(d&&d.ok));
    if (d&&d.ok) { $('rNombre').value=''; $('rTexto').value=''; starRating=5; renderStars(); loadReviewsAdmin(); }
  });
}
function loadReviewsAdmin(){
  renderStars();
  apiGet('reviews_admin').then(data=>{
    if (!data || !data.ok) { $('reviewsTable').innerHTML='<tr><td colspan="5" class="muted">Sin acceso.</td></tr>'; return; }
    if (!data.reviews.length) { $('reviewsTable').innerHTML='<tr><td colspan="5" class="muted">Sin reseñas. Publica la primera.</td></tr>'; return; }
    $('reviewsTable').innerHTML = data.reviews.map((r,i)=>
      '<tr><td>'+esc(r.fecha)+'</td><td>'+esc(r.nombre)+'</td><td>'+'⭐'.repeat(Math.max(1,Math.min(5,parseInt(r.estrellas)||5)))+'</td>' +
      '<td>'+esc(r.texto)+'</td><td><button class="btn btn-danger btn-sm" onclick="deleteReview('+(i+2)+',\''+esc(r.id||'')+'\')">✕</button></td></tr>'
    ).join('');
  }).catch(()=>{});
}
function deleteReview(row, id){
  if (!confirma('review-'+id, 'Eliminar esta reseña del sitio.')) return;
  // FASE 0: se envia el ID estable (y la fila como respaldo para el backend viejo)
  apiPost({tipo:'delete_review', row, id: id || ''}).then(d=>{ notice(d&&d.ok?'Reseña eliminada.':errMsg(d,'No se pudo eliminar.'), !!(d&&d.ok)); if(d&&d.ok) loadReviewsAdmin(); });
}

