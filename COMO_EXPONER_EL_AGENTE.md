# 🎤 Cómo Exponer el Agente - Guía Práctica

## 🎯 Objetivo

Has creado un agente que genera automáticamente casos de prueba. Aquí te muestro cómo exponerlo para que otros lo usen.

---

## 📋 Escenarios de Exposición

### Escenario 1: Demo Ejecutiva (Junta con stakeholders)

**Mejor opción**: CLI

**Flujo**:
1. Siéntate con la laptop proyectada
2. Ejecuta: `./run_cli.sh`
3. Muestra el output en tiempo real
4. Impresiona con:
   - ✅ Casos generados automáticamente
   - ✅ Cobertura alcanzada
   - ✅ Tiempo de ejecución (segundos)

**Comando**:
```bash
./run_cli.sh
```

**Tiempo**: 30 segundos de setup + 5-10 segundos de demo

---

### Escenario 2: Testing Interactivo (QA, devs)

**Mejor opción**: API REST + Swagger UI

**Flujo**:
1. Inicia API: `./run_api.sh`
2. Abre: http://localhost:8000/docs
3. Prueban endpoints interactivamente
4. Ven respuestas en tiempo real
5. Pueden llamar desde su código

**Comando**:
```bash
./run_api.sh
# Luego: http://localhost:8000/docs
```

**Tiempo**: 30 segundos de setup + ilimitado

---

### Escenario 3: Integración (Sistema externo)

**Mejor opción**: API REST via curl/HTTP

**Flujo**:
1. Tu sistema llama endpoint `/generar-casos`
2. Recibe JSON con casos generados
3. Lo procesa según tus necesidades

**Ejemplo**:
```python
import requests

response = requests.post(
    "http://localhost:8000/generar-casos",
    json={
        "historia_usuario": {
            "id": "HU-001",
            "descripcion": "Mi formulario",
            "campos": [...]
        },
        "max_iteraciones": 3,
        "coverage_threshold": 0.80
    }
)

casos = response.json()
print(f"✅ {casos['casos_aprobados']} casos aprobados")
print(f"📊 Cobertura: {casos['cobertura']:.0%}")
```

---

### Escenario 4: CI/CD (Pipeline automatizado)

**Mejor opción**: CLI en script

**Flujo**:
1. GitHub Actions / Jenkins llama: `./run_cli.sh`
2. Valida exit code
3. Procesa `output/casos_aprobados.json`

**Archivo `.github/workflows/generate-test-cases.yml`**:
```yaml
name: Generate Test Cases

on: [push]

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: |
          chmod +x run_cli.sh
          ./run_cli.sh
      - uses: actions/upload-artifact@v3
        with:
          name: test-cases
          path: output/
```

---

### Escenario 5: Documentación Interactiva (Portal técnico)

**Mejor opción**: API REST + ReDoc

**URL**: http://localhost:8000/redoc

**Contenido**:
- Descripción de cada endpoint
- Parámetros de entrada
- Ejemplos de respuesta
- Esquemas de datos

**Para hosting permanente**:
```bash
# Generar HTML estático
pip install redoc-cli
redoc-cli bundle src/api.py -o redoc.html
```

---

## 🚀 Opción Recomendada: Combinación (Best of Both)

Usa ambas simultáneamente para máxima flexibilidad:

```bash
# Terminal 1: API REST
./run_api.sh

# Terminal 2: CLI para demos
./run_cli.sh

# Navegador: Swagger UI
# http://localhost:8000/docs

# Otro programador: Curl
# curl -X POST http://localhost:8000/generar-casos ...
```

---

## 📊 Matriz de Decisión

| Necesidad | Usa | Setup | Demo Time |
|-----------|-----|-------|-----------|
| Junta ejecutiva | CLI | 30s | 10s ✅ |
| QA testing | API Swagger | 30s | ∞ ✅ |
| Integración código | API REST | 30s | - |
| CI/CD | CLI | 30s | - |
| Documentación | API ReDoc | 30s | ∞ ✅ |

---

## 💡 Tips de Presentación

### Para Demo CLI

```bash
# Mostrá algo rápido:
./run_cli.sh --max-iter 1

# Explicá los pasos mientras se ejecuta
```

### Para Demo API

```bash
# Mostrá Swagger UI
# Explica cada endpoint
# Prueba POST /generar-casos en vivo
```

### Talking Points

