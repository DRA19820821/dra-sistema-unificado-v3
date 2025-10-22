# backend/agents/guias/state.py
"""
State do LangGraph para geração de guias educacionais.
Migrado e adaptado do sistema Node.js original.
"""

from typing import TypedDict, List, Literal, Optional
from datetime import datetime


class GuiaState(TypedDict):
    """
    Estado compartilhado entre nodes do grafo de geração de guias.
    
    Este state é equivalente ao state.json do sistema Node.js,
    mas integrado com LangGraph para orquestração elegante.
    """
    
    # ============================================
    # CONFIGURAÇÃO DO PROJETO (do YAML)
    # ============================================
    projeto_nome: str
    """Nome do projeto"""
    
    area_conhecimento: str
    """Área do conhecimento (ex: Direito Constitucional)"""
    
    radical_arquivo: str
    """Radical para nomenclatura (ex: dConst)"""
    
    pasta_saida: str
    """Diretório de output para os guias"""
    
    # ============================================
    # TÓPICOS A PROCESSAR
    # ============================================
    topicos: List[dict]
    """
    Lista de tópicos a processar. Cada tópico:
    {
        "id": "dConst01_DirGarFun",
        "indice": 0,
        "nome_completo": "Direitos e Garantias Fundamentais",
        "status": "aguardando|gerando|em_revisao|concluido|erro_fatal",
        "tentativas_revisao": 0,
        "timestamp_inicio": None,
        "timestamp_conclusao": None,
        "html_gerado": "",
        "nome_arquivo": "",
        "tokens_usados": {},
        "tempo_decorrido_ms": 0,
        "historico": [],
        "ultimo_feedback": None,
        "erro": None
    }
    """
    
    # ============================================
    # CONFIGURAÇÃO DOS MODELOS
    # ============================================
    llm_gerador_provider: str
    llm_gerador_modelo: str
    llm_gerador_temperatura: float
    llm_gerador_max_tokens: int
    
    llm_revisor_provider: str
    llm_revisor_modelo: str
    llm_revisor_temperatura: float
    llm_revisor_max_tokens: int
    
    # ============================================
    # CONFIGURAÇÕES DE PROCESSAMENTO
    # ============================================
    max_paralelo: int
    """Máximo de tópicos processados simultaneamente"""
    
    max_tentativas_revisao: int
    """Máximo de tentativas de revisão por tópico"""
    
    delay_retry: int
    """Delay em segundos entre retries"""
    
    # ============================================
    # PROMPTS
    # ============================================
    prompt_gerador: str
    """Template do prompt do gerador"""
    
    prompt_revisor: str
    """Template do prompt do revisor"""
    
    # ============================================
    # ESTADO DO PROCESSAMENTO
    # ============================================
    status_geral: Literal[
        "inicializando",
        "processando",
        "pausado",
        "concluido",
        "erro"
    ]
    """Status geral do processamento"""
    
    topico_atual_id: Optional[str]
    """ID do tópico sendo processado atualmente"""
    
    # ============================================
    # ESTATÍSTICAS
    # ============================================
    estatisticas: dict
    """
    {
        "total": 10,
        "concluidos": 5,
        "em_processamento": 2,
        "aguardando": 3,
        "erros": 0,
        "tokens_totais": {"input": 50000, "output": 30000},
        "tempo_total_ms": 120000,
        "custos_estimados": {"gerador": 0.05, "revisor": 0.03}
    }
    """
    
    # ============================================
    # LOGS E TELEMETRIA
    # ============================================
    logs: List[dict]
    """
    Lista de eventos de log:
    {
        "timestamp": "2025-01-15T14:30:00",
        "level": "info|success|warning|error",
        "message": "...",
        "topico_id": "...",
        "metadata": {}
    }
    """
    
    erro_msg: Optional[str]
    """Mensagem de erro crítico, se houver"""


# ============================================
# HELPER FUNCTIONS
# ============================================

def criar_topico_inicial(indice: int, nome: str, radical: str) -> dict:
    """
    Cria estrutura inicial de um tópico.
    Migrado de NamingUtils.gerarIdTopico do Node.js
    """
    from backend.services.naming_utils import gerar_id_topico, gerar_nome_arquivo
    
    topico_id = gerar_id_topico(radical, indice, nome)
    
    return {
        "id": topico_id,
        "indice": indice,
        "nome_completo": nome,
        "status": "aguardando",
        "tentativas_revisao": 0,
        "timestamp_inicio": None,
        "timestamp_conclusao": None,
        "html_gerado": "",
        "nome_arquivo": "",
        "tokens_usados": {
            "geracao_input": 0,
            "geracao_output": 0,
            "revisao_input": 0,
            "revisao_output": 0
        },
        "tempo_decorrido_ms": 0,
        "historico": [],
        "ultimo_feedback": None,
        "erro": None
    }


def criar_estatisticas_iniciais(total_topicos: int) -> dict:
    """Cria estrutura inicial de estatísticas."""
    return {
        "total": total_topicos,
        "concluidos": 0,
        "em_processamento": 0,
        "aguardando": total_topicos,
        "erros": 0,
        "tokens_totais": {
            "input": 0,
            "output": 0
        },
        "tempo_total_ms": 0,
        "custos_estimados": {
            "gerador": 0.0,
            "revisor": 0.0,
            "total": 0.0
        }
    }


def atualizar_estatisticas(state: GuiaState) -> dict:
    """
    Recalcula estatísticas baseado no estado dos tópicos.
    Migrado de StateManager.recalcularEstatisticas do Node.js
    """
    stats = {
        "total": len(state["topicos"]),
        "concluidos": 0,
        "em_processamento": 0,
        "aguardando": 0,
        "erros": 0,
        "tokens_totais": {"input": 0, "output": 0},
        "tempo_total_ms": 0,
        "custos_estimados": {"gerador": 0.0, "revisor": 0.0, "total": 0.0}
    }
    
    for topico in state["topicos"]:
        status = topico["status"]
        
        if status == "concluido":
            stats["concluidos"] += 1
        elif status == "aguardando":
            stats["aguardando"] += 1
        elif status == "erro_fatal":
            stats["erros"] += 1
        elif status in ["gerando", "em_revisao", "salvando"]:
            stats["em_processamento"] += 1
        
        # Soma tokens
        if topico.get("tokens_usados"):
            tokens = topico["tokens_usados"]
            stats["tokens_totais"]["input"] += tokens.get("geracao_input", 0)
            stats["tokens_totais"]["input"] += tokens.get("revisao_input", 0)
            stats["tokens_totais"]["output"] += tokens.get("geracao_output", 0)
            stats["tokens_totais"]["output"] += tokens.get("revisao_output", 0)
        
        # Soma tempo
        if topico.get("tempo_decorrido_ms"):
            stats["tempo_total_ms"] += topico["tempo_decorrido_ms"]
    
    return stats


def adicionar_log(
    state: GuiaState,
    level: Literal["info", "success", "warning", "error"],
    message: str,
    topico_id: Optional[str] = None,
    metadata: dict = None
) -> None:
    """Adiciona entrada de log ao state."""
    state["logs"].append({
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "message": message,
        "topico_id": topico_id,
        "metadata": metadata or {}
    })