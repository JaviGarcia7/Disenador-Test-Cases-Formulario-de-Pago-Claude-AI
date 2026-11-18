#!/bin/bash
# Ejemplos de curl para la API REST

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "  API REST - Ejemplos de curl"
echo "=========================================="
echo

# 1. Health check
echo "1️⃣  Health Check"
echo "---"
echo "GET /health"
curl -s $BASE_URL/health | python3 -m json.tool
echo
echo

# 2. Estadísticas
echo "2️⃣  Obtener Estadísticas de Cobertura"
echo "---"
echo "GET /cobertura-estadisticas"
curl -s $BASE_URL/cobertura-estadisticas | python3 -m json.tool
echo
echo

# 3. Edge cases por tipo
echo "3️⃣  Obtener Edge Cases (tipo: monetario, criticidad: high)"
echo "---"
echo "GET /edge-cases?campo_tipo=monetario&criticidad_minima=high"
curl -s "$BASE_URL/edge-cases?campo_tipo=monetario&criticidad_minima=high" | python3 -m json.tool
echo
echo

# 4. Validar edge case
echo "4️⃣  Validar Edge Case"
echo "---"
echo "GET /validar-edge-case?edge_case_id=EC-001-MON"
curl -s "$BASE_URL/validar-edge-case?edge_case_id=EC-001-MON" | python3 -m json.tool
echo
echo

# 5. Generar casos (principal)
echo "5️⃣  Generar Casos de Prueba"
echo "---"
echo "POST /generar-casos"
echo

REQUEST='{
  "historia_usuario": {
    "id": "HU-DEMO-001",
    "descripcion": "Formulario de Pago - Demostración",
    "campos": [
      {"nombre": "Titular", "tipo": "texto"},
      {"nombre": "Número de tarjeta", "tipo": "monetario"},
      {"nombre": "Fecha de expiración", "tipo": "fecha"},
      {"nombre": "CVV", "tipo": "texto"}
    ]
  },
  "max_iteraciones": 2,
  "coverage_threshold": 0.80
}'

echo "Request:"
echo "$REQUEST" | python3 -m json.tool
echo

echo "Response:"
curl -s -X POST $BASE_URL/generar-casos \
  -H "Content-Type: application/json" \
  -d "$REQUEST" | python3 -m json.tool

echo
echo

# 6. Cargar HU desde archivo
echo "6️⃣  Generar Casos con HU personalizada (desde archivo)"
echo "---"
echo "POST /generar-casos (con HU custom)"
echo

curl -s -X POST $BASE_URL/generar-casos \
  -H "Content-Type: application/json" \
  -d @examples/hu_example.json | python3 -m json.tool

echo
echo "=========================================="
echo "✅ Ejemplos completados"
echo "=========================================="
echo
echo "💡 Tip: Abre http://localhost:8000/docs para Swagger UI interactivo"
