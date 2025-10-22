# backend/agents/guias/nodes/revisor_node.py
"""
Node do LLM Revisor de Guias.
Versão atualizada com substituição dinâmica de variáveis.
"""

from ..state import GuiaState
from backend.services.llm_factory import get_llm
from ..prompts.revisor_prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from backend.utils.logger import logger
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
import json


# ============================================
# MODELS PARA STRUCTURED OUTPUT
# ============================================

class Problema(BaseModel):
    categoria: str
    gravidade: str
    descricao: str
    localizacao: str


class AvaliacaoGuia(BaseModel):
    aprovado: bool
    pontuacao_geral: float = Field(ge=0, le=10)
    problemas: List[Problema]
    sugestoes_melhoria: List[str]
    observacoes: str


# ============================================
# NODE FUNCTION
# ============================================

async def revisor_node(state: GuiaState) -> GuiaState:
    """
    Node do LLM Revisor de Guias.
    
    Recebe dinamicamente:
    - area_conhecimento: do state (vem do YAML)
    - topico: nome completo do tópico sendo processado
    - html_gerado: HTML que foi gerado pelo gerador_node
    - tentativa: número da tentativa atual
    - max_tentativas: máximo de tentativas (do YAML)
    """
    
    topico_id = state["topico_atual_id"]
    topico = next(t for t in state["topicos"] if t["id"] == topico_id)
    
    logger.info(f"🔍 Revisando guia: {topico['nome_completo']}")
    
    try:
        # ============================================
        # EXTRAI VARIÁVEIS DINÂMICAS DO STATE
        # ============================================
        
        area_conhecimento = state["area_conhecimento"]  # Ex: "Direito Constitucional"
        nome_topico = topico["nome_completo"]            # Ex: "Direitos Fundamentais"
        html_gerado = topico["html_gerado"]              # HTML completo gerado
        tentativa_atual = topico["tentativas_revisao"] + 1
        max_tentativas = state["max_tentativas_revisao"]
        
        # Feedback anterior (se houver)
        feedback_anterior = ""
        if topico.get("ultimo_feedback"):
            ultimo = topico["ultimo_feedback"]
            if not ultimo.get("aprovado"):
                feedback_anterior = f"""
**FEEDBACK DA TENTATIVA ANTERIOR:**
- Nota: {ultimo.get('pontuacao_geral', 0):.1f}/10
- Problemas: {len(ultimo.get('problemas', []))}
- Principal problema: {ultimo['problemas'][0]['descricao'] if ultimo.get('problemas') else 'N/A'}
"""
        
        logger.debug(
            f"Variáveis dinâmicas:\n"
            f"  - Área: {area_conhecimento}\n"
            f"  - Tópico: {nome_topico}\n"
            f"  - HTML size: {len(html_gerado)} chars\n"
            f"  - Tentativa: {tentativa_atual}/{max_tentativas}"
        )
        
        # ============================================
        # OBTÉM LLM COM STRUCTURED OUTPUT
        # ============================================
        
        llm = get_llm(
            provider=state["llm_revisor_provider"],
            model=state["llm_revisor_modelo"],
            temperature=state["llm_revisor_temperatura"],
            max_tokens=state["llm_revisor_max_tokens"]
        )
        
        structured_llm = llm.with_structured_output(AvaliacaoGuia)
        
        logger.debug(f"LLM configurado: {state['llm_revisor_provider']}/{state['llm_revisor_modelo']}")
        
        # ============================================
        # FORMATA PROMPT COM VARIÁVEIS DINÂMICAS
        # ============================================
        
        user_prompt = USER_PROMPT_TEMPLATE.format(
            topico=nome_topico,
            area_conhecimento=area_conhecimento,
            html_gerado=html_gerado,
            tentativa=tentativa_atual,
            max_tentativas=max_tentativas,
            feedback_anterior=feedback_anterior
        )
        
        logger.debug(f"Prompt montado ({len(user_prompt)} chars)")
        
        # ============================================
        # CHAMA LLM REVISOR
        # ============================================
        
        logger.info(f"📞 Chamando LLM Revisor (tentativa {tentativa_atual}/{max_tentativas})...")
        
        avaliacao = await structured_llm.ainvoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ])
        
        logger.success(
            f"✅ Revisão concluída: "
            f"{'APROVADO' if avaliacao.aprovado else 'REPROVADO'} "
            f"(nota: {avaliacao.pontuacao_geral:.1f}/10)"
        )
        
        # ============================================
        # ARMAZENA FEEDBACK NO STATE
        # ============================================
        
        topico["ultimo_feedback"] = {
            "aprovado": avaliacao.aprovado,
            "pontuacao_geral": avaliacao.pontuacao_geral,
            "problemas": [p.model_dump() for p in avaliacao.problemas],
            "sugestoes_melhoria": avaliacao.sugestoes_melhoria,
            "observacoes": avaliacao.observacoes,
            "tentativa": tentativa_atual
        }
        
        # ============================================
        # REGISTRA NO HISTÓRICO
        # ============================================
        
        topico["historico"].append({
            "timestamp": datetime.now().isoformat(),
            "acao": "revisao",
            "tentativa": tentativa_atual,
            "resultado": "aprovado" if avaliacao.aprovado else "reprovado",
            "pontuacao": avaliacao.pontuacao_geral,
            "num_problemas": len(avaliacao.problemas),
            "problemas_criticos": len([
                p for p in avaliacao.problemas 
                if p.gravidade == "critica" or p.gravidade == "alta"
            ])
        })
        
        # ============================================
        # DECISÃO: APROVAR, REPROVAR OU AUTO-APROVAR
        # ============================================
        
        if avaliacao.aprovado:
            # ✅ APROVADO
            logger.success(
                f"✅ Guia APROVADO!\n"
                f"   Nota: {avaliacao.pontuacao_geral:.1f}/10\n"
                f"   Problemas: {len(avaliacao.problemas)}\n"
                f"   Observações: {avaliacao.observacoes[:100]}..."
            )
            topico["status"] = "salvando"
            
        else:
            # ❌ REPROVADO
            topico["tentativas_revisao"] += 1
            
            logger.warning(
                f"⚠️ Guia REPROVADO\n"
                f"   Nota: {avaliacao.pontuacao_geral:.1f}/10\n"
                f"   Problemas: {len(avaliacao.problemas)}"
            )
            
            # Mostra problemas principais
            for i, problema in enumerate(avaliacao.problemas[:3], 1):
                logger.warning(
                    f"   {i}. [{problema.gravidade.upper()}] {problema.categoria}\n"
                    f"      {problema.descricao}"
                )
            
            # Verifica se atingiu máximo de tentativas
            if topico["tentativas_revisao"] >= max_tentativas:
                logger.error(
                    f"❌ Esgotadas {max_tentativas} tentativas!\n"
                    f"   Auto-aprovando para continuar pipeline..."
                )
                
                # Auto-aprova forçadamente
                topico["status"] = "salvando"
                topico["ultimo_feedback"]["aprovado"] = True
                topico["ultimo_feedback"]["observacoes"] = (
                    f"[AUTO-APROVADO] Esgotadas {max_tentativas} tentativas. "
                    f"Nota original: {avaliacao.pontuacao_geral:.1f}. "
                    f"Revisar manualmente se necessário."
                )
            else:
                # Volta para gerar novamente
                logger.info(
                    f"🔄 Tentando novamente... "
                    f"({topico['tentativas_revisao']}/{max_tentativas})"
                )
                topico["status"] = "gerando"
        
        # ============================================
        # LOG ESTRUTURADO
        # ============================================
        
        state["logs"].append({
            "timestamp": datetime.now().isoformat(),
            "node": "revisor",
            "level": "success" if avaliacao.aprovado else "warning",
            "message": (
                f"Tópico '{nome_topico}' "
                f"{'aprovado' if avaliacao.aprovado else 'reprovado'}"
            ),
            "data": {
                "topico": nome_topico,
                "area": area_conhecimento,
                "tentativa": tentativa_atual,
                "max_tentativas": max_tentativas,
                "aprovado": avaliacao.aprovado,
                "nota": avaliacao.pontuacao_geral,
                "num_problemas": len(avaliacao.problemas),
                "auto_aprovado": (
                    topico["tentativas_revisao"] >= max_tentativas 
                    and not avaliacao.aprovado
                )
            }
        })
        
        return state
        
    except Exception as e:
        logger.error(f"❌ Erro na revisão: {e}")
        logger.exception(e)
        
        # Em caso de erro, auto-aprova para não travar o pipeline
        topico["status"] = "salvando"
        topico["ultimo_feedback"] = {
            "aprovado": True,
            "pontuacao_geral": 5.0,
            "problemas": [],
            "sugestoes_melhoria": [],
            "observacoes": f"[AUTO-APROVADO POR ERRO] Erro no revisor: {str(e)}"
        }
        
        state["logs"].append({
            "timestamp": datetime.now().isoformat(),
            "node": "revisor",
            "level": "error",
            "message": f"Erro ao revisar '{topico['nome_completo']}': {str(e)}",
            "data": {
                "error_type": type(e).__name__,
                "auto_aprovado": True
            }
        })
        
        return state