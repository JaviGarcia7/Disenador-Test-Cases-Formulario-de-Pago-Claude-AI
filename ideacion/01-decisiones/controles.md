# Controles: Guardrails de Entrada, Salida, Frenos y Aprobación

## 1. GUARDRAIL DE ENTRADA

**Qué puede llegar que NO debe entrar al modelo:**

### 1.1 Enmascaramiento de datos sensibles

| Dato | Acción | Regla |
|------|--------|-------|
| Tarjeta real (con espacios, formatos variados) | ENMASCARAR | Si contiene 16 dígitos + espacios → [REDACTED_CARD] |
| Tarjeta de prueba (4111111111111111, 000000...) | PERMITIR | Es ejemplo legítimo en validación/ejemplo |
| CVV en contexto de spec | PERMITIR | Si está en campo `validacion` o `ejemplo` |
| CVV fuera de contexto | ENMASCARAR | Si aparece solo → [REDACTED_CVV] |

### 1.2 Falso positivo probable

**Guardrail incorrecto**: "Rechazar todo HU que contenga un número de 16 dígitos"

**Falso positivo**: HU legítimo con ejemplo de prueba:
```json
{
  "campo": "numero_tarjeta",
  "validacion": "Debe aceptar 16 dígitos",
  "ejemplo_válido": "4111111111111111"
}
```
→ Rechazado incorrectamente (es número de prueba estándar, legítimo)

**Solución**: Distinguir tarjetas reales (formato variado, espacios) de tarjetas de prueba (formato estándar) → enmascarar reales, permitir prueba.

### 1.3 Inyecciones de instrucciones

**No esperadas en este caso.** No validar.

---

## 2. GUARDRAIL DE SALIDA

**Qué NO puede salir nunca en los casos generados:**

### 2.1 Promesas no autorizadas

| Promesa | Quién puede hacerla | Acción |
|---------|-------------------|--------|
| "Este caso aprueba la rúbrica" | Solo Revisor | ❌ RECHAZAR si Diseñador la hace |
| "Recomiendo ejecutar este caso" | Diseñador, Especialista | ✅ PERMITIR |
| "Este caso es apto para producción" | Solo Product Owner | ❌ RECHAZAR si Diseñador/Revisor lo dice |

### 2.2 Enmascaramiento en salida final

| Elemento | Acción |
|----------|--------|
| Número de tarjeta en steps | ENMASCARAR → [REDACTED_CARD] |
| CVV en steps | ENMASCARAR → [REDACTED_CVV] |
| ID de caso (generado por agente) | PERMITIR (único, validado) |
| Nombre del edge case cubierto | PERMITIR (viene del MCP) |

### 2.3 Falso positivo probable

**Guardrail incorrecto**: "Rechazar todo caso que mencione '4111'"

**Falso positivo**: Caso legítimo:
```
Step 1: "Ingrese tarjeta de prueba: 4111111111111111"
```
→ Rechazado (menciona 4111, pero es ejemplo válido de prueba)

**Solución**: Permitir números de prueba en steps descriptivos. Solo enmascarar si es dato real.

---

## 3. FRENOS (Máximo de vueltas y presupuesto)

### 3.1 Límites

| Límite | Valor | Acción si se toca |
|--------|-------|-------------------|
| **Máximo iteraciones** | 3 | Flag `iterations-exhausted`, publica lo que tiene |
| **Token budget total** | 100k | Flag `budget-exhausted`, publica lo que tiene |
| **Timeout Revisor** | 30s | Flag `not-reviewed`, continúa (asume aprobado) |

### 3.2 Qué hace el agente al tocar freno

1. **Si MAX_ITERACIONES = 3**:
   - Genera casos hasta iteración 3
   - Si cobertura < 80% → flag `iterations-exhausted`
   - Publica casos aprobados + reporte con flag

2. **Si TOKEN_BUDGET > 100k**:
   - STOP inmediato
   - Flag `budget-exhausted`
   - Publica casos aprobados hasta ese momento

