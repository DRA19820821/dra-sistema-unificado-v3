#!/usr/bin/env python3
"""
Script de inicialização do Sistema Unificado.

Uso:
    python run.py              # Modo desenvolvimento
    python run.py --prod       # Modo produção
    python run.py --port 8080  # Porta customizada
"""

import sys
import argparse
import uvicorn
from pathlib import Path


def check_environment():
    """Verifica se o ambiente está configurado corretamente."""
    
    print("\n🔍 Verificando ambiente...\n")
    
    # 1. Verifica .env
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ ERRO: Arquivo .env não encontrado!")
        print("\n📝 Copie o arquivo .env.example para .env:")
        print("   cp .env.example .env")
        print("\nDepois edite o arquivo .env com suas API keys.")
        sys.exit(1)
    
    print("✅ Arquivo .env encontrado")
    
    # 2. Verifica se há pelo menos um provider configurado
    with open(env_file) as f:
        env_content = f.read()
    
    providers_found = []
    for provider in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "DEEPSEEK_API_KEY"]:
        if provider in env_content:
            # Verifica se tem valor (mais de 10 chars)
            key_value = env_content.split(f"{provider}=")[1].split("\n")[0].strip()
            if len(key_value) > 10:
                providers_found.append(provider.replace("_API_KEY", ""))
    
    if not providers_found:
        print("⚠️  AVISO: Nenhum provider de LLM configurado no .env")
        print("   Configure pelo menos um provider para usar o sistema")
    else:
        print(f"✅ Providers configurados: {', '.join(providers_found)}")
    
    # 3. Verifica diretórios
    from backend.services.file_manager import ensure_directories
    ensure_directories()
    print("✅ Diretórios criados")
    
    # 4. Testa imports básicos
    try:
        from backend.core.config import get_settings
        from backend.main import app
        print("✅ Imports do backend OK")
    except ImportError as e:
        print(f"❌ ERRO: Falha ao importar módulos: {e}")
        print("\n📦 Instale as dependências:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    print("\n" + "="*70)


def print_startup_banner(args):
    """Imprime banner de inicialização."""
    
    print("\n" + "="*70)
    print("  🚀 SISTEMA UNIFICADO - GUIAS E MAPAS MENTAIS")
    print("="*70)
    print(f"\n📍 Modo: {'PRODUÇÃO' if args.prod else 'DESENVOLVIMENTO'}")
    print(f"🌐 URL: http://{args.host}:{args.port}")
    print(f"📊 Logs: {'INFO' if args.prod else 'DEBUG'}")
    print(f"🔄 Hot reload: {'Desabilitado' if args.prod else 'Habilitado'}")
    print("\n" + "="*70)
    print("\n💡 ACESSO:")
    print(f"   Interface Web: http://localhost:{args.port}")
    print(f"   API Docs: http://localhost:{args.port}/docs")
    print("\n📚 FUNCIONALIDADES:")
    print("   ✅ Geração de Guias HTML")
    print("   ✅ Geração de Mapas Mentais .mmd")
    print("   ✅ Pipeline Completo (Guias → Mapas)")
    print("\n🛑 Para encerrar: Pressione Ctrl+C")
    print("="*70 + "\n")


def main():
    """Função principal."""
    
    parser = argparse.ArgumentParser(
        description="Sistema Unificado - Guias e Mapas Mentais",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python run.py                    # Desenvolvimento (hot reload)
  python run.py --prod             # Produção (sem reload)
  python run.py --port 3000        # Porta customizada
  python run.py --host 0.0.0.0     # Escuta em todas as interfaces
        """
    )
    
    parser.add_argument(
        "--prod",
        action="store_true",
        help="Modo produção (desabilita debug e hot reload)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Porta do servidor (padrão: 8000)"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host do servidor (padrão: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Número de workers (apenas para produção)"
    )
    
    parser.add_argument(
        "--skip-check",
        action="store_true",
        help="Pula verificação de ambiente"
    )
    
    args = parser.parse_args()
    
    # Verifica ambiente (a menos que --skip-check)
    if not args.skip_check:
        check_environment()
    
    # Configurações do servidor
    reload = not args.prod
    log_level = "info" if args.prod else "debug"
    
    # Banner
    print_startup_banner(args)
    
    # Configuração do Uvicorn
    uvicorn_config = {
        "app": "backend.main:app",
        "host": args.host,
        "port": args.port,
        "reload": reload,
        "log_level": log_level,
        "access_log": True,
    }
    
    # Workers apenas em produção
    if args.prod and args.workers > 1:
        uvicorn_config["workers"] = args.workers
        print(f"⚙️  Usando {args.workers} workers")
    
    # Inicia servidor
    try:
        uvicorn.run(**uvicorn_config)
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor encerrado pelo usuário")
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Operação cancelada")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        sys.exit(1)