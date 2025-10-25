#!/usr/bin/env python3
"""
Script de teste para validar correção do processamento paralelo.

Uso:
    python test_parallel_fix.py
"""

import asyncio
import time
import yaml
from pathlib import Path
from datetime import datetime


# ============================================
# CONFIGURAÇÃO DO TESTE
# ============================================

TEST_CONFIG = {
    "projeto": {
        "nome": "Teste Paralelo",
        "area_conhecimento": "Direito Teste",
        "radical_arquivo": "dTest",
        "pasta_saida_guias": "./output/guias"
    },
    "topicos": [
        "Tópico Teste 1 - Conceitos Básicos",
        "Tópico Teste 2 - Aplicação Prática",
        "Tópico Teste 3 - Casos Especiais",
        "Tópico Teste 4 - Jurisprudência",
        "Tópico Teste 5 - Doutrina",
    ],
    "modelos_guias": {
        "gerador": {
            "provedor": "anthropic",
            "modelo": "claude-sonnet-4-20250514",
            "temperatura": 0.7,
            "max_tokens": 4000  # Reduzido para teste
        },
        "revisor": {
            "provedor": "anthropic",
            "modelo": "claude-sonnet-4-20250514",
            "temperatura": 0.3,
            "max_tokens": 2000
        }
    },
    "processamento": {
        "max_paralelo": 3,
        "max_tentativas_revisao": 2,  # Reduzido para teste
        "delay_retry": 3
    }
}


# ============================================
# FUNÇÕES DE TESTE
# ============================================

async def test_sequencial():
    """Testa modo sequencial (baseline)."""
    
    print("\n" + "="*70)
    print("📝 TESTE 1: MODO SEQUENCIAL")
    print("="*70)
    
    from backend.agents.guias.graph import execute_graph_guias
    
    inicio = time.time()
    
    try:
        resultado = await execute_graph_guias(
            config=TEST_CONFIG,
            modo="sequencial"
        )
        
        tempo_total = time.time() - inicio
        
        print(f"\n✅ Teste sequencial PASSOU")
        print(f"   ⏱️ Tempo: {tempo_total:.1f}s")
        print(f"   📚 Arquivos: {len(resultado['arquivos_gerados'])}")
        
        return True, tempo_total
        
    except Exception as e:
        print(f"\n❌ Teste sequencial FALHOU: {e}")
        return False, 0


async def test_paralelo():
    """Testa modo paralelo (corrigido)."""
    
    print("\n" + "="*70)
    print("🚀 TESTE 2: MODO PARALELO")
    print("="*70)
    
    from backend.agents.guias.graph import execute_graph_guias
    
    inicio = time.time()
    
    try:
        resultado = await execute_graph_guias(
            config=TEST_CONFIG,
            modo="paralelo"
        )
        
        tempo_total = time.time() - inicio
        
        print(f"\n✅ Teste paralelo PASSOU")
        print(f"   ⏱️ Tempo: {tempo_total:.1f}s")
        print(f"   📚 Arquivos: {len(resultado['arquivos_gerados'])}")
        
        return True, tempo_total
        
    except Exception as e:
        print(f"\n❌ Teste paralelo FALHOU: {e}")
        return False, 0


def validate_logs():
    """Valida que os logs mostram processamento paralelo."""
    
    print("\n" + "="*70)
    print("🔍 TESTE 3: VALIDAÇÃO DE LOGS")
    print("="*70)
    
    # Procura por marcadores de processamento paralelo
    log_dir = Path("logs")
    
    if not log_dir.exists():
        print("⚠️ Diretório de logs não encontrado")
        return None
    
    # Pega log mais recente
    log_files = sorted(log_dir.glob("app_*.log"), key=lambda x: x.stat().st_mtime)
    
    if not log_files:
        print("⚠️ Nenhum arquivo de log encontrado")
        return None
    
    latest_log = log_files[-1]
    
    with open(latest_log, encoding='utf-8') as f:
        content = f.read()
    
    # Procura marcadores
    marcadores = {
        "processamento_paralelo": "🚀 Usando processamento PARALELO" in content,
        "max_simultaneos": "⚙️ Max simultâneos:" in content,
        "iniciando_paralelo": "[Paralelo] Iniciando:" in content,
        "concluido_paralelo": "[Paralelo] Concluído:" in content,
        "processamento_concluido": "🎉 Processamento paralelo concluído!" in content,
    }
    
    print(f"\n📄 Arquivo: {latest_log.name}")
    print("\n✅ Marcadores encontrados:")
    
    for nome, encontrado in marcadores.items():
        emoji = "✅" if encontrado else "❌"
        print(f"   {emoji} {nome}: {encontrado}")
    
    todos_encontrados = all(marcadores.values())
    
    if todos_encontrados:
        print("\n✅ Todos os marcadores presentes!")
        return True
    else:
        print("\n⚠️ Alguns marcadores ausentes")
        return False


