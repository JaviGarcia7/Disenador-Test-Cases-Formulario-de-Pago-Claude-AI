# 📊 BPMN: Explicación Detallada - Flujo Completo

## 🏗️ Estructura General del BPMN

El BPMN está organizado en **6 carriles (swimlanes)** horizontales que representan actores/sistemas:

```
┌─────────────────────────────────────────────────────────────────────┐
│ CARRIL 1: Usuario (CLI)                                             │
│ Envía Historia de Usuario                                           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ CARRIL 2: Guardrails de Entrada (Código - Seguridad)               │
│ Validación + Enmascaramiento de datos                              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ CARRIL 3: Orquestador Diseñador (Modelo/Agente)                   │
│ Loop iterativo (3 max) - Genera casos                              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ CARRIL 4: Servidor MCP (Código - Catálogo)                        │
│ Proporciona edge cases del catálogo                                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ CARRIL 5: Subagentes (Modelo)                                      │
│ • Revisor: Valida con rúbrica 5-criterios                          │
│ • Especialista en Cobertura: Detecta gaps (paralelo)              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ CARRIL 6: Product Owner (Persona)                                  │
│ Aprobación final de batch completo                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔴 INICIO: El Usuario Envía Historia de Usuario

```
CARRIL 1 (Usuario):
                    ●
                    │
                    ▼
          ┌─────────────────┐
          │ Envía HU.json   │
          │ (CLI)           │
          └────────┬────────┘
                   │
                   ▼ (Flujo a Guardrail)
```

**¿Qué sucede?**
- El usuario ejecuta: `./run_cli.sh --hu historia_usuario.json`
- El CLI recibe el archivo JSON con:
  ```json
  {
    "id": "HU-001",
    "descripcion": "Formulario de Pago",
    "campos": [
      {"nombre": "Titular", "tipo": "texto"},
      {"nombre": "Número tarjeta", "tipo": "monetario"},
      {"nombre": "Fecha expiración", "tipo": "fecha"},
      {"nombre": "CVV", "tipo": "texto"}
    ]
  }
  ```

---

## 🛡️ CARRIL 2: GUARDRAIL DE ENTRADA (Primer Control de Seguridad)

```
CARRIL 2 (Guardrails Entrada):
                        ┌─────────────────────┐
                        │ Validar + Enmascarar│
                        │ • Schema JSON válido?
                        │ • Tarjetas reales?
                        │ • CVV suelto?
                        └────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
              Decisión: ¿OK?                 │
              (Compuerta Diamante)           │
                    │                         │
          ┌─────────┴──────────┐            │
          │                    │            │
         SÍ                   NO            │
          │                    │            │
          ▼                    ▼            │
      Continuar           ERROR:            │
      (flujo OK)          "HU inválida"    │
                          (Fin ERROR)       │
```

### Detalle: ¿Qué valida?

**1. Validación de Schema**
```
¿El JSON tiene estructura correcta?

Esperado:
{
  "id": string,
  "descripcion": string,
  "campos": [
    {
      "nombre": string,
      "tipo": string (uno de: texto, monetario, email, teléfono, select, checkbox, fecha)
    }
  ]
}

Si FALTA algo:
❌ Rechazo: "Error: HU inválida"
   → Flujo → Fin ERROR
```

**2. Enmascaramiento de Datos Sensibles**
```
Busca ANTES de que el modelo vea:

Patrón 1: Tarjetas REALES
  • Regex: /\d{4}\s\d{4}\s\d{4}\s\d{4}/
  • Ejemplo: "4111 1111 1111 1111" (CON ESPACIOS = real)
  • Acción: Reemplazar → "[REDACTED_CARD]"

Patrón 2: CVV fuera de contexto
  • Regex: /CVV.*\d{3,4}/ (si no está en "validacion" o "ejemplo")
  • Ejemplo: "CVV: 123" (suelto)
  • Acción: Reemplazar → "CVV: [REDACTED_CVV]"

