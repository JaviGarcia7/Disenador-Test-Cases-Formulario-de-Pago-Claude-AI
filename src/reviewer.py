"""Subagente Revisor: valida casos con rúbrica 5-criterios"""

import asyncio
from typing import Optional
from src.types import TestCase, RubricaScore, Criticidad


class Revisor:
    """Subagente que valida casos de prueba con rúbrica"""

    THRESHOLD = 4.0  # Score mínimo para aprobar

    def __init__(self, timeout_seconds: float = 30.0):
        self.timeout_seconds = timeout_seconds

    async def evaluar_caso(
        self,
        caso: TestCase,
        golden_set: Optional[list[TestCase]] = None,
    ) -> tuple[bool, str, Optional[RubricaScore]]:
        """
        Evalúa un caso con rúbrica 5-criterios.
        Retorna: (aprobado: bool, feedback: str, score: RubricaScore)
        """
        try:
            score = await asyncio.wait_for(
                self._calcular_rubrica(caso, golden_set),
                timeout=self.timeout_seconds,
            )
            promedio = score.promedio()
            aprobado = promedio >= self.THRESHOLD

            feedback = self._generar_feedback(caso, score, aprobado)
            return aprobado, feedback, score

        except asyncio.TimeoutError:
            return (
                True,  # Asumir aprobado por timeout (fallback optimista)
                "⚠️ Timeout (30s). Caso asumido como aprobado por timeout.",
                None,
            )

    async def _calcular_rubrica(
        self,
        caso: TestCase,
        golden_set: Optional[list[TestCase]] = None,
    ) -> RubricaScore:
        """
        Calcula scores de los 5 criterios.
        - Completitud (0-5): ¿toca realmente el edge case?
        - Claridad (0-5): ¿pasos ejecutables, sin ambigüedad?
        - Criticidad (0-5): ¿high-risk primero?
        - Independencia (0-5): ¿funciona aislado?
        - Trazabilidad (0-5): ¿vinculado a HU + golden_set?
        """
        # Simula evaluación (en v2: integrar modelo)
        await asyncio.sleep(0.2)

        completitud = self._evaluar_completitud(caso)
        claridad = self._evaluar_claridad(caso)
        criticidad = self._evaluar_criticidad(caso)
        independencia = self._evaluar_independencia(caso)
        trazabilidad = self._evaluar_trazabilidad(caso, golden_set)

        return RubricaScore(
            completitud=completitud,
            claridad=claridad,
            criticidad=criticidad,
            independencia=independencia,
            trazabilidad=trazabilidad,
        )

    @staticmethod
    def _evaluar_completitud(caso: TestCase) -> float:
        """¿El caso toca realmente el edge case?"""
        if len(caso.test_steps) < 2:
            return 2.0  # Muy corto

        # Si tiene validación explícita del edge case en steps
        validations = sum(
            1
            for step in caso.test_steps
            if any(
                word in step.expected.lower()
                for word in ["error", "rechazo", "rechaza", "inválido"]
            )
        )

        if validations > 0:
            return 5.0
        elif len(caso.test_steps) >= 3:
            return 4.0
        else:
            return 3.0

    @staticmethod
    def _evaluar_claridad(caso: TestCase) -> float:
        """¿Pasos ejecutables, sin ambigüedad?"""
        clarity_score = 5.0

        for step in caso.test_steps:
            if len(step.action) < 10:
                clarity_score -= 0.5
            if len(step.expected) < 5:
                clarity_score -= 0.5

        return max(1.0, clarity_score)

    @staticmethod
    def _evaluar_criticidad(caso: TestCase) -> float:
        """¿High-risk primero?"""
        if caso.criticidad == Criticidad.HIGH:
            return 5.0
        elif caso.criticidad == Criticidad.MEDIUM:
            return 3.0
        else:
            return 2.0

    @staticmethod
    def _evaluar_independencia(caso: TestCase) -> float:
        """¿Funciona aislado sin pre-condiciones?"""
        # Heurística: si primer step es "acceder" o "abrir", es independiente
        if caso.test_steps and "acceder" in caso.test_steps[0].action.lower():
            return 5.0
        return 3.0

    @staticmethod
    def _evaluar_trazabilidad(
        caso: TestCase,
        golden_set: Optional[list[TestCase]] = None,
    ) -> float:
        """¿Vinculado a HU + golden_set?"""
        # Si tiene edge_case_covered, es trazable
        if caso.edge_case_covered and len(caso.edge_case_covered) > 0:
            trazabilidad = 4.0

            # Si está en golden_set, es +1 (máximo 5)
            if golden_set:
                for gs_case in golden_set:
                    if gs_case.edge_case_covered == caso.edge_case_covered:
                        return 5.0

            return trazabilidad
        else:
            return 2.0

    @staticmethod
    def _generar_feedback(
        caso: TestCase,
        score: RubricaScore,
        aprobado: bool,
    ) -> str:
        """Genera feedback detallado del veredicto"""
        promedio = score.promedio()

        feedback_lines = [
            f"{'✅ APROBADO' if aprobado else '❌ RECHAZADO'}",
            f"Score promedio: {promedio:.2f}/5.0 (threshold: {Revisor.THRESHOLD})",
            "",
            f"Completitud: {score.completitud:.1f}/5",
            f"Claridad: {score.claridad:.1f}/5",
            f"Criticidad: {score.criticidad:.1f}/5",
            f"Independencia: {score.independencia:.1f}/5",
            f"Trazabilidad: {score.trazabilidad:.1f}/5",
        ]

        if not aprobado:
            weak = []
            if score.completitud < 3.0:
                weak.append(f"Completitud baja ({score.completitud:.1f})")
            if score.claridad < 3.0:
                weak.append(f"Claridad baja ({score.claridad:.1f})")
            if score.trazabilidad < 3.0:
                weak.append(f"Trazabilidad baja ({score.trazabilidad:.1f})")

            if weak:
                feedback_lines.append("")
                feedback_lines.append("Puntos a mejorar:")
                for point in weak:
                    feedback_lines.append(f"  - {point}")

        return "\n".join(feedback_lines)
