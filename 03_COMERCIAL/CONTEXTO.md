# 👥 03_COMERCIAL — Leads y Clientes

> NIVEL 2 · Lee primero `00_CORE/CONTEXTO_GLOBAL.md` (§4 auth: endpoints públicos).
> Es el módulo con **superficie pública** (formulario del sitio). Fuente:
> `admin/index.html`, `admin/apps-script.gs`, `generar_web.py` (formulario),
> `scripts/auditoria/test_fase3_api.py`.

## IDENTIDAD

- **Objetivo**: captar y gestionar el pipeline comercial: lead que entra por el
  sitio → prospecto gestionado → cliente del directorio que alimenta cotizaciones
  y proyectos.
- **Responsabilidad**: hojas Leads y Clientes; tabs `leads` y `clientes`.
- **Problema que resuelve**: hoy los contactos del sitio se pierden en WhatsApp;
  este módulo los centraliza y los convierte en clientes sin recapturar datos.

## ALCANCE

- **Hace**: recepción pública de leads (honeypot anti-spam), listado de leads,
  conversión lead→cliente, directorio de clientes (CRUD).
- **NO hace**: cotizar (04), proyectos (05), seguimiento/estados de lead
  (no existe aún — pendiente de producto).
- **Pertenecen aquí**: hojas Leads, Clientes; formulario de contacto del sitio
  (vive en `10_SITIO_PUBLICO`, pero **alimenta a este módulo**).

## DATOS

- **Hojas**: `Leads` (fecha, nombre, telefono, email, ciudad, metros, producto,
  mensaje, pagina, idioma), `Clientes` (ENC_CLIENTES: id, nombre, telefono, email,
  ciudad, direccion, notas, **origen**, fecha, activo). Esquemas: `apps-script.gs`
  L96 (ENC_RESENAS no), L98.
- **Consume**: payload del formulario público (`lead`); datos de lead para convertir.
- **Genera**: filas Leads (alta pública), filas Clientes (con `origen: 'lead'` al
  convertir).

## DEPENDENCIAS

- **DEPENDE DE**: `00_CORE` (auth público del endpoint `lead`).
- **ALIMENTA A**: `04_COTIZADOR` (cliente seleccionable en cotización;
  `matchLead` en el cotizador relaciona lead con cliente), `05_PROYECTOS`
  (cliente del proyecto).
- **COMPARTE CON**: `09_MARKETING` (el lead entra desde el sitio) y
  `10_SITIO_PUBLICO` (formulario).

## REGLAS DE NEGOCIO

1. El endpoint `lead` es **público** y protegido solo por honeypot (`empresa`) —
   no agregar datos sensibles a su respuesta.
2. Convertir lead **copia** los datos a Clientes; el lead original se conserva
   (Leads ∈ HOJAS_BORRABLES: se puede borrar la fila, no el cliente creado).
3. Clientes usan baja lógica (`activo=no`).

## API / BACKEND

| Endpoint | Tipo | Detalle |
|---|---|---|
| `lead` | POST **público** | `{nombre, telefono, email, ciudad, metros, producto, mensaje, pagina, idioma, empresa(honeypot)}` → append Leads |
| `leads` | GET | Lista de leads (token) |
| `clientes` | GET | Directorio (token) |
| `save_cliente` | POST | Crear/editar cliente |
| `delete_cliente` | POST | Baja lógica |

- Handlers: `apps-script.gs` L799–806 (lead), L608–610, L1361–1397.
- Errores: `VALIDACION`.

## FRONTEND (tabs `leads`, `clientes`)

- **Vistas**: tabla de leads con botón convertir; tabla del directorio con CRUD.
- **Funciones clave**: `loadLeads` L1254, `loadClientes` L1272, `showClienteForm`
  L1285, `saveCliente` L1295, `convertLead` L1305, `deleteCliente` L1311.
- **Formulario público**: `generar_web.py` `generate_contacto()` L6935 (envía a
  `LEADS_URL` + abre WhatsApp; honeypot `cfEmpresa`).

## PERMISOS

- **Público**: solo `lead` (crear). **Token admin**: consultar/crear/modificar/
  eliminar leads y clientes. Sin roles.

## ARCHIVOS

| Archivo | Responsabilidad |
|---|---|
| `admin/index.html` L1254–1319 | UI leads + clientes |
| `admin/apps-script.gs` L799–806, L1361–1397 | handlers lead/clientes |
| `generar_web.py` L6935 (`generate_contacto`) | formulario público que alimenta el módulo |
| `scripts/auditoria/test_fase3_api.py` | suite API |

## INTEGRACIONES

- Google Sheets · Apps Script · sitio público (formulario→`lead`) · 04_COTIZADOR
  (consume clientes y matchea leads) · 05_PROYECTOS (cliente_id).

## QUÉ NO MODIFICAR

- El contrato del endpoint público `lead` (lo llama el sitio en producción;
  cambiarlo exige regenerar y publicar el sitio).
- Honeypot `empresa` — no quitar sin reemplazo anti-spam.
- ENC_CLIENTES: agregar columnas solo al final.

## PRUEBAS

- `python scripts/auditoria/test_fase3_api.py` (tras redeploy).
- Casos críticos: lead con honeypot lleno = rechazado; convertir lead conserva
  teléfono/email; cliente duplicado controlado.
- Tras modificar: suite fase3 + regresión fase0 + verificar formulario del sitio
  (generar y probar envío).

## EJEMPLOS DE INTERACCIÓN

1. **Lead entra del sitio (10→03)**: usuario envía formulario → POST `lead` →
   fila en Leads con `pagina` e `idioma` → aparece en el tab Leads del panel.
2. **Convertir (03→04)**: `convertLead(idx)` crea Cliente con `origen='lead'` →
   el cliente queda seleccionable en el cotizador (`productOptionsHTML`/
   selector de cliente del cotizador).
3. **Cliente → proyecto (03→05)**: `save_proyecto` recibe `cliente_id` del
   directorio.
