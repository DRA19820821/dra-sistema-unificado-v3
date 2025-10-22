# backend/api/routes_pipeline.py
"""
Rotas para pipeline completo: Guias → Mapas
VERSÃO CORRIGIDA - Fix erro de argumentos e tratamento robusto
"""

from fastapi import APIRouter, HTTPException, File, UploadFile
from pathlib import Path
from typing import List
import asyncio

from ..core.config import get_settings
from ..services.config_parser import parse_yaml_config
from ..agents.guias.graph import execute_graph_guias
from ..agents.mapas.graph import execute_graph  # ✅ Nome correto!
from ..api.websocket import manager
from ..utils.logger import logger

router = APIRouter()
settings = get_settings()


def extract_llm_providers(config: dict) -> tuple:
    """
    Extrai providers dos LLMs do config.
    
    Returns:
        tuple: (llm01_provider, llm02_provider, llm03_provider)
    """
    try:
        modelos_mapas = config.get("modelos_mapas", {})
        
        llm01 = modelos_mapas.get("divisor", {}).get("provedor", "anthropic")
        llm02 = modelos_mapas.get("gerador", {}).get("provedor", "anthropic")
        llm03 = modelos_mapas.get("revisor", {}).get("provedor", "anthropic")
        
        logger.debug(f"Providers extraídos: LLM01={llm01}, LLM02={llm02}, LLM03={llm03}")
        
        return llm01, llm02, llm03
        
    except Exception as e:
        logger.error(f"Erro ao extrair providers: {e}")
        # Fallback para Anthropic
        return "anthropic", "anthropic", "anthropic"


async def process_mapa_with_retry(
    html_file: str, 
    llm01: str, 
    llm02: str, 
    llm03: str,
    max_tentativas: int = 3,
    max_retries: int = 2
) -> dict:
    """
    Processa mapa com retry robusto em caso de falha.
    
    Args:
        html_file: Nome do arquivo HTML
        llm01, llm02, llm03: Providers dos LLMs
        max_tentativas: Max tentativas de revisão por parte
        max_retries: Max retries em caso de erro crítico
        
    Returns:
        dict: Resultado do processamento
    """
    
    for retry in range(max_retries + 1):
        try:
            logger.info(f"🗺️ Processando {html_file} (tentativa {retry + 1}/{max_retries + 1})...")
            
            resultado = await execute_graph(
                html_filename=html_file,
                llm01_provider=llm01,
                llm02_provider=llm02,
                llm03_provider=llm03,
                max_tentativas=max_tentativas
            )
            
            # Validação do resultado
            if not isinstance(resultado, dict):
                raise ValueError(f"Resultado inválido: não é um dict, é {type(resultado)}")
            
            if resultado.get("status") == "erro":
                erro_msg = resultado.get("erro_msg", "Erro desconhecido")
                logger.warning(f"⚠️ {html_file}: processamento retornou erro: {erro_msg}")
                
                # Se não é a última tentativa, tenta novamente
                if retry < max_retries:
                    logger.info(f"🔄 Tentando novamente {html_file}...")
                    await asyncio.sleep(2 * (retry + 1))  # Backoff exponencial
                    continue
                
                # Última tentativa - retorna o erro
                return resultado
            
            # Sucesso!
            num_partes = len(resultado.get("partes_processadas", []))
            logger.success(f"✅ {html_file}: {num_partes} mapa(s) gerado(s)")
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar {html_file}: {str(e)}")
            
            # Se não é a última tentativa, tenta novamente
            if retry < max_retries:
                logger.info(f"🔄 Tentando novamente {html_file}...")
                await asyncio.sleep(2 * (retry + 1))
                continue
            
            # Última tentativa - retorna erro estruturado
            return {
                "html_file": html_file,
                "status": "erro",
                "erro_msg": f"Falha após {max_retries + 1} tentativas: {str(e)}",
                "partes_processadas": []
            }
    
    # Não deve chegar aqui, mas por segurança
    return {
        "html_file": html_file,
        "status": "erro",
        "erro_msg": "Erro desconhecido no retry",
        "partes_processadas": []
    }


