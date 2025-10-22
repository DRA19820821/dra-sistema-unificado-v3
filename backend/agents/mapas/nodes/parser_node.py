# backend/agents/mapas/nodes/parser_node.py
"""
Node responsável por extrair informações dos arquivos HTML.
VERSÃO FINAL - TODOS OS IMPORTS ABSOLUTOS
"""

from bs4 import BeautifulSoup
from ..state import MindmapState
from backend.utils.logger import logger
from backend.core.config import get_settings
import re
from pathlib import Path
from datetime import datetime

settings = get_settings()


async def parse_html_node(state: MindmapState) -> MindmapState:
    """
    Extrai informações do arquivo HTML.
    
    Processa o HTML para extrair:
    1. Ramo do Direito (do title)
    2. Tópico (do title)
    3. Fundamentação Teórica (da section#fundamentacao)
    """
    
    logger.info(f"📄 Iniciando parsing: {state['html_filename']}")
    
    try:
        # Monta caminho completo do arquivo
        # Tenta primeiro em output/guias
        filepath = Path(settings.output_guias_dir) / state["html_filename"]
        
        # Se não existir, tenta em uploads
        if not filepath.exists():
            filepath = Path(settings.upload_dir) / state["html_filename"]
        
        # Verifica se arquivo existe
        if not filepath.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        
        # Lê o conteúdo do arquivo
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse com BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')
        
        # ============================================
        # EXTRAI O TITLE
        # ============================================
        
        title_tag = soup.find('title')
        if not title_tag:
            raise ValueError("Tag <title> não encontrada no HTML")
        
        title = title_tag.get_text(strip=True)
        logger.debug(f"Title encontrado: {title}")
        
        # ============================================
        # PARSE DO TITLE
        # ============================================
        
        pattern = r'^\[(.+?)\]\s*-\s*\[(.+?)\]\s*-'
        match = re.match(pattern, title)
        
        if not match:
            pattern_alt = r'^(.+?)\s*-\s*(.+?)\s*-'
            match = re.match(pattern_alt, title)
            
            if not match:
                raise ValueError(
                    f"Title não segue o padrão esperado.\n"
                    f"Esperado: [RAMO DO DIREITO] - [TÓPICO] - Guia Completo para Concursos\n"
                    f"Recebido: {title}"
                )
        
        ramo_direito = match.group(1).strip()
        topico = match.group(2).strip()
        
        logger.info(f"✅ Ramo: {ramo_direito}")
        logger.info(f"✅ Tópico: {topico}")
        
        # ============================================
        # EXTRAI FUNDAMENTAÇÃO TEÓRICA
        # ============================================
        
        fundamentacao_section = soup.find('section', id='fundamentacao')
        
        if not fundamentacao_section:
            raise ValueError(
                "Section com id='fundamentacao' não encontrada no HTML.\n"
                "Certifique-se de que existe: <section id=\"fundamentacao\">...</section>"
            )
        
        fundamentacao = fundamentacao_section.get_text(separator='\n', strip=True)
        fundamentacao = re.sub(r'\n{3,}', '\n\n', fundamentacao)
        fundamentacao = re.sub(r' {2,}', ' ', fundamentacao)
        
        logger.info(f"✅ Fundamentação: {len(fundamentacao)} caracteres")
        logger.debug(f"Primeiros 200 chars: {fundamentacao[:200]}...")
        
        # ============================================
        # VALIDAÇÕES
        # ============================================
        
        if len(fundamentacao) < 100:
            raise ValueError(
                f"Fundamentação muito curta ({len(fundamentacao)} chars). "
                "Conteúdo insuficiente para gerar mapas mentais."
            )
        
        if len(fundamentacao) > 100000:
            logger.warning(
                f"⚠️ Fundamentação muito longa ({len(fundamentacao)} chars). "
                "Pode haver problemas com limites de contexto dos LLMs."
            )
        
        # ============================================
        # ATUALIZA ESTADO
        # ============================================
        
        state["ramo_direito"] = ramo_direito
        state["topico"] = topico
        state["fundamentacao"] = fundamentacao
        state["status"] = "dividindo"
        
        state["logs"].append({
            "timestamp": datetime.now().isoformat(),
            "node": "parse_html",
            "level": "success",
            "message": f"HTML parsed com sucesso: {state['html_filename']}",
            "data": {
                "ramo": ramo_direito,
                "topico": topico,
                "tamanho_fundamentacao": len(fundamentacao),
                "num_paragrafos": fundamentacao.count('\n\n') + 1
            }
        })
        
        logger.success(f"✅ Parsing concluído: {ramo_direito} - {topico}")
        
        return state
    
    except FileNotFoundError as e:
        logger.error(f"❌ Arquivo não encontrado: {str(e)}")
        state["status"] = "erro"
        state["erro_msg"] = f"Arquivo não encontrado: {state['html_filename']}"
        return state
    
    except ValueError as e:
        logger.error(f"❌ Erro de validação: {str(e)}")
        state["status"] = "erro"
        state["erro_msg"] = str(e)
        return state
    
    except Exception as e:
        logger.error(f"❌ Erro ao parsear HTML: {str(e)}")
        logger.exception(e)
        
        state["status"] = "erro"
        state["erro_msg"] = f"Erro ao processar HTML: {str(e)}"
        
        state["logs"].append({
            "timestamp": datetime.now().isoformat(),
            "node": "parse_html",
            "level": "error",
            "message": f"Erro ao parsear: {str(e)}",
            "data": {
                "filename": state['html_filename'],
                "error_type": type(e).__name__
            }
        })
        
        return state