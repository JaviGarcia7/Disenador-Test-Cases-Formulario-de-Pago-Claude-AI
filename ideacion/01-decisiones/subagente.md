# Subagente: Especialista en Cobertura

## Definición

**Rol**: Detecta edge cases no cubiertos tras cada iteración y propone cuáles generar a continuación.

**Responsabilidad**: Después de que el Diseñador genera N casos y el Revisor aprueba algunos, este subagente analiza qué edge cases del catálogo siguen sin toque y recomienda prioridad para la siguiente iteración.

**Contexto**: Recibe una tarea autocontenida (NO ve la conversación del Diseñador). No participa en la rúbrica de aprobación; solo analiza gaps.

---

## Herramientas que usa

1. **obtener_edge_cases** — Para listar todos los edge cases disponibles (filtrado por tipo)
2. **obtener_estadísticas_cobertura** — Para ver distribución total de edge cases
3. **validar_edge_case** — Para detalles específicos de cada gap (descripción, criticidad)

---

## Formato de Entrega

**Input** (tarea autocontenida que recibe el subagente):
```json
{
  "objetivo": "Identificar edge cases no cubiertos",
  "iteracion": 2,
  "casos_aprobados": [
    {
      "id": "GS-001-v1",
      "titulo": "Pago exitoso",
      "edge_case_cubierto": "EC-001",
      "criticidad": "high"
    },
    {
      "id": "GS-002-v1",
      "titulo": "Campos vacíos",
      "edge_case_cubierto": "EC-002",
      "criticidad": "high"
    }
  ],
  "hu_campos": ["titular", "numero_tarjeta", "fecha_expiracion", "cvv"],
  "campos_tipos": {
    "titular": "texto",
    "numero_tarjeta": "monetario",
    "fecha_expiracion": "fecha",
    "cvv": "texto"
  },
  "limites": {
    "tiempo_max": "2 min",
    "top_gaps": 3,
    "criticidad_minima": "high"
  }
}
```

**Output** (qué entrega exactamente):
```json
{
  "iteracion": 2,
  "cobertura_actual": 0.33,
  "cobertura_objetivo": 0.80,
  "gaps_detectados": [
    {
      "ranking": 1,
      "edge_case_id": "EC-003",
      "edge_case_descripcion": "Tarjeta expirada",
      "tipo_campo": "fecha",
      "criticidad": "high",
      "por_que_falta": "Ningún caso aprobado toca validación de fecha pasada",
      "sugerencia": "Generar caso: ingresar fecha 05/23 (expirada), verificar rechazo",
      "ejemplo_entrada": "fecha_expiracion: '05/23'",
      "resultado_esperado": "Mensaje 'Tarjeta expirada'"
    },
    {
      "ranking": 2,
      "edge_case_id": "EC-004",
      "edge_case_descripcion": "Número tarjeta con caracteres",
      "tipo_campo": "monetario",
      "criticidad": "high",
      "por_que_falta": "No hay caso que valide rechazo de formato",
      "sugerencia": "Generar caso: ingresar '4111AAAA2222BBBB', verificar validación en tiempo real",
      "ejemplo_entrada": "numero_tarjeta: '4111AAAA2222BBBB'",
      "resultado_esperado": "Validación inline, rechazo con mensaje"
    },
    {
      "ranking": 3,
      "edge_case_id": "EC-005",
      "edge_case_descripcion": "CVV inválido (< 3 dígitos)",
      "tipo_campo": "texto",
      "criticidad": "medium",
      "por_que_falta": "Ningún caso toca validación de CVV corto",
      "sugerencia": "Generar caso: ingresar CVV '12', verificar error",
      "ejemplo_entrada": "cvv: '12'",
      "resultado_esperado": "Mensaje 'CVV debe ser 3 o 4 dígitos'"
    }
  ],
  "recomendacion": "CONTINUAR: Faltan 3 edge cases high-risk. Con 2 más se alcanza ≥80% cobertura.",
  "confianza": 0.92
}
```

---

## Ejemplo de Tarea Autocontenida

**Escenario**: Iteración 2 del proyecto. El Diseñador ya generó 2 casos aprobados (casos 1 y 2 del golden_set). Especialista en Cobertura analiza qué falta.

