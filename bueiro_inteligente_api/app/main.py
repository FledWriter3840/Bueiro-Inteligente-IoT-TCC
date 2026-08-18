from fastapi import FastAPI

from .routers import sensores, alertas, limpeza, compactacao, historico

app = FastAPI(title = "Bueiro Inteligente API", description="API para gerenciamento de sensores de bueiros inteligentes", version="1.0.0")

app.include_router(sensores.router)
app.include_router(alertas.router)
app.include_router(limpeza.router)
app.include_router(compactacao.router)
app.include_router(historico.router)

@app.get("/")
def root():
    return {"message": "API do bueiro inteligente rodando"}