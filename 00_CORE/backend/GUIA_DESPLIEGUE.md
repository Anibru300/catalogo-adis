# Guía de despliegue del backend (Apps Script)

Fuente modular: `00_CORE/backend/core.gs` + `09_MARKETING/backend/analitica.gs`.
Artefacto a pegar: `admin/apps-script.gs` (regenerado con `python 50_BUILD/concat_backend.py`).

> ⚠️ La URL del webapp NO debe cambiar nunca. Si cambia, actualizar
> `00_CORE/config/plataforma.json` (`url_backend`) y redeployar el sitio.

## 1. Preparar el artefacto (en la PC, ya automatizado)

```bash
"C:\Users\Carlos\AppData\Local\Programs\Python\Python313\python" 50_BUILD/concat_backend.py
# Validar sintaxis (node no acepta .gs directo):
cp admin/apps-script.gs /tmp/check.js && node --check /tmp/check.js && echo OK
```

Debe imprimir `admin/apps-script.gs regenerado (2 partes, N lineas)` y `OK`.

## 2. (OBLIGATORIO, una sola vez) Configurar credenciales en Script Properties

La clave anterior (`Adisdiseño2026`) estuvo expuesta en el repositorio. El script
ahora lee las credenciales de las **Script Properties** con fallback a los valores
por defecto. Para completar la rotación:

1. Abre el proyecto Apps Script (desde la hoja de cálculo: **Extensiones > Apps Script**).
2. **Configuración del proyecto (⚙️) > Propiedades del script > Agregar propiedad**:
   | Propiedad | Valor |
   |---|---|
   | `ADMIN_USUARIO` | el usuario (ej. `Adis`) |
   | `ADMIN_CLAVE` | **clave nueva, fuerte, que no haya estado en el repo** |
3. Guarda. El fallback deja de usarse en cuanto la propiedad existe.

**Orden seguro (no deja a nadie fuera):**
1. Despliega el nuevo `.gs` (paso 3). El login sigue aceptando la clave vieja (fallback).
2. Crea las Script Properties con la clave nueva.
3. Prueba entrar al panel con la clave nueva.
4. Avisa al usuario del panel y confirma que entró; recién entonces la clave vieja deja de funcionar.

## 3. Desplegar (misma URL)

1. En el editor Apps Script, borra **todo** el contenido del archivo y pega
   **todo** `admin/apps-script.gs`.
2. **Implementar > Administrar implementaciones > lápiz ✏️ (editar) > Versión: Nueva versión > Implementar.**
   - NUNCA uses "Nueva implementación" (cambia la URL y rompe sitio + panel + tests).
3. Verifica la URL: debe seguir siendo la de `plataforma.json`:
   `https://script.google.com/macros/s/AKfycbxq47t5I3eSqPmJ7zCnk47_RlHGfIwov8mcI1tJ92yNVvSsUXHU5Pe7DQ2Nx_h1wPP2/exec`

## 4. Verificación post-despliegue

```bash
cd scripts/auditoria
"C:\Users\Carlos\AppData\Local\Programs\Python\Python313\python" test_fase0_regresion.py
```
Debe dar **19 PASS + 0 errores JS** (hace login real contra el backend desplegado).
Si la clave fue rotada, actualizar la clave en el test (`test_fase0_regresion.py`)
y en cualquier otro script de auditoría que haga login.

## 5. Autorizaciones (si Google las pide)

Al implementar, Google pedirá autorizar el acceso a Sheets/Cache/Lock/Properties.
Usa la cuenta dueña de la hoja (`ing.carlosurbina300`). Si el proyecto pasó por
la pantalla de "app no verificada", usa **Avanzado > Ir a … (no seguro)** — es el
proyecto propio, no un tercero.

## Estado de este despliegue

- Último despliegue conocido: backend monolítico anterior a M5 (equivalente
  funcional al actual; M5 solo reordenó funciones hoisteadas + P4 añadió
  lectura de PropertiesService con fallback).
- Después de aplicar esta guía, el desplegado queda al día con `core.gs` + `analitica.gs`.