**Input (tarea que recibe)**:
```json
{
  "objetivo": "Identificar edge cases no cubiertos",
  "iteracion": 2,
  "casos_aprobados": [
    {
      "id": "CASO-001",
      "titulo": "Pago exitoso con tarjeta válida",
      "edge_case_cubierto": "pago-exitoso",
      "criticidad": "high",
      "campos_tocados": ["titular", "numero_tarjeta", "fecha_expiracion", "cvv"]
    },
    {
      "id": "CASO-002",
      "titulo": "Campos obligatorios vacíos",
      "edge_case_cubierto": "validacion-campos-vacios",
      "criticidad": "high",
      "campos_tocados": ["titular", "numero_tarjeta", "fecha_expiracion", "cvv"]
    }
  ],
  "hu_campos": ["titular", "numero_tarjeta", "fecha_expiracion", "cvv"],
  "campos_tipos": {
    "titular": "texto",
    "numero_tarjeta": "monetario",
    "fecha_expiracion": "fecha",
    "cvv": "texto"
  },
  "limites": {
    "tiempo_max": "120 segundos",
    "top_gaps": 3,
    "criticidad_minima": "high"
  }
}
```

**Output (lo que entrega)**:
```json
{
  "iteracion": 2,
  "cobertura_actual": 0.33,
  "cobertura_objetivo": 0.80,
  "gaps_detectados": [
    {
      "ranking": 1,
      "edge_case_id": "EC-003",
      "edge_case_descripcion": "Tarjeta con fecha de expiración pasada",
      "tipo_campo": "fecha_expiracion",
      "criticidad": "high",
      "por_que_falta": "Casos 1 y 2 no tocan validación de expiración. Es edge case high-risk (seguridad).",
      "sugerencia": "Generar CASO-003: ingresar fecha_expiracion='05/23' (pasada), verificar rechazo con mensaje 'Tarjeta expirada'",
      "ejemplo_entrada": "titular: 'Test', numero_tarjeta: '4111111111111111', fecha_expiracion: '05/23', cvv: '123'",
      "resultado_esperado": "Sistema rechaza con: 'La tarjeta ingresada está expirada'"
    },
    {
      "ranking": 2,
      "edge_case_id": "EC-004",
      "edge_case_descripcion": "Número de tarjeta con caracteres alfabéticos",
      "tipo_campo": "numero_tarjeta",
      "criticidad": "high",
      "por_que_falta": "Casos 1 y 2 usan números válidos. No hay validación de formato.",
      "sugerencia": "Generar CASO-004: ingresar numero_tarjeta='4111AAAA2222BBBB', verificar validación en tiempo real",
      "ejemplo_entrada": "numero_tarjeta: '4111AAAA2222BBBB', otros campos válidos",
      "resultado_esperado": "Error inline: 'Número de tarjeta inválido. Solo números, 15-16 dígitos'"
    },
    {
      "ranking": 3,
      "edge_case_id": "EC-005",
      "edge_case_descripcion": "CVV con menos de 3 dígitos",
      "tipo_campo": "cvv",
      "criticidad": "medium",
      "por_que_falta": "Casos 1 y 2 usan CVV válido (3 dígitos). No hay validación de corto.",
      "sugerencia": "Generar CASO-005: ingresar cvv='12', verificar rechazo",
      "ejemplo_entrada": "titular: 'Test', numero_tarjeta: '4111111111111111', fecha_expiracion: '12/29', cvv: '12'",
      "resultado_esperado": "Error: 'El código CVV debe ser de 3 o 4 dígitos numéricos'"
    }
  ],
  "resumen_cobertura": {
    "total_edge_cases": 6,
    "cubiertos": 2,
    "faltantes": 4,
    "cobertura_porcentaje": 33.33
  },
  "recomendacion": "CONTINUAR ITERANDO: Después de generar CASO-003, CASO-004 y CASO-005, cobertura alcanzará 83%. Esto pasa el threshold de 80%.",
  "confianza": 0.94,
  "timestamp": "2026-11-13T14:32:00Z"
}
```

---

## Por qué es Subagente (no herramienta)

| Aspecto | Explicación |
|--------|-------------|
| **Rol distinto** | Diseñador redacta. Revisor valida completitud/claridad. Especialista analiza patrones y **decide estrategia**. |
| **Contexto limpio** | NO ve la conversación del Diseñador. Recibe solo datos estructurados. Decisión independiente, sin bias. |
| **Trabajo en paralelo** | Mientras Diseñador itera, este subagente analiza en paralelo (opcional si presupuesto lo permite). |
| **Razonamiento complejo** | Necesita comparar conjuntos, detectar gaps, priorizar por criticidad, sugerir dirección. NO es un lookup. |

---

## Costo Aproximado

| Escenario | Costo | Notas |
|-----------|-------|-------|
| Sin subagente | $0 | Diseñador genera al azar; posibles loops ciegos. |
| Con subagente | +$0.0003 × 5 iteraciones = **+$0.0015 USD** | 1 llamada al modelo por iteración. |
| **Ahorro por claridad** | -$0.001 USD | Evita 3-4 iteraciones ciegas gracias a dirección clara. |
| **Neto** | +$0.0005 USD | Pequeño costo, gran valor estratégico. |

