#!/bin/bash
# Script para ejecutar CLI del Diseñador

set -e

echo "=================================================="
echo "  Diseñador de Casos de Prueba - CLI"
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

# Ejecutar CLI
echo "🚀 Iniciando CLI..."
echo
python3 -m src.cli "$@"
