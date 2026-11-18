# Decide o Ejecuta — Tabla de Acciones

## Flujo Completo: Quién decide, quién ejecuta, qué pasa si falla

| Acción | Quién | Qué pasa si se equivoca | ¿DE ACUERDO? | Notas |
|--------|-------|------------------------|--|---------|
| Analista envía `historia_usuario.json` por CLI | PERSONA | Entra inválido al agente | Si | Input es responsabilidad del usuario |
| Validar schema JSON de entrada | CÓDIGO | HU rechazado, error "schema inválido" | Si | Hook PreExecute: valida antes de que MODELO vea |
| MODELO (Diseñador) lee HU | MODELO | Hallucination en parsed data | Si | Diseñador extrae: campos, tipo, restricciones |
| MODELO solicita `buscar_casos(HU)` al MCP | MODELO | Solicita herramienta correcta | Si | Decidir cuál MCP method llamar |
| CÓDIGO ejecuta llamada MCP | CÓDIGO | Falla conexión, timeout, response vacío | Si | Reintenta 3 veces con backoff exponencial |
| CÓDIGO valida respuesta MCP (schema, no vacío) | CÓDIGO | MCP devuelve data malformada o null → error | Si | Si falla → flag `mcp-validation-error`, propagar |
| MODELO (Diseñador) analiza edge cases devueltos | MODELO | Elige edge cases no relevantes o inventados | Si | Diseñador interpreta catálogo, decide subset a perseguir |
| MODELO prioriza edge cases por criticidad | MODELO | Ordena low-risk primero (incorrecto) | Si | High-risk primero: seguridad, fondos, expiración |
| MODELO decide cuántos escenarios generar | MODELO | Decide generar 20, quebraría presupuesto | Si | Heurística: min 2, max 5 por iteración (guardrail) |
| MODELO genera primer escenario (estructura, pasos) | MODELO | Escenario ambiguo, pasos incompletos | Si | Redacta con template golden_set |
| CÓDIGO ejecuta `crear_caso(escenario)` | CÓDIGO | Falla herramienta, timeout | Si | Reintentos, sanitización, validación schema |
| CÓDIGO valida schema del escenario generado | CÓDIGO | Falta `id`, `title`, `test_steps` → rechazado | Si | Guardrail: si no pasa schema, error antes de Revisor |
| CÓDIGO sanitiza escenario (quita datos sensibles) | CÓDIGO | Deja número de tarjeta o CVV → rechazado | Si | Hook PostGenerate: busca patrones `/\d{15,16}/` |
| MODELO (Revisor) evalúa escenario con rúbrica | MODELO | Aprueba caso mediocre o rechaza válido | Si | Revisor aplica: completitud, claridad, criticidad, independencia, trazabilidad |
| CÓDIGO calcula score rúbrica (5 criterios) | CÓDIGO | Calcula mal el promedio de scores | Si | Cálculo: (C1 + C2 + C3 + C4 + C5) / 5 ≥ 4.0 |
| CÓDIGO timeout Revisor (30s) | CÓDIGO | Revisor no responde → timeout firing | Si | Guardrail: si > 30s → flag `not-reviewed`, continuar |
| MODELO (Revisor) emite veredicto | MODELO | Veredicto inconsistente (aprueba/rechaza sin criterio) | Si | Binario: `aprobado` o `rechazado` + feedback |
| CÓDIGO registra resultado en log | CÓDIGO | Log incompleto o corrupto | Si | Trace: iteración, caso, score, veredicto, tokens |
| Si RECHAZADO: MODELO (Diseñador) decide iterar | MODELO | Decide refinar caso rechazado vs generar nuevo | Si | Heurística: retry mismo edge case x3 max, luego saltar |
| CÓDIGO incrementa contador de iteraciones | CÓDIGO | No cuenta, loop infinito | Si | Guardrail: iteración_actual++ cada vez |
| CÓDIGO verifica MAX_ITERACIONES (5) | CÓDIGO | Sigue iterando después de 5 | Si | Si iteración > 5 → flag `iterations-exhausted`, STOP |
| CÓDIGO suma tokens de esta iteración | CÓDIGO | No suma o suma mal | Si | Cálculo: acumula tokens de MODELO + herramientas |
| CÓDIGO verifica TOKEN_BUDGET (100k) | CÓDIGO | Supera presupuesto, no frena | Si | Si tokens > 100k → flag `budget-exhausted`, STOP |
| Si APROBADO: CÓDIGO agrega a lista `casos_aprobados` | CÓDIGO | Duplica caso o pierde referencia | Si | Append a array, con id único |
| CÓDIGO calcula COBERTURA actual | CÓDIGO | Calcula mal el % | Si | Cálculo: (edge_cases_cubiertos / edge_cases_totales) × 100 |
| CÓDIGO verifica COBERTURA ≥ 80% | CÓDIGO | Threshold incorrecto | Si | Si cobertura ≥ 80% → listo. Si < 80% y iteraciones < 5 → continuar |
| Si cobertura < 80% y iteraciones < 5: MODELO genera nuevo escenario | MODELO | Vuelve a generar mismo caso | Si | Loop: vuelve a "genera primer escenario" |
| Si cobertura ≥ 80% O iteraciones = 5: CÓDIGO genera reports | CÓDIGO | Genera CSV malformado o JSON inválido | Si | Salida: `casos_aprobados.json` + `cobertura_report.csv` |
| CÓDIGO agrega flags finales al report | CÓDIGO | Olvida flag importante | Si | Si aplicable: `iterations-exhausted`, `coverage-partial`, `budget-exhausted`, `not-reviewed` |
| PERSONA (Analista) revisa report | PERSONA | Ignora flags, publica casos rechazados | Si | Revisor lee: casos, cobertura %, flags. Decide publicar o re-ejecutar |
| PERSONA aprueba y autoriza publicación | PERSONA | Aprueba sin validar | Si | Si cobertura ≥ 80% y sin flags críticos → OK publicar |
| CÓDIGO entrega salida final | CÓDIGO | Corrupción de archivo | Si | `casos_aprobados.json` + `cobertura_report.csv` + `execution.log` |

