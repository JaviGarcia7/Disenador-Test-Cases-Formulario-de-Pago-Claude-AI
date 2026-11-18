# 🔄 Flujo Completo del Agente - Explicación Detallada

## 1. Entrada: Usuario Envía Historia de Usuario

```
┌─ Usuario (CLI) ─────────────────────────────────────────────────┐
│                                                                  │
│  $ ./run_cli.sh --hu examples/hu_example.json                  │
│                                                                  │
│  Input (historia_usuario.json):                                │
│  {                                                              │
│    "id": "HU-001",                                             │
│    "descripcion": "Formulario de Pago",                        │
│    "campos": [                                                 │
│      {"nombre": "Titular", "tipo": "texto"},                 │
│      {"nombre": "Número tarjeta", "tipo": "monetario"},      │
│      {"nombre": "Fecha expiración", "tipo": "fecha"},        │
│      {"nombre": "CVV", "tipo": "texto"}                      │
│    ]                                                           │
│  }                                                              │
│                                                                  │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
        ┌─ GUARDRAIL ENTRADA ─┐
        │ (Código - seg. datos)│
        └─────────┬────────────┘
```

---

## 2. Guardrail de Entrada: Validación + Enmascaramiento

```
┌──────────────────────────────────────────────────────────────┐
│  GUARDRAIL DE ENTRADA (src/guardrails.py)                   │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 1. VALIDAR SCHEMA                                       ││
│  │   • ¿JSON válido?                                       ││
│  │   • ¿Tiene campos requeridos? (id, descripcion, campos) ││
│  │   • ¿Cada campo tiene nombre y tipo?                    ││
│  │                                                          ││
│  │   Si NO → Error: "HU inválida" → FIN                    ││
│  └─────────────────────────────────────────────────────────┘│
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 2. ENMASCARAR DATOS SENSIBLES                           ││
│  │                                                          ││
│  │   Detectar:                                             ││
│  │   • Tarjetas reales: /\d{4}\s\d{4}\s\d{4}\s\d{4}/      ││
│  │     Ejemplo: "4111 1111 1111 1111" → [REDACTED_CARD]   ││
│  │                                                          ││
│  │   • CVV fuera de contexto: /CVV.*\d{3,4}/              ││
│  │     Ejemplo: "CVV: 123" → "CVV: [REDACTED_CVV]"        ││
│  │                                                          ││
│  │   ✅ Permitir tarjetas de prueba (sin espacios):        ││
│  │      4111111111111111 (no tiene espacios = test)        ││
│  │                                                          ││
│  │   Si NO OK (datos sensibles residuales) → Error         ││
│  └─────────────────────────────────────────────────────────┘│
│                                                               │
│  ✅ RESULTADO: HU limpia, validada, sin datos reales        │
└──────────────────┬───────────────────────────────────────────┘
                   │ (SÍ, válida)
                   ▼
```

---

## 3. Diseñador: Orquestador Principal

