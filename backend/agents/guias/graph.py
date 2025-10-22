from langgraph.graph import StateGraph, END
from .state import GuiaState
from .nodes.gerador_node import gerador_node
from .nodes.revisor_node import revisor_node
from .nodes.salvar_node import salvar_node

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

async def execute_graph_guias(config: dict, modo: str = "sequencial"):
    """
    Executa geração de guias para todos os tópicos.
    
    Args:
        config: Dict com configuração do YAML
        modo: "sequencial" ou "paralelo"
    """
    from .state import criar_topico_inicial, criar_estatisticas_iniciais
    
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
    
    # Processa cada tópico
    arquivos_gerados = []
    
    for topico in state["topicos"]:
        state["topico_atual_id"] = topico["id"]
        
        # Executa grafo
        final_state = await graph.ainvoke(state)
        
        if topico["status"] == "concluido":
            arquivos_gerados.append(topico["nome_arquivo"])
    
    state["status_geral"] = "concluido"
    state["arquivos_gerados"] = arquivos_gerados
    
    return {
        "status": "concluido",
        "status_geral": "concluido",
        "arquivos_gerados": arquivos_gerados,
        "estatisticas": state.get("estatisticas", {}),
        "logs": state.get("logs", [])
    }