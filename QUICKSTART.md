# 🚀 Quick Start - Prueba el Agente en 5 minutos

## Opción 1: CLI (Terminal) - ⭐ Recomendado para Demo

### 1. Ejecutar en terminal

```bash
cd /workshop/capstone
chmod +x run_cli.sh
./run_cli.sh
```

**Eso es todo.** El script:
- ✅ Crea venv automáticamente
- ✅ Instala dependencias
- ✅ Ejecuta el agente
- ✅ Muestra resultados visuales

### 2. Ver output

Verás algo como esto:

```
======================================================================
  DISEÑADOR DE CASOS DE PRUEBA - CLI
======================================================================

📌 1. Cargando Historia de Usuario
✅ HU por defecto creada

📌 2. Cargando Golden Set
✅ 6 casos de referencia cargados

📌 3. Inicializando componentes
✅ MCP client listo (10 edge cases)
✅ Revisor listo
✅ Diseñador listo

📌 4. Generando casos de prueba
⏳ Esto puede tomar unos segundos...

--- Iteración 1 ---
✅ CASO-1-1 aprobado
✅ CASO-1-2 aprobado
Cobertura actual: 50.0%

📊 RESULTADOS FINALES
Casos aprobados: 4
Cobertura: 85.0%
Iteraciones: 2

✅ ÉXITO: Cobertura 85.0% ≥ 80%
```

### 3. Opciones adicionales

```bash
# Demo rápida (1 iteración)
./run_cli.sh --max-iter 1

# Con HU personalizada
./run_cli.sh --hu examples/hu_example.json

# Con cobertura estricta
./run_cli.sh --coverage 0.95

# Mostrar ayuda
./run_cli.sh --help
```

### 4. Verificar output

```bash
# Ver casos generados
cat output/casos_aprobados.json | python3 -m json.tool

# Ver trace de ejecución
cat output/execution.log
```

---

## Opción 2: API REST (HTTP) - Para Integraciones

### 1. Ejecutar servidor

```bash
chmod +x run_api.sh
./run_api.sh
```

El servidor estará en: **http://localhost:8000**

### 2. Abrir documentación interactiva

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Probar endpoints

#### a) Health check

```bash
curl http://localhost:8000/health
```

#### b) Generar casos (⭐ Principal)

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

#### c) Listar edge cases disponibles

```bash
curl "http://localhost:8000/edge-cases?campo_tipo=monetario"
```

#### d) Ver estadísticas

```bash
curl http://localhost:8000/cobertura-estadisticas
```

### 4. Ejemplos automáticos

```bash
chmod +x examples/api_examples.sh
./examples/api_examples.sh
```

---

## 📊 Comparación Rápida

| Necesidad | Usa | Comando |
|-----------|-----|---------|
| **Demo ejecutiva** | CLI | `./run_cli.sh` |
| **Testing interactivo** | API + Swagger | `./run_api.sh` → http://localhost:8000/docs |
| **Integración automatizada** | API + curl | `curl -X POST http://localhost:8000/generar-casos ...` |
| **HU personalizada** | CLI | `./run_cli.sh --hu tu_hu.json` |
| **Tests automatizados** | pytest | `pytest tests/` |

---

## 📁 Archivos Generados

Después de ejecutar, encontrarás:

```
output/
├── casos_aprobados.json    ← Casos sin datos sensibles
├── execution.log           ← Trace de ejecución
└── .gitkeep
```

---

## 🆘 Troubleshooting

### Error: "Permission denied"

```bash
chmod +x run_cli.sh run_api.sh
./run_cli.sh
```

### Error: "Module not found"

El script `run_cli.sh` / `run_api.sh` maneja esto automáticamente. Si falla:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m src.cli
```

### Error: "Port 8000 already in use"

```bash
# Cambiar puerto en run_api.sh o:
python3 -m uvicorn src.api:app --port 8001
```

---

## 🎯 Qué Está Pasando

El agente **Diseñador**:

1. ✅ Lee tu Historia de Usuario
2. ✅ Obtiene edge cases del catálogo
3. ✅ Genera 2-5 casos por iteración
4. ✅ Valida cada caso con **Revisor** (rúbrica 5-criterios)
5. ✅ Calcula cobertura
6. ✅ Itera hasta: cobertura ≥80% O máximo 3 vueltas
7. ✅ Genera output: `casos_aprobados.json` + `execution.log`

---

## 📚 Más Información

- **README.md** - Guía completa
- **TESTING.md** - Testing avanzado
- **CLAUDE.md** - Especificación oficial
- **ESTRUCTURA_PROYECTO.md** - Arquitectura detallada

---

## ✨ Listo para Exponer

Ambas opciones (CLI y API) están **production-ready**:

- ✅ CLI: Visual, amigable, demo ejecutiva
- ✅ API: Escalable, documentada, integrable

**Elige la que mejor se adapte a tu caso de uso.**

Ahora a **probarlo** 🚀
