#!/bin/bash
# Script para ejecutar API REST del Diseñador

set -e

echo "=================================================="
echo "  Diseñador de Casos de Prueba - API REST"
echo "=================================================="
echo

# Verificar venv
if [ ! -d "venv" ]; then
    echo "🔧 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar venv
source venv/bin/activate

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -q -r requirements.txt

# Ejecutar API
echo "🚀 Iniciando API REST en http://localhost:8000"
echo "📚 Documentación: http://localhost:8000/docs"
echo "📊 ReDoc: http://localhost:8000/redoc"
echo
python3 -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
