#!/usr/bin/env python3
"""
Script de correção automática de imports do projeto.

Uso:
    python fix_imports.py              # Modo interativo (preview + confirmação)
    python fix_imports.py --auto       # Corrige automaticamente
    python fix_imports.py --dry-run    # Apenas mostra o que seria corrigido
    python fix_imports.py --backup     # Cria backup antes de corrigir

Funcionalidades:
    - Detecta e corrige imports relativos incorretos
    - Faz backup automático dos arquivos modificados
    - Mostra diff colorido das mudanças
    - Pode ser revertido facilmente
    - Gera relatório detalhado

Autor: Sistema Unificado
Versão: 1.0.0
"""

import sys
import re
import shutil
from pathlib import Path
from datetime import datetime
import argparse
from typing import List, Tuple, Dict
import difflib

# === CONFIGURAÇÕES ===

# Padrões de imports incorretos e suas correções
IMPORT_PATTERNS = [
    # Padrão 1: ...services.* → backend.services.*
    {
        'pattern': r'from \.\.\.services\.(\w+)',
        'replacement': r'from backend.services.\1',
        'description': '...services → backend.services'
    },
    # Padrão 2: ...utils.* → backend.utils.*
    {
        'pattern': r'from \.\.\.utils\.(\w+)',
        'replacement': r'from backend.utils.\1',
        'description': '...utils → backend.utils'
    },
    # Padrão 3: ...core.* → backend.core.*
    {
        'pattern': r'from \.\.\.core\.(\w+)',
        'replacement': r'from backend.core.\1',
        'description': '...core → backend.core'
    },
    # Padrão 4: ...agents.prompts.* → ..prompts.* (nos nodes)
    {
        'pattern': r'from \.\.\.agents\.prompts\.(\w+)',
        'replacement': r'from ..prompts.\1',
        'description': '...agents.prompts → ..prompts'
    },
    # Padrão 5: ...agents.services.* → backend.services.* (incorreto)
    {
        'pattern': r'from \.\.\.agents\.services\.(\w+)',
        'replacement': r'from backend.services.\1',
        'description': '...agents.services → backend.services'
    },
    # Padrão 6: ..utils.* → backend.utils.* (em mapas/nodes)
    {
        'pattern': r'from \.\.utils\.(\w+) import',
        'replacement': r'from backend.utils.\1 import',
        'description': '..utils → backend.utils',
        'context': 'backend/agents/mapas'
    },
    # Padrão 7: ..core.* → backend.core.* (em mapas/nodes)
    {
        'pattern': r'from \.\.core\.(\w+) import',
        'replacement': r'from backend.core.\1 import',
        'description': '..core → backend.core',
        'context': 'backend/agents/mapas'
    },
]

# Arquivos a serem ignorados
IGNORE_FILES = {
    '__init__.py',
    'fix_imports.py',
    'validate_setup.py',
    'run.py',
    'setup_structure.py',
}

# Diretórios a serem escaneados
SCAN_DIRS = [
    'backend/agents',
    'backend/api',
    'backend/services',
    'backend/core',
    'backend/utils',
]


# === CORES (compatível com Windows) ===

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    # Fallback sem cores
    class Fore:
        RED = GREEN = YELLOW = BLUE = CYAN = MAGENTA = WHITE = RESET = ''
    class Back:
        RED = GREEN = YELLOW = BLUE = CYAN = MAGENTA = WHITE = RESET = ''
    class Style:
        BRIGHT = DIM = RESET_ALL = ''


# === FUNÇÕES AUXILIARES ===

