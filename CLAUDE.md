# CLAUDE.md — Diseñador de Casos de Prueba para Formulario de Pago

## 1. Qué es esto (la rebanada)

Agente `Diseñador` que genera N escenarios de prueba para formularios de pago, cubriendo edge cases automáticamente. Trabaja en tándem con subagente `Revisor` que valida cada caso antes de publicar.

## 2. El caso y quién lo usa

**Quién**: Analista de QA (ingeniería de pruebas)  
**Problema**: Redacta casos manualmente (2-3h), cobertura incompleta de edge cases, procesos repetitivos  
**Solución**: Agente genera casos desde historia de usuario, cubre edge cases automáticamente

## 3. Frase y línea roja

**Frase**: Dado una historia de usuario en JSON, el agente produce N escenarios de prueba, y sé que funciona porque el Revisor los aprueba con cobertura ≥80% en los edge cases.

**Línea roja** (decisión que NO toma el modelo):
- NO decide si un escenario es "válido" → lo decide **Revisor** (rúbrica: completitud, claridad, criticidad, independencia, trazabilidad)
- NO decide cuándo parar → lo decide **guardrails + analista** (max 3 iteraciones, 80% cobertura, token budget)

## 4. Qué decide el modelo y qué ejecuta el código

**Diseñador decide**: Qué edge cases perseguir, orden de prioridad (high-risk primero), cuándo iterar vs parar
**Código ejecuta**: Llamadas a herramientas MCP, creación de escenarios, enmascaramiento de datos sensibles, invocación de Revisor, cálculo de frenos

## 5. Herramientas (servidor MCP)

**Herramientas MCP (3 dedicadas, lectura-only):**

1. **obtener_edge_cases** — Devuelve lista de edge cases filtrados por tipo de campo y criticidad mínima. Tipos soportados: monetario, email, teléfono, select, checkbox, texto, fecha. Otros tipos reciben 400. Usado por: Diseñador
   - Args: `campo_tipo` (obligatorio, Literal), `criticidad_mínima` (opcional, default='low')
   - Devuelve: list de {id, descripción, criticidad, ejemplo_entrada, resultado_esperado}

2. **validar_edge_case** — Verifica si un edge case propuesto existe en el catálogo. NO crea ni modifica. Si no existe, devuelve { existe: false }. Usado por: Diseñador, Revisor
   - Args: `edge_case_id` (obligatorio)
   - Devuelve: {existe: bool, criticidad?, descripción?, campo_tipo?, ejemplo_entrada?}

3. **obtener_estadísticas_cobertura** — Devuelve conteo total y distribución de edge cases por tipo de campo y criticidad. Usado por: Diseñador
   - Args: ninguno
   - Devuelve: {total: int, por_tipo: {...}, por_criticidad: {...}}

## 6. Subagentes

**1. Revisor** (rol: validador de cobertura y claridad)  
Evalúa cada escenario con rúbrica (5 criterios, threshold ≥4/5):
- Completitud (toca realmente el edge case)
- Claridad (pasos ejecutables, sin ambigüedad)
- Criticidad (high-risk primero)
- Independencia (funciona aislado)
- Trazabilidad (vinculado a HU + golden set)

Veredicto: **Aprueba** → sigue, **Rechaza** → Diseñador itera

---

**2. Especialista en Cobertura** (rol: detecta edge cases no cubiertos)  
Tras cada iteración, analiza gaps y propone prioridad. Recibe tarea autocontenida:
- Input: casos aprobados, tipos de campo, catálogo de edge cases
- Output: top 3 gaps ordenados por criticidad, con sugerencias concretas
- Herramientas: `obtener_edge_cases`, `obtener_estadísticas_cobertura`, `validar_edge_case`
- Timeout: 2 min; veredicto: recomendación (continuar iterando o parar)

Contexto limpio, rol distinto, trabajo independiente. Ver `ideacion/01-decisiones/subagente.md`

## 7. Contexto y memoria

