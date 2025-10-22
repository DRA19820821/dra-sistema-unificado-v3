# backend/core/config.py
"""
Configurações unificadas do sistema.
Gerencia settings de guias e mapas.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional, Literal


class Settings(BaseSettings):
    """Configurações globais da aplicação unificada."""
    
    # === APLICAÇÃO ===
    app_name: str = "Sistema Unificado - Guias e Mapas Mentais"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # === SERVIDOR ===
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    
    # === DIRETÓRIOS ===
    upload_dir: str = "uploads"
    output_dir: str = "output"
    output_guias_dir: str = "output/guias"
    output_mapas_dir: str = "output/mapas"
    logs_dir: str = "logs"
    config_dir: str = "config"
    
    # === API KEYS ===
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    deepseek_api_key: str = ""
    
    # === PROCESSAMENTO - GUIAS ===
    guias_max_paralelo: int = 3
    guias_max_tentativas_revisao: int = 3
    guias_delay_retry: int = 5
    
    # === PROCESSAMENTO - MAPAS ===
    mapas_max_tentativas_revisao: int = 3
    mapas_max_workers_per_file: int = 3
    mapas_max_concurrent_files: int = 2
    
    # === LIMITES ===
    max_files_per_upload: int = 20
    max_file_size_mb: int = 10
    llm_timeout: int = 300
    
    # === LOGGING ===
    log_level: str = "INFO"
    log_rotation: str = "100 MB"
    log_retention: str = "30 days"
    
    # === CORS ===
    cors_origins: list[str] = ["*"]
    
    # === CONFIGURAÇÃO PYDANTIC ===
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # === MÉTODOS AUXILIARES ===
    
    def get_provider_key(self, provider: str) -> Optional[str]:
        """Retorna API key do provider."""
        provider = provider.lower()
        key_mapping = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "gemini": self.google_api_key,
            "google": self.google_api_key,
            "deepseek": self.deepseek_api_key,
        }
        return key_mapping.get(provider)
    
    def is_provider_configured(self, provider: str) -> bool:
        """Verifica se provider está configurado."""
        key = self.get_provider_key(provider)
        return key is not None and len(key) > 10
    
    def list_configured_providers(self) -> list[str]:
        """Lista providers configurados."""
        providers = []
        for name in ["openai", "anthropic", "gemini", "deepseek"]:
            if self.is_provider_configured(name):
                providers.append(name)
        return providers
    
    def validate_provider(self, provider: str) -> tuple[bool, str]:
        """Valida provider."""
        valid = ["openai", "anthropic", "gemini", "deepseek"]
        
        if provider.lower() not in valid:
            return False, f"Provider '{provider}' inválido. Opções: {', '.join(valid)}"
        
        if not self.is_provider_configured(provider):
            return False, f"Provider '{provider}' não configurado. Adicione API key no .env"
        
        return True, ""


@lru_cache()
def get_settings() -> Settings:
    """Retorna instância singleton das configurações."""
    return Settings()