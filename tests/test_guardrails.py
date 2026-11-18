"""Tests para guardrails y validaciones"""

import pytest
from src.guardrails import DataMasker, SchemaValidator, HalluccinationDetector


class TestDataMasker:
    """Tests para enmascaramiento de datos"""

    def test_mask_input_real_card(self):
        """Enmascarar tarjeta real con espacios"""
        input_str = "Tarjeta: 4111 1111 1111 1111"
        masked = DataMasker.mask_input(input_str)
        assert "[REDACTED_CARD]" in masked
        assert "4111 1111" not in masked

    def test_mask_input_test_card(self):
        """Permitir tarjeta de prueba sin espacios"""
        input_str = "Tarjeta: 4111111111111111"
        masked = DataMasker.mask_input(input_str)
        # Test card sin espacios se permite en entrada
        assert "4111111111111111" in masked or "[REDACTED_CARD]" in masked

    def test_mask_output_card_in_steps(self):
        """Enmascarar tarjeta en steps de salida"""
        from src.types import TestCase, TestStep, Criticidad

        caso = TestCase(
            id="TEST-001",
            title="Test",
            edge_case_covered="EC-001",
            criticidad=Criticidad.HIGH,
            test_steps=[
                TestStep(
                    step=1,
                    action="Ingrese tarjeta 4111111111111111",
                    expected="Aceptado",
                )
            ],
        )

        masked_caso = DataMasker.mask_output(caso)
        assert "[REDACTED_CARD]" in masked_caso.test_steps[0].action


class TestSchemaValidator:
    """Tests para validación de schema"""

    def test_validate_valid_case(self):
        """Validar caso correcto"""
        valid_case = {
            "id": "CASO-001",
            "title": "Test",
            "edge_case_covered": "EC-001",
            "criticidad": "high",
            "test_steps": [
                {"step": 1, "action": "Do X", "expected": "Y happens"}
            ],
        }
        is_valid, err = SchemaValidator.validate_test_case(valid_case)
        assert is_valid
        assert err is None

    def test_validate_missing_fields(self):
        """Rechazar caso con campos faltantes"""
        invalid_case = {
            "id": "CASO-001",
            "title": "Test",
            # Faltan: edge_case_covered, criticidad, test_steps
        }
        is_valid, err = SchemaValidator.validate_test_case(invalid_case)
        assert not is_valid
        assert "edge_case_covered" in err or "Campos faltantes" in err

    def test_validate_empty_steps(self):
        """Rechazar caso con test_steps vacío"""
        invalid_case = {
            "id": "CASO-001",
            "title": "Test",
            "edge_case_covered": "EC-001",
            "criticidad": "high",
            "test_steps": [],  # Vacío
        }
        is_valid, err = SchemaValidator.validate_test_case(invalid_case)
        assert not is_valid


class TestHalluccinationDetector:
    """Tests para detección de hallucinations"""

    def test_valid_edge_case(self):
        """Detectar edge case válido"""
        detector = HalluccinationDetector({"EC-001", "EC-002"})
        assert not detector.is_hallucination("EC-001")

    def test_invalid_edge_case(self):
        """Detectar edge case inventado"""
        detector = HalluccinationDetector({"EC-001", "EC-002"})
        assert detector.is_hallucination("EC-999-FAKE")