@router.post("/process-full")
async def process_full_pipeline(
    config_file: UploadFile = File(...),
    modo: str = "sequencial"
):
    """
    Pipeline completo: Gera guias e depois mapas automaticamente.
    VERSÃO CORRIGIDA com tratamento robusto de erros.
    
    Fluxo:
    1. Parse do YAML de configuração
    2. Executa LangGraph GUIAS para gerar HTMLs
    3. Detecta HTMLs gerados
    4. Executa LangGraph MAPAS para gerar .mmd (COM RETRY)
    
    Args:
        config_file: Arquivo YAML de configuração
        modo: "sequencial" ou "paralelo"
    """
    
    try:
        logger.info("🚀 Iniciando pipeline completo")
        
        # === ETAPA 1: PARSE CONFIG ===
        await manager.send_progress({
            "stage": "config",
            "pipeline": "full",
            "message": "Carregando configuração...",
            "percentage": 0
        })
        
        config_content = await config_file.read()
        config = parse_yaml_config(config_content)
        
        logger.info(f"📋 Config carregada: {config['projeto']['nome']}")
        
        # Valida config
        if "modelos_mapas" not in config:
            logger.warning("⚠️ 'modelos_mapas' não encontrado no YAML. Usando defaults.")
            config["modelos_mapas"] = {
                "divisor": {"provedor": "anthropic"},
                "gerador": {"provedor": "anthropic"},
                "revisor": {"provedor": "anthropic"}
            }
        
        # === ETAPA 2: GERAR GUIAS ===
        await manager.send_progress({
            "stage": "guias",
            "pipeline": "full",
            "message": "Iniciando geração de guias...",
            "percentage": 5
        })
        
        await manager.send_log({
            "level": "info",
            "message": f"📚 Gerando {len(config['topicos'])} guia(s)..."
        })
        
        # Executa graph de guias
        resultado_guias = await execute_graph_guias(
            config=config,
            modo=modo
        )
        
        if resultado_guias["status_geral"] != "concluido":
            raise Exception(f"Falha na geração de guias: {resultado_guias.get('erro_msg')}")
        
        arquivos_html = resultado_guias.get("arquivos_gerados", [])
        
        logger.success(f"✅ {len(arquivos_html)} guia(s) gerado(s)")
        
        await manager.send_progress({
            "stage": "guias",
            "pipeline": "full",
            "message": f"✅ {len(arquivos_html)} guias gerados",
            "percentage": 50
        })
        
        # === ETAPA 3: GERAR MAPAS ===
        await manager.send_progress({
            "stage": "mapas",
            "pipeline": "full",
            "message": "Iniciando geração de mapas mentais...",
            "percentage": 55
        })
        
        await manager.send_log({
            "level": "info",
            "message": f"🗺️ Processando {len(arquivos_html)} HTML(s) para mapas..."
        })
        
        # Extrai providers do config
        llm01, llm02, llm03 = extract_llm_providers(config)
        
        max_tentativas_revisao = config.get("processamento", {}).get("max_tentativas_revisao", 3)
        
        # Executa graph de mapas para cada HTML (COM RETRY)
        resultados_mapas = []
        
        for i, html_file in enumerate(arquivos_html, 1):
            progress = 55 + (40 * i / len(arquivos_html))
            
            await manager.send_progress({
                "stage": "mapas",
                "pipeline": "full",
                "message": f"Processando {html_file} ({i}/{len(arquivos_html)})...",
                "percentage": int(progress)
            })
            
            # ✅ CHAMADA CORRIGIDA COM RETRY
            resultado_mapa = await process_mapa_with_retry(
                html_file=html_file,
                llm01=llm01,
                llm02=llm02,
                llm03=llm03,
                max_tentativas=max_tentativas_revisao,
                max_retries=2  # 3 tentativas totais
            )
            
            resultados_mapas.append(resultado_mapa)
            
            # Log do resultado
            if resultado_mapa.get("status") == "concluido":
                num_partes = len(resultado_mapa.get("partes_processadas", []))
                await manager.send_log({
                    "level": "success",
                    "message": f"✅ {html_file}: {num_partes} mapa(s)"
                })
            else:
                erro_msg = resultado_mapa.get("erro_msg", "Erro desconhecido")
                await manager.send_log({
                    "level": "error",
                    "message": f"❌ {html_file}: {erro_msg}"
                })
        
        # === CONCLUSÃO ===
        await manager.send_progress({
            "stage": "completo",
            "pipeline": "full",
            "message": "Pipeline completo concluído!",
            "percentage": 100
        })
        
        # Conta arquivos .mmd gerados
        total_mmds = sum(
            len(r.get("partes_processadas", []))
            for r in resultados_mapas
            if r.get("status") == "concluido"
        )
        
        # Conta erros
        total_erros = sum(
            1 for r in resultados_mapas
            if r.get("status") == "erro"
        )
        
        await manager.send_completion({
            "success": total_erros == 0,
            "pipeline": "full",
            "guias": {
                "total": len(arquivos_html),
                "arquivos": arquivos_html
            },
            "mapas": {
                "total": total_mmds,
                "erros": total_erros,
                "resultados": resultados_mapas
            }
        })
        
        logger.success(
            f"🎉 Pipeline completo!\n"
            f"   📚 Guias: {len(arquivos_html)}\n"
            f"   🗺️ Mapas: {total_mmds}\n"
            f"   ❌ Erros: {total_erros}"
        )
        
        return {
            "status": "completed",
            "pipeline": "full",
            "guias": {
                "total": len(arquivos_html),
                "arquivos": arquivos_html,
                "estatisticas": resultado_guias.get("estatisticas")
            },
            "mapas": {
                "total": total_mmds,
                "erros": total_erros,
                "resultados": resultados_mapas
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro no pipeline: {e}")
        logger.exception(e)  # Stack trace completo
        
        await manager.send_log({
            "level": "error",
            "message": f"❌ Erro crítico: {str(e)}"
        })
        
        raise HTTPException(500, str(e))


@router.post("/process-guias-only")
async def process_guias_only(config_file: UploadFile = File(...)):
    """Processa apenas geração de guias (sem mapas)."""
    try:
        config_content = await config_file.read()
        config = parse_yaml_config(config_content)
        
        resultado = await execute_graph_guias(config=config)
        
        return {
            "status": "completed",
            "pipeline": "guias-only",
            "resultado": resultado
        }
        
    except Exception as e:
        logger.error(f"❌ Erro em guias-only: {e}")
        raise HTTPException(500, str(e))


@router.post("/process-mapas-only")
async def process_mapas_only(
    html_files: List[str],
    config_file: UploadFile = File(...)
):
    """
    Processa apenas geração de mapas (de HTMLs existentes).
    VERSÃO CORRIGIDA com retry.
    
    Args:
        html_files: Lista de nomes de arquivos HTML em output/guias/
        config_file: YAML com config dos modelos de mapas
    """
    try:
        config_content = await config_file.read()
        config = parse_yaml_config(config_content)
        
        # Extrai providers
        llm01, llm02, llm03 = extract_llm_providers(config)
        max_tentativas = config.get("processamento", {}).get("max_tentativas_revisao", 3)
        
        resultados = []
        
        for html_file in html_files:
            # ✅ Usa função com retry
            resultado = await process_mapa_with_retry(
                html_file=html_file,
                llm01=llm01,
                llm02=llm02,
                llm03=llm03,
                max_tentativas=max_tentativas,
                max_retries=2
            )
            resultados.append(resultado)
        
        total_sucesso = sum(1 for r in resultados if r.get("status") == "concluido")
        total_erros = sum(1 for r in resultados if r.get("status") == "erro")
        
        return {
            "status": "completed",
            "pipeline": "mapas-only",
            "total": len(html_files),
            "sucesso": total_sucesso,
            "erros": total_erros,
            "resultados": resultados
        }
        
    except Exception as e:
        logger.error(f"❌ Erro em mapas-only: {e}")
        raise HTTPException(500, str(e))