# backend/agents/guias/graph.py
"""
Grafo LangGraph para geração de guias.
VERSÃO CORRIGIDA - Processamento paralelo funcional
"""

from langgraph.graph import StateGraph, END
from .state import GuiaState
from .nodes.gerador_node import gerador_node
from .nodes.revisor_node import revisor_node
from .nodes.salvar_node import salvar_node
import asyncio
from typing import List
from backend.utils.logger import logger


def create_guias_graph():
    """Cria grafo LangGraph para geração de guias."""
    
    workflow = StateGraph(GuiaState)
    
    # Adiciona nodes
    workflow.add_node("gerar", gerador_node)
    workflow.add_node("revisar", revisor_node)
    workflow.add_node("salvar", salvar_node)
    
    # Entry point
    workflow.set_entry_point("gerar")
    
    # Edges
    workflow.add_edge("gerar", "revisar")
    
    # Edge condicional (revisar → gerar ou salvar)
    def should_retry(state: GuiaState) -> str:
        topico = next(t for t in state["topicos"] if t["id"] == state["topico_atual_id"])
        
        if topico["status"] == "gerando":
            return "gerar"  # Retry
        else:
            return "salvar"  # Aprovado
    
    workflow.add_conditional_edges(
        "revisar",
        should_retry,
        {"gerar": "gerar", "salvar": "salvar"}
    )
    
    workflow.add_edge("salvar", END)
    
    return workflow.compile()


# ============================================
# PROCESSAMENTO DE UM ÚNICO TÓPICO
# ============================================

