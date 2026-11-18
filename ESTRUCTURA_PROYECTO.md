# 📦 Estructura del Proyecto - Diseñador de Casos de Prueba

## 🎯 Objetivo
Generador automático de escenarios de prueba para formularios de pago, con validación automática por subagente revisor y cobertura de edge cases.

## 📂 Árbol de directorios

```
/workshop/capstone/
│
├── 📄 CLAUDE.md                          ← Especificación oficial del proyecto
├── 📄 README.md                          ← Guía rápida de uso
├── 📄 ESTRUCTURA_PROYECTO.md             ← Este archivo
│
├── 🔧 Configuración
│   ├── .env.example                      ← Template de variables de entorno
│   ├── .gitignore                        ← Archivos excluidos de git
│   ├── pyproject.toml                    ← Definición del proyecto (build, deps)
│   └── requirements.txt                  ← Dependencias (pip install)
│
├── 🐍 src/                               ← Código principal
│   ├── __init__.py
│   ├── types.py                          ← Type definitions (Pydantic models)
│   ├── mcp_client.py                     ← Cliente MCP (edge cases catalog)
│   ├── guardrails.py                     ← Validaciones y enmascaramiento
│   ├── reviewer.py                       ← Subagente revisor (rúbrica)
│   └── designer.py                       ← Orquestador principal (loop)
│
├── 🧪 tests/                             ← Suite de tests
│   ├── __init__.py
│   └── test_guardrails.py                ← Tests de validaciones
│
├── ⚙️ config/                            ← Configuración
│   └── config.py                         ← Settings centralizados
│
├── 📊 ideacion/                          ← Documentación de diseño (existente)
│   ├── 01-decisiones/
│   │   ├── subagente.md
│   │   ├── decide-o-ejecuta.md
│   │   ├── controles.md
│   │   ├── herramientas.csv
│   │   └── guardrails.md
│   └── 02-entregables/
│       ├── golden_set.json               ← 6 casos de referencia
│       └── bpmn-agente.html              ← Diagrama de flujo
│
├── 📁 output/                            ← Salida generada (creada al ejecutar)
│   ├── casos_aprobados.json              ← Casos finales sin datos sensibles
│   └── execution.log                     ← Trace de ejecución
│
├── 📁 data/                              ← Datos
│   └── cache/                            ← Caché local
│
└── 🚀 main.py                            ← Punto de entrada principal
```

---

## 🏗️ Componentes Implementados

### 1️⃣ **Tipos Base** (`src/types.py`)
Define estructuras de datos con Pydantic:
- `FieldType`: 7 tipos de campo soportados
- `Criticidad`: high, medium, low
- `EdgeCase`: estructura de catálogo MCP
- `TestCase`: caso de prueba generado
- `TestStep`: paso individual
- `RubricaScore`: scores de rúbrica (5 criterios)
- `ExecutionMetrics`: trazas de ejecución

**Status**: ✅ Completo

---

### 2️⃣ **Cliente MCP** (`src/mcp_client.py`)
Interfaz con catálogo de edge cases (actualmente mock):

**3 Herramientas (read-only)**:
```python
obtener_edge_cases(campo_tipo, criticidad_minima)
  → list[EdgeCase]

validar_edge_case(edge_case_id)
  → {existe: bool, ...detalles}

obtener_estadisticas_cobertura()
  → {total: int, por_tipo, por_criticidad}
```

**Catálogo Local** (10 edge cases):
- Monetario: 2 casos (formato, longitud)
- Fecha: 1 caso (expiración)
- Texto: 2 casos (CVV, titular)
- *Expandible en v2*

**Status**: ✅ Mock funcional (lista para integración servidor real)

---

### 3️⃣ **Guardrails** (`src/guardrails.py`)
Validaciones y seguridad:

**DataMasker**:
```python
mask_input(data)     # Tarjetas reales → [REDACTED_CARD]
mask_output(case)    # Oculta datos sensibles en output
```

**SchemaValidator**:
```python
validate_test_case(case)    # Valida estructura JSON
validate_edge_case(case)    # Valida edge case
```

**HalluccinationDetector**:
```python
is_hallucination(edge_case_id)      # ¿Edge case inventado?
validate_case_coverage(case)        # Rechaza si edge case no en catálogo
```

**Status**: ✅ Completo

---

### 4️⃣ **Revisor Subagente** (`src/reviewer.py`)
Valida casos con rúbrica 5-criterios:

**Rúbrica** (0-5 cada una):
1. Completitud: ¿toca el edge case?
2. Claridad: ¿pasos ejecutables?
3. Criticidad: ¿high-risk primero?
4. Independencia: ¿funciona aislado?
5. Trazabilidad: ¿vinculado a HU?

**Veredicto**: Score ≥ 4.0/5.0 → APROBADO

**Timeout**: 30s (fallback: asumir aprobado)

