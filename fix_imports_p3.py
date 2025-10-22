#!/usr/bin/env python3
"""
Patch para adicionar função save_mmd_file em file_manager.py

Uso:
    python patch_file_manager.py
"""

import sys
from pathlib import Path

def patch_file_manager():
    """Adiciona função save_mmd_file ao file_manager.py"""
    
    filepath = Path('backend/services/file_manager.py')
    
    if not filepath.exists():
        print(f"❌ Arquivo não encontrado: {filepath}")
        return False
    
    # Lê conteúdo atual
    content = filepath.read_text(encoding='utf-8')
    
    # Verifica se já tem a função
    if 'def save_mmd_file' in content:
        print(f"ℹ️  Função save_mmd_file já existe em {filepath}")
        return False
    
    # Conteúdo completo correto
    correct_content = '''from pathlib import Path
from backend.core.config import get_settings
import json

settings = get_settings()

def ensure_directories():
    """Garante que diretórios existem."""
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.output_guias_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.output_mapas_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.logs_dir).mkdir(parents=True, exist_ok=True)

def salvar_guia_html(filename: str, content: str) -> str:
    """Salva guia HTML."""
    filepath = Path(settings.output_guias_dir) / filename
    filepath.write_text(content, encoding='utf-8')
    return str(filepath)

def save_mmd_file(filename: str, content: str, metadata: dict = None) -> str:
    """Salva mapa mental .mmd."""
    filepath = Path(settings.output_mapas_dir) / filename
    filepath.write_text(content, encoding='utf-8')
    
    # Salva metadata em arquivo .json separado (opcional)
    if metadata:
        meta_filepath = filepath.with_suffix('.json')
        meta_filepath.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False), 
            encoding='utf-8'
        )
    
    return str(filepath)

def listar_guias_html() -> list[str]:
    """Lista guias HTML gerados."""
    path = Path(settings.output_guias_dir)
    return [f.name for f in path.glob("*.html")]
'''
    
    # Backup
    backup_path = filepath.with_suffix('.py.bak')
    backup_path.write_text(content, encoding='utf-8')
    
    # Salva corrigido
    filepath.write_text(correct_content, encoding='utf-8')
    
    print(f"✅ Função save_mmd_file adicionada ao {filepath}")
    print(f"💾 Backup: {backup_path}")
    return True


def main():
    print("\n" + "="*70)
    print("  PATCH - FILE MANAGER")
    print("="*70 + "\n")
    
    print("🔧 Adicionando função save_mmd_file...\n")
    
    if patch_file_manager():
        print("\n" + "="*70)
        print("  SUCESSO")
        print("="*70 + "\n")
        print("✅ Função adicionada com sucesso!")
        print("\n💡 Próximo passo: python run.py\n")
    else:
        print("\n⚠️  Nenhuma modificação necessária")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)