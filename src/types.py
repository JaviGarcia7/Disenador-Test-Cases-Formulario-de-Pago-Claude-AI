"""Type definitions for test case designer"""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class FieldType(str, Enum):
    """Tipos de campo soportados por el MCP"""
    MONETARIO = "monetario"
    EMAIL = "email"
    TELEFONO = "teléfono"
    SELECT = "select"
    CHECKBOX = "checkbox"
    TEXTO = "texto"
    FECHA = "fecha"


class Criticidad(str, Enum):
    """Niveles de criticidad de edge cases"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EdgeCase(BaseModel):
    """Edge case del catálogo MCP"""
    id: str
    descripcion: str
    criticidad: Criticidad
    ejemplo_entrada: str
    resultado_esperado: str
    campo_tipo: FieldType


class TestStep(BaseModel):
    """Un paso de un caso de prueba"""
    step: int
    action: str
    expected: str


class TestCase(BaseModel):
    """Caso de prueba generado"""
    id: str
    title: str
    edge_case_covered: str
    criticidad: Criticidad
    test_steps: list[TestStep]
    aprobado: bool = False
    feedback_revisor: Optional[str] = None
    score_rubrica: Optional[float] = None


class HistoriaUsuario(BaseModel):
    """Historia de usuario de entrada"""
    id: str
    descripcion: str
    campos: list[dict[str, Any]]


class MCPStatistics(BaseModel):
    """Estadísticas de cobertura del MCP"""
    total: int
    por_tipo: dict[str, int] = Field(default_factory=dict)
    por_criticidad: dict[str, int] = Field(default_factory=dict)


class ExecutionMetrics(BaseModel):
    """Métricas de ejecución del orquestador"""
    iteracion_actual: int = 0
    tokens_usados: int = 0
    casos_generados: int = 0
    casos_aprobados: int = 0
    cobertura_actual: float = 0.0
    flags: list[str] = Field(default_factory=list)


class RubricaScore(BaseModel):
    """Score de rúbrica para un caso"""
    completitud: float
    claridad: float
    criticidad: float
    independencia: float
    trazabilidad: float

    def promedio(self) -> float:
        """Calcula el promedio de scores"""
        scores = [
            self.completitud,
            self.claridad,
            self.criticidad,
            self.independencia,
            self.trazabilidad,
        ]
        return sum(scores) / len(scores)
