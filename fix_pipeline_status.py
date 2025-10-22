#!/usr/bin/env python3
"""
Corrige o erro 'status' no routes_pipeline.py

O problema: execute_graph_guias retorna um dict, mas routes_pipeline
está tentando acessar resultado_guias["status"] quando deveria ser
resultado_guias["status_geral"] ou verificar se "status" existe.

Uso:
    python fix_pipeline_status.py
"""

import sys
from pathlib import Path

def fix_routes_pipeline():
    """Corrige verificação de status em routes_pipeline.py"""
    print("🔧 Corrigindo routes_pipeline.py...")
    
    filepath = Path('backend/api/routes_pipeline.py')
    
    if not filepath.exists():
        print(f"   ❌ Arquivo não encontrado: {filepath}")
        return False
    
    content = filepath.read_text(encoding='utf-8')
    original = content
    
    # Backup
    backup = filepath.with_suffix('.py.bak')
    backup.write_text(content, encoding='utf-8')
    print(f"   💾 Backup: {backup.name}")
    
    # Procura pelo erro: if resultado_guias["status"] != "concluido"
    # Deve trocar para verificar "status" ou usar get() com fallback
    
    # Opção 1: Trocar ["status"] por .get("status", "concluido")
    content = content.replace(
        'if resultado_guias["status"] != "concluido":',
        'if resultado_guias.get("status") != "concluido":'
    )
    
    # Opção 2: Também ajustar outras referências a status
    content = content.replace(
        'resultado_guias.get("erro_msg")',
        'resultado_guias.get("erro_msg", "Erro desconhecido")'
    )
    
    # Salva
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        print("   ✅ Verificação de status corrigida")
        return True
    else:
        print("   ℹ️  Nenhuma mudança necessária")
        return False


def fix_graph_guias_return():
    """Garante que execute_graph_guias retorna dict com 'status'"""
    print("\n🔧 Verificando graph.py (guias)...")
    
    filepath = Path('backend/agents/guias/graph.py')
    
    if not filepath.exists():
        print(f"   ❌ Arquivo não encontrado: {filepath}")
        return False
    
    content = filepath.read_text(encoding='utf-8')
    original = content
    
    # Verifica se já tem "status" no retorno
    if '"status": "concluido"' in content:
        print("   ℹ️  Já retorna 'status' corretamente")
        return False
    
    # Backup
    backup = filepath.with_suffix('.py.bak2')
    backup.write_text(content, encoding='utf-8')
    print(f"   💾 Backup: {backup.name}")
    
    # Procura pelo return no final da função execute_graph_guias
    # e garante que tem "status"
    
    old_return = '''    return {
        "arquivos_gerados": arquivos_gerados,
        "estatisticas": state["estatisticas"],
        "logs": state["logs"]
    }'''
    
    new_return = '''    return {
        "status": "concluido",
        "status_geral": "concluido",
        "arquivos_gerados": arquivos_gerados,
        "estatisticas": state["estatisticas"],
        "logs": state["logs"]
    }'''
    
    if old_return in content:
        content = content.replace(old_return, new_return)
        filepath.write_text(content, encoding='utf-8')
        print("   ✅ Retorno ajustado para incluir 'status'")
        return True
    
    print("   ⚠️  Padrão não encontrado, pode já estar correto")
    return False


def main():
    print("\n" + "="*70)
    print("  FIX PIPELINE STATUS - Correção Final")
    print("="*70 + "\n")
    
    fixed = []
    
    if fix_graph_guias_return():
        fixed.append('graph.py (guias)')
    
    if fix_routes_pipeline():
        fixed.append('routes_pipeline.py')
    
    print("\n" + "="*70)
    print("  RESUMO")
    print("="*70 + "\n")
    
    if fixed:
        print(f"✅ {len(fixed)} arquivo(s) corrigido(s):")
        for f in fixed:
            print(f"   • {f}")
        print("\n🎉 Correção final aplicada!")
        print("\n💡 Próximo passo:")
        print("   1. Pare o servidor (Ctrl+C)")
        print("   2. Execute: python run.py")
        print("   3. Teste novamente!")
    else:
        print("ℹ️  Arquivos já estão corretos")
        print("\n📝 CORREÇÃO MANUAL:")
        print("\nAbra: backend/api/routes_pipeline.py")
        print("Linha ~88:")
        print('   Troque: if resultado_guias["status"] != "concluido":')
        print('   Por:    if resultado_guias.get("status") != "concluido":')
    
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operação cancelada")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)