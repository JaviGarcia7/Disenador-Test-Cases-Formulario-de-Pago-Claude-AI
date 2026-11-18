# 🧪 Guía de Testing - Diseñador de Casos de Prueba

## 📋 Opciones de Prueba

Tenemos 2 formas de probar y exponer el agente:

### 1️⃣ **CLI (Interfaz de Línea de Comandos)**
- ✅ Ideal para **demos en vivo**
- ✅ Output visual y amigable
- ✅ Rápido de usar
- ✅ No requiere navegador

### 2️⃣ **API REST (FastAPI)**
- ✅ Ideal para **integraciones**
- ✅ Documentación interactiva (Swagger UI)
- ✅ Reutilizable por otros sistemas
- ✅ Escalable

---

## 🚀 Opción 1: CLI

### Instalación rápida

```bash
# 1. Instalar dependencias (crea venv automáticamente)
chmod +x run_cli.sh
./run_cli.sh

# O manual:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Uso

```bash
# Demo simple (valores por defecto)
./run_cli.sh

# Con archivo HU personalizado
./run_cli.sh --hu mi_hu.json

# Demo rápida (1 iteración)
./run_cli.sh --max-iter 1

# Con cobertura estricta
./run_cli.sh --coverage 0.95

# Ayuda
./run_cli.sh --help
```

### Output esperado

```
======================================================================
  DISEÑADOR DE CASOS DE PRUEBA - CLI
======================================================================

📌 1. Cargando Historia de Usuario
───────────────────────────────────────────────────────────────────
✅ HU por defecto creada
  • ID: HU-001
  • Descripción: Formulario de Pago: completar datos de tarjeta
  • Campos: 4

📌 2. Cargando Golden Set
───────────────────────────────────────────────────────────────────
✅ 6 casos de referencia cargados

📌 3. Inicializando componentes
───────────────────────────────────────────────────────────────────
✅ MCP client listo (10 edge cases)
✅ Revisor listo
✅ Diseñador listo

📌 4. Generando casos de prueba
───────────────────────────────────────────────────────────────────
⏳ Esto puede tomar unos segundos...

--- Iteración 1 ---
✅ CASO-1-1 aprobado
✅ CASO-1-2 aprobado
Cobertura actual: 50.0%

--- Iteración 2 ---
✅ CASO-2-1 aprobado
✅ CASO-2-2 aprobado
Cobertura actual: 85.0%

📌 5. Resultados Finales
───────────────────────────────────────────────────────────────────

📊 CASOS GENERADOS:
──────────────────────────────────────────────────────────────────
ID              Título                         Estado       Score
──────────────────────────────────────────────────────────────────
CASO-1-1        Número de tarjeta con ...     ✅ APROBADO  4.6
CASO-1-2        Fecha de expiración p...      ✅ APROBADO  4.4
CASO-2-1        CVV con menos de 3 ...        ✅ APROBADO  4.2
CASO-2-2        Titular vacío                 ✅ APROBADO  4.8
──────────────────────────────────────────────────────────────────

📊 MÉTRICAS DE EJECUCIÓN
───────────────────────────────────────────────────────────────────
  • Casos generados: 4
  • Casos aprobados: 4
  • Iteraciones: 2
  • Cobertura: 85.0%
  • Tokens usados: 0
  • Flags: ninguno

✨ VEREDICTO FINAL
───────────────────────────────────────────────────────────────────
✅ ÉXITO: Cobertura 85.0% ≥ 80%

📁 ARCHIVOS GENERADOS
───────────────────────────────────────────────────────────────────
  • Casos aprobados: output/casos_aprobados.json
  • Trace de ejecución: output/execution.log

======================================================================
```

---

## 🌐 Opción 2: API REST

### Inicio rápido

```bash
# 1. Ejecutar servidor
./run_api.sh

# O manual:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

### Acceso

- **Swagger UI (interactive)**: http://localhost:8000/docs
- **ReDoc (docs)**: http://localhost:8000/redoc
- **API base**: http://localhost:8000

### Endpoints Disponibles

#### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "mcp": {
    "total_edge_cases": 10,
    "tipos_soportados": ["monetario", "email", "teléfono", "select", "checkbox", "texto", "fecha"]
  },
  "timestamp": "..."
}
```

#### 2. Obtener Edge Cases

```bash
curl "http://localhost:8000/edge-cases?campo_tipo=monetario&criticidad_minima=high"
```

**Response:**
```json
[
  {
    "id": "EC-001-MON",
    "descripcion": "Número de tarjeta con caracteres alfabéticos",
    "criticidad": "high",
    "ejemplo_entrada": "4111AAAA2222BBBB",
    "resultado_esperado": "Rechazo con mensaje de validación",
    "campo_tipo": "monetario"
  },
  ...
]
```

#### 3. Obtener Estadísticas

```bash
curl http://localhost:8000/cobertura-estadisticas
```

**Response:**
```json
{
  "total": 10,
  "por_tipo": {
    "monetario": 2,
    "fecha": 1,
    "texto": 2,
    ...
  },
  "por_criticidad": {
    "high": 6,
    "medium": 2,
    "low": 2
  }
}
```

#### 4. Generar Casos (⭐ Principal)

```bash
curl -X POST http://localhost:8000/generar-casos \
  -H "Content-Type: application/json" \
  -d '{
    "historia_usuario": {
      "id": "HU-001",
      "descripcion": "Formulario de Pago",
      "campos": [
        {"nombre": "Titular", "tipo": "texto"},
        {"nombre": "Número de tarjeta", "tipo": "monetario"},
        {"nombre": "Fecha de expiración", "tipo": "fecha"},
        {"nombre": "CVV", "tipo": "texto"}
      ]
    },
    "max_iteraciones": 3,
    "coverage_threshold": 0.80
  }'
