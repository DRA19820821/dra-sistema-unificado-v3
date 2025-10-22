#!/usr/bin/env python3
"""
Patch para corrigir imports restantes que o fix_imports.py não pegou.

Uso:
    python patch_remaining_imports.py
"""

import sys
from pathlib import Path

def fix_graph_parallel():
    """Corrige imports em graph_parallel.py"""
    filepath = Path('backend/agents/mapas/graph_parallel.py')
    
    if not filepath.exists():
        print(f"⚠️  Arquivo não encontrado: {filepath}")
        return False
    
    content = filepath.read_text(encoding='utf-8')
    original_content = content
    
    # Correções necessárias
    replacements = [
        ('from ..services.llm_factory import get_llm', 
         'from backend.services.llm_factory import get_llm'),
        ('from ..agents.prompts.gerador_prompts import SYSTEM_PROMPT as GERADOR_SYSTEM',
         'from .prompts.gerador_prompts import SYSTEM_PROMPT as GERADOR_SYSTEM'),
        ('from ..agents.prompts.gerador_prompts import USER_PROMPT_TEMPLATE as GERADOR_TEMPLATE',
         'from .prompts.gerador_prompts import USER_PROMPT_TEMPLATE as GERADOR_TEMPLATE'),
        ('from ..agents.prompts.revisor_prompts import SYSTEM_PROMPT as REVISOR_SYSTEM',
         'from .prompts.revisor_prompts import SYSTEM_PROMPT as REVISOR_SYSTEM'),
        ('from ..agents.prompts.revisor_prompts import USER_PROMPT_TEMPLATE as REVISOR_TEMPLATE',
         'from .prompts.revisor_prompts import USER_PROMPT_TEMPLATE as REVISOR_TEMPLATE'),
        ('from ..utils.logger import logger',
         'from backend.utils.logger import logger'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    if content != original_content:
        # Backup
        backup_path = filepath.with_suffix('.py.bak')
        backup_path.write_text(original_content, encoding='utf-8')
        
        # Salva corrigido
        filepath.write_text(content, encoding='utf-8')
        
        print(f"✅ Corrigido: {filepath}")
        print(f"💾 Backup: {backup_path}")
        return True
    else:
        print(f"ℹ️  Nenhuma correção necessária em {filepath}")
        return False


def fix_graph_mapas():
    """Corrige imports em graph.py de mapas"""
    filepath = Path('backend/agents/mapas/graph.py')
    
    if not filepath.exists():
        print(f"⚠️  Arquivo não encontrado: {filepath}")
        return False
    
    content = filepath.read_text(encoding='utf-8')
    original_content = content
    
    # Correções necessárias
    replacements = [
        ('from ..utils.logger import logger',
         'from backend.utils.logger import logger'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    if content != original_content:
        # Backup
        backup_path = filepath.with_suffix('.py.bak')
        backup_path.write_text(original_content, encoding='utf-8')
        
        # Salva corrigido
        filepath.write_text(content, encoding='utf-8')
        
        print(f"✅ Corrigido: {filepath}")
        print(f"💾 Backup: {backup_path}")
        return True
    else:
        print(f"ℹ️  Nenhuma correção necessária em {filepath}")
        return False


def fix_routes_pipeline():
    """Corrige imports em routes_pipeline.py"""
    filepath = Path('backend/api/routes_pipeline.py')
    
    if not filepath.exists():
        print(f"⚠️  Arquivo não encontrado: {filepath}")
        return False
    
    content = filepath.read_text(encoding='utf-8')
    original_content = content
    
    # Verifica se já está correto
    if 'from backend.core.config import get_settings' in content:
        print(f"ℹ️  {filepath} já está correto")
        return False
    
    # Correções necessárias
    replacements = [
        ('from ..core.config import get_settings',
         'from backend.core.config import get_settings'),
        ('from ..services.config_parser import parse_yaml_config',
         'from backend.services.config_parser import parse_yaml_config'),
        ('from ..agents.guias.graph import execute_graph_guias',
         'from backend.agents.guias.graph import execute_graph_guias'),
        ('from ..agents.mapas.graph import execute_graph',
         'from backend.agents.mapas.graph import execute_graph'),
        ('from ..api.websocket import manager',
         'from backend.api.websocket import manager'),
        ('from ..utils.logger import logger',
         'from backend.utils.logger import logger'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    if content != original_content:
        # Backup
        backup_path = filepath.with_suffix('.py.bak')
        backup_path.write_text(original_content, encoding='utf-8')
        
        # Salva corrigido
        filepath.write_text(content, encoding='utf-8')
        
        print(f"✅ Corrigido: {filepath}")
        print(f"💾 Backup: {backup_path}")
        return True
    else:
        print(f"ℹ️  Nenhuma correção necessária em {filepath}")
        return False


def main():
    print("\n" + "="*70)
    print("  PATCH - CORREÇÕES ADICIONAIS DE IMPORTS")
    print("="*70 + "\n")
    
    fixed = []
    
    print("🔧 Corrigindo arquivos adicionais...\n")
    
    if fix_graph_parallel():
        fixed.append('graph_parallel.py')
    
    if fix_graph_mapas():
        fixed.append('graph.py')
    
    if fix_routes_pipeline():
        fixed.append('routes_pipeline.py')
    
    print("\n" + "="*70)
    print("  RESUMO")
    print("="*70 + "\n")
    
    if fixed:
        print(f"✅ {len(fixed)} arquivo(s) corrigido(s):")
        for f in fixed:
            print(f"   - {f}")
        print("\n🎉 Patch aplicado com sucesso!")
    else:
        print("ℹ️  Todos os arquivos já estavam corretos!")
    
    print("\n💡 Próximo passo: python run.py\n")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)