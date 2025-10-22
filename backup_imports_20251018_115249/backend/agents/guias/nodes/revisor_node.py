from ..state import GuiaState
from ...services.llm_factory import get_llm
from ..prompts.revisor_prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from backend.utils.logger import logger
from pydantic import BaseModel
from typing import List
import json

class Problema(BaseModel):
    categoria: str
    gravidade: str
    descricao: str
    localizacao: str

class AvaliacaoGuia(BaseModel):
    aprovado: bool
    nota_geral: float
    problemas: List[Problema]
    sugestoes_melhoria: List[str]
    justificativa: str

async def revisor_node(state: GuiaState) -> GuiaState:
    """
    Node do LLM Revisor de Guias.
    Migrado de autobase/server/processor/reviewer.js
    """
    
    topico_id = state["topico_atual_id"]
    topico = next(t for t in state["topicos"] if t["id"] == topico_id)
    
    logger.info(f"🔍 Revisando guia: {topico['nome_completo']}")
    
    try:
        # Obtém LLM com structured output
        llm = get_llm(
            provider=state["llm_revisor_provider"],
            model=state["llm_revisor_modelo"],
            temperature=state["llm_revisor_temperatura"],
            max_tokens=state["llm_revisor_max_tokens"]
        )
        
        structured_llm = llm.with_structured_output(AvaliacaoGuia)
        
        # Prepara prompt
        prompt = USER_PROMPT_TEMPLATE.format(
            area_conhecimento=state["area_conhecimento"],
            topico=topico["nome_completo"],
            html_gerado=topico["html_gerado"],
            tentativa=topico["tentativas_revisao"] + 1,
            max_tentativas=state["max_tentativas_revisao"]
        )
        
        # Chama LLM
        avaliacao = await structured_llm.ainvoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ])
        
        # Armazena feedback
        topico["ultimo_feedback"] = avaliacao.model_dump()
        
        # Histórico
        topico["historico"].append({
            "timestamp": datetime.now().isoformat(),
            "acao": "revisao",
            "tentativa": topico["tentativas_revisao"] + 1,
            "resultado": "aprovado" if avaliacao.aprovado else "reprovado",
            "pontuacao": avaliacao.nota_geral
        })
        
        if avaliacao.aprovado:
            logger.success(f"✅ Guia APROVADO (nota: {avaliacao.nota_geral})")
            topico["status"] = "salvando"
        else:
            topico["tentativas_revisao"] += 1
            
            if topico["tentativas_revisao"] >= state["max_tentativas_revisao"]:
                logger.error(f"❌ Máximo de tentativas atingido. Auto-aprovando...")
                topico["status"] = "salvando"
                topico["ultimo_feedback"]["aprovado"] = True
            else:
                logger.warning(f"⚠️ Guia REPROVADO. Tentando novamente...")
                topico["status"] = "gerando"  # Volta para gerar novamente
        
        return state
        
    except Exception as e:
        logger.error(f"❌ Erro na revisão: {e}")
        # Em caso de erro, auto-aprova
        topico["status"] = "salvando"
        return state