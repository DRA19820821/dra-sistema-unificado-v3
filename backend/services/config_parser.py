import yaml
from pathlib import Path
from typing import Dict, Any

def parse_yaml_config(content: bytes) -> Dict[str, Any]:
    """Parse configuração YAML."""
    config_dict = yaml.safe_load(content)
    
    # Validações básicas
    required_keys = ["projeto", "topicos", "modelos_guias"]
    for key in required_keys:
        if key not in config_dict:
            raise ValueError(f"Chave obrigatória ausente: {key}")
    
    return config_dict

def load_yaml_file(filepath: Path) -> Dict[str, Any]:
    """Carrega YAML de arquivo."""
    with open(filepath, 'rb') as f:
        return parse_yaml_config(f.read())