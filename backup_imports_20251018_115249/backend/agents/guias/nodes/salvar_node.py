from ..state import GuiaState
from ...services.file_manager import salvar_guia_html
from ...services.naming_utils import gerar_nome_arquivo
from backend.utils.logger import logger
from datetime import datetime

async def salvar_node(state: GuiaState) -> GuiaState:
    """Salva guia HTML no disco."""
    
    topico_id = state["topico_atual_id"]
    topico = next(t for t in state["topicos"] if t["id"] == topico_id)
    
    logger.info(f"💾 Salvando guia: {topico['nome_completo']}")
    
    try:
        # Gera nome do arquivo
        nome_arquivo = gerar_nome_arquivo(
            state["radical_arquivo"],
            topico["indice"],
            topico["nome_completo"]
        )
        
        # Salva
        filepath = salvar_guia_html(nome_arquivo, topico["html_gerado"])
        
        # Atualiza state
        topico["nome_arquivo"] = nome_arquivo
        topico["status"] = "concluido"
        topico["timestamp_conclusao"] = datetime.now().isoformat()
        
        # Calcula tempo
        inicio = datetime.fromisoformat(topico["timestamp_inicio"])
        fim = datetime.now()
        topico["tempo_decorrido_ms"] = int((fim - inicio).total_seconds() * 1000)
        
        logger.success(f"✅ Salvo: {nome_arquivo}")
        
        return state
        
    except Exception as e:
        logger.error(f"❌ Erro ao salvar: {e}")
        topico["status"] = "erro_fatal"
        topico["erro"] = {"message": str(e), "timestamp": datetime.now().isoformat()}
        return state