Patrón 3: Permitir tarjetas DE PRUEBA
  • Ejemplo: 4111111111111111 (SIN ESPACIOS)
  • Razón: Es estándar en testing, no es dato real
  • Acción: PERMITIR (no enmascarar)
```

**3. Si NO OK**
```
Ejemplos de rechazo:
- "JSON malformado"
- "Campo 'campos' faltante"
- "Tipo de campo no soportado: 'boolean'"
- "Contiene tarjeta real no autorizada"

Resultado:
┌─────────────────────────┐
│ Error: HU inválida      │
│ Razón: [descripción]    │
│                         │
│ FIN ERROR ●             │
└─────────────────────────┘
```

**✅ Si OK:**
```
Resultado:
┌─────────────────────────┐
│ HU limpia + validada    │
│ Listo para Diseñador    │
│                         │
│ CONTINUAR ▼             │
└─────────────────────────┘
```

---

## 🎯 CARRIL 3: DISEÑADOR - Orquestador Principal (Loop)

```
CARRIL 3 (Diseñador):

┌──────────────────────┐
│ 1. Parsear HU        │  ← Extrae campos
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 2. Init Loop:        │  ← Prepara variables
│ iteración = 1        │
│ casos_aprobados = [] │
│ tokens = 0           │
│ cobertura = 0%       │
└──────────┬───────────┘
           │
           ▼
    ╔══════════════════════════════════════════╗
    ║ LOOP PRINCIPAL (MAX 3 ITERACIONES)       ║
    ║                                          ║
    ║ 3. Por cada campo en HU:                ║
    ║    Solicita edge cases → MCP            ║
    ║                                          ║
    ║ 4. Por cada edge case:                  ║
    ║    Genera caso de prueba                ║
    ║    (estructura con test_steps)          ║
    ║                                          ║
    ║ 5. Valida:                              ║
    ║    ¿Edge case existe en MCP?            ║
    ║    (Detecta hallucinations)             ║
    ║                                          ║
    ║ 6. Sanitiza:                            ║
    ║    Enmascaramiento de salida            ║
    ║                                          ║
    ║ 7. Invoca Revisor:                      ║
    ║    Pasa caso limpio a validar           ║
    ║                                          ║
    ║ 8. Si APROBADO:                         ║
    ║    Agrega a casos_aprobados[]           ║
    ║    Calcula cobertura                    ║
    ║                                          ║
    ║ 9. Si RECHAZADO:                        ║
    ║    Itera (feedback → mejor caso)        ║
    ║                                          ║
    ║ 10. Chequea Frenos:                     ║
    ║     ¿Cobertura ≥80%? → SALIR            ║
    ║     ¿Iteraciones=3? → SALIR             ║
    ║     ¿Tokens>100k? → SALIR               ║
    ║                                          ║
    ╚═════════════┬══════════════════════════╝
                  │
           ¿Continuar Loop?
                  │
        ┌─────────┴─────────┐
        │                   │
       SÍ                   NO
        │                   │
    Iteración++      Generar Reporte
        │            + Flags
        │                   │
        └────────┬──────────┘
                 │
                 ▼
         (Continúa...)
```

### Desglose detallado de cada paso:

#### **PASO 3: Solicitar Edge Cases al MCP**

```
Usuario tiene 4 campos:
├─ Titular (tipo: texto)
├─ Número tarjeta (tipo: monetario)
├─ Fecha expiración (tipo: fecha)
└─ CVV (tipo: texto)

Diseñador ITERA por cada uno:

For campo in hu.campos:
  obtener_edge_cases(
    campo_tipo = campo.tipo,
    criticidad_minima = "high"
  )