**Entrada**: `historia_usuario.json` (HU en CLI) — enmascarar tarjetas/CVV reales antes de que lo vea el modelo

**Contexto cargado** (mínimo, lo que ya existe):
- `golden_set.json` (6 casos de referencia)
- Rúbrica 5-criterios (completitud, claridad, criticidad, independencia, trazabilidad)
- Tipos de campo soportados (monetario, email, teléfono, select, checkbox, texto, fecha)
- Límites de guardrails (3 iteraciones, 100k tokens, 30s timeout)

**Contexto consultado vía herramientas** (lectura-only):
- Edge cases del MCP (via `obtener_edge_cases`)
- Estadísticas de cobertura (via `obtener_estadísticas_cobertura`)

**Nunca en memoria** (transitorio):
- Historias de usuario individuales (por caso, no reutilizable)
- Casos generados en una ejecución (transitorio)
- Token count (métrica de sesión)
- Feedback específico del Revisor (de esa iteración)

**Salida**: `casos_aprobados.json` (N escenarios sin datos sensibles) + `cobertura_report.csv` (matriz)  
**Trazas**: `execution.log` (iteraciones, rechazos, feedback Revisor, token count)

## 8. Guardrails, frenos y aprobación humana

**GUARDRAIL DE ENTRADA**:
- Enmascarar tarjetas reales (con espacios) → [REDACTED_CARD]
- Permitir tarjetas de prueba (4111111111111111) en validaciones
- Enmascarar CVV fuera de contexto → [REDACTED_CVV]
- Permitir CVV en campos `validacion` o `ejemplo`

**GUARDRAIL DE SALIDA**:
- ❌ NO permitir: promesa "aprueba la rúbrica" (solo Revisor)
- ❌ NO permitir: "apto para producción" (solo Product Owner)
- Enmascarar tarjeta/CVV en steps finales
- Validar schema antes de publicar

**FRENOS**:
- **Max 3 iteraciones**: Si se toca → flag `iterations-exhausted`, publica lo que tiene
- **Token budget: 100k total**: Si > 100k → STOP, flag `budget-exhausted` (permitir 10% extra si última iteración)
- **Timeout Revisor: 30s**: Si timeout → flag `not-reviewed`, asume aprobado, continúa
- **Cobertura mínima: ≥80%**: Si <80% y iteraciones = 3 → flag `coverage-partial`

**MCP falla**: 3 reintentos con backoff, luego error  
**Hallucinations**: Rechazo automático si propone edge case no en MCP

**APROBACIÓN HUMANA** (BATCH):
- Revisor aprueba cada caso (veredicto binario)
- Cuando cobertura ≥80% O iteraciones = 3 → PAUSA
- Se genera reporte completo
- **Product Owner revisa batch y aprueba** (usuario final que utiliza el formulario)
- Si Product Owner aprueba → publicar archivo final
- Si rechaza → devuelve feedback al Diseñador

## 9. Cómo sé que funcionó y cómo sé que falló

**FUNCIONÓ** (éxito):
- ✅ Cobertura ≥80% en reporte
- ✅ Todos los casos aprobados por Revisor (sin flags `not-reviewed`)
- ✅ Ningún dato sensible en output (tarjetas/CVV enmascarados)
- ✅ Token usage ≤100k (o ≤110k si última iteración)
- ✅ Iteraciones ≤3 (sin flag `iterations-exhausted`)
- ✅ Comparación con golden_set muestra ≥70% coincidencia
- ✅ Product Owner aprobó batch completo

**FALLÓ** (alertas):
- 🚩 Flag `iterations-exhausted` (3 iteraciones, aún hay rechazos)
- 🚩 Flag `coverage-partial` (cobertura <80% al parar)
- 🚩 Flag `budget-exhausted` (tokens >100k sin ser última iteración)
- 🚩 Flag `data-exposure-risk` (datos sensibles en output, enmascaramiento falló)
- 🚩 Flag `not-reviewed` (Revisor timeout, casos sin validación completa)
- 🚩 Comparación con golden_set muestra <70% coincidencia (casos no son comparables)
- 🚩 Product Owner rechazó batch (feedback: ajustes necesarios)

