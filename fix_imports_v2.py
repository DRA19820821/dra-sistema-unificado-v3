#!/usr/bin/env python3
"""
Script para corrigir imports incorretos nos nodes de mapas.

Problema: from ...services (3 níveis) → backend.agents.services ❌
Correção: from ....services (4 níveis) → backend.services ✅

Uso: python fix_imports.py
"""

import sys
from pathlib import Path
import re

def fix_file_imports(filepath):
    """Corrige imports em um arquivo específico."""
    
    print(f"🔍 Verificando: {filepath}")
    
    if not filepath.exists():
        print(f"   ⚠️  Arquivo não encontrado")
        return False
    
    content = filepath.read_text(encoding='utf-8')
    original_content = content
    
    # Padrões a corrigir
    replacements = [
        # De 3 pontos para 4 pontos
        ('from ...services.llm_factory', 'from ....services.llm_factory'),
        ('from ...agents.prompts', 'from ..prompts'),
        ('from ...utils.logger', 'from ....utils.logger'),
        ('from ...core.config', 'from ....core.config'),
        
        # Alternativa: usar paths absolutos (mais seguro)
        # ('from ...services', 'from backend.services'),
        # ('from ...utils', 'from backend.utils'),
    ]
    
    changes = []
    
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            changes.append(f"{old} → {new}")
    
    if changes:
        # Salva arquivo corrigido
        filepath.write_text(content, encoding='utf-8')
        
        print(f"   ✅ Corrigido ({len(changes)} mudança(s)):")
        for change in changes:
            print(f"      • {change}")
        
        return True
    else:
        print(f"   ✓ Já está correto")
        return False


def main():
    """Função principal."""
    
    print("\n" + "="*70)
    print("  CORREÇÃO DE IMPORTS - Nodes de Mapas")
    print("="*70 + "\n")
    
    # Arquivos para corrigir
    files_to_fix = [
        "backend/agents/mapas/nodes/divisor_node.py",
        "backend/agents/mapas/nodes/gerador_node.py",
        "backend/agents/mapas/nodes/revisor_node.py",
        "backend/agents/mapas/nodes/salvar_node.py",
        "backend/agents/mapas/nodes/parser_node.py",
    ]
    
    fixed_count = 0
    
    for filepath_str in files_to_fix:
        filepath = Path(filepath_str)
        if fix_file_imports(filepath):
            fixed_count += 1
    
    print("\n" + "="*70)
    print(f"✅ Correção concluída: {fixed_count} arquivo(s) modificado(s)")
    print("="*70 + "\n")
    
    # Testa imports
    print("🧪 Testando imports...\n")
    
    try:
        # Tenta importar os módulos corrigidos
        from backend.agents.mapas.nodes import divisor_node
        print("   ✅ divisor_node importado")
        
        from backend.agents.mapas.nodes import gerador_node
        print("   ✅ gerador_node importado")
        
        from backend.agents.mapas.nodes import revisor_node
        print("   ✅ revisor_node importado")
        
        from backend.agents.mapas.nodes import salvar_node
        print("   ✅ salvar_node importado")
        
        print("\n✅ Todos os imports funcionando!\n")
        print("🚀 Próximo passo: python run.py")
        
        return 0
        
    except ImportError as e:
        print(f"\n❌ Erro nos imports: {e}\n")
        print("📝 Verifique manualmente os arquivos corrigidos")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)