Respuesta del MCP para "monetario":
[
  {
    "id": "EC-001-MON",
    "descripcion": "Número tarjeta con chars alfabéticos",
    "criticidad": "high",
    "ejemplo_entrada": "4111AAAA2222BBBB",
    "resultado_esperado": "Validación rechaza"
  },
  {
    "id": "EC-002-MON",
    "descripcion": "Número tarjeta incompleto",
    "criticidad": "high",
    "ejemplo_entrada": "411111111111",
    "resultado_esperado": "Validación rechaza"
  }
]
```

---

## 🔗 CARRIL 4: SERVIDOR MCP (Catálogo de Edge Cases)

```
CARRIL 4 (MCP Server):
                        │ (Solicitud: obtener_edge_cases)
                        ▼
          ┌──────────────────────────┐
          │ 1. Validar tipo_campo    │
          │    ¿Es válido?           │
          └────────┬─────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
       SÍ                    NO
        │                     │
        ▼                     ▼
    Continuar           ERROR 400
    Buscar en           "Tipo no
    catálogo            soportado"
        │                     │
        ▼                     ▼
    ┌─────────────┐      Devuelve
    │ Buscar por  │      error
    │ criticidad  │
    │ mínima      │
    └──────┬──────┘
           │
           ▼
    ┌──────────────────┐
    │ Retorna lista:   │
    │ [EC-001, EC-002] │
    └──────────────────┘
```

### Tipos soportados y qué devuelve:

```
obtener_edge_cases(campo_tipo="monetario")
  ↓
Devuelve: [
  EC-001-MON (Tarjeta con chars)
  EC-002-MON (Tarjeta incompleta)
]

obtener_edge_cases(campo_tipo="fecha")
  ↓
Devuelve: [
  EC-003-FEC (Fecha expirada)
]

obtener_edge_cases(campo_tipo="texto")
  ↓
Devuelve: [
  EC-004-CVV (CVV < 3 dígitos)
  EC-005-TIT (Titular vacío)
]

Total catálogo: ~10 edge cases
```

**Si falla MCP:**

```
Compuerta: ¿MCP OK?
       │
    NO │ (MCP timeout/error)
       ▼
┌─────────────────────────┐
│ REINTENTOS (3x + backoff)│
│ • Intento 1: espera 1s  │
│ • Intento 2: espera 2s  │
│ • Intento 3: espera 4s  │
└──────────┬──────────────┘
           │
      ¿Recuperado?
           │
    ┌──────┴──────┐
    │             │
   SÍ            NO
    │             │
    ▼             ▼
 Continuar   ERROR FATAL
  (OK)       "MCP sin
             recuperación"
             (Fin ERROR)
```

---

## 🧩 PASO 4-6: Diseñador Genera + Valida Caso

```
CARRIL 3 (Diseñador):

Paso 4: GENERAR CASO
────────────────────

Para edge_case in edge_cases:  # EC-001-MON
  
  test_steps = [
    {
      "step": 1,
      "action": "Acceder al formulario de pago",
      "expected": "Formulario visible"
    },
    {
      "step": 2,
      "action": f"Ingrese número tarjeta: {edge_case.ejemplo}",
      # = "Ingrese número tarjeta: 4111AAAA2222BBBB"
      "expected": f"{edge_case.resultado_esperado}"
      # = "Validación rechaza"
    },
    {
      "step": 3,
      "action": "Haga clic en 'Confirmar Pago'",
      "expected": "Mensaje de error de validación"
    }
  ]
  
  caso = TestCase(
    id=f"CASO-{iteracion}-{contador}",
    # = "CASO-1-1"
    title=edge_case.descripcion,
    # = "Número tarjeta con chars alfabéticos"
    edge_case_covered=edge_case.id,
    # = "EC-001-MON"
    criticidad=edge_case.criticidad,
    # = "high"
    test_steps=test_steps
  )


Paso 5: VALIDAR HALLUCINATIONS (¿Edge case existe?)
──────────────────────────────────────

# Previene que el modelo invente edge cases

Compuerta: ¿Edge case "EC-001-MON" existe?
       │
    ┌──┴──┐
   SÍ    NO
    │     │
    ▼     ▼
 OK  RECHAZAR CASO
       (Hallucination
        detectado)


Paso 6: SANITIZAR (Enmascaramiento previo a Revisor)
────────────────────────────────────

caso_sanitized = DataMasker.mask_output(caso)

Busca en test_steps:
├─ Tarjetas 16 dígitos → [REDACTED_CARD]
├─ CVV 3-4 dígitos → [REDACTED_CVV]
└─ Otros datos sensibles → Sanitizar