```

**Response:**
```json
{
  "success": true,
  "casos_aprobados": 4,
  "cobertura": 0.85,
  "iteraciones": 2,
  "flags": [],
  "archivo_json": "output/casos_aprobados.json",
  "archivo_log": "output/execution.log"
}
```

#### 5. Validar Edge Case

```bash
curl "http://localhost:8000/validar-edge-case?edge_case_id=EC-001-MON"
```

**Response:**
```json
{
  "existe": true,
  "id": "EC-001-MON",
  "criticidad": "high",
  "descripcion": "Número de tarjeta con caracteres alfabéticos",
  "campo_tipo": "monetario",
  "ejemplo_entrada": "4111AAAA2222BBBB"
}
```

---

## 📝 Ejemplo: Historia de Usuario Personalizada

Crea archivo `mi_hu.json`:

```json
{
  "id": "HU-PAGO-001",
  "descripcion": "Como cliente, quiero realizar un pago con tarjeta de crédito",
  "campos": [
    {
      "nombre": "Titular",
      "tipo": "texto",
      "restricciones": "Máximo 50 caracteres, solo letras y espacios"
    },
    {
      "nombre": "Número de tarjeta",
      "tipo": "monetario",
      "restricciones": "16 dígitos, validación Luhn"
    },
    {
      "nombre": "Fecha de expiración",
      "tipo": "fecha",
      "restricciones": "Formato MM/YY, debe ser futura"
    },
    {
      "nombre": "CVV",
      "tipo": "texto",
      "restricciones": "3-4 dígitos numéricos"
    }
  ]
}
```

Luego:

```bash
./run_cli.sh --hu mi_hu.json
```

---

## 🧪 Testing Avanzado

### Cargar archivo HU desde API

```bash
# Crear HU
echo '{
  "historia_usuario": {
    "id": "HU-CUSTOM",
    "descripcion": "Mi test",
    "campos": [
      {"nombre": "Email", "tipo": "email"},
      {"nombre": "Monto", "tipo": "monetario"}
    ]
  },
  "max_iteraciones": 2,
  "coverage_threshold": 0.75
}' > /tmp/request.json

# Enviar a API
curl -X POST http://localhost:8000/generar-casos \
  -H "Content-Type: application/json" \
  -d @/tmp/request.json
```

### Tests con pytest

```bash
# Instalar pytest
pip install pytest pytest-asyncio

# Ejecutar tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=src --cov-report=html
```

---

## 📊 Comparación CLI vs API

| Aspecto | CLI | API |
|---------|-----|-----|
| **Setup** | `./run_cli.sh` | `./run_api.sh` |
| **Ideal para** | Demos, desarrollo | Producción, integraciones |
| **Interfaz** | Terminal visual | HTTP REST + Swagger |
| **Requiere browser** | No | Sí (docs) |
| **Reutilizable** | Scripts bash | Cualquier cliente HTTP |
| **Tiempo respuesta** | ~5-10s | ~5-10s (+ latencia HTTP) |
| **Escalabilidad** | Ejecución local | Múltiples clientes |

---

## 🎯 Próximos Pasos

### Para Demo Ejecutiva
1. Ejecutar `./run_cli.sh` con HU de ejemplo
2. Mostrar output visual
3. Abrir `output/casos_aprobados.json` en editor

### Para Integración
1. Ejecutar `./run_api.sh`
2. Ir a http://localhost:8000/docs
3. Probar endpoints interactivamente
4. Integrar con tu sistema

### Para Testing Automatizado
1. Crear tests en `tests/test_integration.py`
2. Ejecutar `pytest tests/`
3. Setup CI/CD (GitHub Actions)

---

## 🆘 Troubleshooting

### "No module named 'pydantic'"

```bash
# Activar venv
source venv/bin/activate

# Instalar
pip install pydantic fastapi uvicorn
```

### Puerto 8000 ocupado

```bash
# Cambiar puerto
python3 -m uvicorn src.api:app --port 8001
```

### Output JSON incorrecto

```bash
# Verificar archivo
cat output/casos_aprobados.json | python3 -m json.tool
```

---

## 📞 Soporte

- 📚 Documentación: `/README.md`
- 🏗️ Arquitectura: `/ESTRUCTURA_PROYECTO.md`
- 📋 Especificación: `/CLAUDE.md`
- 🐛 Issues: GitHub Issues
