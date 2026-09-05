# Guía de configuración — Leads, Reseñas, Panel de administración y Cotizador

> ⚠️ **ACTUALIZACIÓN (septiembre 2026):** el panel ahora incluye el **Cotizador profesional**
> (propuestas con el formato ADIS, folio automático y fotos). Para que funcione el guardado:
> abre Apps Script → pega de nuevo el código de `admin/apps-script.gs` → Guardar →
> **Implementar → Administrar implementaciones → ✏️ (editar) → Nueva versión → Implementar**.
> La URL no cambia; todo lo que ya tenías sigue igual.

> Todo se apoya en **Google Sheets + Apps Script** (gratis, sin servidores, sin contraseñas de terceros).
> Tiempo estimado: **15-20 minutos**. Solo hay que hacerlo una vez.

---

## Paso 1 — Crear la hoja de Google (la "base de datos")

1. Entra a <https://sheets.new> con la cuenta de ADIS (`adis.remodelacion@gmail.com`).
2. Ponle nombre: **ADIS — Leads y Cotizaciones**.
3. No necesitas crear pestañas: el script las crea solo (Leads, Cotizaciones, Reseñas).
4. Copia el **ID** de la hoja de la URL (el código largo entre `/d/` y `/edit`). Lo necesitarás en el Paso 3.

---

## Paso 2 — Pegar el script

1. En la hoja: **Extensiones → Apps Script**.
2. Borra todo el contenido del archivo `Código.gs` y pega el contenido completo de
   [`admin/apps-script.gs`](apps-script.gs) (está en el proyecto, ábrelo con el bloc de notas).
3. **Cambia las credenciales** en las primeras líneas:
   ```js
   var ADMIN_USUARIO = 'admin';          // tu usuario
   var ADMIN_CLAVE   = 'pon-una-clave-larga-y-segura';
   ```

---

## Paso 3 — Desplegar como aplicación web

1. En Apps Script: **Implementar → Nueva implementación**.
2. Tipo: **Aplicación web** y configura:
   - *Ejecutar como:* **Yo** (la cuenta de la hoja)
   - *Quién tiene acceso:* **Cualquier persona** ← necesario para que el formulario del sitio pueda enviar leads
3. Presiona **Implementar** → autoriza los permisos (Google mostrará una advertencia de "app no verificada": **Opciones avanzadas → Ir a…** → permitir).
4. Copia la **URL de la aplicación web** (termina en `/exec`).

> ⚠️ Si más adelante editas el script, debes volver a **Implementar → Administrar implementaciones → editar → Nueva versión** para que los cambios surtan efecto.

---

## Paso 4 — Conectar el sitio web y el panel

Dame la URL `/exec` y yo la pongo en los 3 lugares (o hazlo tú):

| Archivo | Variable |
|---|---|
| `generar_web.py` (arriba, sección CONFIGURACIÓN) | `LEADS_URL` y `REVIEWS_URL` |
| `admin/index.html` (bloque `CONFIG` al final) | `API_URL` |

Después: regenerar el sitio y subir a GitHub:
```bash
cd C:\Users\Carlos\Desktop\Pagina
"C:\Users\Carlos\AppData\Local\Programs\Python\Python313\python" generar_web.py
git add -A && git commit -m "feat: captacion de leads, reseñas en vivo y panel admin" && git push origin main
```

## Cómo queda todo funcionando

- **Captación de leads:** cada envío del formulario de contacto guarda una fila en la pestaña **Leads** (y sigue abriendo WhatsApp como antes).
- **Reseñas:** desde el panel publicas reseñas (copiadas de Google) y aparecen en la sección de testimonios de todo el sitio. Botón "WA" por lead para contactar al cliente al instante.
- **Panel de administración:** entra a `https://adis-diseño.com/admin.html` con tu usuario y contraseña. Ahí ves leads, creas cotizaciones (imprimibles/PDF y enviables por WhatsApp), gestionas reseñas y las estadísticas.

---

## El panel también es tu mini-ERP (ya incluido)

El mismo panel administra el negocio. Todas estas pestañas se crean solas en la hoja de Google:

| Pestaña | Función |
|---|---|
| 📦 **Inventario** | Productos con costo/precio, stock por almacén, alertas de stock mínimo, movimientos (entradas/salidas/ajustes) |
| 💵 **Ventas** | Registrar ventas — descuenta stock automáticamente y calcula la utilidad por venta |
| 📉 **Gastos** | Gastos por categoría (renta, luz, nómina...) en MXN o USD |
| 📊 **Resultados** | Estado de resultados mensual completo: ventas − costos − gastos = utilidad neta, con márgenes e imprimible |

