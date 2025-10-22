from pathlib import Path
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
