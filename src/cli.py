#!/usr/bin/env python3
"""CLI mejorada para el Diseñador de Casos de Prueba"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.types import HistoriaUsuario, TestCase, Criticidad, TestStep
from src.mcp_client import MCPClient
from src.reviewer import Revisor
from src.designer import Diseñador


class CLIReporter:
    """Reportes visuales para CLI"""

    @staticmethod
    def header(title: str):
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)

    @staticmethod
    def section(title: str):
        print(f"\n📌 {title}")
        print("-" * 70)

    @staticmethod
    def success(msg: str):
        print(f"✅ {msg}")

    @staticmethod
    def error(msg: str):
        print(f"❌ {msg}")

    @staticmethod
    def info(msg: str):
        print(f"ℹ️  {msg}")

    @staticmethod
    def metric(label: str, value: str):
        print(f"  • {label}: {value}")

    @staticmethod
    def result_table(casos: list[TestCase]):
        """Tabla de resultados"""
        print("\n📊 CASOS GENERADOS:")
        print("-" * 70)
        print(f"{'ID':<15} {'Título':<30} {'Estado':<12} {'Score':<8}")
        print("-" * 70)

        for caso in casos:
            estado = "✅ APROBADO" if caso.aprobado else "❌ RECHAZADO"
            score = f"{caso.score_rubrica:.1f}" if caso.score_rubrica else "N/A"
            titulo = caso.title[:27] + "..." if len(caso.title) > 27 else caso.title
            print(f"{caso.id:<15} {titulo:<30} {estado:<12} {score:<8}")

        print("-" * 70)


async def run_designer_cli(
    hu_file: Optional[str] = None,
    max_iter: int = 3,
    coverage: float = 0.80,
) -> int:
    """Ejecuta el diseñador desde CLI con reportes visuales"""

    CLIReporter.header("DISEÑADOR DE CASOS DE PRUEBA - CLI")

    # Cargar HU
    CLIReporter.section("1. Cargando Historia de Usuario")

    if hu_file and Path(hu_file).exists():
        try:
            with open(hu_file, "r") as f:
                hu_data = json.load(f)
            hu = HistoriaUsuario(**hu_data)
            CLIReporter.success(f"HU cargada desde {hu_file}")
        except Exception as e:
            CLIReporter.error(f"No se pudo cargar HU: {e}")
            return 1
    else:
        # HU por defecto
        hu = HistoriaUsuario(
            id="HU-001",
            descripcion="Formulario de Pago: completar datos de tarjeta",
            campos=[
                {"nombre": "Titular", "tipo": "texto"},
                {"nombre": "Número de tarjeta", "tipo": "monetario"},
                {"nombre": "Fecha de expiración", "tipo": "fecha"},
                {"nombre": "CVV", "tipo": "texto"},
            ],
        )
        CLIReporter.success("HU por defecto creada")

    CLIReporter.metric("ID", hu.id)
    CLIReporter.metric("Descripción", hu.descripcion)
    CLIReporter.metric("Campos", str(len(hu.campos)))

    # Cargar golden_set
    CLIReporter.section("2. Cargando Golden Set")

    golden_set_path = Path("ideacion/02-entregables/golden_set.json")
    golden_set = []

    if golden_set_path.exists():
        try:
            with open(golden_set_path, "r") as f:
                data = json.load(f)

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
                golden_set.append(case)

            CLIReporter.success(f"{len(golden_set)} casos de referencia cargados")
        except Exception as e:
            CLIReporter.info(f"Golden set no disponible: {e}")

    # Inicializar componentes
    CLIReporter.section("3. Inicializando componentes")

    mcp_client = MCPClient()
    stats = await mcp_client.obtener_estadisticas_cobertura()
    CLIReporter.success(f"MCP client listo ({stats.total} edge cases)")

    reviewer = Revisor(timeout_seconds=30)
    CLIReporter.success("Revisor listo")

    diseñador = Diseñador(
        mcp_client=mcp_client,
        reviewer=reviewer,
        max_iteraciones=max_iter,
        token_budget=100000,
        coverage_threshold=coverage,
        output_dir="output",
    )
    CLIReporter.success("Diseñador listo")

    # Generar casos
    CLIReporter.section("4. Generando casos de prueba")
    print("\n⏳ Esto puede tomar unos segundos...\n")

    try:
        casos_aprobados, metrics = await diseñador.generar_casos(hu, golden_set)
    except Exception as e:
        CLIReporter.error(f"Error durante generación: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Mostrar resultados
    CLIReporter.section("5. Resultados Finales")

    CLIReporter.result_table(casos_aprobados)

    CLIReporter.section("📊 MÉTRICAS DE EJECUCIÓN")
    CLIReporter.metric("Casos generados", str(metrics.casos_generados))
    CLIReporter.metric("Casos aprobados", str(metrics.casos_aprobados))
    CLIReporter.metric("Iteraciones", str(metrics.iteracion_actual))
    CLIReporter.metric("Cobertura", f"{metrics.cobertura_actual:.1%}")
    CLIReporter.metric("Tokens usados", str(metrics.tokens_usados))

    if metrics.flags:
        CLIReporter.metric("Flags", ", ".join(metrics.flags))

    # Validar éxito
    CLIReporter.section("✨ VEREDICTO FINAL")

    if metrics.cobertura_actual >= coverage:
        CLIReporter.success(f"✅ ÉXITO: Cobertura {metrics.cobertura_actual:.1%} ≥ {coverage:.0%}")
        status = 0
    else:
        CLIReporter.error(
            f"❌ Cobertura {metrics.cobertura_actual:.1%} < {coverage:.0%}"
        )
        status = 1

    if "budget-exhausted" in metrics.flags:
        CLIReporter.error("⚠️ Token budget excedido")
        status = 1

    if "iterations-exhausted" in metrics.flags:
        CLIReporter.error("⚠️ Max iteraciones alcanzadas")

    # Mostrar ubicación de output
    CLIReporter.section("📁 ARCHIVOS GENERADOS")
    CLIReporter.metric("Casos aprobados", "output/casos_aprobados.json")
    CLIReporter.metric("Trace de ejecución", "output/execution.log")

    print("\n" + "=" * 70 + "\n")

    return status


def show_help():
    """Muestra ayuda"""
    help_text = """