3. **Si Revisor timeout (>30s)**:
   - Asume caso aprobado (fallback optimista)
   - Flag `not-reviewed` en ese caso
   - Continúa con siguiente caso

### 3.3 Falso positivo probable

**Guardrail incorrecto**: "100k tokens es límite firme, parar exactamente en 100k"

**Falso positivo**: Última iteración usa 105k tokens legítimamente (caso complejo, Revisor lento)
→ Se mata ejecución que casi termina

**Solución**: 100k es límite suave. Si es última iteración y casos están aprobados, permitir 10% extra (110k máximo).

---

## 4. PUNTO DE PARADA Y APROBACIÓN HUMANA

### 4.1 Flujo de aprobación (BATCH)

```
1. Diseñador genera caso 1 → Revisor valida
2. Diseñador genera caso 2 → Revisor valida
3. ...
4. Diseñador genera caso N → Revisor valida
5. [PAUSA AQUÍ - todos los casos generados y aprobados por Revisor]
6. Se genera reporte: casos_aprobados.json + cobertura_report.csv
7. Product Owner revisa batch completo
8. Product Owner: ✅ Aprueba → Archivo final publicado
   O: ❌ Rechaza → Se devuelve feedback para re-iterar
```

### 4.2 Quién aprueba qué

| Paso | Quién | Veredicto |
|------|-------|-----------|
| Cada caso individual | **Revisor** (subagente) | ✅ Aprueba o ❌ Rechaza (vuelve a Diseñador) |
| Cobertura total | **Especialista en Cobertura** | 🟢 Recomendación (continuar o parar) |
| Batch completo | **Product Owner** (usuario final) | ✅ Publica o ❌ Devuelve para ajustes |

### 4.3 Punto exacto de parada

**DESPUÉS que Revisor dice "OK" en todos los N casos** (cuando cobertura ≥ 80% o iteraciones = 3).

En ese momento:
- Se generan archivos finales
- Se envía a Product Owner para aprobación
- **AQUÍ SE DETIENE el proceso automatizado**
- Product Owner revisa y decide (publicar o re-iterar)

### 4.4 Rol que aprueba

**Product Owner** — Valida que los casos generados cubren las necesidades del negocio y son aptos para ejecutar.

---

## 5. TABLA RESUMEN: GUARDRAILS + FALSOS POSITIVOS

| Guardrail | Regla | Falso Positivo | Solución |
|-----------|-------|---|----------|
| Enmascarar tarjetas reales | Rechazo de 16 dígitos | Número de prueba (4111...) rechazado | Distinguir formato (espacio = real, estándar = prueba) |
| No prometer aprobación rúbrica | Diseñador no dice "aprueba" | Caso legítimo rechazado | Solo Revisor hace esa promesa |
| Enmascarar CVV | Todo CVV → [REDACTED] | CVV en spec permitido rechazado | Permitir en `validacion`/`ejemplo` |
| Max 3 iteraciones | Parar en iteración 3 | Caso casi listo se mata | Flag en lugar de error |
| 100k token limit | Parar en 100k | Última iteración legítima con 105k | Límite suave: permitir 10% extra si es última |
| Revisor timeout | Asumir aprobado si >30s | Caso malo aprobado por timeout | Flag `not-reviewed` para auditarla después |

---

## 6. CHECKLIST DE VALIDACIÓN ANTES DE PUBLICAR

- [ ] Ningún número de tarjeta real en output (solo [REDACTED_CARD])
- [ ] Ningún CVV real en output (solo [REDACTED_CVV])
- [ ] Revisor aprobó todos los casos (sin flag `not-reviewed` o con explicación)
- [ ] Cobertura ≥ 80% O flag `iterations-exhausted` agregado
- [ ] Iteraciones ≤ 3
- [ ] Tokens ≤ 100k (o ≤ 110k si es última iteración)
- [ ] Ningún caso contiene promesa "aprueba rúbrica"
- [ ] Archivo con schema válido (casos_aprobados.json + cobertura_report.csv)
- [ ] Product Owner aprobó batch completo