Ejemplo:
ANTES:
  "action": "Ingrese tarjeta: 4111111111111111"
DESPUÉS:
  "action": "Ingrese tarjeta: [REDACTED_CARD]"

Compuerta: ¿Seguro?
       │
    ┌──┴──┐
   SÍ    NO
    │     │
    ▼     ▼
Pasar a  ERROR:
Revisor  "data-exposure-risk"
         (Fin ERROR)
```

---

## 👤 CARRIL 5A: REVISOR (Subagente - Validación Independiente)

```
CARRIL 5 (Revisor):
                        │ (Recibe: caso limpio)
                        ▼
          ┌────────────────────────┐
          │ EVALÚA CON RÚBRICA     │
          │ 5 criterios (0-5):     │
          │ 1. Completitud         │
          │ 2. Claridad            │
          │ 3. Criticidad          │
          │ 4. Independencia       │
          │ 5. Trazabilidad        │
          └────────┬───────────────┘
                   │
         Compuerta: ¿Timeout >30s?
                   │
            ┌──────┴──────┐
           SÍ            NO
            │             │
            ▼             ▼
        TIMEOUT      Calcular Score
        Flag:        Promedio de
        "not-        5 criterios
        reviewed"    │
            │        ▼
            │    ┌───────────────┐
            │    │ Score ≥ 4.0?  │
            │    └───┬───────────┘
            │        │
            │   ┌────┴────┐
            │   │         │
            │  SÍ        NO
            │   │         │
            │   ▼         ▼
            ▼ APROBADO RECHAZADO
        Asumir    (veredicto (veredicto
        OK        binario)   binario)
                    │         │
                    ▼         ▼
               ✅ Agregar   ❌ Feedback
               a lista      al Diseñador
```

### Rúbrica 5-Criterios: Ejemplo Detallado

**CRITERIO 1: COMPLETITUD (¿toca realmente el edge case?)**

```
CASO EVALUADO:
  title: "Número tarjeta con caracteres alfabéticos"
  test_steps: [
    {step: 1, action: "Acceder formulario", expected: "Visible"},
    {step: 2, action: "Ingrese 4111AAAA2222BBBB", expected: "Validación rechaza"},
    {step: 3, action: "Haga clic Confirmar", expected: "Error de validación"}
  ]

EVALUACIÓN:
├─ ¿El caso tiene pasos? SÍ (3 pasos) → +1.0
├─ ¿Toca el edge case? SÍ (paso 2 ingresa tarjeta inválida) → +2.0
├─ ¿Valida rechazo? SÍ (paso 3 verifica error) → +2.0
└─ SCORE COMPLETITUD: 5.0/5.0 ✅
```

**CRITERIO 2: CLARIDAD (¿pasos ejecutables sin ambigüedad?)**

```
EVALUACIÓN:
├─ Paso 1: "Acceder formulario" (17 chars, claro) → +1.0
├─ Paso 2: "Ingrese 4111AAAA2222BBBB" (específico) → +1.5
├─ Paso 3: "Haga clic Confirmar" (claro) → +1.5
│
├─ ¿Hay palabras vagas? No ("algo", "aquí", "etc")
├─ ¿Expected es específico? Sí
└─ SCORE CLARIDAD: 4.0/5.0 ✅
```

**CRITERIO 3: CRITICIDAD (¿high-risk primero?)**

```
EVALUACIÓN:
├─ edge_case.criticidad = "high"
├─ ¿Afecta seguridad? Sí (validación de tarjeta)
├─ ¿Es business-critical? Sí
└─ SCORE CRITICIDAD: 5.0/5.0 ✅
```

**CRITERIO 4: INDEPENDENCIA (¿funciona aislado?)**

```
EVALUACIÓN:
├─ ¿Primer step es "acceder"? Sí
├─ ¿Depende de pre-condición? No
├─ ¿Puede ejecutarse sin contexto previo? Sí
└─ SCORE INDEPENDENCIA: 5.0/5.0 ✅
```

**CRITERIO 5: TRAZABILIDAD (¿vinculado a HU + golden_set?)**

```
EVALUACIÓN:
├─ edge_case_covered = "EC-001-MON"
├─ ¿Existe en MCP? Sí
├─ ¿Está en golden_set? Sí (es uno de los 6 casos)
└─ SCORE TRAZABILIDAD: 4.0/5.0 ✅