╔════════════════════════════════════════════════════════════════╗
║       DISEÑADOR DE CASOS DE PRUEBA - CLI                      ║
╚════════════════════════════════════════════════════════════════╝

USO:
  python3 -m src.cli [OPTIONS]

OPTIONS:
  --hu FILE           Archivo JSON de Historia de Usuario
  --max-iter N        Max iteraciones (default: 3)
  --coverage PCT      Cobertura mínima (default: 0.80)
  --help             Mostrar esta ayuda

EJEMPLOS:

  1. Ejecutar con valores por defecto:
     python3 -m src.cli

  2. Con archivo HU personalizado:
     python3 -m src.cli --hu mi_hu.json

  3. Con cobertura más estricta:
     python3 -m src.cli --coverage 0.95

  4. Demo rápida (1 iteración):
     python3 -m src.cli --max-iter 1

OUTPUT:
  • output/casos_aprobados.json   - Casos sin datos sensibles
  • output/execution.log          - Trace de ejecución
"""
    print(help_text)


async def main():
    """Punto de entrada CLI"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Diseñador de Casos de Prueba - CLI",
        add_help=False,
    )
    parser.add_argument("--hu", type=str, help="Archivo JSON de Historia de Usuario")
    parser.add_argument(
        "--max-iter", type=int, default=3, help="Max iteraciones (default: 3)"
    )
    parser.add_argument(
        "--coverage", type=float, default=0.80, help="Cobertura mínima (default: 0.80)"
    )
    parser.add_argument("--help", action="store_true", help="Mostrar ayuda")

    args = parser.parse_args()

    if args.help:
        show_help()
        sys.exit(0)

    exit_code = await run_designer_cli(
        hu_file=args.hu,
        max_iter=args.max_iter,
        coverage=args.coverage,
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