```
┌─────────────────────────────────────────────────────────────────┐
│  ORQUESTADOR: DISEÑADOR (src/designer.py)                       │
│  (Modelo/Agente - toma decisiones)                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ PASO 1: Extraer Información de HU                      │  │
│  │                                                         │  │
│  │ hu.campos = [                                          │  │
│  │   {"nombre": "Titular", "tipo": "texto"},            │  │
│  │   {"nombre": "Número tarjeta", "tipo": "monetario"}, │  │
│  │   ...                                                 │  │
│  │ ]                                                      │  │
│  │                                                         │  │
│  │ Decisión Diseñador:                                    │  │
│  │ "Voy a generar casos para CADA tipo de campo"        │  │
│  │ Priority: HIGH-RISK PRIMERO                           │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ PASO 2: Init Loop (Iteración 1)                        │  │
│  │                                                         │  │
│  │ iteracion = 1                                          │  │
│  │ casos_aprobados = []                                  │  │
│  │ tokens_usados = 0                                     │  │
│  │ cobertura_actual = 0%                                 │  │
│  │                                                         │  │
│  │ while iteracion <= MAX_ITERACIONES (3):              │  │
│  │   # Loop principal aquí                                │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ PASO 3: Por Cada Campo → Solicita Edge Cases al MCP   │  │
│  │                                                         │  │
│  │ For campo in hu.campos:                                │  │
│  │   obtener_edge_cases(                                  │  │
│  │     campo_tipo = "monetario",  # Ej: tipo de tarjeta │  │
│  │     criticidad_minima = "high"                        │  │
│  │   )                                                     │  │
│  │                                                         │  │
│  │ Respuesta del MCP:                                     │  │
│  │ [                                                      │  │
│  │   {                                                    │  │
│  │     "id": "EC-001-MON",                              │  │
│  │     "descripcion": "Número tarjeta con chars",      │  │
│  │     "criticidad": "high",                            │  │
│  │     "ejemplo_entrada": "4111AAAA2222BBBB",          │  │
│  │     "resultado_esperado": "Validación rechaza"      │  │
│  │   },                                                  │  │
│  │   {                                                    │  │
│  │     "id": "EC-002-MON",                              │  │
│  │     "descripcion": "Número tarjeta incompleto",      │  │
│  │     "criticidad": "high",                            │  │
│  │     "ejemplo_entrada": "411111111111",               │  │
│  │     "resultado_esperado": "Validación rechaza"       │  │
│  │   },                                                  │  │
│  │   ...                                                  │  │
│  │ ]                                                      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ PASO 4: Generar Caso Único                             │  │
│  │                                                         │  │
│  │ for edge_case in edge_cases:  # Max 2-5 por iter    │  │
│  │   # Crear estructura de prueba                         │  │
│  │   test_steps = [                                       │  │
│  │     {                                                  │  │
│  │       "step": 1,                                       │  │
│  │       "action": "Acceder al formulario",             │  │
│  │       "expected": "Formulario visible"               │  │
│  │     },                                                 │  │
│  │     {                                                  │  │
│  │       "step": 2,                                       │  │
│  │       "action": f"Ingrese {edge_case.ejemplo}",      │  │
│  │       "expected": f"{edge_case.resultado_esperado}"  │  │
│  │     },                                                 │  │
│  │     {                                                  │  │
│  │       "step": 3,                                       │  │
│  │       "action": "Haga clic en 'Confirmar Pago'",     │  │
│  │       "expected": f"{edge_case.resultado_esperado}"  │  │
│  │     }                                                  │  │
│  │   ]                                                     │  │
│  │                                                         │  │
│  │   caso = TestCase(                                     │  │
│  │     id=f"CASO-{iter}-{i}",                          │  │
│  │     title=edge_case.descripcion,                     │  │
│  │     edge_case_covered=edge_case.id,                 │  │
│  │     test_steps=test_steps                           │  │
│  │   )                                                    │  │
│  │                                                         │  │
│  │ Decisión Diseñador:                                    │  │
│  │ "Este caso toca el edge case de tarjeta inválida"   │  │
│  │ "Voy a validar que existe en el catálogo"           │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ PASO 5: Validar que Edge Case Existe (Hallucination)  │  │
│  │                                                         │  │
│  │ # Evita que el modelo invente edge cases               │  │
│  │ validar_edge_case(caso.edge_case_covered)            │  │
│  │   → ¿"EC-001-MON" existe en catálogo?                │  │
│  │                                                         │  │
│  │ Si NO → Rechazar caso                                  │  │
│  │ Si SÍ → Continuar                                      │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ PASO 6: Sanitizar Antes de Revisor                     │  │
│  │                                                         │  │
│  │ caso_sanitized = DataMasker.mask_output(caso)         │  │
│  │   → Enmascarar [REDACTED_CARD], [REDACTED_CVV]       │  │
│  │                                                         │  │
│  │ ✅ Resultado seguro                                    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ PASO 7: Invocar Revisor (Subagente)                    │  │
│  │                                                         │  │
│  │ revisor.evaluar_caso(caso_sanitized, golden_set)      │  │
│  │   # Revisor toma decisión INDEPENDIENTE                │  │
│  │   # Con contexto limpio (solo caso + golden_set)      │  │
│  │                                                         │  │
│  │ ➜ Ver Sección 4 (Revisor)                             │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ PASO 8: Después del Revisor (Aprobado o Rechazado)    │  │
│  │                                                         │  │
│  │ if veredicto == "APROBADO":                            │  │
│  │   casos_aprobados.append(caso)                        │  │
│  │   print(f"✅ {caso.id} aprobado (score: {score})")   │  │
│  │ else:                                                   │  │
│  │   print(f"❌ {caso.id} rechazado")                    │  │
│  │   print(f"   Feedback: {feedback}")                  │  │
│  │   # Loop: volver a generar este o ir al siguiente    │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ PASO 9: Calcular Cobertura                             │  │
│  │                                                         │  │
│  │ stats = obtener_estadisticas_cobertura()              │  │
│  │   → total_edge_cases = 10                              │  │
│  │                                                         │  │
│  │ cobertura = len(casos_aprobados) / total_edge_cases   │  │
│  │           = 2 / 10                                     │  │
│  │           = 20%                                        │  │
│  │                                                         │  │
│  │ print(f"Cobertura actual: {cobertura:.0%}")          │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ PASO 10: Chequear Frenos (Guardrails de Loop)         │  │
│  │                                                         │  │
│  │ if cobertura >= 0.80:                                  │  │
│  │   print("✅ Cobertura ≥80% alcanzada")               │  │
│  │   BREAK  # Salir del loop                              │  │
│  │                                                         │  │
│  │ elif tokens_usados > TOKEN_BUDGET (100k):             │  │
│  │   flags.append("budget-exhausted")                    │  │
│  │   print("❌ Token budget excedido")                  │  │
│  │   BREAK                                                │  │
│  │                                                         │  │
│  │ elif iteracion >= MAX_ITERACIONES (3):                │  │
│  │   if cobertura < 0.80:                                │  │
│  │     flags.append("coverage-partial")                 │  │
│  │   print("⛔ Max iteraciones alcanzadas")            │  │
│  │   BREAK                                                │  │
│  │                                                         │  │
│  │ else:                                                   │  │
│  │   iteracion += 1                                        │  │
│  │   continue  # Siguiente iteración                     │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼ (Si todos OK)
```

