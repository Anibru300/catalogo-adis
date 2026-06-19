import re

path = r'G:\Mi unidad\ADIS DISEÑO\Pagina\generar_web.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Reemplazar CSS del buscador
old_search_css = '''/* BUSCADOR GLOBAL */
.search-box {
  position: relative; display: flex; align-items: center;
}
.search-box input {
  background: rgba(255,255,255,0.08); border: 1px solid rgba(197,160,89,0.2);
  border-radius: 25px; padding: 0.5rem 2.5rem 0.5rem 1rem;
  color: var(--light); font-family: 'Montserrat', sans-serif; font-size: 0.8rem;
  width: 180px; transition: all 0.3s;
}
.search-box input:focus {
  outline: none; border-color: var(--gold); width: 240px; background: rgba(255,255,255,0.12);
}
.search-box input::placeholder { color: rgba(245,245,245,0.4); }
.search-box button {
  position: absolute; right: 8px; background: none; border: none;
  color: var(--gold); cursor: pointer; font-size: 1rem;
}
.search-dropdown {
  position: absolute; top: calc(100% + 8px); right: 0;
  width: 320px; max-height: 400px; overflow-y: auto;
  background: var(--dark); border: 1px solid rgba(197,160,89,0.3);
  border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.6);
  display: none; z-index: 1001;
}
.search-dropdown.active { display: block; }
.search-item {
  display: flex; align-items: center; gap: 0.8rem;
  padding: 0.7rem 1rem; text-decoration: none;
  border-bottom: 1px solid rgba(197,160,89,0.08);
  transition: background 0.2s;
}
.search-item:hover { background: rgba(197,160,89,0.1); }
.search-item img {
  width: 45px; height: 45px; object-fit: cover; border-radius: 6px;
}
.search-item-info { flex: 1; }
.search-item-name {
  color: var(--white); font-size: 0.8rem; font-weight: 600; display: block;
}
.search-item-cat {
  color: rgba(245,245,245,0.5); font-size: 0.7rem; display: block;
}
.search-empty {
  padding: 1.5rem; text-align: center; color: rgba(245,245,245,0.5); font-size: 0.85rem;
}
@media (max-width: 768px) {
  .search-box input { width: 140px; }
  .search-box input:focus { width: 180px; }
  .search-dropdown { width: 280px; right: -40px; }
}'''

new_search_css = '''/* BUSCADOR GLOBAL */
.search-box {
  position: relative; display: flex; align-items: center;
}
.search-box input {
  background: rgba(255,255,255,0.08); border: 1px solid rgba(197,160,89,0.2);
  border-radius: 25px; padding: 0.5rem 2.5rem 0.5rem 1rem;
  color: var(--light); font-family: 'Montserrat', sans-serif; font-size: 0.8rem;
  width: 180px; transition: all 0.3s;
}
.search-box input:focus {
  outline: none; border-color: var(--gold); width: 260px; background: rgba(255,255,255,0.12);
}
.search-box input::placeholder { color: rgba(245,245,245,0.4); }
.search-box button {
  position: absolute; right: 8px; background: none; border: none;
  color: var(--gold); cursor: pointer; font-size: 1rem;
}
.search-dropdown {
  position: absolute; top: calc(100% + 10px); right: 0;
  width: 360px; max-height: 450px; overflow-y: auto;
  background: rgba(26,26,26,0.98); border: 1px solid rgba(197,160,89,0.25);
  border-radius: 16px; box-shadow: 0 25px 70px rgba(0,0,0,0.7);
  display: none; z-index: 1001; padding: 0.5rem 0;
  backdrop-filter: blur(20px);
}
.search-dropdown.active { display: block; animation: searchPop 0.2s ease-out; }
@keyframes searchPop {
  from { opacity: 0; transform: translateY(-8px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.search-dropdown-header {
  padding: 0.6rem 1rem; font-size: 0.65rem; text-transform: uppercase;
  letter-spacing: 2px; color: rgba(245,245,245,0.4); border-bottom: 1px solid rgba(197,160,89,0.1);
}
.search-item {
  display: flex; align-items: center; gap: 0.9rem;
  padding: 0.75rem 1rem; text-decoration: none;
  border-bottom: 1px solid rgba(197,160,89,0.06);
  transition: all 0.2s; cursor: pointer;
}
.search-item:hover, .search-item.active {
  background: rgba(197,160,89,0.12); border-left: 3px solid var(--gold);
  padding-left: calc(1rem - 3px);
}
.search-item img {
  width: 50px; height: 50px; object-fit: cover; border-radius: 8px;
  border: 1px solid rgba(197,160,89,0.15);
}
.search-item-info { flex: 1; min-width: 0; }
.search-item-name {
  color: var(--white); font-size: 0.82rem; font-weight: 600; display: block;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.search-item-name mark {
  background: rgba(197,160,89,0.3); color: var(--gold); border-radius: 2px; padding: 0 2px;
}
.search-item-cat {
  color: rgba(245,245,245,0.5); font-size: 0.72rem; display: block; margin-top: 2px;
}
.search-empty {
  padding: 2rem; text-align: center; color: rgba(245,245,245,0.5); font-size: 0.85rem;
}
.search-shortcut {
  display: inline-block; padding: 2px 6px; border-radius: 4px;
  background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.15);
  font-size: 0.65rem; color: rgba(245,245,245,0.5); margin-left: 6px;
}
@media (max-width: 768px) {
  .search-box input { width: 140px; }
  .search-box input:focus { width: 200px; }
  .search-dropdown { width: calc(100vw - 40px); right: auto; left: -20px; }
}'''

