"""API REST con FastAPI para el Diseñador de Casos de Prueba"""

import asyncio
import json
from typing import Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pathlib import Path

from src.types import HistoriaUsuario, TestCase, Criticidad, TestStep
from src.mcp_client import MCPClient
from src.reviewer import Revisor
from src.designer import Diseñador


# Models para API
class Campo(BaseModel):
    nombre: str
    tipo: str


class HistoriaUsuarioInput(BaseModel):
    id: str
    descripcion: str
    campos: List[Campo]


class GenerarCasosRequest(BaseModel):
    historia_usuario: HistoriaUsuarioInput
    max_iteraciones: int = 3
    coverage_threshold: float = 0.80


class GenerarCasosResponse(BaseModel):
    success: bool
    casos_aprobados: int
    cobertura: float
    iteraciones: int
    flags: List[str]
    archivo_json: str
    archivo_log: str


class EdgeCaseResponse(BaseModel):
    id: str
    descripcion: str
    criticidad: str
    ejemplo_entrada: str
    resultado_esperado: str
    campo_tipo: str


class CoberturaResponse(BaseModel):
    total: int
    por_tipo: dict
    por_criticidad: dict


# Inicializar FastAPI
app = FastAPI(
    title="Diseñador de Casos de Prueba",
    description="API para generar y validar casos de prueba automáticamente",
    version="0.1.0",
)

# Almacenar estado de ejecuciones recientes
executions = {}


# ==================== ENDPOINTS ====================


@app.get("/", tags=["Health"])
async def root():
    """Health check"""
    return {
        "servicio": "Diseñador de Casos de Prueba",
        "version": "0.1.0",
        "estado": "operativo",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check detallado"""
    mcp = MCPClient()
    stats = await mcp.obtener_estadisticas_cobertura()

    return {
        "status": "healthy",
        "mcp": {
            "total_edge_cases": stats.total,
            "tipos_soportados": list(stats.por_tipo.keys()),
        },
        "timestamp": str(asyncio.get_event_loop().time()),
    }


@app.get("/edge-cases", tags=["MCP"], response_model=List[EdgeCaseResponse])
async def obtener_edge_cases(
    campo_tipo: str,
    criticidad_minima: str = "low",
):
    """
    Obtiene edge cases por tipo de campo y criticidad.

    - **campo_tipo**: monetario, email, teléfono, select, checkbox, texto, fecha
    - **criticidad_minima**: high, medium, low
    """
    try:
        mcp = MCPClient()
        cases = await mcp.obtener_edge_cases(
            campo_tipo=campo_tipo,
            criticidad_minima=criticidad_minima,
        )

        return [
            EdgeCaseResponse(
                id=case.id,
                descripcion=case.descripcion,
                criticidad=case.criticidad.value,
                ejemplo_entrada=case.ejemplo_entrada,
                resultado_esperado=case.resultado_esperado,
                campo_tipo=case.campo_tipo.value,
            )
            for case in cases
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/cobertura-estadisticas", tags=["MCP"], response_model=CoberturaResponse)
async def obtener_estadisticas():
    """Obtiene estadísticas de cobertura del catálogo MCP"""
    mcp = MCPClient()
    stats = await mcp.obtener_estadisticas_cobertura()

    return CoberturaResponse(
        total=stats.total,
        por_tipo=stats.por_tipo,
        por_criticidad=stats.por_criticidad,
    )


@app.post("/generar-casos", tags=["Diseñador"], response_model=GenerarCasosResponse)
async def generar_casos(
    request: GenerarCasosRequest,
    background_tasks: BackgroundTasks,
):
    """
    Genera casos de prueba automáticamente.

    **Parámetros:**
    - historia_usuario: Historia de usuario con campos
    - max_iteraciones: Máximo de vueltas (1-3)
    - coverage_threshold: Cobertura mínima requerida (0.0-1.0)

    **Retorna:**
    - success: ¿Éxito?
    - casos_aprobados: Cantidad
    - cobertura: Porcentaje alcanzado
    - iteraciones: Vueltas ejecutadas
    - flags: Alertas (si las hay)
    - archivo_json: Ruta de casos_aprobados.json
    - archivo_log: Ruta de execution.log
    """
    try:
        # Convertir input a tipos internos
        hu = HistoriaUsuario(
            id=request.historia_usuario.id,
            descripcion=request.historia_usuario.descripcion,
            campos=[c.model_dump() for c in request.historia_usuario.campos],
        )

        # Validar parámetros
        if not 1 <= request.max_iteraciones <= 3:
            raise HTTPException(
                status_code=400, detail="max_iteraciones debe estar entre 1 y 3"
            )

        if not 0.0 <= request.coverage_threshold <= 1.0:
            raise HTTPException(
                status_code=400, detail="coverage_threshold debe estar entre 0.0 y 1.0"
            )

        # Cargar golden_set
        golden_set = []
        golden_set_path = Path("ideacion/02-entregables/golden_set.json")

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
                        criticidad=Criticidad(
                            caso_raw.get("criticidad", "high").lower()
                        ),
                        test_steps=test_steps,
                    )
                    golden_set.append(case)
            except Exception as e:
                pass  # Continuar sin golden_set

        # Ejecutar diseñador
        mcp_client = MCPClient()
        reviewer = Revisor(timeout_seconds=30)
        diseñador = Diseñador(
            mcp_client=mcp_client,
            reviewer=reviewer,
            max_iteraciones=request.max_iteraciones,
            token_budget=100000,
            coverage_threshold=request.coverage_threshold,
            output_dir="output",
        )

        casos_aprobados, metrics = await diseñador.generar_casos(hu, golden_set)

        # Preparar respuesta
        success = metrics.cobertura_actual >= request.coverage_threshold
        if "budget-exhausted" in metrics.flags:
            success = False

        return GenerarCasosResponse(
            success=success,
            casos_aprobados=metrics.casos_aprobados,
            cobertura=metrics.cobertura_actual,
            iteraciones=metrics.iteracion_actual,
            flags=metrics.flags,
            archivo_json="output/casos_aprobados.json",
            archivo_log="output/execution.log",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@app.post("/validar-edge-case", tags=["MCP"])
async def validar_edge_case(edge_case_id: str):
    """
    Valida si un edge case existe en el catálogo.

    **Parámetro:**
    - edge_case_id: ID del edge case a validar

    **Retorna:**
    - existe: bool
    - detalles: metadata del edge case (si existe)
    """
    try:
        mcp = MCPClient()
        result = await mcp.validar_edge_case(edge_case_id)

        if result["existe"]:
            return {
                "existe": True,
                "id": edge_case_id,
                "criticidad": result.get("criticidad"),
                "descripcion": result.get("descripcion"),
                "campo_tipo": result.get("campo_tipo"),
                "ejemplo_entrada": result.get("ejemplo_entrada"),
            }
        else:
            return {"existe": False, "id": edge_case_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MANEJO DE ERRORES ====================


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
    }


# ==================== INICIALIZACIÓN ====================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
