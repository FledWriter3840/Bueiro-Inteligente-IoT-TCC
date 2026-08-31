from fastapi import FastAPI
from contextlib import asynccontextmanager

from .routers import sensores, alertas, limpeza, compactacao, historico, ia
from .dados_externos import inicializar_dados_externos

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa provedores de datasets externos configurados via .env
    inicializar_dados_externos()
    yield

app = FastAPI(
    title="Bueiro Inteligente API",
    description="API para gerenciamento de sensores e Inteligência Artificial de bueiros inteligentes",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(sensores.router)
app.include_router(alertas.router)
app.include_router(limpeza.router)
app.include_router(compactacao.router)
app.include_router(historico.router)
app.include_router(ia.router)

@app.get("/")
def root():
    return {"message": "API do bueiro inteligente rodando"}