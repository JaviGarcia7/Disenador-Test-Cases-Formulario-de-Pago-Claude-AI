#!/usr/bin/env python3
"""Punto de entrada principal para el diseñador de casos de prueba"""

import asyncio
import json
import sys
from pathlib import Path

from config.config import (
    GOLDEN_SET_PATH,
    OUTPUT_DIR,
    MAX_ITERATIONS,
    TOKEN_BUDGET,
    REVIEWER_TIMEOUT_SECONDS,
    COVERAGE_THRESHOLD,
)
from src.types import HistoriaUsuario, TestCase, Criticidad, TestStep
from src.mcp_client import MCPClient
from src.reviewer import Revisor
from src.designer import Diseñador


async def load_golden_set() -> list[TestCase]:
    """Carga golden_set.json como referencia"""
    try:
        with open(GOLDEN_SET_PATH, "r") as f:
            data = json.load(f)

        cases = []
        for caso_raw in data.get("golden_set", []):
            test_steps = [
                TestStep(
                    step=step["step"],
                    action=step["action"],
                    expected=step["expected"],
                )
                for step in caso_raw.get("test_steps", [])
            ]

            case = TestCase(
                id=caso_raw["id"],
                title=caso_raw["title"],
                edge_case_covered=caso_raw["edge_case_covered"],
                criticidad=Criticidad(caso_raw.get("criticidad", "high").lower()),
                test_steps=test_steps,
            )
            cases.append(case)

        return cases
    except Exception as e:
        print(f"⚠️ No se pudo cargar golden_set: {e}")
        return []


async def create_test_hu() -> HistoriaUsuario:
    """Crea una Historia de Usuario de prueba"""
    return HistoriaUsuario(
        id="HU-001",
        descripcion="Formulario de Pago: completar datos de tarjeta",
        campos=[
            {"nombre": "Titular", "tipo": "texto"},
            {"nombre": "Número de tarjeta", "tipo": "monetario"},
            {"nombre": "Fecha de expiración", "tipo": "fecha"},
            {"nombre": "CVV", "tipo": "texto"},
        ],
    )


async def main():
    """Loop principal"""
    print("=" * 60)
    print("Diseñador de Casos de Prueba para Formularios de Pago")
    print("=" * 60)

    # Cargar configuración
    print(f"\n📋 Configuración:")
    print(f"  - Max iteraciones: {MAX_ITERATIONS}")
    print(f"  - Token budget: {TOKEN_BUDGET}")
    print(f"  - Revisor timeout: {REVIEWER_TIMEOUT_SECONDS}s")
    print(f"  - Coverage threshold: {COVERAGE_THRESHOLD:.0%}")
    print(f"  - Output dir: {OUTPUT_DIR}")

    # Crear directorio de output
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Cargar golden_set
    print(f"\n📚 Cargando golden_set...")
    golden_set = await load_golden_set()
    print(f"  ✅ {len(golden_set)} casos de referencia cargados")

    # Inicializar componentes
    print(f"\n🔧 Inicializando componentes...")
    mcp_client = MCPClient()
    stats = await mcp_client.obtener_estadisticas_cobertura()
    print(f"  ✅ MCP client listo ({stats.total} edge cases en catálogo)")

    reviewer = Revisor(timeout_seconds=REVIEWER_TIMEOUT_SECONDS)
    print(f"  ✅ Revisor listo")

    diseñador = Diseñador(
        mcp_client=mcp_client,
        reviewer=reviewer,
        max_iteraciones=MAX_ITERATIONS,
        token_budget=TOKEN_BUDGET,
        coverage_threshold=COVERAGE_THRESHOLD,
        output_dir=str(OUTPUT_DIR),
    )
    print(f"  ✅ Diseñador listo")

    # Crear HU de prueba
    print(f"\n📝 Creando Historia de Usuario...")
    hu = await create_test_hu()
    print(f"  ✅ HU-001 lista ({len(hu.campos)} campos)")

    # Generar casos
    print(f"\n🚀 Iniciando generación de casos...")
    try:
        casos_aprobados, metrics = await diseñador.generar_casos(hu, golden_set)

        # Resumen final
        print(f"\n" + "=" * 60)
        print(f"RESULTADO FINAL")
        print(f"=" * 60)
        print(f"✅ Casos aprobados: {metrics.casos_aprobados}")
        print(f"📊 Cobertura: {metrics.cobertura_actual:.1%}")
        print(f"🔄 Iteraciones: {metrics.iteracion_actual}")
        print(f"⚠️ Flags: {', '.join(metrics.flags) if metrics.flags else 'ninguno'}")

        if metrics.cobertura_actual >= COVERAGE_THRESHOLD:
            print(f"\n✅ ÉXITO: Cobertura ≥{COVERAGE_THRESHOLD:.0%}")
        else:
            print(
                f"\n⚠️ ADVERTENCIA: Cobertura {metrics.cobertura_actual:.1%} < {COVERAGE_THRESHOLD:.0%}"
            )

        print(f"\n📁 Archivos generados:")
        print(f"  - {OUTPUT_DIR}/casos_aprobados.json")
        print(f"  - {OUTPUT_DIR}/execution.log")

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
