# 📋 Resumen del Proyecto - Catálogo Web ADIS

> **Última actualización:** 18 de mayo de 2026  
> **Repositorio:** https://github.com/Anibru300/catalogo-adis.git  
> **Sitio en vivo:** https://anibru300.github.io/catalogo-adis/

---

## 🏗️ Estructura del Proyecto

```
G:\Mi unidad\ADIS DISEÑO\Pagina\           ← Código fuente del sitio web
G:\Mi unidad\ADIS DISEÑO\CATALOGO FINAL\  ← Catálogo de imágenes fuente
```

### Archivos clave en `Pagina/`
| Archivo | Descripción |
|---------|-------------|
| `generar_web.py` | Script principal. Genera todo el sitio web (HTML, CSS, JSON) desde `CATALOGO FINAL` |
| `generar_pdf.py` | Genera el catálogo PDF (`catalogo_adis.pdf`) con ReportLab |
| `style.css` | Generado automáticamente por `generar_web.py` |
| `products.json` | Catálogo de 250 productos en JSON (para el buscador) |
| `img/` | Imágenes de productos sincronizadas desde `CATALOGO FINAL` |
| `media/` | Videos y fotos de proyectos (Material de Facebook) |

---

## 🚀 Funcionalidades Implementadas

### 1. Sitio Web Estático (GitHub Pages)
- **9 categorías**, **250 productos**, **11 páginas HTML**
- Tema oscuro premium con acentos dorados (`#C5A059`)
- Fondo animado con partículas conectadas (canvas)
- Animaciones de scroll (`reveal` con IntersectionObserver)
- Contador animado de estadísticas (productos, categorías, proyectos, clientes)
- Totalmente responsive (mobile menu, grids adaptables)

### 2. Especificaciones Técnicas Reales (Spec Bars)
- Datos extraídos manualmente de las **23 fichas técnicas** del catálogo
- Diccionario `SPECS_DATA` en `generar_web.py` con specs por subcategoría
- Campos: Material, Dimensiones, Presentación, Garantía, Uso

### 3. Buscador Global Mejorado
- Búsqueda en tiempo real con **debounce** (150ms)
- Busca en nombre, categoría y subcategoría con **scoring**
- **Highlight** de coincidencias en dorado
- **Navegación con teclado**: flechas ↑↓, Enter, Escape
- Shortcut **"/"** para enfocar el buscador desde cualquier página
- Dropdown animado con miniaturas y contador de resultados
- Fuente: archivo `products.json` (250 productos)

### 4. Lightbox / Ampliar Imágenes
- Modal a pantalla completa al hacer clic en cualquier producto
- Cierra con ✕, clic fuera o tecla ESC
- Muestra caption con nombre del producto

### 5. WhatsApp por Producto
- Cada tarjeta tiene botón **"Solicitar Cotización"** (mailto) y **"WhatsApp"**
- WhatsApp abre con mensaje predefinido incluyendo nombre del producto, categoría y subcategoría

### 6. Índice de Subcategorías
- Pills/links de navegación rápida al inicio de cada página de categoría
- Permite compartir links directos: `.../5-paneles-tridimensionales.html#oro`

### 7. SEO y Open Graph
- Meta tags personalizados por página (título, descripción, imagen OG)
- Cada categoría tiene su propia imagen OG
- Twitter Card incluido

### 8. Página de Proyectos (`proyectos.html`)
- Galería antes/después
- Fotos de proyectos reales
- Videos con autoplay/pause basado en visibilidad (IntersectionObserver)

### 9. Chatbot Virtual
- Flotante en esquina inferior izquierda
- Respuestas automáticas: ubicación, fichas técnicas, venta, precios, WhatsApp

### 10. Categorías Estrella Destacadas
- **Lambrin WPC** y **Placas PVC** son las categorías estrella
- Sección exclusiva "⭐ Productos Estrella" en el home
- Tarjetas grandes con borde dorado, resplandor animado y descripciones especiales
- Badge "⭐ Estrella" en el catálogo general y en los heroes de sus páginas

---

## 📱 Contactos y Redes Sociales

| Canal | Valor |
|-------|-------|
| WhatsApp MX | +52 631-192-8993 |
| Teléfono USA | +1 (520) 839-2877 |
| Email | adis.remodelacion@gmail.com |
| Facebook | https://www.facebook.com/p/Adis-Dise%C3%B1o-Remodelaci%C3%B3n-61579849591594/ |
| Ubicación | Nogales, Sonora · Rio Rico, AZ |

---

## 🛠️ Cómo Trabajar con el Proyecto