CÁLCULO FINAL:
(5.0 + 4.0 + 5.0 + 5.0 + 4.0) / 5 = 4.6/5.0

¿4.6 ≥ THRESHOLD (4.0)?
→ SÍ → APROBADO ✅
```

**Ejemplo de RECHAZO:**

```
CASO EVALUADO:
  title: "CVV inválido"
  test_steps: [
    {step: 1, action: "Haz algo", expected: "Pasa"},
    {step: 2, action: "Ingresa CVV", expected: "Error"}
  ]

EVALUACIÓN:
├─ COMPLETITUD: 2.5 ← Falta validación explícita
├─ CLARIDAD: 3.0 ← "Haz algo", "Pasa" → muy vago
├─ CRITICIDAD: 5.0
├─ INDEPENDENCIA: 4.0
├─ TRAZABILIDAD: 3.0 ← No trazable bien

PROMEDIO: (2.5 + 3.0 + 5.0 + 4.0 + 3.0) / 5 = 3.5/5.0

¿3.5 ≥ THRESHOLD (4.0)?
→ NO → RECHAZADO ❌

FEEDBACK:
"Completitud baja (2.5). El caso no valida realmente
el rechazo. Claridad baja (3.0). Los pasos son
imprecisos ('Haz algo'). Trazabilidad baja (3.0).
Edge case no bien vinculado a la HU."
```

---

## 🔄 CARRIL 5B: ESPECIALISTA EN COBERTURA (Paralelo)

```
CARRIL 5 (Especialista - PARALELO):
                        │ (Recibe: casos_aprobados)
                        ▼
          ┌────────────────────────────────┐
          │ ANÁLISIS DE GAPS               │
          │                                │
          │ Input:                         │
          │ • casos_aprobados = [CASO-1-1]│
          │ • total_edge_cases = 10        │
          │ • criticidad_minima = "high"   │
          └────────┬─────────────────────┘
                   │
                   ▼
          ┌────────────────────────────────┐
          │ Calcular cobertura             │
          │ 1 caso / 10 total = 10%        │
          │ (Necesito 80%)                 │
          └────────┬─────────────────────┘
                   │
                   ▼
          ┌────────────────────────────────┐
          │ Detectar TOP 3 GAPS            │
          │ (Edge cases NO cubiertos)      │
          │                                │
          │ Ranking 1: EC-002-MON (HIGH)   │
          │   Por qué falta: No hay caso  │
          │   de tarjeta incompleta       │
          │                                │
          │ Ranking 2: EC-003-FEC (HIGH)   │
          │   Por qué falta: No hay caso  │
          │   de fecha expirada           │
          │                                │
          │ Ranking 3: EC-004-CVV (MED)    │
          │   Por qué falta: No hay caso  │
          │   de CVV corto                │
          └────────┬─────────────────────┘
                   │
                   ▼
          ┌────────────────────────────────┐
          │ RECOMENDACIÓN                  │
          │ "CONTINUAR ITERANDO"           │
          │ Faltan 3 HIGH-RISK cases.      │
          │ Con 3 más → ~40% cobertura    │
          │ (aún bajo, pero avanzamos)    │
          │ Confianza: 95%                 │
          └────────────────────────────────┘
```

**¿Cómo se usa?**

El Especialista trabaja en PARALELO mientras el Diseñador sigue iterando.
Es información para el Diseñador sobre qué generar después.

---

## 🔁 VUELTA AL LOOP: Decisión de Frenos

```
CARRIL 3 (Diseñador - después de Revisor):

