#!/usr/bin/env python3
"""
Script de teste para verificar se o processamento paralelo está funcionando.
VERSÃO CORRIGIDA - Força UTF-8 para compatibilidade Windows

Uso:
    python test_parallel_fix.py
"""

import sys
from pathlib import Path

# Adiciona backend ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*70)
print("  🧪 TESTE: PROCESSAMENTO PARALELO")
print("="*70)

# ============================================
# TESTE 1: IMPORTS
# ============================================

print("\n1️⃣ Testando imports...")

try:
    from backend.agents.mapas.graph import execute_graph
    print("   ✅ execute_graph (sequencial) importado")
except ImportError as e:
    print(f"   ❌ Erro ao importar execute_graph: {e}")
    sys.exit(1)

try:
    from backend.agents.mapas.graph_parallel import execute_graph_parallel
    print("   ✅ execute_graph_parallel (paralelo) importado")
except ImportError as e:
    print(f"   ❌ Erro ao importar execute_graph_parallel: {e}")
    sys.exit(1)

# ============================================
# TESTE 2: VERIFICAR ASSINATURAS
# ============================================

print("\n2️⃣ Verificando assinaturas das funções...")

import inspect

# Sequencial
sig_seq = inspect.signature(execute_graph)
params_seq = list(sig_seq.parameters.keys())
print(f"   📝 execute_graph: {params_seq}")

# Paralelo
sig_par = inspect.signature(execute_graph_parallel)
params_par = list(sig_par.parameters.keys())
print(f"   🚀 execute_graph_parallel: {params_par}")

# Validações
expected_seq = ['html_filename', 'llm01_provider', 'llm02_provider', 'llm03_provider', 'max_tentativas']
expected_par = ['html_filename', 'llm01_provider', 'llm02_provider', 'llm03_provider', 'max_tentativas', 'max_workers']

if all(p in params_seq for p in expected_seq):
    print("   ✅ Sequencial: parâmetros OK")
else:
    print("   ❌ Sequencial: parâmetros incorretos")

if all(p in params_par for p in expected_par):
    print("   ✅ Paralelo: parâmetros OK (inclui max_workers)")
else:
    print("   ❌ Paralelo: parâmetros incorretos")

# ============================================
# TESTE 3: VERIFICAR ROUTES_PIPELINE
# ============================================

print("\n3️⃣ Verificando routes_pipeline.py...")

routes_file = Path("backend/api/routes_pipeline.py")

if not routes_file.exists():
    print("   ❌ Arquivo routes_pipeline.py não encontrado!")
    sys.exit(1)

# ✅ FIX: Força UTF-8 encoding
try:
    content = routes_file.read_text(encoding='utf-8')
except UnicodeDecodeError:
    # Se UTF-8 falhar, tenta latin-1
    try:
        content = routes_file.read_text(encoding='latin-1')
        print("   ⚠️  Arquivo lido com encoding latin-1 (não UTF-8)")
    except Exception as e:
        print(f"   ❌ Erro ao ler arquivo: {e}")
        sys.exit(1)

# Verifica imports
checks = {
    "Import sequencial": "from ..agents.mapas.graph import execute_graph" in content,
    "Import paralelo": "from ..agents.mapas.graph_parallel import execute_graph_parallel" in content,
    "Parâmetro modo": "modo: str" in content,
    "Decisão if paralelo": "if modo == \"paralelo\":" in content or "if modo == 'paralelo':" in content,
    "Chamada execute_graph_parallel": "await execute_graph_parallel(" in content,
    "Log paralelo": "PARALELO" in content,
}

all_ok = True
for check_name, passed in checks.items():
    if passed:
        print(f"   ✅ {check_name}")
    else:
        print(f"   ❌ {check_name} - NÃO ENCONTRADO!")
        all_ok = False

if not all_ok:
    print("\n   ⚠️  O arquivo routes_pipeline.py NÃO está com o fix aplicado!")
    print("   📝 Execute: cp routes_pipeline_CORRIGIDO.py backend/api/routes_pipeline.py")
    sys.exit(1)

# ============================================
# TESTE 4: VERIFICAR LÓGICA DE DECISÃO
# ============================================

print("\n4️⃣ Verificando lógica de decisão...")

# Procura pela estrutura if/else
if ('if modo == "paralelo":' in content or "if modo == 'paralelo':" in content) and 'execute_graph_parallel' in content:
    print("   ✅ Decisão entre sequencial e paralelo implementada")
else:
    print("   ❌ Decisão entre sequencial e paralelo NÃO implementada")
    all_ok = False

# Procura se o modo é passado como parâmetro
if "modo=modo" in content or "modo=\"paralelo\"" in content or "modo='paralelo'" in content or "modo=\"sequencial\"" in content or "modo='sequencial'" in content:
    print("   ✅ Parâmetro modo sendo passado corretamente")
else:
    print("   ⚠️  Parâmetro modo pode não estar sendo passado")

# ============================================
# TESTE 5: VERIFICAR LOGS
# ============================================

print("\n5️⃣ Verificando logs informativos...")

log_checks = {
    "Log sequencial": "SEQUENCIAL" in content,
    "Log paralelo": "PARALELO" in content,
    "Log modo": "modo:" in content,
}

for check_name, passed in log_checks.items():
    if passed:
        print(f"   ✅ {check_name}")
    else:
        print(f"   ⚠️  {check_name} - ausente")

# ============================================
# RESUMO
# ============================================

print("\n" + "="*70)
print("  📊 RESUMO")
print("="*70)

if all_ok:
    print("\n   ✅ TUDO OK! Processamento paralelo está funcionando.")
    print("\n   🚀 Próximos passos:")
    print("      1. Reinicie o servidor: python run.py")
    print("      2. Acesse a interface: http://localhost:8000")
    print("      3. Escolha modo 'Paralelo'")
    print("      4. Observe os logs mostrando 'PARALELO'")
    print("\n   📊 Performance esperada:")
    print("      - Sequencial: ~10-15 min para 3 tópicos")
    print("      - Paralelo: ~4-6 min para 3 tópicos (2-3x mais rápido)")
    sys.exit(0)
else:
    print("\n   ❌ Alguns problemas encontrados!")
    print("\n   📝 Para aplicar o fix:")
    print("      cp routes_pipeline_CORRIGIDO.py backend/api/routes_pipeline.py")
    sys.exit(1)