def calculate_speedup(tempo_seq, tempo_par):
    """Calcula speedup do processamento paralelo."""
    
    if tempo_seq == 0 or tempo_par == 0:
        return None
    
    speedup = tempo_seq / tempo_par
    
    print("\n" + "="*70)
    print("📊 ANÁLISE DE PERFORMANCE")
    print("="*70)
    
    print(f"\n⏱️ Tempo Sequencial: {tempo_seq:.1f}s")
    print(f"⏱️ Tempo Paralelo: {tempo_par:.1f}s")
    print(f"🚀 Speedup: {speedup:.2f}x")
    
    # Speedup esperado (teórico)
    max_paralelo = TEST_CONFIG["processamento"]["max_paralelo"]
    num_topicos = len(TEST_CONFIG["topicos"])
    
    speedup_teorico = min(max_paralelo, num_topicos)
    
    print(f"📈 Speedup Teórico (máx): {speedup_teorico:.2f}x")
    
    eficiencia = (speedup / speedup_teorico) * 100
    print(f"⚡ Eficiência: {eficiencia:.1f}%")
    
    if speedup >= 1.5:
        print(f"\n✅ SPEEDUP SIGNIFICATIVO! ({speedup:.2f}x)")
        return True
    elif speedup >= 1.1:
        print(f"\n⚠️ Speedup modesto ({speedup:.2f}x) - esperado maior")
        return True
    else:
        print(f"\n❌ SEM SPEEDUP ({speedup:.2f}x) - possível problema!")
        return False


# ============================================
# MAIN
# ============================================

async def main():
    """Executa todos os testes."""
    
    print("\n" + "="*70)
    print("🧪 TESTE DE CORREÇÃO - PROCESSAMENTO PARALELO")
    print("="*70)
    print(f"\n📋 Configuração:")
    print(f"   Tópicos: {len(TEST_CONFIG['topicos'])}")
    print(f"   Max Paralelo: {TEST_CONFIG['processamento']['max_paralelo']}")
    print(f"   Provider: {TEST_CONFIG['modelos_guias']['gerador']['provedor']}")
    
    # Verifica se arquivo foi corrigido
    print("\n🔍 Verificando se correção foi aplicada...")
    
    try:
        with open("backend/agents/guias/graph.py", encoding='utf-8') as f:
            content = f.read()
        
        if "processar_topicos_paralelo" in content:
            print("✅ Arquivo corrigido detectado!")
        else:
            print("❌ AVISO: Arquivo pode não estar corrigido!")
            print("   Certifique-se de ter substituído o graph.py")
            return
    except FileNotFoundError:
        print("❌ Arquivo graph.py não encontrado!")
        return
    
    # Executa testes
    resultados = {}
    
    # Teste 1: Sequencial
    success_seq, tempo_seq = await test_sequencial()
    resultados["sequencial"] = success_seq
    
    if not success_seq:
        print("\n❌ Teste sequencial falhou. Abortando.")
        return
    
    # Aguarda um pouco entre testes
    print("\n⏳ Aguardando 5s antes do próximo teste...")
    await asyncio.sleep(5)
    
    # Teste 2: Paralelo
    success_par, tempo_par = await test_paralelo()
    resultados["paralelo"] = success_par
    
    if not success_par:
        print("\n❌ Teste paralelo falhou.")
        return
    
    # Teste 3: Logs
    resultados["logs"] = validate_logs()
    
    # Teste 4: Performance
    if tempo_seq > 0 and tempo_par > 0:
        resultados["speedup"] = calculate_speedup(tempo_seq, tempo_par)
    
    # Resumo final
    print("\n" + "="*70)
    print("📋 RESUMO DOS TESTES")
    print("="*70)
    
    for nome, passou in resultados.items():
        if passou is None:
            emoji = "⚠️"
            status = "N/A"
        elif passou:
            emoji = "✅"
            status = "PASSOU"
        else:
            emoji = "❌"
            status = "FALHOU"
        
        print(f"   {emoji} {nome.upper()}: {status}")
    
    # Veredicto final
    testes_criticos = ["sequencial", "paralelo", "speedup"]
    passou_criticos = all(
        resultados.get(t) for t in testes_criticos
        if resultados.get(t) is not None
    )
    
    print("\n" + "="*70)
    
    if passou_criticos:
        print("🎉 TODOS OS TESTES CRÍTICOS PASSARAM!")
        print("✅ Correção funcionando corretamente")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("⚠️ Revise a implementação")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()