---

## 4. Revisor: Validación con Rúbrica

```
┌──────────────────────────────────────────────────────────────┐
│  SUBAGENTE: REVISOR (src/reviewer.py)                        │
│  (Modelo/Agente - valida con rúbrica)                        │
│                                                               │
│  INPUT (context limpio):                                     │
│  ├─ caso: TestCase (estructura generada)                    │
│  ├─ golden_set: list[TestCase] (6 referencia)              │
│  └─ Rúbrica: 5 criterios                                    │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ RÚBRICA 5-CRITERIOS (escala 0-5)                      │ │
│  │                                                        │ │
│  │ 1. COMPLETITUD (¿toca realmente el edge case?)        │ │
│  │    Heurística:                                         │ │
│  │    • Si <2 pasos: 2/5                                 │ │
│  │    • Si tiene validación de rechazo: +2               │ │
│  │    • Si tiene 3+ pasos bien definidos: 5/5            │ │
│  │                                                        │ │
│  │    Ejemplo:                                            │ │
│  │    Caso: "Tarjeta expirada"                           │ │
│  │    Steps: [acceder, ingresar fecha 05/23, clic, ...]  │ │
│  │    ✅ Score: 5.0 (completo)                           │ │
│  │                                                        │ │
│  │ 2. CLARIDAD (¿pasos ejecutables, sin ambigüedad?)     │ │
│  │    Heurística:                                         │ │
│  │    • action/expected <10 chars: -0.5 c/u             │ │
│  │    • Palabras vagas ("algo", "aquí"): -0.5            │ │
│  │                                                        │ │
│  │    Ejemplo CLARO:                                      │ │
│  │    Step: "Ingrese CVV: 12"                            │ │
│  │    Expected: "Error: 'CVV debe ser 3-4 dígitos'"      │ │
│  │    ✅ Score: 5.0                                      │ │
│  │                                                        │ │
│  │    Ejemplo CONFUSO:                                    │ │
│  │    Step: "Haz algo aquí"                              │ │
│  │    Expected: "Pasa"                                    │ │
│  │    ❌ Score: 2.0                                      │ │
│  │                                                        │ │
│  │ 3. CRITICIDAD (¿high-risk primero?)                   │ │
│  │    Heurística:                                         │ │
│  │    • HIGH: 5.0                                        │ │
│  │    • MEDIUM: 3.0                                      │ │
│  │    • LOW: 2.0                                         │ │
│  │                                                        │ │
│  │ 4. INDEPENDENCIA (¿funciona aislado?)                 │ │
│  │    Heurística:                                         │ │
│  │    • Primer step es "acceder/abrir": 5.0             │ │
│  │    • Depende de pre-condición: 2.0                    │ │
│  │                                                        │ │
│  │ 5. TRAZABILIDAD (¿vinculado a HU + golden_set?)      │ │
│  │    Heurística:                                         │ │
│  │    • edge_case_covered existe: +3.0                   │ │
│  │    • Edge case está en golden_set: +1.0 (max 5.0)    │ │
│  │    • No hay referencia: 2.0                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ CÁLCULO DE SCORE                                       │ │
│  │                                                        │ │
│  │ promedio = (C1 + C2 + C3 + C4 + C5) / 5               │ │
│  │                                                        │ │
│  │ Ejemplo Caso Aprobado:                                │ │
│  │ Completitud: 5.0                                      │ │
│  │ Claridad:    4.0                                      │ │
│  │ Criticidad:  5.0                                      │ │
│  │ Independencia: 5.0                                    │ │
│  │ Trazabilidad: 4.0                                     │ │
│  │ ───────────────────                                   │ │
│  │ Promedio: (5+4+5+5+4)/5 = 4.6                         │ │
│  │                                                        │ │
│  │ ✅ 4.6 ≥ THRESHOLD (4.0) → APROBADO                 │ │
│  │                                                        │ │
│  │ Ejemplo Caso Rechazado:                               │ │
│  │ Completitud: 2.5  ← Falta validación                 │ │
│  │ Claridad:    3.0  ← Pasos poco claros                │ │
│  │ Criticidad:  5.0                                      │ │
│  │ Independencia: 4.0                                    │ │
│  │ Trazabilidad: 3.0  ← No vinculado bien               │ │
│  │ ───────────────────                                   │ │
│  │ Promedio: (2.5+3+5+4+3)/5 = 3.5                      │ │
│  │                                                        │ │
│  │ ❌ 3.5 < THRESHOLD (4.0) → RECHAZADO               │ │
│  │    Feedback: "Completitud baja (2.5). Falta          │ │
│  │    validación de rechazo. Claridad baja (3.0).       │ │
│  │    Pasos poco claros."                               │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ TIMEOUT (Fallback Optimista)                          │ │
│  │                                                        │ │
│  │ if tiempo > 30 segundos:                              │ │
│  │   # Revisor tardó demasiado                           │ │
│  │   flag = "not-reviewed"                              │ │
│  │   veredicto = "APROBADO"  # Asumir OK (fallback)      │ │
│  │   print("⚠️ Timeout (30s). Asumido como aprobado")   │ │
│  │                                                        │ │
│  │ RAZONAMIENTO:                                         │ │
│  │ Mejor publicar un caso sin validar que perder tiempo  │ │
│  │ (será auditado después por Product Owner)             │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  OUTPUT:                                                      │
│  ├─ veredicto: "APROBADO" o "RECHAZADO"                 │
│  ├─ feedback: string (explicación si rechaza)            │
│  └─ score: float (promedio de rúbrica)                   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
```

