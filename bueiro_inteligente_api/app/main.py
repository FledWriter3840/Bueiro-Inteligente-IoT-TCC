from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routers import (
    alertas,
    app_mobile,
    bueiros,
    camera,
    compactacao,
    historico,
    ia,
    limpeza,
    sensores,
)
from .dados_externos import inicializar_dados_externos
from .errors import register_exception_handlers
from . import schemas
from .routers.app_mobile import UPLOADS_DIR

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Inicializa os provedores externos durante o ciclo de vida da API."""
    # Inicializa provedores de datasets externos configurados via .env
    inicializar_dados_externos()
    yield

app = FastAPI(
    title="Bueiro Inteligente API",
    description="API para gerenciamento de sensores e Inteligência Artificial de bueiros inteligentes",
    version="1.0.0",
    lifespan=lifespan
)
register_exception_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sensores.router)
app.include_router(alertas.router)
app.include_router(limpeza.router)
app.include_router(compactacao.router)
app.include_router(historico.router)
app.include_router(ia.router)
app.include_router(bueiros.router)
app.include_router(camera.router)
app.include_router(app_mobile.router)
app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOADS_DIR), check_dir=False),
    name="uploads",
)

@app.get("/", response_model=schemas.HealthOut)
def root() -> dict[str, str]:
    """Informa que a API está disponível."""
    return {"message": "API do bueiro inteligente rodando"}
