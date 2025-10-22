# backend/main.py
"""
Aplicação FastAPI unificada.
Combina geração de guias e mapas mentais.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path

from .core.config import get_settings
from .utils.logger import setup_logger
from .api.routes_guias import router as guias_router
from .api.routes_mapas import router as mapas_router
from .api.routes_pipeline import router as pipeline_router
from .api.websocket import manager
from .services.file_manager import ensure_directories

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação."""
    # === STARTUP ===
    setup_logger(settings)
    ensure_directories()
    
    print("\n" + "="*70)
    print(f"🚀 {settings.app_name} v{settings.app_version}")
    print("="*70)
    print(f"📍 Ambiente: {'DEV' if settings.debug else 'PROD'}")
    print(f"🔑 Providers: {', '.join(settings.list_configured_providers())}")
    print(f"📁 Output Guias: {settings.output_guias_dir}")
    print(f"📁 Output Mapas: {settings.output_mapas_dir}")
    print("="*70 + "\n")
    
    yield
    
    # === SHUTDOWN ===
    print("\n🛑 Encerrando aplicação...")


# === CRIAR APP ===
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Sistema unificado para geração automatizada de guias educacionais HTML "
        "e mapas mentais Mermaid a partir de conteúdo jurídico"
    ),
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)


# === MIDDLEWARE CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === ROTAS ===
app.include_router(guias_router, prefix="/api/guias", tags=["guias"])
app.include_router(mapas_router, prefix="/api/mapas", tags=["mapas"])
app.include_router(pipeline_router, prefix="/api", tags=["pipeline"])


# === INTERFACE WEB ===
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve interface web unificada."""
    html_path = Path("frontend/index.html")
    
    if not html_path.exists():
        return HTMLResponse(
            "<h1>Erro: Interface não encontrada</h1>",
            status_code=500
        )
    
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# === WEBSOCKET ===
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket para progresso em tempo real.
    Usado por ambos os pipelines (guias e mapas).
    """
    await manager.connect(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# === HEALTH CHECK ===
@app.get("/health")
async def health_check():
    """Verifica saúde do sistema."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "providers": settings.list_configured_providers(),
        "features": {
            "guias": True,
            "mapas": True,
            "pipeline_completo": True
        }
    }


# === ARQUIVOS ESTÁTICOS ===
static_path = Path("frontend/static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# === HANDLER DE ERROS ===
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global de exceções."""
    from .utils.logger import logger
    
    logger.error(f"Erro não tratado: {exc}")
    
    return {
        "error": "Internal server error",
        "message": str(exc) if settings.debug else "Ocorreu um erro interno",
        "type": type(exc).__name__
    }