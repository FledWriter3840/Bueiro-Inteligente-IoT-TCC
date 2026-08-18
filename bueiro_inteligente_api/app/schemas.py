from pydantic import BaseModel
from datetime import datetime

class LeituraSensorCreate(BaseModel):
    id_sensor: int
    valor_leitura: float
    unidade_medida: str

class LeituraSensorOut(LeituraSensorCreate):
    id_leitura: int
    data_hora: datetime
    class Config:
        from_attributes = True

class LimpezaCreate(BaseModel):
    status_limpeza: str

class LimpezaOut(LimpezaCreate):
    id_limpeza: int
    data_hora: datetime
    class Config:
        from_attributes = True

class AlertaCreate(BaseModel):
    descricao: str
    nivel_criticidade: str
    id_leitura: int

class AlertaOut(AlertaCreate):
    id_alerta: int
    data_hora: datetime
    class Config:
        from_attributes = True

class CompactacaoCreate(BaseModel):
    nivel_residuo: float

class CompactacaoOut(CompactacaoCreate):
    id_compactacao: int
    data_hora: datetime
    class Config:
        from_attributes = True

class HistoricoCreate(BaseModel):
    descricao_evento: str
    id_usuario: int | None = None

class HistoricoOut(HistoricoCreate):
    id_historico: int
    data_hora: datetime
    class Config:
        from_attributes = True