def print_header(text: str):
    """Imprime cabeçalho formatado."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_success(text: str):
    """Imprime mensagem de sucesso."""
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")


def print_error(text: str):
    """Imprime mensagem de erro."""
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")


def print_warning(text: str):
    """Imprime mensagem de aviso."""
    print(f"{Fore.YELLOW}⚠️  {text}{Style.RESET_ALL}")


def print_info(text: str):
    """Imprime mensagem de informação."""
    print(f"{Fore.CYAN}ℹ️  {text}{Style.RESET_ALL}")


def should_skip_file(filepath: Path) -> bool:
    """Verifica se arquivo deve ser ignorado."""
    return filepath.name in IGNORE_FILES or filepath.suffix != '.py'


def detect_import_issues(content: str, filepath: Path) -> List[Dict]:
    """
    Detecta problemas de imports no conteúdo.
    
    Returns:
        Lista de dicts com {line_num, original, fixed, pattern_desc}
    """
    issues = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        for pattern_def in IMPORT_PATTERNS:
            # Verifica contexto se especificado
            if 'context' in pattern_def:
                if pattern_def['context'] not in str(filepath):
                    continue
            
            pattern = pattern_def['pattern']
            replacement = pattern_def['replacement']
            
            if re.search(pattern, line):
                fixed_line = re.sub(pattern, replacement, line)
                if fixed_line != line:
                    issues.append({
                        'line_num': i,
                        'original': line,
                        'fixed': fixed_line,
                        'description': pattern_def['description']
                    })
    
    return issues


def fix_imports(content: str, filepath: Path) -> Tuple[str, int]:
    """
    Corrige imports no conteúdo.
    
    Returns:
        (conteúdo_corrigido, número_de_correções)
    """
    fixed_content = content
    num_fixes = 0
    
    for pattern_def in IMPORT_PATTERNS:
        # Verifica contexto se especificado
        if 'context' in pattern_def:
            if pattern_def['context'] not in str(filepath):
                continue
        
        pattern = pattern_def['pattern']
        replacement = pattern_def['replacement']
        
        fixed_content, count = re.subn(pattern, replacement, fixed_content)
        num_fixes += count
    
    return fixed_content, num_fixes


def create_backup(filepath: Path, backup_dir: Path) -> Path:
    """Cria backup do arquivo."""
    # Preserva estrutura de diretórios no backup
    relative_path = filepath.relative_to(Path.cwd())
    backup_path = backup_dir / relative_path
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    
    shutil.copy2(filepath, backup_path)
    return backup_path


def show_diff(original: str, fixed: str, filepath: Path):
    """Mostra diff colorido entre original e corrigido."""
    print(f"\n{Fore.CYAN}📄 {filepath}{Style.RESET_ALL}")
    print("-" * 70)
    
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        fixed.splitlines(keepends=True),
        fromfile='original',
        tofile='fixed',
        lineterm=''
    )
    
    for line in diff:
        if line.startswith('+') and not line.startswith('+++'):
            print(f"{Fore.GREEN}{line}{Style.RESET_ALL}", end='')
        elif line.startswith('-') and not line.startswith('---'):
            print(f"{Fore.RED}{line}{Style.RESET_ALL}", end='')
        elif line.startswith('@@'):
            print(f"{Fore.CYAN}{line}{Style.RESET_ALL}", end='')
        else:
            print(line, end='')
    
    print()


def scan_files(base_dir: Path = Path.cwd()) -> List[Path]:
    """Escaneia arquivos Python para correção."""
    files = []
    
    for scan_dir in SCAN_DIRS:
        dir_path = base_dir / scan_dir
        if not dir_path.exists():
            continue
        
        for py_file in dir_path.rglob('*.py'):
            if not should_skip_file(py_file):
                files.append(py_file)
    
    return sorted(files)


def analyze_project() -> Dict:
    """Analisa projeto e retorna estatísticas."""
    print_info("Escaneando projeto...")
    
    files = scan_files()
    total_issues = 0
    files_with_issues = []
    
    for filepath in files:
        try:
            content = filepath.read_text(encoding='utf-8')
            issues = detect_import_issues(content, filepath)
            
            if issues:
                total_issues += len(issues)
                files_with_issues.append({
                    'path': filepath,
                    'issues': issues
                })
        except Exception as e:
            print_warning(f"Erro ao ler {filepath}: {e}")
    
    return {
        'total_files': len(files),
        'files_with_issues': files_with_issues,
        'total_issues': total_issues
    }


def preview_fixes(analysis: Dict):
    """Mostra preview das correções."""
    print_header("PREVIEW DAS CORREÇÕES")
    
    if analysis['total_issues'] == 0:
        print_success("Nenhum problema de import encontrado! ✨")
        return
    
    print_info(f"Encontrados {analysis['total_issues']} problema(s) em {len(analysis['files_with_issues'])} arquivo(s)\n")
    
    for file_info in analysis['files_with_issues']:
        filepath = file_info['path']
        issues = file_info['issues']
        
        print(f"\n{Fore.YELLOW}📄 {filepath.relative_to(Path.cwd())}{Style.RESET_ALL}")
        print(f"   {len(issues)} correção(ões):\n")
        
        for issue in issues:
            print(f"   {Fore.CYAN}Linha {issue['line_num']}{Style.RESET_ALL} - {issue['description']}")
            print(f"   {Fore.RED}  - {issue['original'].strip()}{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}  + {issue['fixed'].strip()}{Style.RESET_ALL}\n")


def apply_fixes(analysis: Dict, create_backups: bool = True, show_diffs: bool = False) -> Dict:
    """Aplica correções nos arquivos."""
    print_header("APLICANDO CORREÇÕES")
    
    if analysis['total_issues'] == 0:
        print_success("Nada a corrigir!")
        return {'fixed': 0, 'errors': 0}
    
    # Cria diretório de backup
    backup_dir = None
    if create_backups:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = Path(f'backup_imports_{timestamp}')
        backup_dir.mkdir(exist_ok=True)
        print_info(f"Backups serão salvos em: {backup_dir}")
    
    fixed_count = 0
    error_count = 0
    
    for file_info in analysis['files_with_issues']:
        filepath = file_info['path']
        
        try:
            # Lê conteúdo original
            original_content = filepath.read_text(encoding='utf-8')
            
            # Aplica correções
            fixed_content, num_fixes = fix_imports(original_content, filepath)
            
            if num_fixes > 0:
                # Cria backup
                if create_backups:
                    backup_path = create_backup(filepath, backup_dir)
                    print_info(f"Backup: {backup_path}")
                
                # Mostra diff se solicitado
                if show_diffs:
                    show_diff(original_content, fixed_content, filepath)
                
                # Escreve arquivo corrigido
                filepath.write_text(fixed_content, encoding='utf-8')
                
                print_success(f"Corrigido: {filepath.relative_to(Path.cwd())} ({num_fixes} correção(ões))")
                fixed_count += num_fixes
        
        except Exception as e:
            print_error(f"Erro ao processar {filepath}: {e}")
            error_count += 1
    
    return {
        'fixed': fixed_count,
        'errors': error_count,
        'backup_dir': backup_dir
    }


def restore_from_backup(backup_dir: Path):
    """Restaura arquivos do backup."""
    print_header("RESTAURANDO BACKUP")
    
    if not backup_dir.exists():
        print_error(f"Diretório de backup não encontrado: {backup_dir}")
        return
    
    restored = 0
    for backup_file in backup_dir.rglob('*.py'):
        relative_path = backup_file.relative_to(backup_dir)
        original_path = Path.cwd() / relative_path
        
        try:
            shutil.copy2(backup_file, original_path)
            print_success(f"Restaurado: {relative_path}")
            restored += 1
        except Exception as e:
            print_error(f"Erro ao restaurar {relative_path}: {e}")
    
    print_info(f"\n{restored} arquivo(s) restaurado(s)")


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='Corrige automaticamente imports incorretos no projeto',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python fix_imports.py                # Modo interativo (preview + confirmação)
  python fix_imports.py --auto         # Corrige automaticamente
  python fix_imports.py --dry-run      # Apenas mostra o que seria corrigido
  python fix_imports.py --no-backup    # Não cria backup (não recomendado)
  python fix_imports.py --restore BACKUP_DIR  # Restaura do backup

Padrões corrigidos:
  ...services.* → backend.services.*
  ...utils.* → backend.utils.*
  ...agents.prompts.* → ..prompts.*
  E mais...
        """
    )
    
    parser.add_argument(
        '--auto',
        action='store_true',
        help='Corrige automaticamente sem confirmação'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Apenas mostra o que seria corrigido (não modifica arquivos)'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Não cria backup (não recomendado)'
    )
    
    parser.add_argument(
        '--show-diff',
        action='store_true',
        help='Mostra diff detalhado das mudanças'
    )
    
    parser.add_argument(
        '--restore',
        metavar='BACKUP_DIR',
        help='Restaura arquivos do diretório de backup'
    )
    
    args = parser.parse_args()
    
    # Modo restauração
    if args.restore:
        restore_from_backup(Path(args.restore))
        return
    
    # Header
    print_header("FIX IMPORTS - CORREÇÃO AUTOMÁTICA")
    print_info("Script de correção de imports do Sistema Unificado\n")
    
    # Analisa projeto
    analysis = analyze_project()
    
    # Preview
    preview_fixes(analysis)
    
    if analysis['total_issues'] == 0:
        return
    
    # Modo dry-run
    if args.dry_run:
        print_info("\nModo DRY-RUN: Nenhum arquivo foi modificado")
        print_info("Execute sem --dry-run para aplicar as correções")
        return
    
    # Confirmação (se não for modo --auto)
    if not args.auto:
        print("\n" + "="*70)
        response = input(f"\n{Fore.YELLOW}Deseja aplicar as correções? (s/N): {Style.RESET_ALL}").lower()
        if response not in ['s', 'sim', 'y', 'yes']:
            print_warning("Operação cancelada pelo usuário")
            return
    
    # Aplica correções
    result = apply_fixes(
        analysis,
        create_backups=not args.no_backup,
        show_diffs=args.show_diff
    )
    
    # Resumo
    print_header("RESUMO")
    print_success(f"✅ {result['fixed']} correção(ões) aplicada(s)")
    
    if result['errors'] > 0:
        print_error(f"❌ {result['errors']} erro(s)")
    
    if result.get('backup_dir'):
        print_info(f"\n💾 Backup salvo em: {result['backup_dir']}")
        print_info(f"   Para restaurar: python fix_imports.py --restore {result['backup_dir']}")
    
    print_success("\n🎉 Correções concluídas com sucesso!")
    print_info("Execute 'python run.py' para testar o sistema")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠️  Operação cancelada pelo usuário{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Fore.RED}❌ Erro fatal: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)