Después que todos los casos de la iteración
fueron aprobados o rechazados:

                    Compuerta: ¿FRENOS?
                    (3 condiciones)
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
    ¿Iter=3?         ¿Cobertura       ¿Tokens
     AND            ≥80%? OR          >100k?
    Coverage        Iter=3?
    <80%?
        │                 │                 │
        ▼                 ▼                 ▼
    FLAG:           SÍ:              SÍ:
    "coverage-      BREAK            BREAK
    partial"        (Salir           (Parar
    → PARAR         del loop)        inmediato)
                                     FLAG:
                                     "budget-
                                     exhausted"
                                     → PARAR
```

### Ejemplo de Decisión:

**Iteración 1:**
```
Casos aprobados: [CASO-1-1, CASO-1-2] = 2
Total edge cases: 10
Cobertura: 2/10 = 20% < 80% ❌
Iteraciones: 1 < 3 ✓

Frenos NO se activan:
→ CONTINUAR a Iteración 2 ✓
```

**Iteración 2:**
```
Casos aprobados: [CASO-1-1, CASO-1-2, CASO-2-1, CASO-2-2] = 4
Total edge cases: 10
Cobertura: 4/10 = 40% < 80% ❌
Iteraciones: 2 < 3 ✓

Frenos NO se activan:
→ CONTINUAR a Iteración 3 ✓
```

**Iteración 3 (última):**
```
Casos aprobados: [CASO-1-1, CASO-1-2, CASO-2-1, CASO-2-2,
                  CASO-3-1, CASO-3-2, CASO-3-3] = 7
Total edge cases: 10
Cobertura: 7/10 = 70% < 80% ❌
Iteraciones: 3 = MAX ⛔

Freno 1: ¿Iter=3 AND Coverage<80%?
→ SÍ → FLAG "coverage-partial" → SALIR
```

---

## 📋 PASO 10: Generar Reporte y Validar Salida

```
CARRIL 3 (Diseñador):
                        │ (Tras salir del loop)
                        ▼
          ┌──────────────────────────┐
          │ Generar Reporte Final    │
          │ • casos_aprobados.json   │
          │ • execution.log          │
          │ • flags (si los hay)     │
          └────────┬─────────────────┘
                   │
                   ▼ (Envía a Guardrail Salida)

CARRIL 2 (Guardrail Salida):
                        │
                        ▼
          ┌──────────────────────────┐
          │ VALIDAR SALIDA           │
          │                          │
          │ CHECK 1:                 │
          │ ¿Sin datos sensibles?    │
          │ • No tarjetas reales     │
          │ • No CVVs reales         │
          └────────┬─────────────────┘
                   │
          ┌────────┴────────┐
         SÍ                NO
          │                 │
          ▼                 ▼
     Continuar         ERROR:
                      "data-
          │            exposure
    CHECK 2:           -risk"
    ¿Schema            → FIN ERROR
    válido?
          │
    ┌─────┴─────┐
   SÍ          NO
    │           │
    ▼           ▼
 Continuar   ERROR:
             "schema
    │        -invalid"
    │        → FIN
    │
  CHECK 3:    ERROR
  ¿Edge
  cases
  en
  catálogo?
    │
 ┌──┴──┐
SÍ    NO
 │     │
 ▼     ▼
 OK  ERROR:
     "halluc
     -ination
     -detected"
     → FIN ERROR
```

### Checks Detallados:

**CHECK 1: Sin datos sensibles**

```
For caso in casos_aprobados:
  For step in caso.test_steps:
    
    # ¿Contiene tarjeta 16 dígitos?
    if re.search(r"\d{16}", step.action):
      → ERROR: data-exposure-risk
    
    # ¿Contiene CVV?
    if re.search(r"CVV.*\d{3,4}", step.action):
      → ERROR: data-exposure-risk
    
    # ¿Contiene teléfono o email real?
    # (Si es requerido)

Esperado:
"Ingrese tarjeta: [REDACTED_CARD]" ✅
"CVV: [REDACTED_CVV]" ✅
```

**CHECK 2: Schema válido**

```
For caso in casos_aprobados:
  required_fields = {
    id, title, criticidad, 
    edge_case_covered, test_steps
  }
  
  if not required_fields.issubset(caso.keys()):
    → ERROR: campos-faltantes
  
  if len(caso.test_steps) == 0:
    → ERROR: test-steps-vacio
  
  for step in caso.test_steps:
    if not {step, action, expected}.issubset(step.keys()):
      → ERROR: step-incompleto