content = content.replace(old_search_css, new_search_css)

# 2. Reemplazar JS del buscador en generate_footer
old_search_js = '''    <!-- Buscador Global -->
  <script>
    let allProducts = [];
    fetch('products.json')
      .then(r => r.json())
      .then(data => { allProducts = data; })
      .catch(() => { allProducts = []; });

    function doSearch(query, dropdown) {
      if (!query || query.length < 2) { dropdown.classList.remove('active'); return; }
      const q = query.toLowerCase();
      const results = allProducts.filter(p => p.name.toLowerCase().includes(q)).slice(0, 8);
      if (results.length === 0) {
        dropdown.innerHTML = '<div class="search-empty">No se encontraron productos</div>';
      } else {
        dropdown.innerHTML = results.map(p => `
          <a href="${p.url}" class="search-item" onclick="document.getElementById('searchDropdown').classList.remove('active');var m=document.getElementById('searchDropdownMobile');if(m)m.classList.remove('active');">
            <img src="${p.thumb}" alt="${p.name}">
            <div class="search-item-info">
              <span class="search-item-name">${p.name}</span>
              <span class="search-item-cat">${p.category}${p.subcategory ? ' / ' + p.subcategory : ''}</span>
            </div>
          </a>
        `).join('');
      }
      dropdown.classList.add('active');
    }
    function performSearch() {
      const input = document.getElementById('searchInput');
      const dropdown = document.getElementById('searchDropdown');
      doSearch(input.value, dropdown);
    }
    function performSearchMobile() {
      const input = document.getElementById('searchInputMobile');
      const dropdown = document.getElementById('searchDropdownMobile');
      doSearch(input.value, dropdown);
    }
    const sInput = document.getElementById('searchInput');
    const sMobile = document.getElementById('searchInputMobile');
    if (sInput) {
      sInput.addEventListener('input', e => doSearch(e.target.value, 'searchDropdown'));
      sInput.addEventListener('focus', e => doSearch(e.target.value, 'searchDropdown'));
    }
    if (sMobile) {
      sMobile.addEventListener('input', e => doSearch(e.target.value, 'searchDropdownMobile'));
      sMobile.addEventListener('focus', e => doSearch(e.target.value, 'searchDropdownMobile'));
    }
    document.addEventListener('click', function(e) {
      const sdd = document.getElementById('searchDropdown');
      const sdm = document.getElementById('searchDropdownMobile');
      if (sdd && !e.target.closest('.search-box')) sdd.classList.remove('active');
      if (sdm && !e.target.closest('.search-box')) sdm.classList.remove('active');
    });
  </script>'''