- **Moneda dual:** en ⚙ Moneda (pestaña Inventario) defines la moneda base y el tipo de cambio; todo se convierte automáticamente.
- **Importar tu catálogo:** cuando tengas tu Excel/Sheets de productos con precios y costos, pásamelo y lo importo de una vez (el endpoint `import_productos` ya está listo).

## 📝 Cotizador profesional (formato ADIS)

En la pestaña **Cotizador** del panel armas la propuesta completa, igual que tu formato de Word:

1. **01 Datos:** cliente (si ya es lead, teléfono y ciudad se rellenan solos), proyecto, ubicación, fecha y vigencia.
2. **02 Alcance:** sube la **foto o render del proyecto**, marca el tipo de proyecto (casillas), área, materiales y descripción.
3. **03 Desglose:** elige cada producto de una **lista desplegable del catálogo** — código, descripción y unidad se rellenan solos; captura la cantidad y el precio. Subtotal, IVA (16%, se puede quitar) e **inversión total se calculan solos**. Moneda MXN o USD.
4. **04 Fotos de productos:** sube hasta 6 fotos con su descripción.
5. **05-06:** especificaciones técnicas, forma de pago y tiempo de entrega.
6. Las secciones de **garantía, logística premium y firmas** salen automáticas (se pueden quitar con sus casillas).

**Botones de arriba:**
- 💾 **Guardar** → la cotización se guarda en Google Sheets con **folio automático** (ADIS-2026-001, 002...).
- 🖨️ **Descargar PDF** → el documento se ve exactamente como tu formato de Word, listo para imprimir o mandar por correo.
- 🟢 **WhatsApp** → envía un resumen (folio, proyecto y total) al teléfono del cliente.
- 📂 **Cargar** (en "Cotizaciones guardadas") → reabre cualquier cotización en el editor para ajustarla y volverla a guardar.

> 💡 Todo lo que escribes queda guardado automáticamente como borrador en el navegador:
> si cierras el panel y vuelves a entrar, tu cotización sigue ahí (incluidas las fotos).
> Las fotos van **incrustadas en el PDF**; en la hoja de Google se guardan los datos y partidas.

---

## Paso 5 — Seguridad y ocultamiento del panel

Ya está hecho en el código, pero conviene saberlo:

- El panel **no está enlazado en ninguna parte del sitio** (no se puede encontrar navegando).
- `admin.html` tiene `noindex` (Google no lo indexa) y está en `Disallow` del `robots.txt`.
- La contraseña **nunca** viaja al navegador: se valida en el servidor (Apps Script) y solo regresa un *token* de sesión temporal (8 horas).
- La URL directa sigue existiendo (`/admin.html`) — la contraseña es la barrera. Usa una clave larga.
- Los datos del panel (leads/cotizaciones) solo se entregan con sesión válida; el único endpoint público es el de enviar leads y el de leer reseñas publicadas.

---

## Paso 6 — Estadísticas (Google Analytics en el panel)

1. Entra a <https://analytics.google.com> con la cuenta de ADIS y crea la propiedad para `https://xn--adis-diseo-19a.com/` (si ya existe GA4, úsala). Copia el ID de medición (`G-XXXXXXXXXX`).
2. Dámelo y yo lo configuro en `generar_web.py` (la etiqueta ya se inyecta en todas las páginas).
3. Para ver las gráficas **dentro del panel admin**: entra a <https://lookerstudio.google.com> → crear informe → conecta GA4 → **Compartir → insertar informe** → copia el enlace de iframe y pégalo en `LOOKER_STUDIO_URL` dentro de `admin/index.html`.

---

## Paso 7 — Enlace de reseñas de Google

1. Busca "ADIS Diseño y Remodelación Nogales" en Google Maps → tu ficha → **Escribir reseña**.
2. Copia la URL del perfil y pégala en `generar_web.py` → `CONTACTO['google_business_url']` (así el botón "Ver reseñas en Google" lleva directo a tu ficha).

---

## Resumen de lo que hay que hacer (checklist)

- [ ] Crear hoja de Google
- [ ] Pegar `apps-script.gs`, cambiar usuario/clave
- [ ] Desplegar como app web (acceso: cualquier persona)
- [ ] Pasarme la URL `/exec` → yo la conecto al sitio y al panel
- [ ] (Opcional) ID de GA4 → estadísticas en el panel
- [ ] (Opcional) URL de Looker Studio → gráficas dentro del panel
- [ ] (Opcional) URL de la ficha de Google → botón de reseñas