```

**CHECK 3: Edge cases en catálogo**

```
For caso in casos_aprobados:
  exists = validar_edge_case(caso.edge_case_covered)
  
  if not exists:
    # Esto NO debería pasar (ya se validó antes)
    # Pero es double-check de seguridad
    → ERROR: hallucination-detected
```

---

## ✅ CARRIL 6: PRODUCT OWNER - Aprobación Final

```
CARRIL 6 (Product Owner):
                        │ (Recibe reporte validado)
                        ▼
          ┌──────────────────────────────┐
          │ PAUSA: REVISIÓN BATCH        │
          │                              │
          │ El Sistema para.             │
          │ Espera decisión humana.      │
          │                              │
          │ PO abre:                     │
          │ • casos_aprobados.json       │
          │ • execution.log              │
          │ • Cuenta: 7 casos            │
          │ • Cobertura: 70%             │
          │ • Flags: coverage-partial    │
          └────────┬─────────────────────┘
                   │
        PO Valida:
        - ¿Casos ejecutables?
        - ¿Cobertura acceptable?
        - ¿Faltan escenarios críticos?
                   │
          ┌────────┴────────┐
         SÍ                 NO
    APRUEBA            RECHAZA
          │                 │
          ▼                 ▼
      Publicar        Devolver Feedback
      Final JSON      al Diseñador
          │            │
          ▼            └──→ RE-ITERAR
                             (Vuelta a
                              Paso 1)
      ┌──────────┐
      │ FIN OK ●  │
      │ ÉXITO ✅   │
      └──────────┘
```

### Decisiones del Product Owner:

**OPCIÓN 1: APRUEBA**

```
"Los 7 casos cubren lo que necesitaba.
La cobertura al 70% es aceptable.
Los casos son ejecutables.
Listo para pasar a staging."

Resultado:
├─ Publicar: output/casos_aprobados.json
├─ Publicar: output/execution.log
└─ FIN: ÉXITO ✅
```

**OPCIÓN 2: RECHAZA con Feedback**

```
"Faltan validaciones de A y B.
Este caso (CASO-2-1) no es claro.
Necesito más cobertura de HIGH-RISK."

Resultado:
├─ Feedback → Diseñador
├─ RE-ITERAR (vuelve a Paso 1)
└─ (Si iter ya llegó a 3 y rechaza:
   Sale con flag "coverage-partial"
   PO revisa de nuevo)
