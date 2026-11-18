# Diseñador de Casos de Prueba para Formularios de Pago

Agente que genera automáticamente N escenarios de prueba para formularios de pago, cubriendo edge cases y validados por un subagente revisor.

## 📋 Estructura

```
.
├── src/                      # Código principal
│   ├── types.py             # Type definitions (Pydantic)
│   ├── mcp_client.py        # Cliente MCP (catálogo de edge cases)
│   ├── guardrails.py        # Validaciones y enmascaramiento
│   ├── reviewer.py          # Subagente revisor (rúbrica 5-criterios)
│   └── designer.py          # Orquestador principal (loop iterativo)
├── tests/                    # Suite de tests (pytest)
├── config/                   # Configuración
│   └── config.py            # Settings centralizados
├── ideacion/                 # Documentación de diseño
│   ├── 01-decisiones/       # Análisis y decisiones
│   └── 02-entregables/      # Artefactos (golden_set.json, BPMN)
├── CLAUDE.md                # Especificación del proyecto
├── main.py                  # Punto de entrada
├── pyproject.toml           # Definición del proyecto
└── requirements.txt         # Dependencias
```

## 🚀 Inicio rápido

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con API key y configuración
```

### 3. Ejecutar

```bash
python main.py
```

## 📊 Componentes

### 1. **MCP Client** (`src/mcp_client.py`)
- Interfaz con catálogo de edge cases
- 3 herramientas: `obtener_edge_cases`, `validar_edge_case`, `obtener_estadisticas_cobertura`
- Mock local (sin servidor externo por ahora)

### 2. **Guardrails** (`src/guardrails.py`)
- Enmascaramiento de entrada: tarjetas reales → `[REDACTED_CARD]`
- Validación de schema: casos deben tener `id`, `title`, `test_steps`, etc.
- Detección de hallucinations: edge cases inventados son rechazados

### 3. **Revisor** (`src/reviewer.py`)
Subagente que valida cada caso con rúbrica 5-criterios:
- **Completitud**: ¿toca realmente el edge case?
- **Claridad**: ¿pasos ejecutables?
- **Criticidad**: ¿high-risk primero?
- **Independencia**: ¿funciona aislado?
- **Trazabilidad**: ¿vinculado a HU + golden_set?

Score ≥ 4.0/5.0 → APROBADO

### 4. **Diseñador** (`src/designer.py`)
Orquestador que:
1. Extrae campos de la HU
2. Obtiene edge cases del MCP por tipo de campo
3. Genera 2-5 casos por iteración
4. Invoca Revisor para cada caso
5. Itera hasta:
   - Cobertura ≥ 80% O
   - Iteraciones = 3 O
   - Tokens > 100k

## ⚙️ Configuración

Editar `.env`:

```env
MAX_ITERATIONS=3              # Max vueltas (1-3)
TOKEN_BUDGET=100000          # Presupuesto de tokens
REVIEWER_TIMEOUT_SECONDS=30  # Timeout revisor
COVERAGE_THRESHOLD=0.80      # Cobertura mínima
```

## 📚 Output

Al finalizar, genera:

```json
// output/casos_aprobados.json
{
  "timestamp": "2026-11-18T...",
  "casos_totales": 4,
  "cobertura": 0.85,
  "casos": [
    {
      "id": "CASO-1-1",
      "title": "Pago exitoso con tarjeta válida",
      "edge_case_covered": "EC-001-MON",
      "criticidad": "high",
      "test_steps": [...],
      "aprobado": true,
      "score_rubrica": 4.6
    },
    ...
  ],
  "flags": []
}
```

```
// output/execution.log
Timestamp: 2026-11-18T...
Iteraciones: 2
Casos generados: 5
Casos aprobados: 4
Cobertura: 85.0%
Tokens usados: 45230
Flags: ninguno
```

## 🧪 Tests

```bash
# Ejecutar tests
pytest tests/

# Con cobertura
pytest tests/ --cov=src --cov-report=html
```

## 📖 Documentación

- **CLAUDE.md**: Especificación completa del proyecto (rol, línea roja, guardrails, frenos)
- **ideacion/**: Análisis completo de diseño (decisiones, herramientas, BPMN)
- **golden_set.json**: 6 casos de referencia para comparación

## 🔄 Flujo

```
Historia Usuario (HU-001)
    ↓
MCP obtiene edge cases por tipo de campo
    ↓
Diseñador genera 2-5 casos por iteración
    ↓
Para cada caso:
  • Validar schema ✓
  • Enmascarar datos sensibles ✓
  • Revisor aplica rúbrica 5-criterios
    • Completitud, Claridad, Criticidad, Independencia, Trazabilidad
  • Score ≥ 4.0 → APROBADO (agrega a lista)
  • Score < 4.0 → RECHAZADO (genera alternativa)
    ↓
¿Cobertura ≥ 80% o Iteraciones = 3?
  SÍ → PARAR, generar reporte
  NO → próxima iteración
    ↓
casos_aprobados.json + execution.log
```

## 🚨 Guardrails y Frenos

| Control | Límite | Acción |
|---------|--------|--------|
| Max iteraciones | 3 | Flag `iterations-exhausted` |
| Token budget | 100k | Flag `budget-exhausted` |
| Revisor timeout | 30s | Flag `not-reviewed` |
| Cobertura mínima | 80% | Flag `coverage-partial` si no se alcanza |
| Datos sensibles | Ninguno | Enmascaramiento automático |
| Edge case inventado | N/A | Rechazo automático |

## 📝 Próximos Pasos (v2+)

- [ ] Integrar modelo Anthropic (en lugar de mocks)
- [ ] Subagente Especialista en Cobertura (detecta gaps)
- [ ] Hooks de guardrails (PreExecute, PostGenerate)
- [ ] Suite de tests con pytest vs golden_set
- [ ] API REST para invocar desde CLI/UI
