#!/usr/bin/env python3
"""
Correção FINAL do retorno do graph.py (guias)

O problema: execute_graph_guias retorna state mas routes_pipeline 
espera um dict com "status" no nível raiz.

Uso:
    python fix_graph_return_final.py
"""

import sys
from pathlib import Path

def fix_graph_guias_return():
    """Corrige o retorno final de execute_graph_guias"""
    print("🔧 Corrigindo backend/agents/guias/graph.py...")
    
    filepath = Path('backend/agents/guias/graph.py')
    
    if not filepath.exists():
        print(f"   ❌ Arquivo não encontrado: {filepath}")
        return False
    
    content = filepath.read_text(encoding='utf-8')
    original = content
    
    # Backup
    backup = filepath.with_suffix('.py.bak_final')
    backup.write_text(content, encoding='utf-8')
    print(f"   💾 Backup: {backup.name}")
    
    # Procura pela função execute_graph_guias e ajusta o retorno final
    # O retorno deve ter "status" no nível raiz
    
    # Padrão atual que pode estar no código
    patterns_to_replace = [
        # Padrão 1: Sem "status"
        (
            '''    state["status_geral"] = "concluido"
    state["arquivos_gerados"] = arquivos_gerados
    
    return state''',
            '''    state["status_geral"] = "concluido"
    state["arquivos_gerados"] = arquivos_gerados
    
    return {
        "status": "concluido",
        "status_geral": "concluido",
        "arquivos_gerados": arquivos_gerados,
        "estatisticas": state.get("estatisticas", {}),
        "logs": state.get("logs", [])
    }'''
        ),
        # Padrão 2: Com status mas sem status_geral
        (
            '''    return {
        "status": "concluido",
        "arquivos_gerados": arquivos_gerados,
        "estatisticas": state["estatisticas"],
        "logs": state["logs"]
    }''',
            '''    return {
        "status": "concluido",
        "status_geral": "concluido",
        "arquivos_gerados": arquivos_gerados,
        "estatisticas": state.get("estatisticas", {}),
        "logs": state.get("logs", [])
    }'''
        ),
    ]
    
    replaced = False
    for old, new in patterns_to_replace:
        if old in content:
            content = content.replace(old, new)
            replaced = True
            break
    
    if not replaced:
        print("   ⚠️  Padrão específico não encontrado")
        print("   🔧 Aplicando correção genérica...")
        
        # Abordagem genérica: procura por "return state" no final da função
        lines = content.split('\n')
        new_lines = []
        in_execute_graph = False
        
        for i, line in enumerate(lines):
            if 'async def execute_graph_guias' in line:
                in_execute_graph = True
            
            # Se encontrou "return state" dentro da função execute_graph_guias
            if in_execute_graph and line.strip() == 'return state':
                indent = len(line) - len(line.lstrip())
                # Substitui por return dict
                new_lines.append(' ' * indent + 'return {')
                new_lines.append(' ' * (indent + 4) + '"status": "concluido",')
                new_lines.append(' ' * (indent + 4) + '"status_geral": "concluido",')
                new_lines.append(' ' * (indent + 4) + '"arquivos_gerados": arquivos_gerados,')
                new_lines.append(' ' * (indent + 4) + '"estatisticas": state.get("estatisticas", {}),')
                new_lines.append(' ' * (indent + 4) + '"logs": state.get("logs", [])')
                new_lines.append(' ' * indent + '}')
                in_execute_graph = False
            else:
                new_lines.append(line)
        
        content = '\n'.join(new_lines)
    
    if content != original:
        filepath.write_text(content, encoding='utf-8')
        print("   ✅ Retorno corrigido para incluir 'status' no nível raiz")
        return True
    else:
        print("   ℹ️  Nenhuma mudança necessária")
        return False


def verify_revisor_structured_output():
    """Verifica se revisor_node.py usa structured output corretamente"""
    print("\n🔍 Verificando backend/agents/guias/nodes/revisor_node.py...")
    
    filepath = Path('backend/agents/guias/nodes/revisor_node.py')
    
    if not filepath.exists():
        print(f"   ❌ Arquivo não encontrado: {filepath}")
        return False
    
    content = filepath.read_text(encoding='utf-8')
    
    # Verifica se usa structured output
    if 'with_structured_output' in content:
        print("   ✅ Já usa structured output do LangChain")
        
        # Verifica se tem os models Pydantic
        if 'class AvaliacaoGuia(BaseModel)' in content:
            print("   ✅ Model Pydantic definido")
        else:
            print("   ⚠️  Model Pydantic não encontrado")
            return False
        
        return True
    else:
        print("   ⚠️  NÃO usa structured output")
        print("   💡 Recomendado implementar structured output para robustez")
        return False


def show_manual_fix_instructions():
    """Mostra instruções de correção manual se necessário"""
    print("\n" + "="*70)
    print("  CORREÇÃO MANUAL (SE NECESSÁRIO)")
    print("="*70 + "\n")
    
    print("📝 Se o script não conseguiu corrigir automaticamente:")
    print()
    print("1. Abra: backend/agents/guias/graph.py")
    print()
    print("2. No final da função execute_graph_guias, troque:")
    print()
    print("   DE:")
    print("   ```python")
    print("   return state")
    print("   ```")
    print()
    print("   PARA:")
    print("   ```python")
    print("   return {")
    print('       "status": "concluido",')
    print('       "status_geral": "concluido",')
    print('       "arquivos_gerados": arquivos_gerados,')
    print('       "estatisticas": state.get("estatisticas", {}),')
    print('       "logs": state.get("logs", [])')
    print("   }")
    print("   ```")
    print()


def main():
    print("\n" + "="*70)
    print("  FIX GRAPH RETURN - Correção Final do Retorno")
    print("="*70 + "\n")
    
    fixed = []
    
    # Corrige graph.py
    if fix_graph_guias_return():
        fixed.append('graph.py')
    
    # Verifica revisor
    revisor_ok = verify_revisor_structured_output()
    
    print("\n" + "="*70)
    print("  RESUMO")
    print("="*70 + "\n")
    
    if fixed:
        print(f"✅ {len(fixed)} arquivo(s) corrigido(s):")
        for f in fixed:
            print(f"   • {f}")
    else:
        print("ℹ️  Nenhuma correção automática foi possível")
        show_manual_fix_instructions()
    
    if revisor_ok:
        print("\n✅ Revisor já usa structured output (ótimo!)")
    else:
        print("\n💡 Sugestão: Implementar structured output no revisor")
    
    print("\n" + "="*70)
    print("  PRÓXIMOS PASSOS")
    print("="*70 + "\n")
    print("1. Pare o servidor (Ctrl+C)")
    print("2. Execute: python run.py")
    print("3. Teste o pipeline completo")
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