## 10. PENDIENTES

**BLOQUEADORES (necesarios para MVP):**
- [ ] Implementar servidor MCP: `obtener_edge_cases`, `validar_edge_case`, `obtener_estadísticas_cobertura`
- [ ] Codificar orquestador Diseñador: loop iterativo (3 max), decisiones de edge cases, frenos
- [ ] Codificar subagente Revisor: rúbrica 5-criterios, veredicto binario, timeout 30s

**NICE-TO-HAVE (v2+):**
- [ ] Codificar subagente Especialista en Cobertura: top 3 gaps, recomendaciones
- [ ] Guardrails: PreToolUse (enmascaramiento entrada), PostToolUse (enmascaramiento salida)
- [ ] Suite de tests (pytest vs golden_set)
- [ ] Demo en 2 min con HU de ejemplo

## 11. Bitácora (fecha, qué cambió y por qué)

**2026-11-13 PM Sesión Completa**: Ideación → Especificación → BPMN → Cierre
- Resolvimos 4 bloqueadores: rol Diseñador/Revisor, golden_set, rúbrica, guardrails
- Definidas 3 herramientas MCP: obtener_edge_cases, validar_edge_case, obtener_estadísticas_cobertura
- 2 subagentes: Revisor (valida rúbrica), Especialista en Cobertura (detecta gaps)
- 5 temas entrevista: contexto, guardrail entrada/salida, frenos, aprobación humana
- BPMN v1→v2: corregidos 5 problemas críticos (MCP terminal, timeout, hallucinations, feedback)
- Creados 8 archivos: CLAUDE.md, golden_set.json, guardrails.md, decide-o-ejecuta.md, herramientas.csv, subagente.md, controles.md, bpmn-agente.html

**2026-11-13 PM**: CIERRE de Ideación — Proyecto listo para implementación
- Revisión final: CLAUDE.md completo (190 líneas, ✅ < 200), coherente con BPMN v2, sin contradicciones
- Correcciones menores: línea 19 (5 → 3 iter), línea 24 (nombres herramientas reales)
- Pendientes reorganizados: 3 bloqueadores + 4 nice-to-have
- Puntos de partida identificados: MCP → Agent SDK labs, Subagente → Agent Delegation, Guardrails → Hooks, Frenos → Loops
- Archivos ideación: 7 documentos (CLAUDE.md, golden_set.json, guardrails.md, decide-o-ejecuta.md, herramientas.csv, subagente.md, controles.md, bpmn-agente.html)
- **DISEÑO 100% COMPLETADO**: Listo para pasar a IMPLEMENTACIÓN
- Próximo: Crear estructura proyecto + implementar MCP (3 herramientas) → Diseñador loop → Revisor subagente

**2026-11-18 PM**: Validación de cierre y puntos de partida
- Revisión final de coherencia: CLAUDE.md vs ideacion/ → 100% alineado, 0 contradicciones
- Confirmado: línea count 170 (✅ bajo 200), todas herramientas MCP definidas, subagentes claros, guardrails + frenos documentados
- Ordenamiento PENDIENTES: MCP → Diseñador loop → Revisor subagente = bloqueadores (v1); Guardrails + tests + demo = nice-to-have (v2+)
- Puntos de partida identificados por pieza:
  - **MCP Server**: `mcp-servers` quickstart (3 tools, lectura-only, estructura)
  - **Subagente Revisor**: `agent-delegation` lab (contexto limpio, tarea autocontenida, timeout)
  - **Guardrails**: `hooks` lab (PreExecute entrada, PostGenerate salida para enmascaramiento)
  - **Frenos**: `loop-manager` o `managed-loops` lab (3 max iter, cobertura threshold, token budget)
- Archivos ideación validados: 7 documentos + golden_set.json (6 casos) + CLAUDE.md principal
- **IDEACIÓN CERRADA**: Transición a implementación. Próximo: setup estructura `/src` + labs
