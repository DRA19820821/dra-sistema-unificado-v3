# backend/agents/mapas/nodes/salvar_node.py
"""
Node responsável por salvar arquivos .mmd gerados.
VERSÃO FINAL - TODOS OS IMPORTS ABSOLUTOS
"""

from ..state import MindmapState
from backend.utils.logger import logger
from backend.core.config import get_settings
from pathlib import Path
from datetime import datetime
import json

settings = get_settings()


def save_mmd_file(filename: str, content: str, metadata: dict = None) -> str:
    """
    Salva arquivo .mmd com metadados opcionais.
    
    Args:
        filename: Nome do arquivo
        content: Conteúdo Mermaid
        metadata: Metadados opcionais (dict)
        
    Returns:
        str: Path completo do arquivo salvo
    """
    
    output_dir = Path(settings.output_mapas_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / filename
    
    # Salva conteúdo
    filepath.write_text(content, encoding='utf-8')
    
    # Salva metadados se fornecidos
    if metadata:
        metadata_file = filepath.with_suffix('.json')
        metadata_file.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
    
    return str(filepath)


async def salvar_mindmap_node(state: MindmapState) -> MindmapState:
    """
    Salva os arquivos .mmd gerados.
    """
    logger.info("💾 Salvando mapas mentais...")
    
    try:
        arquivos_salvos = []
        
        # Pega o nome base do HTML (sem extensão)
        import os
        html_base = os.path.splitext(state["html_filename"])[0]
        
        # Salva cada parte processada
        for parte in state["partes_processadas"]:
            # Nome do arquivo: base_parte01.mmd, base_parte02.mmd, etc
            filename = f"{html_base}_parte{parte['parte_numero']:02d}.mmd"
            
            filepath = save_mmd_file(
                filename=filename,
                content=parte["mapa_gerado"],
                metadata={
                    "ramo_direito": state["ramo_direito"],
                    "topico": state["topico"],
                    "parte_titulo": parte["parte_titulo"],
                    "parte_numero": parte["parte_numero"],
                    "aprovado": parte["aprovado"],
                    "nota_geral": parte.get("nota_geral"),
                    "tentativas": parte["tentativas"],
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            arquivos_salvos.append(filepath)
            logger.success(f"💾 Salvo: {filename}")
        
        state["status"] = "concluido"
        state["logs"].append({
            "timestamp": datetime.now().isoformat(),
            "node": "salvar_mindmap",
            "level": "success",
            "message": f"Salvos {len(arquivos_salvos)} arquivo(s)",
            "data": {
                "arquivos_salvos": arquivos_salvos,
                "total": len(arquivos_salvos)
            }
        })
        
        logger.success(f"✅ Processamento concluído! {len(arquivos_salvos)} arquivos salvos.")
        
        return state
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar arquivos: {str(e)}")
        logger.exception(e)
        
        state["status"] = "erro"
        state["erro_msg"] = str(e)
        
        state["logs"].append({
            "timestamp": datetime.now().isoformat(),
            "node": "salvar_mindmap",
            "level": "error",
            "message": f"Erro ao salvar: {str(e)}",
            "data": {
                "error_type": type(e).__name__
            }
        })
        
        return state