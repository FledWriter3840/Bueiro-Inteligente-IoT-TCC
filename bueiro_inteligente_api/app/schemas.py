from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class ProblemValidationError(BaseModel):
    location: list[str | int]
    message: str
    code: str


class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str
    errors: list[ProblemValidationError] | None = None


class HealthOut(BaseModel):
    message: str


class BueiroCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", allow_inf_nan=False)

    regional: str = Field(min_length=1, max_length=80)
    elemento: str = Field(default="Bueiro", min_length=1, max_length=80)
    rodovia: str = Field(min_length=1, max_length=80)
    levantamento: str = Field(min_length=1, max_length=20)
    km: float = Field(ge=0)
    extensao_m: float | None = Field(default=None, ge=0)
    dimensao_m: float | None = Field(default=None, ge=0)
    tipo: str = Field(min_length=1, max_length=160)
    latitude_montante: float = Field(ge=-90, le=90)
    longitude_montante: float = Field(ge=-180, le=180)
    latitude_jusante: float = Field(ge=-90, le=90)
    longitude_jusante: float = Field(ge=-180, le=180)


class BueiroOut(BaseModel):
    id: int | str
    regional: str
    elemento: str
    rodovia: str
    levantamento: str
    km: float
    extensao_m: float | None
    dimensao_m: float | None
    tipo: str
    latitude_montante: float
    longitude_montante: float
    latitude_jusante: float
    longitude_jusante: float


class LocalSACOut(BaseModel):
    id: str
    latitude: float
    longitude: float
    logradouro: str
    numero: str
    total_solicitacoes: int


class SolicitacaoSACOut(BaseModel):
    id: str
    latitude: float
    longitude: float
    logradouro: str
    numero: str
    data_abertura: str
    data_parecer: str
    situacao: str
    canal: str
    servico: str
    distancia_m: float


class SolicitacoesProximasOut(BaseModel):
    latitude_referencia: float
    longitude_referencia: float
    raio_m: int
    total_encontradas: int
    total_finalizadas: int
    total_canceladas: int
    indice_constancia_chamados: float | None
    intervalo_medio_dias: float | None
    periodo_inicio: str | None
    periodo_fim: str | None
    solicitacoes: list[SolicitacaoSACOut]


class LeituraSensorCreate(BaseModel):
    id_sensor: int = Field(gt=0)
    valor_leitura: float = Field(allow_inf_nan=False)
    unidade_medida: str = Field(min_length=1, max_length=20)

class LeituraSensorOut(LeituraSensorCreate):
    id_leitura: int
    data_hora: datetime
    acionar_limpeza: bool = False
    tempo_limpeza_segundos: int = 0
    motivo_limpeza: str = ""
    nivel_risco: str = "Baixo"
    nivel_risco_multivariado: str = "Baixo"
    nivel_risco_ml: str = "Baixo"
    modelo_decisao: str = "Multivariada + Machine Learning"
    class Config:
        from_attributes = True

class LimpezaCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    status_limpeza: str = Field(min_length=1, max_length=20)

class LimpezaOut(LimpezaCreate):
    id_limpeza: int
    data_hora: datetime
    class Config:
        from_attributes = True

class AlertaCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    descricao: str = Field(min_length=1, max_length=255)
    nivel_criticidade: str = Field(min_length=1, max_length=20)
    id_leitura: int = Field(gt=0)

class AlertaOut(AlertaCreate):
    id_alerta: int
    data_hora: datetime
    class Config:
        from_attributes = True

class CompactacaoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nivel_residuo: float = Field(ge=0, allow_inf_nan=False)

class CompactacaoOut(CompactacaoCreate):
    id_compactacao: int
    data_hora: datetime
    class Config:
        from_attributes = True

class HistoricoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    descricao_evento: str = Field(min_length=1, max_length=255)
    id_usuario: int | None = Field(default=None, gt=0)

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
    # ── Campos originais (mantidos para compatibilidade) ──────────
    probabilidade_entupimento: float
    nivel_risco: str
    tendencia: str
    taxa_variacao_cm_min: float
    distancia_atual_cm: float
    tempo_estimado_transbordo_min: float | None
    recomendacao: str
    alerta_gerado: bool
    data_analise: datetime

    # ── Novos campos: recomendação de limpeza ─────────────────────
    urgencia_limpeza: str = "Rotina"
    """Rotina / Preventiva / Urgente / Emergência"""
    recomendacao_limpeza: str = ""
    """Texto detalhado da recomendação de limpeza."""
    proxima_limpeza_sugerida_min: float | None = None
    """Tempo sugerido até a próxima limpeza (minutos). None = manter rotina."""

    # ── Novos campos: detalhamento do scoring ─────────────────────
    scores_detalhados: dict[str, float] = {}
    """Score individual de cada dimensão (sensor, clima, temporal, etc)."""
    dados_climaticos_utilizados: dict | None = None
    """Dados climáticos usados na análise (None se indisponível)."""
    fontes_dados_disponiveis: list[str] = []
    """Lista de fontes de dados que foram efetivamente utilizadas."""

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