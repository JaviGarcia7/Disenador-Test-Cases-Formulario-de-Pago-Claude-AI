"""Cliente MCP para llamadas a herramientas de edge cases"""

import asyncio
import json
from typing import Any, Optional
from src.types import EdgeCase, FieldType, Criticidad, MCPStatistics


class MCPClient:
    """Cliente para interactuar con servidor MCP (mock por ahora)"""

    def __init__(self, catalog: Optional[dict[str, Any]] = None):
        """
        Inicializa con catálogo de edge cases.
        catalog: dict con estructura {tipo: [edge_cases]}
        """
        self.catalog = catalog or self._load_default_catalog()
        self._edge_case_ids = self._build_id_set()

    def _build_id_set(self) -> set[str]:
        """Construye set de IDs válidos del catálogo"""
        ids = set()
        for tipo, cases in self.catalog.items():
            for case in cases:
                ids.add(case["id"])
        return ids

    def _load_default_catalog(self) -> dict[str, Any]:
        """Carga catálogo por defecto (mock)"""
        return {
            FieldType.MONETARIO: [
                {
                    "id": "EC-001-MON",
                    "descripcion": "Número de tarjeta con caracteres alfabéticos",
                    "criticidad": "high",
                    "ejemplo_entrada": "4111AAAA2222BBBB",
                    "resultado_esperado": "Rechazo con mensaje de validación",
                },
                {
                    "id": "EC-002-MON",
                    "descripcion": "Número de tarjeta incompleto (< 15 dígitos)",
                    "criticidad": "high",
                    "ejemplo_entrada": "411111111111",
                    "resultado_esperado": "Rechazo con mensaje de longitud",
                },
            ],
            FieldType.FECHA: [
                {
                    "id": "EC-003-FEC",
                    "descripcion": "Fecha de expiración pasada",
                    "criticidad": "high",
                    "ejemplo_entrada": "05/23",
                    "resultado_esperado": "Rechazo: tarjeta expirada",
                },
            ],
            FieldType.TEXTO: [
                {
                    "id": "EC-004-CVV",
                    "descripcion": "CVV con menos de 3 dígitos",
                    "criticidad": "medium",
                    "ejemplo_entrada": "12",
                    "resultado_esperado": "Rechazo: CVV debe ser 3-4 dígitos",
                },
                {
                    "id": "EC-005-TIT",
                    "descripcion": "Titular vacío",
                    "criticidad": "high",
                    "ejemplo_entrada": "",
                    "resultado_esperado": "Rechazo: campo obligatorio",
                },
            ],
        }

    async def obtener_edge_cases(
        self,
        campo_tipo: str,
        criticidad_minima: str = "low",
    ) -> list[EdgeCase]:
        """
        Obtiene edge cases filtrados por tipo y criticidad.
        Simula: retardo + validación.
        """
        # Simula latencia de red
        await asyncio.sleep(0.1)

        # Validar tipo
        try:
            tipo = FieldType(campo_tipo)
        except ValueError:
            raise ValueError(f"Tipo de campo no soportado: {campo_tipo}")

        # Validar criticidad
        try:
            crit_min = Criticidad(criticidad_minima)
        except ValueError:
            raise ValueError(f"Criticidad inválida: {criticidad_minima}")

        # Filtrar casos
        cases = self.catalog.get(tipo.value, [])
        criticidad_order = {"high": 3, "medium": 2, "low": 1}
        min_value = criticidad_order.get(crit_min.value, 1)

        result = []
        for case in cases:
            if criticidad_order.get(case["criticidad"], 1) >= min_value:
                result.append(EdgeCase(
                    id=case["id"],
                    descripcion=case["descripcion"],
                    criticidad=Criticidad(case["criticidad"]),
                    ejemplo_entrada=case["ejemplo_entrada"],
                    resultado_esperado=case["resultado_esperado"],
                    campo_tipo=tipo,
                ))

        return result

    async def validar_edge_case(self, edge_case_id: str) -> dict[str, Any]:
        """
        Verifica si un edge case existe en el catálogo.
        Retorna: {existe: bool, ...detalles}
        """
        await asyncio.sleep(0.05)

        for tipo, cases in self.catalog.items():
            for case in cases:
                if case["id"] == edge_case_id:
                    return {
                        "existe": True,
                        "criticidad": case["criticidad"],
                        "descripcion": case["descripcion"],
                        "campo_tipo": tipo,
                        "ejemplo_entrada": case["ejemplo_entrada"],
                    }

        return {"existe": False}

    async def obtener_estadisticas_cobertura(self) -> MCPStatistics:
        """
        Retorna estadísticas de cobertura: total y distribución.
        """
        await asyncio.sleep(0.05)

        total = sum(len(cases) for cases in self.catalog.values())

        por_tipo = {
            tipo.value: len(cases) for tipo, cases in self.catalog.items()
        }

        por_criticidad = {}
        for tipo, cases in self.catalog.items():
            for case in cases:
                crit = case["criticidad"]
                por_criticidad[crit] = por_criticidad.get(crit, 0) + 1

        return MCPStatistics(
            total=total,
            por_tipo=por_tipo,
            por_criticidad=por_criticidad,
        )

    def get_catalog_ids(self) -> set[str]:
        """Retorna set de IDs válidos del catálogo"""
        return self._edge_case_ids
