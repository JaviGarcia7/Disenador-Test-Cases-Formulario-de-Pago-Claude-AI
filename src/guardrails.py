"""Guardrails de entrada/salida: validación y enmascaramiento de datos sensibles"""

import re
from typing import Any, Optional
from src.types import TestCase, EdgeCase


class DataMasker:
    """Enmascaramiento de datos sensibles en entrada y salida"""

    # Patrones para tarjetas reales (con espacios, formatos variados)
    CARD_REAL_PATTERN = re.compile(r"\d{4}\s\d{4}\s\d{4}\s\d{4}")

    # Tarjetas de prueba permitidas (formato estándar, sin espacios)
    TEST_CARDS = {
        "4111111111111111",  # Visa test
        "4111111111110005",  # Visa test - insufficient funds
        "000000000000",      # Generic test
    }

    # Patrones para CVV
    CVV_PATTERN = re.compile(r"CVV[:\s]+(\d{3,4})")

    @staticmethod
    def mask_input(data: str) -> str:
        """
        Enmascarar datos sensibles en entrada.
        - Tarjetas reales (con espacios) → [REDACTED_CARD]
        - CVV fuera de contexto → [REDACTED_CVV]
        - Tarjetas de prueba sin espacios → permitir
        """
        # Enmascarar tarjetas reales (con espacios)
        masked = DataMasker.CARD_REAL_PATTERN.sub("[REDACTED_CARD]", data)

        # Enmascarar CVV fuera de contexto (que no esté en 'validacion' o 'ejemplo')
        # Simplificado: solo si está libre, no en estructura JSON
        if "validacion" not in data.lower() and "ejemplo" not in data.lower():
            masked = DataMasker.CVV_PATTERN.sub(
                "CVV: [REDACTED_CVV]", masked
            )

        return masked

    @staticmethod
    def mask_output(test_case: TestCase) -> TestCase:
        """
        Enmascarar datos sensibles en salida.
        - Número de tarjeta en steps → [REDACTED_CARD]
        - CVV en steps → [REDACTED_CVV]
        """
        masked_case = test_case.model_copy(deep=True)

        for step in masked_case.test_steps:
            # Enmascarar tarjetas (16 dígitos sin espacios = test permitido, pero igualmente ocultamos en salida)
            step.action = re.sub(r"\d{15,16}", "[REDACTED_CARD]", step.action)
            step.expected = re.sub(r"\d{15,16}", "[REDACTED_CARD]", step.expected)

            # Enmascarar CVV
            step.action = re.sub(r"CVV[:\s]+\d{3,4}", "CVV: [REDACTED_CVV]", step.action)
            step.expected = re.sub(
                r"CVV[:\s]+\d{3,4}", "CVV: [REDACTED_CVV]", step.expected
            )

        return masked_case


class SchemaValidator:
    """Validación de schema de casos generados"""

    @staticmethod
    def validate_test_case(case: Any) -> tuple[bool, Optional[str]]:
        """
        Valida que un caso tenga todos los campos requeridos.
        Retorna (válido: bool, error: Optional[str])
        """
        required_fields = {"id", "title", "edge_case_covered", "criticidad", "test_steps"}

        if not isinstance(case, dict):
            return False, "Caso debe ser un dict"

        missing = required_fields - set(case.keys())
        if missing:
            return False, f"Campos faltantes: {missing}"

        if not isinstance(case.get("test_steps"), list) or len(case["test_steps"]) == 0:
            return False, "test_steps debe ser una lista no vacía"

        for step in case["test_steps"]:
            step_required = {"step", "action", "expected"}
            if not isinstance(step, dict) or not step_required.issubset(step.keys()):
                return False, f"Step incompleto: {step}"

        return True, None

    @staticmethod
    def validate_edge_case(case: EdgeCase) -> tuple[bool, Optional[str]]:
        """Valida que un edge case sea válido"""
        if not case.id or not case.descripcion:
            return False, "Edge case debe tener id y descripción"

        return True, None


class HalluccinationDetector:
    """Detecta si el modelo genera edge cases inventados (no en catálogo)"""

    def __init__(self, catalog_ids: set[str]):
        """
        catalog_ids: set de IDs válidos del catálogo MCP
        """
        self.catalog_ids = catalog_ids

    def is_hallucination(self, edge_case_id: str) -> bool:
        """Retorna True si el edge case no existe en el catálogo"""
        return edge_case_id not in self.catalog_ids

    def validate_case_coverage(self, case: TestCase) -> tuple[bool, Optional[str]]:
        """Valida que el edge_case_covered existe en el catálogo"""
        if self.is_hallucination(case.edge_case_covered):
            return (
                False,
                f"Edge case inventado: '{case.edge_case_covered}' no en catálogo",
            )
        return True, None