---

## 5. Especialista en Cobertura (Paralelo)

```
┌──────────────────────────────────────────────────────────────┐
│  SUBAGENTE: ESPECIALISTA EN COBERTURA                        │
│  (Paralelo, detecta gaps)                                    │
│                                                               │
│  Trigger: Después de cada iteración                          │
│                                                               │
│  INPUT:                                                      │
│  ├─ casos_aprobados: [CASO-1, CASO-2, ...]               │
│  ├─ total_edge_cases: 10                                   │
│  └─ criticidad_minima: "high"                              │
│                                                               │
│  ANÁLISIS:                                                   │
│  • ¿Qué edge cases NO están cubiertos?                     │
│  • Prioridad por criticidad                                │
│  • Top 3 gaps con sugerencias concretas                    │
│                                                               │
│  Ejemplo (Iteración 1):                                     │
│  Casos aprobados: [EC-001-MON, EC-003-FEC] (2/10 = 20%)  │
│  Gaps detectados:                                           │
│    1. EC-002-MON (tarjeta incompleta) - HIGH              │
│    2. EC-004-CVV (CVV corto) - MEDIUM                     │
│    3. EC-005-TIT (titular vacío) - HIGH                   │
│                                                               │
│  Recomendación: "CONTINUAR. Faltan 3 HIGH-RISK."          │
│                                                               │
│  OUTPUT:                                                     │
│  {                                                           │
│    "gaps": [EC-002, EC-004, EC-005],                      │
│    "recomendacion": "CONTINUAR",                          │
│    "confianza": 0.95                                       │
│  }                                                           │
│                                                               │
└──────────────────────────────────────────────────────────────┘
         │
         ▼ (Informa al Diseñador)
```