1. **Problema**: "Redactar casos de prueba manualmente toma 2-3 horas"
2. **Solución**: "El agente lo hace automáticamente en segundos"
3. **Validación**: "Un revisor con rúbrica valida cada caso"
4. **Cobertura**: "Alcanzamos 80%+ de edge cases"
5. **Output**: "Casos limpios, sin datos sensibles"

---

## 🔒 Consideraciones de Seguridad

### Para Exposición Pública (Demo):

✅ **Permitido en API pública**:
- Algoritmos (lógica del agente)
- Edge cases genéricos
- Documentación técnica

❌ **NO permitido**:
- Datos de clientes reales
- Números de tarjeta reales
- CVV reales

**Solución**: Usa ejemplos de prueba (`4111111111111111`)

---

## 📈 Metricas para Mostrar

Cuando expongas, destaca:

```
✅ Casos generados: 4
✅ Cobertura: 85%
✅ Validación: Rúbrica 5-criterios
✅ Tiempo: 2 segundos
✅ Iteraciones: 2 de 3
✅ Tokens: 45k de 100k
✅ Output: JSON limpio
```

---

## 🎬 Script de Demo (5 minutos)

```
SLIDE 1: PROBLEMA
- "Redactar casos de prueba es manual y lento"

SLIDE 2: SOLUCIÓN
- "Agente que genera casos automáticamente"

SLIDE 3: DEMOSTRACIÓN (EJECUTAR)
$ ./run_cli.sh

MIENTRAS SE EJECUTA, EXPLICA:
- "El agente lee la Historia de Usuario"
- "Obtiene edge cases del catálogo"
- "Genera casos por iteración"
- "El Revisor valida cada uno"
- "Calcula la cobertura"

RESULTADO VISIBLE:
✅ 4 casos aprobados
📊 Cobertura: 85%
⏱️ Tiempo: 2 segundos

SLIDE 4: IMPACTO
- "Ahora: 2-3 horas → 2-3 segundos"
- "Cobertura: automática"
- "Validación: rúbrica 5-criterios"

SLIDE 5: PRÓXIMOS PASOS
- "Integración con Anthropic API (modelo real)"
- "Especialista en Cobertura (subagente)"
- "Hooks de seguridad"
```

---

## 🌐 Hosting (Opcional)

Si quieres alojar la API permanentemente:

### Opción 1: Heroku (Gratis con limitaciones)

```bash
# 1. Crear Procfile
echo "web: python3 -m uvicorn src.api:app --host 0.0.0.0 --port \$PORT" > Procfile

# 2. Push a Heroku
heroku create mi-agente
git push heroku main

# 3. Acceso
curl https://mi-agente.herokuapp.com/health
```

### Opción 2: Docker

```dockerfile
FROM python:3.10

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python3", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t agente-casos .
docker run -p 8000:8000 agente-casos
```

### Opción 3: AWS / Azure / Google Cloud

- Deploy el `src/api.py` como Cloud Function
- Endpoint HTTP público
- Escalabilidad automática

---

## 📞 Preguntas Frecuentes en Demo

**P: ¿Funciona con datos reales?**
R: "Sí, pero enmascaramos tarjetas/CVV automáticamente. Usa test cards como 4111..."

**P: ¿Qué tan precisa es?**
R: "Rúbrica 5-criterios: completitud, claridad, criticidad, independencia, trazabilidad"

**P: ¿Cuánto tiempo toma?**
R: "Generación + revisión: 2-10 segundos. Depende de iteraciones."

**P: ¿Se puede integrar con nuestro sistema?**
R: "Sí, API REST + JSON. Documentación en /docs"

**P: ¿Qué viene después?**
R: "Integrar con modelo Claude para generación inteligente"

---

## ✅ Checklist pre-Demo

- [ ] Probaste `./run_cli.sh` localmente
- [ ] Probaste `./run_api.sh` + http://localhost:8000/docs
- [ ] Verificaste que output es legible
- [ ] Leíste QUICKSTART.md
- [ ] Preparaste talking points
- [ ] Tienes ejemplos listos (examples/hu_example.json)
- [ ] Git está actualizado en GitHub
- [ ] WiFi testeatdo (si es virtual)

---

## 🎊 ¡Listo para Exponer!

Elige tu escenario y **déjalos impresionados** con tu agente. 🚀

**Recordá**: El código no habla solo. La demo sí.

---

## 📚 Documentación Adicional

- `QUICKSTART.md` - Start aquí
- `TESTING.md` - Testing avanzado
- `README.md` - Overview
- `CLAUDE.md` - Spec técnica
- Swagger UI - http://localhost:8000/docs