async def processar_topico(
    state_base: GuiaState,
    topico_id: str,
    graph
) -> tuple[str, dict]:
    """
    Processa um único tópico.
    
    Args:
        state_base: Estado base (compartilhado, mas não modificado)
        topico_id: ID do tópico a processar
        graph: Grafo compilado
        
    Returns:
        tuple: (topico_id, topico_atualizado)
    """
    
    # Cria cópia do state para este tópico
    # IMPORTANTE: Cada tópico precisa de seu próprio state isolado
    state_topico = state_base.copy()
    state_topico["topico_atual_id"] = topico_id
    
    # Pega o tópico específico
    topico = next(t for t in state_topico["topicos"] if t["id"] == topico_id)
    
    logger.info(f"🎯 [Paralelo] Iniciando: {topico['nome_completo']}")
    
    try:
        # Executa grafo para este tópico
        final_state = await graph.ainvoke(state_topico)
        
        # Pega o tópico atualizado
        topico_atualizado = next(
            t for t in final_state["topicos"] 
            if t["id"] == topico_id
        )
        
        if topico_atualizado["status"] == "concluido":
            logger.success(f"✅ [Paralelo] Concluído: {topico['nome_completo']}")
        else:
            logger.warning(f"⚠️ [Paralelo] Status: {topico_atualizado['status']} - {topico['nome_completo']}")
        
        return topico_id, topico_atualizado
        
    except Exception as e:
        logger.error(f"❌ [Paralelo] Erro em {topico['nome_completo']}: {e}")
        
        # Marca como erro
        topico["status"] = "erro_fatal"
        topico["erro"] = {
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        return topico_id, topico


# ============================================
# PROCESSAMENTO PARALELO DE MÚLTIPLOS TÓPICOS
# ============================================

async def processar_topicos_paralelo(
    state: GuiaState,
    graph,
    max_paralelo: int = 3
) -> List[dict]:
    """
    Processa múltiplos tópicos em paralelo.
    
    Args:
        state: Estado base
        graph: Grafo compilado
        max_paralelo: Máximo de tópicos simultâneos
        
    Returns:
        Lista de tópicos processados
    """
    
    topicos_ids = [t["id"] for t in state["topicos"]]
    total_topicos = len(topicos_ids)
    
    logger.info(
        f"🚀 Iniciando processamento PARALELO de {total_topicos} tópico(s)\n"
        f"   ⚙️ Max simultâneos: {max_paralelo}"
    )
    
    # Semáforo para limitar concorrência
    semaphore = asyncio.Semaphore(max_paralelo)
    
    async def process_with_semaphore(topico_id: str):
        """Wrapper que usa semáforo para limitar concorrência."""
        async with semaphore:
            return await processar_topico(state, topico_id, graph)
    
    # Cria tasks para todos os tópicos
    tasks = [process_with_semaphore(tid) for tid in topicos_ids]
    
    # Executa todas as tasks em paralelo (respeitando max_paralelo)
    logger.info(f"⏳ Aguardando conclusão de {total_topicos} tópico(s)...")
    
    resultados = await asyncio.gather(
        *tasks,
        return_exceptions=True  # Não para se um falhar
    )
    
    # Processa resultados
    topicos_processados = {}
    
    for i, resultado in enumerate(resultados):
        if isinstance(resultado, Exception):
            logger.error(f"❌ Tópico {i+1} falhou com exceção: {resultado}")
            # Usa tópico original com status de erro
            topico_original = state["topicos"][i]
            topico_original["status"] = "erro_fatal"
            topico_original["erro"] = {
                "message": str(resultado),
                "timestamp": datetime.now().isoformat()
            }
            topicos_processados[topico_original["id"]] = topico_original
        else:
            topico_id, topico_atualizado = resultado
            topicos_processados[topico_id] = topico_atualizado
    
    # Reconstrói lista na ordem original
    topicos_finais = [
        topicos_processados[t["id"]]
        for t in state["topicos"]
    ]
    
    # Estatísticas
    concluidos = sum(1 for t in topicos_finais if t["status"] == "concluido")
    erros = sum(1 for t in topicos_finais if t["status"] == "erro_fatal")
    
    logger.success(
        f"🎉 Processamento paralelo concluído!\n"
        f"   ✅ Sucesso: {concluidos}/{total_topicos}\n"
        f"   ❌ Erros: {erros}/{total_topicos}"
    )
    
    return topicos_finais


# ============================================
# FUNÇÃO PRINCIPAL - EXECUTE GRAPH GUIAS
# ============================================

async def execute_graph_guias(config: dict, modo: str = "sequencial"):
    """
    Executa geração de guias para todos os tópicos.
    
    VERSÃO CORRIGIDA - Suporta processamento paralelo real.
    
    Args:
        config: Dict com configuração do YAML
        modo: "sequencial" ou "paralelo"
    """
    from .state import criar_topico_inicial, criar_estatisticas_iniciais
    from datetime import datetime
    
    logger.info(f"📋 Modo de processamento: {modo.upper()}")
    
    # Cria state inicial
    state: GuiaState = {
        "projeto_nome": config["projeto"]["nome"],
        "area_conhecimento": config["projeto"]["area_conhecimento"],
        "radical_arquivo": config["projeto"]["radical_arquivo"],
        "pasta_saida": config["projeto"].get("pasta_saida_guias", "output/guias"),
        
        "topicos": [
            criar_topico_inicial(i, nome, config["projeto"]["radical_arquivo"])
            for i, nome in enumerate(config["topicos"])
        ],
        
        "llm_gerador_provider": config["modelos_guias"]["gerador"]["provedor"],
        "llm_gerador_modelo": config["modelos_guias"]["gerador"]["modelo"],
        "llm_gerador_temperatura": config["modelos_guias"]["gerador"].get("temperatura", 0.7),
        "llm_gerador_max_tokens": config["modelos_guias"]["gerador"].get("max_tokens", 8000),
        
        "llm_revisor_provider": config["modelos_guias"]["revisor"]["provedor"],
        "llm_revisor_modelo": config["modelos_guias"]["revisor"]["modelo"],
        "llm_revisor_temperatura": config["modelos_guias"]["revisor"].get("temperatura", 0.3),
        "llm_revisor_max_tokens": config["modelos_guias"]["revisor"].get("max_tokens", 2048),
        
        "max_paralelo": config["processamento"].get("max_paralelo", 3),
        "max_tentativas_revisao": config["processamento"].get("max_tentativas_revisao", 3),
        "delay_retry": config["processamento"].get("delay_retry", 5),
        
        "prompt_gerador": "",  # Carregado dos prompts.py
        "prompt_revisor": "",
        
        "status_geral": "processando",
        "topico_atual_id": None,
        "estatisticas": criar_estatisticas_iniciais(len(config["topicos"])),
        "logs": [],
        "erro_msg": None
    }
    
    graph = create_guias_graph()
    
    # ============================================
    # ESCOLHE MODO DE PROCESSAMENTO
    # ============================================
    
    if modo.lower() == "paralelo":
        # ✅ PROCESSAMENTO PARALELO
        logger.info("🚀 Usando processamento PARALELO")
        
        max_paralelo = state["max_paralelo"]
        
        topicos_finais = await processar_topicos_paralelo(
            state=state,
            graph=graph,
            max_paralelo=max_paralelo
        )
        
        # Atualiza state com tópicos processados
        state["topicos"] = topicos_finais
        
    else:
        # ✅ PROCESSAMENTO SEQUENCIAL (original)
        logger.info("📝 Usando processamento SEQUENCIAL")
        
        for topico in state["topicos"]:
            state["topico_atual_id"] = topico["id"]
            
            logger.info(f"🎯 Processando: {topico['nome_completo']}")
            
            # Executa grafo
            final_state = await graph.ainvoke(state)
            
            # Atualiza o tópico no state principal
            topico_atualizado = next(
                t for t in final_state["topicos"]
                if t["id"] == topico["id"]
            )
            
            # Atualiza in-place
            for key in topico_atualizado:
                topico[key] = topico_atualizado[key]
            
            if topico["status"] == "concluido":
                logger.success(f"✅ Concluído: {topico['nome_completo']}")
    
    # ============================================
    # FINALIZAÇÃO
    # ============================================
    
    # Lista arquivos gerados
    arquivos_gerados = [
        t["nome_arquivo"]
        for t in state["topicos"]
        if t["status"] == "concluido" and t.get("nome_arquivo")
    ]
    
    state["status_geral"] = "concluido"
    state["arquivos_gerados"] = arquivos_gerados
    
    # Recalcula estatísticas
    from .state import atualizar_estatisticas
    state["estatisticas"] = atualizar_estatisticas(state)
    
    logger.success(
        f"🎉 Processamento concluído!\n"
        f"   📚 Arquivos gerados: {len(arquivos_gerados)}\n"
        f"   ⏱️ Modo: {modo.upper()}"
    )
    
    return {
        "status": "concluido",
        "status_geral": "concluido",
        "arquivos_gerados": arquivos_gerados,
        "estatisticas": state.get("estatisticas", {}),
        "logs": state.get("logs", [])
    }