new_search_js = '''    <!-- Buscador Global Mejorado -->
  <script>
    (function() {
      let allProducts = [];
      let debounceTimer = null;
      let activeIndex = -1;
      let currentResults = [];
      
      fetch('products.json')
        .then(r => r.json())
        .then(data => { allProducts = data; })
        .catch(() => { allProducts = []; });
      
      function normalize(str) {
        return (str || '').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
      }
      
      function highlight(text, query) {
        const nq = normalize(query);
        const nt = normalize(text);
        let out = '';
        let last = 0;
        let idx = nt.indexOf(nq);
        while (idx >= 0 && nq.length > 0) {
          out += text.slice(last, idx);
          const end = idx + nq.length;
          out += '<mark>' + text.slice(idx, end) + '</mark>';
          last = end;
          idx = nt.indexOf(nq, last);
        }
        out += text.slice(last);
        return out;
      }
      
      function doSearch(query, dropdownId) {
        const dropdown = document.getElementById(dropdownId);
        if (!query || query.length < 2) {
          dropdown.classList.remove('active');
          currentResults = [];
          activeIndex = -1;
          return;
        }
        const q = normalize(query);
        const terms = q.split(/\\s+/).filter(t => t.length > 0);
        
        const scored = allProducts.map(p => {
          const name = normalize(p.name);
          const cat = normalize(p.category);
          const sub = normalize(p.subcategory || '');
          let score = 0;
          for (const t of terms) {
            if (name.startsWith(t)) score += 10;
            else if (name.includes(t)) score += 5;
            if (sub.startsWith(t)) score += 3;
            else if (sub.includes(t)) score += 2;
            if (cat.includes(t)) score += 1;
          }
          return { p, score };
        }).filter(x => x.score > 0).sort((a,b) => b.score - a.score).slice(0, 8);
        
        currentResults = scored.map(x => x.p);
        activeIndex = -1;
        
        if (scored.length === 0) {
          dropdown.innerHTML = '<div class="search-empty">No se encontraron productos</div>';
        } else {
          dropdown.innerHTML = '<div class="search-dropdown-header">' + scored.length + ' resultado' + (scored.length > 1 ? 's' : '') + ' encontrado' + (scored.length > 1 ? 's' : '') + '</div>' +
            scored.map((x, i) => `
              <a href="${x.p.url}" class="search-item" data-index="${i}" onclick="clearSearch()">
                <img src="${x.p.thumb}" alt="${x.p.name}" loading="lazy">
                <div class="search-item-info">
                  <span class="search-item-name">${highlight(x.p.name, query)}</span>
                  <span class="search-item-cat">${x.p.category}${x.p.subcategory ? ' / ' + x.p.subcategory : ''}</span>
                </div>
              </a>
            `).join('');
        }
        dropdown.classList.add('active');
      }
      
      window.clearSearch = function() {
        const dd = document.getElementById('searchDropdown');
        const dm = document.getElementById('searchDropdownMobile');
        if (dd) dd.classList.remove('active');
        if (dm) dm.classList.remove('active');
      };
      
      function setupInput(inputId, dropdownId) {
        const input = document.getElementById(inputId);
        if (!input) return;
        input.addEventListener('input', e => {
          clearTimeout(debounceTimer);
          debounceTimer = setTimeout(() => doSearch(e.target.value, dropdownId), 150);
        });
        input.addEventListener('focus', e => doSearch(e.target.value, dropdownId));
        input.addEventListener('keydown', e => {
          if (e.key === 'ArrowDown') {
            e.preventDefault();
            activeIndex = Math.min(activeIndex + 1, currentResults.length - 1);
            updateActive(dropdownId);
          } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            activeIndex = Math.max(activeIndex - 1, -1);
            updateActive(dropdownId);
          } else if (e.key === 'Enter') {
            e.preventDefault();
            if (activeIndex >= 0 && currentResults[activeIndex]) {
              window.location.href = currentResults[activeIndex].url;
              clearSearch();
            }
          } else if (e.key === 'Escape') {
            clearSearch();
            input.blur();
          }
        });
      }
      
      function updateActive(dropdownId) {
        const dropdown = document.getElementById(dropdownId);
        if (!dropdown) return;
        dropdown.querySelectorAll('.search-item').forEach((el, i) => {
          el.classList.toggle('active', i === activeIndex);
        });
        const active = dropdown.querySelector('.search-item.active');
        if (active) active.scrollIntoView({ block: 'nearest' });
      }
      
      setupInput('searchInput', 'searchDropdown');
      setupInput('searchInputMobile', 'searchDropdownMobile');
      
      // Shortcut "/" para enfocar buscador
      document.addEventListener('keydown', e => {
        if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
          e.preventDefault();
          const inp = document.getElementById('searchInput');
          if (inp) { inp.focus(); }
        }
      });
      
      document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-box')) clearSearch();
      });
    })();
  </script>'''

content = content.replace(old_search_js, new_search_js)

# 3. Actualizar placeholder del input para mencionar shortcut
content = content.replace(
    'placeholder="Buscar producto..." autocomplete="off">',
    'placeholder="Buscar producto..." autocomplete="off" title="Presiona / para buscar">'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Buscador mejorado aplicado')
