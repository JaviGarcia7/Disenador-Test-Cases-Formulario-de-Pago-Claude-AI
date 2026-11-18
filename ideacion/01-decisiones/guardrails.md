# Guardrails del Agente Diseñador de Casos de Prueba

## 1. MAX ITERACIONES

**Límite**: 5 iteraciones máximas por ejecución

**Lógica**:
- Iteración 1: Diseñador genera 2 casos iniciales
- Iteración 2-4: Revisor rechaza → Diseñador refina (máximo 3 refinamientos)
- Iteración 5: Última oportunidad. Si aún hay rechazos, se publica con flag "parcial"

**Qué pasa en iteración 6**:
```
STOP: Máximo de iteraciones alcanzado.
Casos generados: [listado]
Casos rechazados pendientes: [listado]
Acción: Publicar casos aprobados + generar reporte "Cobertura parcial"
```

**Por qué**: Evita loops infinitos donde el Diseñador never-ending-refine.

---

## 2. TOKEN BUDGET

**Presupuesto**: 100k tokens por ejecución (estimado ~$0.30 USD con Opus)

**Desglose esperado**:
- Agente Diseñador: ~40k tokens (generación + validación)
- Subagente Revisor: ~30k tokens (validación × 5 iteraciones máx)
- MCP calls: ~5k tokens
- Margen: ~25k tokens

**Monitoreo**:
```
Token usage en cada iteración:
- Si > 80k después de iteración 3 → Advertencia "Budget agotándose"
- Si > 100k → STOP inmediato, publicar lo que hay
```

**Fallback**: Si presupuesto se agota antes de iteración 5:
```
STOP: Token budget excedido.
Razón: Posible loop o caso muy complejo.
Acción: Publicar casos aprobados + log de error para debug.
```

---

## 3. TIMEOUT DEL SUBAGENTE (REVISOR)

**Límite de tiempo**: 30 segundos por evaluación

**Lógica**:
- Revisor inicia evaluación
- Si > 30s sin respuesta → Timeout
- Diseñador asume "aprobado parcialmente" y continúa

**Qué pasa en timeout**:
```
TIMEOUT: Revisor no respondió en 30s.
Caso: [nombre del caso]
Acción: Publicar caso con flag "no-revisado" (requiere validación manual)
Reintento: No. Continuar con siguiente caso.
```

**Razón**: El Revisor no debe bloquear indefinidamente. Si tarda mucho, probablemente hay un bug en la evaluación.

---

## 4. THRESHOLD DE COBERTURA ACEPTABLE

**Objetivo**: ≥ 80% de edge cases cubiertos

**Cálculo**:
```
Cobertura = (Casos aprobados que toca edge case X) / (Total edge cases del MCP)
```

**Ejemplo con 10 edge cases**:
- 8 casos aprobados → 80% → ✅ ACEPTABLE
- 7 casos aprobados → 70% → 🟡 ADVERTENCIA
- 6 o menos → < 60% → 🔴 RECHAZAR, reintentar

**Qué pasa si NO alcanza 80%**:
```
ALERTA: Cobertura insuficiente (65%).
Edge cases faltantes: [listado]
Acción:
  - Si iteraciones < 5 → Diseñador genera casos para gaps
  - Si iteraciones ≥ 5 → Publicar con flag "cobertura-parcial"
```

---

## 5. OTROS GUARDRAILS (SEGURIDAD)

### 5.1 Sanitización de Outputs
**Regla**: Ningún número de tarjeta, CVV o dato sensible en la salida final
```
Si output contiene patrón /\d{15,16}/ (tarjeta)
  → Reemplazar con [REDACTED_CARD]
Si output contiene patrón /CVV.*\d{3,4}/ 
  → Reemplazar con [REDACTED_CVV]
```

### 5.2 Validación de Casos contra Schema
**Regla**: Cada caso generado DEBE tener:
- `id`, `title`, `edge_case_covered`, `criticidad`, `test_steps`
- Cada `test_step` DEBE tener: `step` (número), `action`, `expected`

Si falta alguno → Rechazar caso antes de que Revisor lo vea

### 5.3 Rechazo de Hallucinations
**Regla**: Si Diseñador propone edge case NO en el MCP, Revisor rechaza automáticamente
```
Edge case propuesto: "Tarjeta de crédito de 17 dígitos"
Verificación: ¿Existe en MCP? NO
Veredicto: RECHAZADO - Caso propone edge case inventado
```

---

## 📊 TABLA RESUMEN DE GUARDRAILS

| Guardrail | Límite | Acción en Fallo | Flag de Salida |
|-----------|--------|-----------------|----------------|
| Max Iteraciones | 5 | Publicar parcial | `iterations-exhausted` |
| Token Budget | 100k | Publicar parcial | `budget-exhausted` |
| Timeout Revisor | 30s | Asumir aprobado | `not-reviewed` |
| Cobertura Min | 80% | Generar más casos o parar | `coverage-partial` |
| Sanitización | Ningún dato sensible | Rechazar output | `data-exposure-risk` |
| Schema | Campos requeridos | Rechazar caso | `invalid-schema` |
| Hallucinations | Edge case en MCP | Rechazar caso | `hallucination-detected` |

---

## 🚨 TABLA DE DECISIÓN: ¿QUÉ HACER?

```
IF iteraciones ≥ 5 AND cobertura < 80%
  → Publicar con flag "coverage-partial" + lista de gaps
  → NO reintentar

IF tokens > 100k
  → STOP inmediato
  → Publicar lo que hay
  → Generar log para debug

IF revisor timeout en iteración 1-2
  → Asumir aprobado, continuar (puede ser transiente)

IF revisor timeout en iteración 3+
  → Generar alerta, flag "not-reviewed"

IF caso tiene hallucination
  → Rechazar inmediatamente
  → Diseñador genera alternativa
  → Si falla 3 veces en mismo edge case → Omitir y marcar como gap

IF output contiene datos sensibles
  → Sanitizar automáticamente
  → Flag "sanitized" en salida
```

---

## ✅ CHECKLIST ANTES DE PUBLICAR

- [ ] Todos los casos tienen schema válido
- [ ] Ningún dato sensible en output
- [ ] Cobertura ≥ 80% O flag "coverage-partial" agregado
- [ ] Número de iteraciones ≤ 5
- [ ] Tokens usados ≤ 100k
- [ ] Todos los cases con rechazo tienen razón documentada
- [ ] Trazas de decisión del agente grabadas