```

---

## 🎬 Resumen Visual Completo del Flujo

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USUARIO ENVÍA HU.json                                        │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│ 2. GUARDRAIL ENTRADA: Validar + Enmascarar                      │
│    ¿OK? → Continuar                                             │
│    ¿ERROR? → Fin ERROR                                          │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│ 3. DISEÑADOR: LOOP (3 iteraciones máx)                          │
│                                                                 │
│   3.1 Parsear HU                                                │
│   3.2 Para cada campo:                                          │
│        ├─ Solicita edge cases → MCP                            │
│        ├─ Genera casos                                          │
│        ├─ Valida hallucinations                                │
│        ├─ Sanitiza                                              │
│        └─ Invoca Revisor ──┐                                   │
│                             │                                  │
│                      ┌──────▼──────┐                           │
│                      │ 4. REVISOR   │                           │
│                      │ Rúbrica      │                           │
│                      │ 5-criterios  │                           │
│                      │ Score ≥4.0?  │                           │
│                      └──────┬───────┘                           │
│                             │                                  │
│                      ┌──────┴──────────────────┐               │
│                      │                         │               │
│                  APROBADO              RECHAZADO               │
│                      │                  │                     │
│                  Agregar           Feedback                   │
│                  a lista           (re-generar)              │
│                      │                  │                     │
│        ┌─────────────┴──────────────────┴──┐                  │
│        │ 5. Calcular cobertura             │                  │
│        │ 6. Chequear frenos                │                  │
│        │    • ¿Cobertura ≥80%? → SALIR   │                  │
│        │    • ¿Iter = 3? → SALIR          │                  │
│        │    • ¿Tokens > 100k? → SALIR     │                  │
│        └─────────────┬──────────────────────┘                  │
│                      │                                         │
│   ¿Continuar Loop?                                             │
│        ├─ SÍ → Siguiente iteración                            │
│        └─ NO → Salir del loop                                 │
│                      │                                         │
└────────────────┬─────▼────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│ 7. GUARDRAIL SALIDA: Validar antes de publicar                 │
│    • ¿Sin datos sensibles?                                      │
│    • ¿Schema válido?                                            │
│    • ¿Edge cases en catálogo?                                   │
│    → SÍ a todo: Continuar                                       │
│    → NO en algo: Fin ERROR                                      │
└────────────────┬─────────────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────────────┐
│ 8. PRODUCT OWNER: Aprobación batch final                        │
│                                                                 │
│    Revisa batch completo:                                      │
│    • Todos los N casos                                          │
│    • Cobertura alcanzada                                        │
│    • Flags (si los hay)                                         │
│                                                                 │
│    Decisión:                                                    │
│    ├─ APRUEBA → FIN OK (publicar JSON) ✅                      │
│    └─ RECHAZA → RE-ITERAR (feedback → vuelta a Paso 1) ❌     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Puntos Críticos del BPMN

### 1. **5 Puntos de Rechazo (Fin ERROR)**

```
① GUARDRAIL ENTRADA: HU inválida
② MCP FALLA: 3 reintentos → sin recuperación
③ REVISOR TIMEOUT: Flag "not-reviewed" (pero continúa)
④ GUARDRAIL SALIDA: data-exposure-risk O schema-invalid
⑤ PRODUCT OWNER: Rechaza batch (re-iterar)
```

### 2. **3 Puntos de Parada (Salir del Loop)**

```
① Cobertura ≥80%
② Iteración = 3 (y cobertura <80% → flag coverage-partial)
③ Tokens >100k (flag budget-exhausted)
```

### 3. **Paralelización**

```
Mientras Diseñador itera:
├─ Revisor valida casos
└─ Especialista en Cobertura analiza gaps
    (NO bloquea, información paralela)
```

### 4. **Línea Roja de Responsabilidades**

```
Diseñador DECIDE:     Qué edge cases perseguir
Revisor VALIDA:       Si cumple rúbrica
Especialista ANALIZA: Qué falta (gaps)
Product Owner APRUEBA: Batch completo
```

### 5. **Guardrails en 3 Lugares**

```
① ENTRADA: Datos reales no vean al modelo
② DURANTE: Hallucinations bloqueadas
③ SALIDA: Validación final antes de publicar
```

---

## 🎊 Fin del BPMN

```
Resultado final:
├─ Casos aprobados: N (sin datos sensibles)
├─ Cobertura: X% (≥80% objetivo)
├─ Trace: execution.log
└─ Product Owner aprobó: SÍ

Output:
├─ output/casos_aprobados.json (publicable)
└─ output/execution.log (auditoría)

Estado: ✅ ÉXITO
```

---

## Matriz de Referencia Rápida

| Evento | Carril | Decisión | Resultado |
|--------|--------|----------|-----------|
| Usuario envía HU | 1 → 2 | Guardrail valida | ¿OK? |
| MCP solicitud | 3 → 4 | MCP busca | Edge cases |
| Generar caso | 3 | Diseñador | Caso bruto |
| Validar EC | 3 | ¿Existe? | Rechaza si NO |
| Sanitizar | 3 | DataMasker | Caso limpio |
| Revisor | 5 | Rúbrica 5 criterios | Score + veredicto |
| Frenos | 3 | 3 condiciones | ¿Salir? |
| Guardrail salida | 2 | Validar | ¿OK? |
| Product Owner | 6 | Batch | ¿Aprueba? |