---

## 6. Guardrail de Salida: Validación Final

```
┌──────────────────────────────────────────────────────────────┐
│  GUARDRAIL DE SALIDA (src/guardrails.py)                    │
│  Antes de publicar casos_aprobados.json                      │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ CHECK 1: Sin Datos Sensibles                          │ │
│  │                                                        │ │
│  │ for caso in casos_aprobados:                          │ │
│  │   for step in caso.test_steps:                        │ │
│  │     # ¿Contiene tarjeta 16 dígitos sin [REDACTED]?   │ │
│  │     if re.search(r"\d{16}", step.action):             │ │
│  │       flag = "data-exposure-risk"                    │ │
│  │       return ERROR                                    │ │
│  │                                                        │ │
│  │     # ¿Contiene CVV sin [REDACTED]?                  │ │
│  │     if re.search(r"CVV.*\d{3,4}", step.action):       │ │
│  │       flag = "data-exposure-risk"                    │ │
│  │       return ERROR                                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ CHECK 2: Schema Válido                                │ │
│  │                                                        │ │
│  │ for caso in casos_aprobados:                          │ │
│  │   required = {id, title, criticidad, test_steps}      │ │
│  │   if not required.issubset(caso.keys()):              │ │
│  │     return ERROR: f"Campos faltantes: {required}"    │ │
│  │                                                        │ │
│  │   if len(caso.test_steps) == 0:                       │ │
│  │     return ERROR: "test_steps vacío"                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ CHECK 3: Edge Cases en Catálogo (Hallucinations)      │ │
│  │                                                        │ │
│  │ for caso in casos_aprobados:                          │ │
│  │   is_valid = validar_edge_case(caso.edge_case_covered)│ │
│  │   if not is_valid:                                    │ │
│  │     return ERROR: f"Hallucination: {edge_case}"      │ │
│  │                                                        │ │
│  │ # Esto no debería pasar (ya se validó antes)         │ │
│  │ # Pero es double-check de seguridad                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  Si TODO OK:                                                 │
│  ✅ Publicar casos_aprobados.json                           │
│                                                               │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
```

---

## 7. Product Owner: Aprobación Batch

```
┌──────────────────────────────────────────────────────────────┐
│  PRODUCT OWNER (Persona - Usuario Final)                     │
│                                                               │
│  PAUSA AQUÍ:                                                 │
│  • Todos los N casos generados                              │
│  • Todos aprobados por Revisor                              │
│  • Guardrail de salida: ✅ OK                               │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ REVISIÓN DEL BATCH COMPLETO                           │ │
│  │                                                        │ │
│  │ Product Owner abre: output/casos_aprobados.json       │ │
│  │                                                        │ │
│  │ Valida:                                               │ │
│  │ 1. ¿Los N casos cubren lo que necesito?             │ │
│  │ 2. ¿Cobertura ≥80%?                                 │ │
│  │ 3. ¿Casos ejecutables (puedo correrlos)?            │ │
│  │ 4. ¿Faltan escenarios críticos?                     │ │
│  │                                                        │ │
│  │ Veredicto:                                            │ │
│  │ ✅ APRUEBA → Publicar JSON + tracer (FIN OK)        │ │
│  │ ❌ RECHAZA → Feedback al Diseñador (RE-ITERAR)     │ │
│  │              "Falta validación de X"                │ │
│  │              "Este caso no es claro"               │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
└──────────────────────────────────────────────────────────────┘
         │
    ┌────┴──────┐
    │            │
  APRUEBA    RECHAZA
    │            │
    ▼            ▼
  FIN OK    (Feedback →
  Publicar   Diseñador re-itera)
```

