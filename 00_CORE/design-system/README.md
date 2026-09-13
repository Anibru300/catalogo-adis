# 00_CORE/design-system — Sistema de diseno global

**Estado: pendiente (Fase M1).** Hoy:

- Sitio publico: CSS completo como string en `generar_web.py` L1396-3555 (~2 150 lineas).
  Tokens `:root`: --gold:#C5A059 --gold-light:#E8D5A3 --black:#0F0F0F --dark:#1A1A1A
  --gray:#2A2A2A --light:#F5F5F5 --white:#FFFFFF; tipografia Montserrat.
- Panel admin: CSS propio embebido `admin/index.html` L10-293 (mismas variables base).

**Plan M1**: `tokens.css` + `componentes_publico.css` + `componentes_admin.css` + `UI.md`,
extraidos del generador sin cambiar la salida (verificacion byte-a-byte de public/).
