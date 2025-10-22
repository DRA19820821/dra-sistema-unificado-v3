# test_dynamic_prompts.py
import asyncio
from backend.agents.guias.graph import execute_graph_guias
from backend.services.config_parser import load_yaml_file
from pathlib import Path

async def test():
    # Carrega config
    config = load_yaml_file(Path("config/projetos/exemplo.yaml"))
    
    # Executa
    resultado = await execute_graph_guias(config)
    
    # Verifica logs
    for log in resultado["logs"]:
        if log["node"] == "revisor":
            print(f"Revisão: {log['data']}")

asyncio.run(test())