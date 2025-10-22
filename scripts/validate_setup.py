#!/usr/bin/env python3
"""
Script de validação completa do sistema.
Verifica instalação, configuração e conectividade.

Uso: python scripts/validate_setup.py
"""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_section(title):
    """Imprime seção formatada."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def check_python_version():
    """Verifica versão do Python."""
    print("🐍 Verificando Python...")
    version = sys.version_info
    
    if version.major == 3 and version.minor >= 9:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro}")
        print("   ⚠️  Requer Python 3.9+")
        return False


def check_packages():
    """Verifica pacotes instalados."""
    print("\n📦 Verificando pacotes...")
    
    packages = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "langgraph": "LangGraph",
        "langchain": "LangChain",
        "langchain_openai": "LangChain OpenAI",
        "langchain_anthropic": "LangChain Anthropic",
        "langchain_google_genai": "LangChain Google",
        "bs4": "BeautifulSoup4",
        "loguru": "Loguru",
        "yaml": "PyYAML",
        "pydantic": "Pydantic",
    }
    
    all_ok = True
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} (não instalado)")
            all_ok = False
    
    return all_ok


def check_directories():
    """Verifica estrutura de diretórios."""
    print("\n📁 Verificando diretórios...")
    
    required_dirs = [
        "backend",
        "backend/agents/guias",
        "backend/agents/mapas",
        "backend/api",
        "backend/core",
        "backend/services",
        "backend/utils",
        "frontend",
        "config",
        "output/guias",
        "output/mapas",
        "logs",
        "uploads",
    ]
    
    all_ok = True
    for directory in required_dirs:
        path = Path(directory)
        if path.exists():
            print(f"   ✅ {directory}")
        else:
            print(f"   ❌ {directory} (não existe)")
            all_ok = False
    
    return all_ok


def check_env_file():
    """Verifica arquivo .env."""
    print("\n🔑 Verificando .env...")
    
    env_path = Path(".env")
    if not env_path.exists():
        print("   ❌ Arquivo .env não encontrado")
        print("   💡 Execute: cp .env.example .env")
        return False
    
    print("   ✅ Arquivo .env existe")
    
    with open(env_path) as f:
        content = f.read()
    
    providers = {
        "OpenAI": "OPENAI_API_KEY",
        "Anthropic": "ANTHROPIC_API_KEY",
        "Google": "GOOGLE_API_KEY",
        "DeepSeek": "DEEPSEEK_API_KEY",
    }
    
    configured = []
    for name, key in providers.items():
        if key in content:
            key_value = content.split(f"{key}=")[1].split("\n")[0].strip()
            if len(key_value) > 10:
                print(f"   ✅ {name} configurado")
                configured.append(name)
            else:
                print(f"   ⚠️  {name} (sem API key)")
        else:
            print(f"   ⚠️  {name} (não encontrado)")
    
    if configured:
        print(f"\n   ℹ️  {len(configured)} provider(s) configurado(s)")
        return True
    else:
        print("\n   ❌ Nenhum provider configurado!")
        return False


def check_imports():
    """Testa imports do projeto."""
    print("\n🔍 Testando imports...")
    
    imports_to_test = [
        ("backend.core.config", "get_settings"),
        ("backend.agents.guias.state", "GuiaState"),
        ("backend.agents.mapas.state", "MindmapState"),
        ("backend.services.llm_factory", "get_llm"),
        ("backend.utils.logger", "setup_logger"),
    ]
    
    all_ok = True
    for module_name, item_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[item_name])
            getattr(module, item_name)
            print(f"   ✅ {module_name}.{item_name}")
        except ImportError as e:
            print(f"   ❌ {module_name} (erro: {e})")
            all_ok = False
        except AttributeError as e:
            print(f"   ❌ {module_name}.{item_name} (não existe)")
            all_ok = False
    
    return all_ok


def check_config_example():
    """Verifica arquivo de configuração exemplo."""
    print("\n📋 Verificando config exemplo...")
    
    example_path = Path("config/projetos/exemplo.yaml")
    if not example_path.exists():
        print("   ❌ exemplo.yaml não encontrado")
        return False
    
    print("   ✅ exemplo.yaml existe")
    
    try:
        import yaml
        with open(example_path) as f:
            config = yaml.safe_load(f)
        
        required_sections = ["projeto", "topicos", "modelos_guias", "modelos_mapas"]
        for section in required_sections:
            if section in config:
                print(f"   ✅ Seção '{section}' presente")
            else:
                print(f"   ❌ Seção '{section}' ausente")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao parsear YAML: {e}")
        return False


def test_llm_connectivity():
    """Testa conectividade com LLMs."""
    print("\n🤖 Testando conectividade com LLMs...")
    
    try:
        from backend.core.config import get_settings
        from backend.services.llm_factory import get_llm
        
        settings = get_settings()
        configured_providers = settings.list_configured_providers()
        
        if not configured_providers:
            print("   ⚠️  Nenhum provider configurado para testar")
            return True  # Não é erro crítico
        
        print(f"   ℹ️  Testando {len(configured_providers)} provider(s)...")
        
        for provider in configured_providers:
            try:
                llm = get_llm(provider, temperature=0.5, max_tokens=10)
                print(f"   ✅ {provider.capitalize()} - instância criada")
            except Exception as e:
                print(f"   ❌ {provider.capitalize()} - erro: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro no teste: {e}")
        return False


def print_summary(results):
    """Imprime resumo dos testes."""
    print_section("RESUMO")
    
    total = len(results)
    passed = sum(results.values())
    failed = total - passed
    
    print(f"   ✅ Passou: {passed}/{total}")
    print(f"   ❌ Falhou: {failed}/{total}")
    
    if passed == total:
        print("\n   🎉 SISTEMA PRONTO PARA USO!")
        print("\n   Execute: python run.py")
        return True
    else:
        print("\n   ⚠️  Alguns problemas encontrados.")
        print("   Revise as seções com erro acima.")
        return False


def main():
    """Executa validação completa."""
    
    print_section("VALIDAÇÃO DO SISTEMA UNIFICADO")
    print("Verificando instalação e configuração...\n")
    
    results = {
        "Python": check_python_version(),
        "Pacotes": check_packages(),
        "Diretórios": check_directories(),
        "Arquivo .env": check_env_file(),
        "Imports": check_imports(),
        "Config Exemplo": check_config_example(),
        "Conectividade LLM": test_llm_connectivity(),
    }
    
    success = print_summary(results)
    
    if not success:
        print("\n📖 Consulte o ROTEIRO_IMPLEMENTACAO.md para ajuda")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Validação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro durante validação: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)