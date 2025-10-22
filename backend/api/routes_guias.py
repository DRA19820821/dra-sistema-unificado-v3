from fastapi import APIRouter, UploadFile, File
from ..services.config_parser import parse_yaml_config
from ..agents.guias.graph import execute_graph_guias

router = APIRouter()

@router.post("/process")
async def process_guias(config_file: UploadFile = File(...)):
    """Processa apenas guias."""
    config_content = await config_file.read()
    config = parse_yaml_config(config_content)
    
    resultado = await execute_graph_guias(config)
    
    return {"status": "completed", "resultado": resultado}