**Status**: ✅ Completo (mock async, lista para modelo real)

---

### 5️⃣ **Diseñador Orquestador** (`src/designer.py`)
Loop principal que coordina generación:

**Flujo**:
```
1. Extrae campos de HU
   ↓
2. Para cada campo:
   - Obtiene edge cases del MCP
   - Genera 2-5 casos por iteración
   ↓
3. Valida cada caso:
   - Schema check
   - Enmascaramiento
   - Hallucination check
   ↓
4. Invoca Revisor (rúbrica)
   ↓
5. Chequea frenos:
   - Cobertura ≥ 80%? → PARAR
   - Iteraciones ≥ 3? → PARAR
   - Tokens > 100k? → PARAR
   ↓
6. Genera output JSON + LOG
```

**Guardias de Control**:
- Max 3 iteraciones
- 100k tokens presupuesto
- 30s timeout revisor
- 80% cobertura mínima

**Status**: ✅ Completo (mock async, lista para modelo real)

---

### 6️⃣ **Configuración** (`config/config.py`)
Centraliza variables de entorno:
```python
MAX_ITERATIONS=3
TOKEN_BUDGET=100000
REVIEWER_TIMEOUT_SECONDS=30
COVERAGE_THRESHOLD=0.80
```

**Status**: ✅ Completo

---

### 7️⃣ **Tests** (`tests/test_guardrails.py`)
Suite básica de tests:
- DataMasker: enmascaramiento correcto
- SchemaValidator: validación de estructura
- HalluccinationDetector: detección de casos inventados

**Status**: ✅ Básico (expandir en iteraciones)

---

### 8️⃣ **Punto de Entrada** (`main.py`)
Script ejecutable que:
1. Carga golden_set.json
2. Inicializa componentes
3. Crea HU de prueba
4. Ejecuta diseñador
5. Genera reporte

**Status**: ✅ Completo

---

## 🚀 Cómo Ejecutar

```bash
# 1. Ir al directorio
cd /workshop/capstone

# 2. (Opcional) Crear venv
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar .env
cp .env.example .env
# Editar .env con valores (opcional para mocks)

# 5. Ejecutar
python3 main.py
```

**Output esperado**:
```
✅ 4 casos aprobados
📊 Cobertura: 85%
🔄 Iteraciones: 2
📁 output/casos_aprobados.json
📁 output/execution.log
```

---

## 📋 Checklist de Implementación

### ✅ Completado (MVP v0.1)
- [x] Estructura de directorios
- [x] Types base + Pydantic
- [x] MCP client (mock)
- [x] Guardrails (enmascaramiento + validación)
- [x] Revisor (rúbrica 5-criterios)
- [x] Diseñador (loop iterativo)
- [x] Configuración centralizada
- [x] Tests básicos
- [x] main.py ejecutable
- [x] README + documentación

### 🔄 Próximos (MVP v1.0 - Integración Modelo)
- [ ] Reemplazar mocks con llamadas a Anthropic API
- [ ] Diseñador como Agent real (tool-runner)
- [ ] Revisor como Subagente real (agent-delegation)
- [ ] MCP server (en lugar de client mock)
- [ ] Hooks de guardrails (PreExecute, PostGenerate)
- [ ] Especialista en Cobertura (subagente paralelo)
- [ ] Expand tests (pytest vs golden_set)
- [ ] API REST / CLI mejorado

### 🎁 Nice-to-Have (v2.0+)
- [ ] UI / Dashboard
- [ ] Integración CI/CD
- [ ] Reporte HTML interactivo
- [ ] Métricas de performance
- [ ] Caché de edge cases

---

## 🔗 Puntos de Partida para Próxima Fase

| Componente | Lab Recomendado | Razón |
|-----------|-----------------|-------|
| Diseñador + Modelo | `agent-delegation` | Invocar modelo para generar casos |
| Revisor Subagent | `tool-runner-manual` | Delegación con contexto limpio |
| MCP Server Real | `mcp-servers` quickstart | Transformar mock → servidor |
| Guardrails | `hooks` lab | PreExecute (entrada), PostGenerate (salida) |
| Loop Control | `managed-loops` lab | Iteraciones + frenos |

---

## 📚 Archivos de Referencia

- **CLAUDE.md**: Especificación completa (línea roja, guardrails, frenos)
- **ideacion/**: Documentación de diseño (7 archivos)
- **golden_set.json**: 6 casos de referencia para benchmark

---

## 🎯 Estado General

```
IDEACIÓN:       ✅ 100% CERRADA (2026-11-13/18)
ESTRUCTURA:     ✅ 100% CREADA (2026-11-18)
MOCKS:          ✅ FUNCIONALES
TESTS:          ⚠️ BÁSICOS (expandir)
INTEGRACIÓN:    ❌ PRÓXIMA FASE
```

**Listo para pasar a: Integración con Anthropic API + Subagentes reales**