---

## 8. Output Final

```
output/
├── casos_aprobados.json
│   {
│     "timestamp": "2026-11-18T00:28:00Z",
│     "casos_totales": 4,
│     "cobertura": 0.85,
│     "casos": [
│       {
│         "id": "CASO-1-1",
│         "title": "Número tarjeta con chars alfabéticos",
│         "edge_case_covered": "EC-001-MON",
│         "criticidad": "high",
│         "test_steps": [...],
│         "aprobado": true,
│         "score_rubrica": 4.6
│       },
│       ...
│     ],
│     "flags": []
│   }
│
└── execution.log
    Timestamp: 2026-11-18T00:28:00Z
    Iteraciones: 2
    Casos generados: 5
    Casos aprobados: 4
    Cobertura: 85.0%
    Tokens usados: 45230
    Flags: ninguno

✅ FIN: Éxito
   • 4 casos sin datos sensibles
   • Cobertura 85% (≥80%)
   • Todos aprobados por Revisor
   • Product Owner validó batch
   • Listo para ejecutar en staging
```

---

## Puntos Clave del Flujo

### 1. **Línea Roja de Responsabilidades**
```
Diseñador DECIDE:     Qué edge cases perseguir, orden de prioridad
Revisor VALIDA:      Si cada caso cumple rúbrica
Product Owner APRUEBA: Batch completo (uso en producción)
```

### 2. **Frenos de Seguridad**
```
ENTRADA:      Enmascarar datos reales
DURANTE:      Validar hallucinations, timeout Revisor
SALIDA:       Double-check de seguridad
```

### 3. **Guardrails de Control**
```
Max 3 iteraciones → coverage-partial
Tokens >100k → budget-exhausted
Revisor >30s → not-reviewed (con flag)
Cobertura <80% al iter=3 → coverage-partial
```

### 4. **Paralelización**
```
Diseñador genera casos
    ↓
Revisor valida (subagente)
Especialista en Cobertura analiza gaps (subagente paralelo)
    ↓
Diseñador itera con feedback
```

---

## Resumen Visual: De Entrada a Salida

```
Historia Usuario   Guardrail    Diseñador      MCP         Revisor
(JSON)             (Validar)    (Generar)      (Edge)      (Rúbrica)
   │                 │              │          │              │
   ├──Entrada────────┤              │          │              │
   │                 ├─Limpia────────┤         │              │
   │                 │               ├─Obtiene─┤              │
   │                 │               │         ├─Envía────────┤
   │                 │               │         │              ├─Evalúa
   │                 │               │         │              │  (5 criterios)
   │                 │               │         │              │
   │                 │               │◄────────┴──Respuesta───┤
   │                 │               │         │              │
   │                 │               ├─Genera caso            │
   │                 │               ├─Sanitiza               │
   │                 │               │                        │
   │                 │               ├─Valida EC existe───────┤
   │                 │               ├─Envía a Revisor───────→├─Score ≥4.0?
   │                 │               │                        │
   │                 │               │                    SÍ/NO
   │                 │               │                        │
   │                 │◄──────────────┴────────────────────────┤
   │                 │  (feedback si NO)
   │                 │
   │     (FIN ERROR/OK)
   │
  Guardrail Salida
   │
   ▼
Output:
├─ casos_aprobados.json (sin datos sensibles)
└─ execution.log (trace)
```

---

## Glosario Rápido

| Término | Definición |
|---------|-----------|
| **Edge Case** | Escenario excepcional (ej: tarjeta expirada, CVV inválido) |
| **Guardrail** | Control de seguridad (valida entrada/salida) |
| **MCP** | Catálogo de edge cases por tipo de campo |
| **Revisor** | Subagente que valida con rúbrica 5-criterios |
| **Cobertura** | % de edge cases cubiertos (≥80% objetivo) |
| **Hallucination** | Edge case inventado (rechazado automáticamente) |
| **Sanitizar** | Enmascarar datos sensibles ([REDACTED_*]) |
| **Flag** | Alerta (coverage-partial, budget-exhausted, not-reviewed) |
| **Golden Set** | 6 casos de referencia para benchmark |
