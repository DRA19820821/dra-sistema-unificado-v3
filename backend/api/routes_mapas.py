from fastapi import APIRouter
from ..agents.mapas.graph import execute_graph

router = APIRouter()

@router.post("/process")
async def process_mapas(html_files: list[str]):
    """Processa apenas mapas."""
    resultados = []
    
    for html_file in html_files:
        resultado = await execute_graph(html_filename=html_file)
        resultados.append(resultado)
    
    return {"status": "completed", "resultados": resultados}