#!/usr/bin/env python3
"""
Corrige os 2 últimos erros:
1. Import datetime faltando em revisor_node.py
2. Retorno incorreto em graph.py (guias)

Uso:
    python fix_final_errors.py
"""

import sys
from pathlib import Path

def fix_revisor_datetime():
    """Adiciona import datetime em revisor_node.py de guias"""
    print("1️⃣  Corrigindo revisor_node.py (guias)...")
    
    filepath = Path('backend/agents/guias/nodes/revisor_node.py')
    
    if not filepath.exists():
        print(f"   ⚠️  Arquivo não encontrado: {filepath}")
        return False
    
    content = filepath.read_text(encoding='utf-8')
    
    # Verifica se já tem datetime
    if 'from datetime import datetime' in content:
        print("   ℹ️  Já está correto (datetime importado)")
        return False
    
    # Backup
    backup = filepath.with_suffix('.py.bak')
    backup.write_text(content, encoding='utf-8')
    print(f"   💾 Backup: {backup.name}")
    
    # Adiciona import após as outras importações
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        # Adiciona após a última importação
        if line.startswith('from typing import List'):
            new_lines.append('from datetime import datetime')
    
    content = '\n'.join(new_lines)
    filepath.write_text(content, encoding='utf-8')
    
    print("   ✅ Import datetime adicionado")
    return True


def fix_graph_guias():
    """Corrige retorno de execute_graph_guias em graph.py"""
    print("\n2️⃣  Corrigindo graph.py (guias)...")
    
    filepath = Path('backend/agents/guias/graph.py')
    
    if not filepath.exists():
        print(f"   ⚠️  Arquivo não encontrado: {filepath}")
        return False
    
    content = filepath.read_text(encoding='utf-8')
    original = content
    
    # Verifica se já está correto
    if 'state["status_geral"] = "concluido"' in content and 'state["arquivos_gerados"] = arquivos_gerados' in content:
        print("   ℹ️  Já está correto")
        return False
    
    # Backup
    backup = filepath.with_suffix('.py.bak')
    backup.write_text(content, encoding='utf-8')
    print(f"   💾 Backup: {backup.name}")
    
    # Procura pela função execute_graph_guias e ajusta o retorno
    # A função deve retornar o state completo
    
    # Substitui o final da função
    old_ending = '''    state["status_geral"] = "concluido"
    state["arquivos_gerados"] = arquivos_gerados
    
    return state'''
    
    new_ending = '''    state["status_geral"] = "concluido"
    
    return {
        "status": "concluido",
        "arquivos_gerados": arquivos_gerados,
        "estatisticas": state["estatisticas"],
        "logs": state["logs"]
    }'''
    
    if old_ending in content:
        content = content.replace(old_ending, new_ending)
        filepath.write_text(content, encoding='utf-8')
        print("   ✅ Retorno corrigido")
        return True
    
    # Se não encontrou o padrão exato, tenta uma abordagem mais genérica
    print("   ⚠️  Padrão não encontrado, tentando abordagem genérica...")
    
    # Procura por "return state" no final da função
    lines = content.split('\n')
    new_lines = []
    in_function = False
    
    for i, line in enumerate(lines):
        if 'async def execute_graph_guias' in line:
            in_function = True
        
        if in_function and line.strip() == 'return state':
            # Substitui o return
            indent = len(line) - len(line.lstrip())
            new_lines.append(' ' * indent + 'return {')
            new_lines.append(' ' * (indent + 4) + '"status": "concluido",')
            new_lines.append(' ' * (indent + 4) + '"arquivos_gerados": arquivos_gerados,')
            new_lines.append(' ' * (indent + 4) + '"estatisticas": state["estatisticas"],')
            new_lines.append(' ' * (indent + 4) + '"logs": state["logs"]')
            new_lines.append(' ' * indent + '}')
            in_function = False
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        print("   ✅ Retorno corrigido (abordagem genérica)")
        return True
    
    print("   ❌ Não foi possível corrigir automaticamente")
    return False


def main():
    print("\n" + "="*70)
    print("  FIX FINAL ERRORS - Correções Finais")
    print("="*70 + "\n")
    
    fixed = []
    
    if fix_revisor_datetime():
        fixed.append('revisor_node.py')
    
    if fix_graph_guias():
        fixed.append('graph.py')
    
    print("\n" + "="*70)
    print("  RESUMO")
    print("="*70 + "\n")
    
    if fixed:
        print(f"✅ {len(fixed)} arquivo(s) corrigido(s):")
        for f in fixed:
            print(f"   • {f}")
        print("\n🎉 Correções aplicadas!")
        print("\n💡 Próximo passo:")
        print("   1. Pare o servidor (Ctrl+C)")
        print("   2. Execute novamente: python run.py")
        print("   3. Teste o sistema!")
    else:
        print("ℹ️  Todos os arquivos já estavam corretos")
        print("\n⚠️  CORREÇÃO MANUAL NECESSÁRIA")
        print("\nVeja instruções abaixo...")
    
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