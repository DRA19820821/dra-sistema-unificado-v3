#!/usr/bin/env python3
"""
Corrige referências a execute_graph (nome incorreto).
O nome correto é apenas execute_graph.

Uso:
    python fix_execute_graph_name.py
"""

import sys
from pathlib import Path
import re

def find_and_fix_imports(directory='.', extensions=['.py']):
    """Encontra e corrige imports incorretos de execute_graph"""
    
    print("\n🔍 Procurando referências a 'execute_graph'...\n")
    
    files_to_fix = []
    
    # Escaneia todos os arquivos Python
    for ext in extensions:
        for filepath in Path(directory).rglob(f'*{ext}'):
            # Ignora alguns diretórios
            if any(x in str(filepath) for x in ['.venv', 'venv', '__pycache__', '.git', 'backup_']):
                continue
            
            try:
                content = filepath.read_text(encoding='utf-8')
                
                # Procura por execute_graph
                if 'execute_graph' in content:
                    files_to_fix.append(filepath)
                    
                    # Mostra onde encontrou
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if 'execute_graph' in line:
                            print(f"📄 {filepath}")
                            print(f"   Linha {i}: {line.strip()}")
                            print()
            
            except Exception as e:
                # Ignora erros de leitura
                pass
    
    if not files_to_fix:
        print("✅ Nenhuma referência incorreta encontrada!\n")
        return []
    
    print(f"\n⚠️  Encontradas {len(files_to_fix)} arquivo(s) com problema\n")
    
    return files_to_fix


def fix_file(filepath):
    """Corrige um arquivo específico"""
    
    print(f"🔧 Corrigindo: {filepath}")
    
    # Lê conteúdo
    content = filepath.read_text(encoding='utf-8')
    original_content = content
    
    # Backup
    backup_path = filepath.with_suffix(filepath.suffix + '.bak')
    backup_path.write_text(content, encoding='utf-8')
    print(f"   💾 Backup: {backup_path}")
    
    # Correções
    # 1. Import statements
    content = re.sub(
        r'from\s+(.+?)\s+import\s+execute_graph',
        r'from \1 import execute_graph',
        content
    )
    
    # 2. Função sendo chamada
    content = re.sub(
        r'\bexecute_graph_mapas\b',
        r'execute_graph',
        content
    )
    
    # Salva se mudou
    if content != original_content:
        filepath.write_text(content, encoding='utf-8')
        
        # Conta quantas mudanças
        changes = len(re.findall(r'execute_graph', content)) - len(re.findall(r'execute_graph', original_content))
        print(f"   ✅ {changes} referência(s) corrigida(s)")
        return True
    else:
        print(f"   ⚠️  Nenhuma mudança feita")
        return False


def main():
    print("\n" + "="*70)
    print("  FIX EXECUTE_GRAPH - Correção de Nome de Função")
    print("="*70)
    
    # Encontra arquivos com problema
    files_to_fix = find_and_fix_imports()
    
    if not files_to_fix:
        print("✅ Sistema OK! Nenhuma correção necessária.")
        return
    
    print("="*70)
    print("  APLICANDO CORREÇÕES")
    print("="*70 + "\n")
    
    fixed_count = 0
    for filepath in files_to_fix:
        if fix_file(filepath):
            fixed_count += 1
        print()
    
    print("="*70)
    print("  RESUMO")
    print("="*70 + "\n")
    
    print(f"✅ {fixed_count} arquivo(s) corrigido(s)")
    print(f"📁 {len(files_to_fix)} arquivo(s) processado(s)")
    
    print("\n💡 Próximo passo: python run.py\n")


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