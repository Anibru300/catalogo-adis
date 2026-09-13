# 📚 Análisis de documentación legacy — validez y migración (2026-09-13)

> Resultado del punto 7 del encargo: qué se conserva, qué queda histórico y a
> dónde migró cada información válida. **El código es la fuente de verdad.**

## docs/ADMIN_ARCHITECTURE.md (Fase 0, 2026-09-06) → ⚠️ HISTÓRICO

| Sección | Estado | Destino de la información válida |
|---|---|---|
| §1 Visión 3 capas | ✅ Válida | `00_CORE/CONTEXTO_GLOBAL.md` §1 |
| §2 Endpoints | ⚠️ Desactualizada (faltan ~20 handlers de fases 2–6, `admin_purge`, `recibir_oc`, `registrar_cobro`, `anular_venta`…) | Reemplazada por las tablas API de cada `CONTEXTO.md` (extraídas del código) |
| §3 Esquemas de hojas | ⚠️ Desactualizada (los ENC_* reales difieren: Clientes tiene `origen`; existen Recepciones; Proyectos tiene `cliente`/`cotizacion_folio`) | Fuente oficial ahora: `ENC_*` en `apps-script.gs` L79–106, resumido en `CONTEXTO_GLOBAL.md` §6 |
| §4 Folios | ⚠️ Incompleta (faltan LOTE-, OC-, PRY- con año, COB-) | `CONTEXTO_GLOBAL.md` §7 (completa, desde código) |
| §5 Regla de inventario | ✅ Válida (regla central intacta) | `CONTEXTO_GLOBAL.md` §3.1 (fuente oficial única) |
| §6 Reglas financieras | ✅ Válida (moneda dual, utilidad al vender) | `CONTEXTO_GLOBAL.md` §8 |
| §7 Integridad transaccional | ✅ Válida (conLock, compensación) | `CONTEXTO_GLOBAL.md` §9 |
| §8 Seguridad | ✅ Mayormente válida; pendiente rotar ADMIN_CLAVE | `CONTEXTO_GLOBAL.md` §4 |
| §9 Flujos (venta, cotización, movimiento) | ✅ Válidos como concepto | Detalle por módulo en cada CONTEXTO.md (Ejemplos) |
| §10 Puntos de extensión por fase | ⛔ Obsoleto — **las fases 2–6 ya están implementadas** | El estado real está en cada CONTEXTO.md |
| §11 Pruebas | ⚠️ Incompleta (existen test_fase1–6, movimientos_ui/lote, cotizador) | Sección PRUEBAS de cada CONTEXTO.md |
| §12 Operación (build/deploy/redeploy) | ✅ Válida | `CONTEXTO_GLOBAL.md` §13 |

## docs/HANDOFF.md (2026-09-07) → ⚠️ HISTÓRICO

| Contenido | Estado | Destino |
|---|---|---|
| Novedades por sesión (jul–sep 2026) | ✅ Válido como bitácora | Se conserva; las conclusiones permanentes migraron a `CONTEXTO_GLOBAL.md` §14–15 |
| "Push pendiente" | ⛔ Obsoleto (repo limpio y al día, 2026-09-13) | — |
| Pendientes del dueño (rotar clave, reseñas Google, precios reales…) | ⚠️ Parcialmente vigentes | `00_CORE/auth/README.md` (rotación de clave) y `CONTEXTO_GLOBAL.md` §4 |
| Estado general / entorno / comandos | ✅ Válido | `CONTEXTO_GLOBAL.md` §13, §16 |
| Notas de sesiones 2026-07-25 | ✅ Válidas (lecciones visuales/móvil) | `CONTEXTO_GLOBAL.md` §15 |
| Decisiones pendientes | ⚠️ Varias resueltas o transferidas a CONTEXTO de su módulo | Cada módulo documenta su propio estado |

## docs/AUDITORIA_SISTEMA_2026-09-06.md → ✅ HISTÓRICO-CONSULTA

- Validez: el diagnóstico (problemas C.1–C.30) sigue siendo la mejor referencia
  del **porqué** de Fase 0. Los problemas de arquitectura vigentes se
  re-evaluaron en la auditoría modular (2026-09-13) y viven en
  `docs/PROPUESTA_ARQUITECTURA_MODULAR.md` §5.
- No se migra: los planes de fases §E quedaron en gran parte **ejecutados**;
  el estado real está en los CONTEXTO.md.

## docs/RESUMEN.md y docs/RESUMEN_SESION_*.md → ✅ HISTÓRICOS (bitácora)

- Conservar como registro de sesiones. Las lecciones técnicas permanentes ya
  están en `CONTEXTO_GLOBAL.md` §15. Regla futura: rotar, mantener solo los
  3–4 más recientes en `docs/`, el resto puede archivarse.

## docs/GUIA_CONFIGURACION.md (admin/) → ✅ VIGENTE

- Guía de configuración del panel para el dueño; sigue siendo válida y
  referenciada desde el propio admin (`CONFIG` L947).

## docs/PROPUESTA_ARQUITECTURA_MODULAR.md → ✅ VIGENTE (proyecto)

- Es el documento de la migración M1–M6; se actualizará al avanzar cada fase.

## Regla de oro aplicada a partir de ahora

1. **Nunca actualizar los docs marcados HISTÓRICO**; corregir siempre las
   fuentes oficiales (`00_CORE/CONTEXTO_GLOBAL.md`, `MAPA_DEPENDENCIAS.md`,
   `CONTEXTO.md` de cada módulo).
2. Un commit que cambie dependencias, hojas, endpoints o reglas **debe** tocar
   la documentación oficial en el mismo cambio.
3. Si documentación y código contradicen: **el código manda** y se corrige la
   documentación (no al revés).