### Requisitos
- Python 3.11
- Virtual env: `C:\temp\kimi_venv\`
- Tesseract OCR instalado (vía winget): `C:\Program Files\Tesseract-OCR\tesseract.exe`

### Regenerar el sitio web
```powershell
cd "G:\Mi unidad\ADIS DISEÑO\Pagina"
C:\temp\kimi_venv\Scripts\python.exe generar_web.py
```

Esto genera:
- `style.css`
- `index.html`, `contacto.html`, `proyectos.html`
- `1-placas-pvc.html` ... `9-cladding.html`
- `products.json`
- Sincroniza `img/` y `media/`

### Generar el PDF
```powershell
cd "G:\Mi unidad\ADIS DISEÑO\Pagina"
C:\temp\kimi_venv\Scripts\python.exe generar_pdf.py
```

### Subir cambios a GitHub
```powershell
cd "G:\Mi unidad\ADIS DISEÑO\Pagina"
git add -A
git commit -m "descripción del cambio"
git push origin main
```

⚠️ **Si falla el commit** con error de `index.lock`:
```powershell
Remove-Item .git\index.lock -Force
git add -A && git commit -m "..." && git push origin main
```

---

## 📦 Catálogo de Productos

| # | Categoría | Subcategorías | Productos | Ficha Técnica |
|---|-----------|---------------|-----------|---------------|
| 1 | Placas PVC | 3 (madera, texturizadas, espejo) | 34 | ✅ Completa |
| 2 | Lambrin WPC | 5 (interior, exterior, desigual, media luna, media luna PS) | 40 | ⚠️ 2 sin ficha |
| 3 | Revestimiento Flexible | 0 (productos directos) | 6 | ✅ Completa |
| 4 | Plafon PVC | 2 (laminado, wood) | 13 | ✅ Completa |
| 5 | Paneles tridimensionales | 5 (blanco, grises, madera, negro, oro) | 24 | ✅ Completa |
| 6 | Vigas PVC | 2 (interior, exterior) | 15 | ✅ Completa |
| 7 | Pisos | 4 (laminado, WPC, SPC, deck sintético) | 78 | ⚠️ 2 sin ficha |
| 8 | Zacate | 2 (follaje, pasto recreativo) | 29 | ✅ Completa |
| 9 | Cladding | 1 (placa tipo roca) | 11 | ✅ Completa |

**Sin ficha técnica:**
- 2.2 Lambrin Exterior
- 2.3 Desigual
- 7.1 Laminado
- 7.2 WPC

---

## ⚠️ Issues Conocidos

1. **Encoding de consola Windows**: PowerShell a veces muestra caracteres con tilde como `�`, pero los archivos en disco están correctos en UTF-8.
2. **Git `index.lock`**: Ocurre ocasionalmente. Solución: eliminar manualmente antes de commit.
3. **OCR de fichas técnicas**: Tesseract funciona pero con precisión limitada en tablas. La extracción actual fue manual con revisión visual.

---

## 📝 Pendientes del Usuario

- [ ] **Integrar precios** en el chatbot y en las tarjetas de producto (el usuario los proporcionará más tarde)
- [ ] Posiblemente agregar más contenido de Facebook

---

## 💡 Ideas de Mejoras Futuras Discutidas

1. **Carrusel de imágenes** en la sección estrella mostrando los productos más populares
2. **Skeleton loading** mientras carga el buscador
3. **Scroll suave** hasta el producto exacto al hacer clic en un resultado de búsqueda
4. **Testimonios de clientes** en los productos estrella
5. **Comparador de productos** (seleccionar 2-3 y comparar specs lado a lado)
6. **Calculadora de materiales** integrada por categoría
7. **Analytics** (Google Analytics o similar)
8. **Modo claro/oscuro** toggle

---

## 🔧 Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| Generador | Python 3.11 + pathlib |
| PDF | ReportLab |
| OCR | Tesseract 5.4 + pytesseract |
| Hosting | GitHub Pages (gratis) |
| Frontend | HTML5, CSS3 puro, Vanilla JS |
| Fuentes | Google Fonts (Montserrat + Playfair Display) |
| Mapas | Google Maps embed |

---

## 👤 Contexto para Continuar Mañana

Si vas a retomar este proyecto, los puntos más probables de trabajo son:

1. **Agregar precios**: Modificar `SPECS_DATA` y/o crear un diccionario de precios, integrar en `generate_category_page()` y actualizar respuestas del chatbot.
2. **Nuevas fichas técnicas**: Si el usuario agrega fichas faltantes (2.2, 2.3, 7.1, 7.2), transcribirlas a `SPECS_DATA`.
3. **Nuevas imágenes/productos**: Solo ejecutar `python generar_web.py` y `git push`.
4. **Mejoras UX**: Las ideas listadas arriba en "Mejoras Futuras".

El archivo más importante a modificar siempre es **`generar_web.py`**. Todo fluye desde ahí.
