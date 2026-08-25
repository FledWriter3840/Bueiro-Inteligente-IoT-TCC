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

class PrevisaoEntupimentoCreate(BaseModel):
    probabilidade: float
    nivel_risco: str
    id_leitura: int

class PrevisaoEntupimentoOut(PrevisaoEntupimentoCreate):
    id_previsao: int
    data_hora: datetime
    class Config:
        from_attributes = True

class AnaliseIAResult(BaseModel):
    probabilidade_entupimento: float
    nivel_risco: str
    tendencia: str
    taxa_variacao_cm_min: float
    distancia_atual_cm: float
    tempo_estimado_transbordo_min: float | None
    recomendacao: str
    alerta_gerado: bool
    data_analise: datetime

class CenarioSimulacaoRequest(BaseModel):
    distancia_inicial_cm: float = 350.0
    velocidade_subida_cm_min: float = 25.0
    minutos_simulacao: int = 10

class AnaliseIAMLResult(BaseModel):
    nivel_risco: str
    probabilidade_classe: float
    classes_probabilidades: dict[str, float]
    distancia_atual_cm: float
    taxa_subida_cm_min: float
    media_movel_3_cm: float
    modelo_utilizado: str
    data_analise: datetime

class TreinoMLResult(BaseModel):
    acuracia: float
    relatorio_classificacao: str
    matriz_confusao: list
    classes: list[str]
    n_amostras_treino: int
    n_amostras_teste: int

class ComparativoIAResult(BaseModel):
    motor_regressao: AnaliseIAResult
    motor_machine_learning: AnaliseIAMLResult
    convergencia: bool
    observacao: str