---

## Análisis: MODELO → ¿Debe moverse a CÓDIGO?

### Fila: MODELO (Diseñador) lee HU
**Hoy**: MODELO decide qué campos extraer  
**¿Mover a CÓDIGO?** Parcialmente  
**Por qué**: La lectura es IA-decision (buscar nombre, tipo, restricciones). Pero validar que el HU tenga estructura JSON correcta debe ser CÓDIGO (PreExecute hook).

---

### Fila: MODELO solicita `buscar_casos(HU)` al MCP
**Hoy**: MODELO decide cuál MCP method llamar  
**¿Mover a CÓDIGO?** No  
**Por qué**: Es decisión adaptativa. Si HU tiene campo "email", solicita edge cases para email. Si tiene "monto", solicita para monetario. Eso es IA.

---

### Fila: MODELO prioriza edge cases por criticidad
**Hoy**: MODELO ordena por criticidad  
**¿Mover a CÓDIGO?** Sí, parcialmente  
**Por qué**: La clasificación "high/medium/low" está en MCP como metadata. CÓDIGO debería **ordenar** por criticidad (sort). MODELO puede decidir **cuáles perseguir**, pero el ordering debe ser guardrail.

---

### Fila: MODELO decide cuántos escenarios generar
**Hoy**: MODELO elige subset  
**¿Mover a CÓDIGO?** Sí  
**Por qué**: "Min 2, max 5 por iteración" es un guardrail numérico. CÓDIGO debe forzar límites. MODELO elige "criticidad HIGH primero", CÓDIGO elige "máximo 5".

---

### Fila: MODELO genera primer escenario
**Hoy**: MODELO redacta steps, estructura  
**¿Mover a CÓDIGO?** No  
**Por qué**: Es creación de contenido (responsabilidad IA). Validación de schema (PreToolUse hook) es CÓDIGO.

---

### Fila: Si RECHAZADO: MODELO decide iterar
**Hoy**: MODELO elige "refinar caso X" vs "generar nuevo"  
**¿Mover a CÓDIGO?** No  
**Por qué**: Es decisión contextual. Si feedback es "falta validación de rechazo", refina. Si es "edge case no existe en MCP", salta. Eso requiere razonamiento.

---

### Fila: MODELO (Revisor) emite veredicto
**Hoy**: MODELO aplica rúbrica  
**¿Mover a CÓDIGO?** Sí, parcialmente  
**Por qué**: Los **cálculos de score** (completitud 5/5, claridad 4/5) deben ser CÓDIGO (evita hallucinations). MODELO decide la **interpretación** (si score 4.2 es "rechazar" o "aprobar con warning"). El threshold 4.0 es guardrail → CÓDIGO.

---

## 🎯 RESUMEN DE MOVIMIENTOS PROPUESTOS

| Fila | Hoy: MODELO | Propuesta | Herramienta |
|-----|-----------|-----------|-----------|
| Leer HU | MODELO | CÓDIGO valida schema | PreExecute hook |
| Priorizar por criticidad | MODELO | CÓDIGO ordena (guardrail) | Sort function |
| Cuántos escenarios | MODELO | CÓDIGO limita (min 2, max 5) | Guardrail constant |
| Score rúbrica | MODELO | CÓDIGO calcula (5 criterios) | Función Python |

Todo lo demás = **MODELO sigue siendo responsable** (decisión adaptativa, redacción, reasoning).

---

**¿Estás de acuerdo con estos movimientos, o ajusto?**
