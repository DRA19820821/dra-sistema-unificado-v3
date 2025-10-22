from ..state import GuiaState
from ...services.llm_factory import get_llm
from ..prompts.gerador_prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from backend.utils.logger import logger
from datetime import datetime

async def gerador_node(state: GuiaState) -> GuiaState:
    """
    Node do LLM Gerador de Guias.
    Migrado de autobase/server/processor/generator.js
    """
    
    topico_id = state["topico_atual_id"]
    topico = next(t for t in state["topicos"] if t["id"] == topico_id)
    
    logger.info(f"🎨 Gerando guia: {topico['nome_completo']}")
    
    # Atualiza status
    topico["status"] = "gerando"
    topico["timestamp_inicio"] = datetime.now().isoformat()
    
    try:
        # Obtém LLM
        llm = get_llm(
            provider=state["llm_gerador_provider"],
            model=state["llm_gerador_modelo"],
            temperature=state["llm_gerador_temperatura"],
            max_tokens=state["llm_gerador_max_tokens"]
        )
        
        # Prepara prompt
        prompt = USER_PROMPT_TEMPLATE.format(
            area_conhecimento=state["area_conhecimento"],
            topico=topico["nome_completo"]
        )
        
        # Chama LLM
        response = await llm.ainvoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ])
        
        html_gerado = response.content
        
        # Armazena resultado
        topico["html_gerado"] = html_gerado
        topico["tokens_usados"]["geracao_input"] = response.usage_metadata.get("input_tokens", 0)
        topico["tokens_usados"]["geracao_output"] = response.usage_metadata.get("output_tokens", 0)
        
        # Histórico
        topico["historico"].append({
            "timestamp": datetime.now().isoformat(),
            "acao": "geracao",
            "tentativa": topico["tentativas_revisao"] + 1,
            "tokens": {
                "input": topico["tokens_usados"]["geracao_input"],
                "output": topico["tokens_usados"]["geracao_output"]
            }
        })
        
        topico["status"] = "em_revisao"
        
        logger.success(f"✅ HTML gerado ({len(html_gerado)} chars)")
        
        return state
        
    except Exception as e:
        logger.error(f"❌ Erro na geração: {e}")
        topico["status"] = "erro_fatal"
        topico["erro"] = {"message": str(e), "timestamp": datetime.now().isoformat()}
        state["erro_msg"] = str(e)
        return state
