export type RiskLevel = 'Baixo' | 'Médio' | 'Alto' | 'Crítico'

export type SensorReading = {
  id_leitura: number
  id_sensor: number
  valor_leitura: number
  unidade_medida: string
  data_hora: string
  acionar_limpeza?: boolean
  tempo_limpeza_segundos?: number
  nivel_risco?: RiskLevel
}

export type AlertRecord = {
  id_alerta: number
  descricao: string
  nivel_criticidade: string
  id_leitura: number
  data_hora: string
}

export type CleaningRecord = {
  id_limpeza: number
  status_limpeza: string
  data_hora: string
}

export type CompactionRecord = {
  id_compactacao: number
  nivel_residuo: number
  data_hora: string
}

export type HistoryRecord = {
  id_historico: number
  descricao_evento: string
  id_usuario: number | null
  data_hora: string
}

export type Prediction = {
  nivel_risco: RiskLevel
  probabilidade_entupimento: number
  urgencia_limpeza?: string
  recomendacao: string
  recomendacao_limpeza?: string
  tendencia: string
  taxa_variacao_cm_min: number
  scores_detalhados?: Record<string, number>
  dados_climaticos_utilizados?: Record<string, unknown> | null
}

export type MlPrediction = {
  nivel_risco: RiskLevel
  probabilidade_classe: number
  classes_probabilidades: Record<string, number>
  modelo_utilizado: string
}

export type Comparison = {
  motor_regressao: Prediction
  motor_machine_learning: MlPrediction
  convergencia: boolean
  observacao: string
}

export type DataSource = {
  nome: string
  status: string
  descricao: string
}

export type DataSources = {
  fontes: DataSource[]
  total_ativas: number
  total_fontes: number
}

export type WeatherData = {
  disponivel: boolean
  descricao_clima?: string
  temperatura_c?: number
  umidade_pct?: number
  chuva_mm_h?: number
  previsao_chuva_proximas_3h_mm?: number
  vento_ms?: number
}

export type TopographyData = {
  disponivel: boolean
  altitude_metros?: number
  eh_fundo_de_vale?: boolean
  declividade_pct?: number
  classificacao_risco?: string
  dataset_origem?: string
}

export type Bueiro = {
  id: number | string
  regional: string
  elemento: string
  rodovia: string
  levantamento: string
  km: number
  extensao_m: number | null
  dimensao_m: number | null
  tipo: string
  latitude_montante: number
  longitude_montante: number
  latitude_jusante: number
  longitude_jusante: number
}

export type SacLocation = {
  id: string
  latitude: number
  longitude: number
  logradouro: string
  numero: string
  total_solicitacoes: number
}

export type SacRequest = {
  id: string
  latitude: number
  longitude: number
  logradouro: string
  numero: string
  data_abertura: string
  data_parecer: string
  situacao: string
  canal: string
  distancia_m: number
}

export type SacSearch = {
  latitude_referencia: number
  longitude_referencia: number
  raio_m: number
  total_encontradas: number
  total_finalizadas: number
  total_canceladas: number
  indice_constancia_chamados: number | null
  intervalo_medio_dias: number | null
  periodo_inicio: string | null
  periodo_fim: string | null
  solicitacoes: SacRequest[]
}

export type Simulation = {
  cenario: {
    distancia_inicial_cm: number
    velocidade_subida_cm_min: number
    tempo_total_simulado_min: number
  }
  projecoes: {
    minuto: number
    distancia_prevista_cm: number
    probabilidade_alagamento: number
    nivel_risco: RiskLevel
  }[]
}

export type TrainingResult = {
  acuracia: number
  relatorio_classificacao: string
  matriz_confusao: number[][]
  classes: string[]
  n_amostras_treino: number
  n_amostras_teste: number
}