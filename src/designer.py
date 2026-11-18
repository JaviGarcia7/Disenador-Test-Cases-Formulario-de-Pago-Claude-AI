"""Orquestador Diseñador: genera casos de prueba iterativamente"""

import asyncio
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.types import (
    TestCase,
    ExecutionMetrics,
    Criticidad,
    TestStep,
    HistoriaUsuario,
)
from src.mcp_client import MCPClient
from src.reviewer import Revisor
from src.guardrails import DataMasker, SchemaValidator, HalluccinationDetector


class Diseñador:
    """Orquestador que genera casos de prueba iterativamente"""

    def __init__(
        self,
        mcp_client: MCPClient,
        reviewer: Revisor,
        max_iteraciones: int = 3,
        token_budget: int = 100000,
        coverage_threshold: float = 0.80,
        output_dir: str = "output",
    ):
        self.mcp_client = mcp_client
        self.reviewer = reviewer
        self.max_iteraciones = max_iteraciones
        self.token_budget = token_budget
        self.coverage_threshold = coverage_threshold
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.metrics = ExecutionMetrics()
        self.casos_aprobados: list[TestCase] = []
        self.casos_rechazados: list[TestCase] = []
        self.hallucination_detector = HalluccinationDetector(
            mcp_client.get_catalog_ids()
        )

    async def generar_casos(
        self,
        historia_usuario: HistoriaUsuario,
        golden_set: Optional[list[TestCase]] = None,
    ) -> tuple[list[TestCase], ExecutionMetrics]:
        """
        Loop principal: genera casos, llama Revisor, itera hasta:
        - Cobertura ≥80% O
        - Iteraciones ≥3 O
        - Tokens >100k
        """
        self.metrics.iteracion_actual = 0
        self.metrics.tokens_usados = 0

        while self.metrics.iteracion_actual < self.max_iteraciones:
            self.metrics.iteracion_actual += 1
            print(f"\n--- Iteración {self.metrics.iteracion_actual} ---")

            # Generar casos para esta iteración
            casos_nuevos = await self._generar_casos_iteracion(
                historia_usuario, golden_set
            )

            if not casos_nuevos:
                print("⚠️ No se generaron casos nuevos. Parando.")
                break

            # Revisar cada caso
            for caso in casos_nuevos:
                aprobado, feedback, score = await self.reviewer.evaluar_caso(
                    caso, golden_set
                )

                caso.aprobado = aprobado
                caso.feedback_revisor = feedback
                if score:
                    caso.score_rubrica = score.promedio()

                if aprobado:
                    self.casos_aprobados.append(caso)
                    print(f"✅ {caso.id} aprobado")
                else:
                    self.casos_rechazados.append(caso)
                    print(f"❌ {caso.id} rechazado")

                self.metrics.casos_generados += 1
                self.metrics.casos_aprobados = len(self.casos_aprobados)

            # Calcular cobertura actual
            stats = await self.mcp_client.obtener_estadisticas_cobertura()
            self.metrics.cobertura_actual = (
                self.metrics.casos_aprobados / stats.total
                if stats.total > 0
                else 0.0
            )

            print(f"Cobertura actual: {self.metrics.cobertura_actual:.1%}")
            print(f"Casos aprobados: {self.metrics.casos_aprobados}")

            # Chequear frenos
            if self._chequear_frenos():
                print("⛔ Freno activado")
                break

            if self.metrics.cobertura_actual >= self.coverage_threshold:
                print(f"✅ Cobertura ≥{self.coverage_threshold:.0%} alcanzada")
                break

        # Generar reporte final
        await self._generar_reporte()

        return self.casos_aprobados, self.metrics

    async def _generar_casos_iteracion(
        self,
        hu: HistoriaUsuario,
        golden_set: Optional[list[TestCase]] = None,
    ) -> list[TestCase]:
        """Genera 2-5 casos nuevos para esta iteración"""
        casos = []

        # Por cada campo en la HU, obtener edge cases
        for campo_info in hu.campos:
            campo_nombre = campo_info.get("nombre")
            campo_tipo = campo_info.get("tipo")

            if not campo_tipo:
                continue

            try:
                edge_cases = await self.mcp_client.obtener_edge_cases(
                    campo_tipo=campo_tipo,
                    criticidad_minima="high",
                )
            except Exception as e:
                print(f"⚠️ Error obteniendo edge cases para {campo_tipo}: {e}")
                continue

            # Generar un caso por edge case (máximo 2 por iteración)
            for i, edge_case in enumerate(edge_cases[:2]):
                caso = await self._generar_caso_unico(
                    hu, campo_nombre, edge_case
                )

                # Validar hallucinations
                if not self.hallucination_detector.is_hallucination(
                    caso.edge_case_covered
                ):
                    valid, err = SchemaValidator.validate_test_case(
                        caso.model_dump()
                    )
                    if valid:
                        casos.append(caso)
                    else:
                        print(f"❌ Schema inválido: {err}")

        return casos[:5]  # Max 5 por iteración

    async def _generar_caso_unico(
        self, hu: HistoriaUsuario, campo_nombre: str, edge_case
    ) -> TestCase:
        """Genera un caso único para un edge case"""
        caso_id = f"CASO-{self.metrics.iteracion_actual}-{self.metrics.casos_generados + 1}"

        # Crear steps de prueba basado en el edge case
        test_steps = [
            TestStep(
                step=1,
                action=f"Acceder al formulario de pago",
                expected="Formulario visible",
            ),
            TestStep(
                step=2,
                action=f"Ingrese {campo_nombre}: {edge_case.ejemplo_entrada}",
                expected=edge_case.resultado_esperado,
            ),
            TestStep(
                step=3,
                action="Haga clic en botón 'Confirmar Pago'",
                expected=edge_case.resultado_esperado,
            ),
        ]

        caso = TestCase(
            id=caso_id,
            title=edge_case.descripcion,
            edge_case_covered=edge_case.id,
            criticidad=edge_case.criticidad,
            test_steps=test_steps,
        )

        # Enmascarar datos sensibles
        caso_enmascarado = DataMasker.mask_output(caso)

        return caso_enmascarado

    def _chequear_frenos(self) -> bool:
        """Retorna True si algún freno se activó"""
        # Freno de tokens
        if self.metrics.tokens_usados > self.token_budget:
            self.metrics.flags.append("budget-exhausted")
            print(f"❌ Token budget excedido ({self.metrics.tokens_usados} > {self.token_budget})")
            return True

        # Freno de iteraciones
        if self.metrics.iteracion_actual >= self.max_iteraciones:
            if self.metrics.cobertura_actual < self.coverage_threshold:
                self.metrics.flags.append("iterations-exhausted")
                print(f"⛔ Max iteraciones ({self.max_iteraciones}) sin alcanzar cobertura")

        return False

    async def _generar_reporte(self):
        """Genera archivos de salida: JSON + CSV"""
        timestamp = datetime.now().isoformat()

        # Archivo de casos aprobados
        casos_json = {
            "timestamp": timestamp,
            "casos_totales": self.metrics.casos_aprobados,
            "cobertura": self.metrics.cobertura_actual,
            "casos": [caso.model_dump() for caso in self.casos_aprobados],
            "flags": self.metrics.flags,
        }

        casos_file = self.output_dir / "casos_aprobados.json"
        with open(casos_file, "w") as f:
            json.dump(casos_json, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n📄 Casos guardados: {casos_file}")

        # Archivo de log de ejecución
        log_file = self.output_dir / "execution.log"
        with open(log_file, "w") as f:
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Iteraciones: {self.metrics.iteracion_actual}\n")
            f.write(f"Casos generados: {self.metrics.casos_generados}\n")
            f.write(f"Casos aprobados: {self.metrics.casos_aprobados}\n")
            f.write(f"Cobertura: {self.metrics.cobertura_actual:.1%}\n")
            f.write(f"Tokens usados: {self.metrics.tokens_usados}\n")
            f.write(f"Flags: {', '.join(self.metrics.flags) if self.metrics.flags else 'ninguno'}\n")
        print(f"📋 Log guardado: {log_file}")
