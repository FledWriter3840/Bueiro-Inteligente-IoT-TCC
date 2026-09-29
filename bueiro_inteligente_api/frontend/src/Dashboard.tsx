import { useEffect, useState, type CSSProperties, type FormEvent, type ReactNode } from 'react'
import {
  Activity, AlertTriangle, ArrowUpRight, BrainCircuit, Check, ChevronRight,
  CloudRain, Compass, Droplets, Gauge, Layers3, MapPinned, Plus, RefreshCw,
  Waves, Wrench, X,
} from 'lucide-react'
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Line, LineChart,
  ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { apiRequest } from './api'
import { LocationControls, type Coordinates } from './components/LocationControls'
import { LazyMapPanel as MapPanel } from './components/LazyMapPanel'
import type {
  AlertRecord, CleaningRecord, Comparison, CompactionRecord, DataSources,
  HistoryRecord, Prediction, SacLocation, SensorReading, Simulation,
  TopographyData, TrainingResult, WeatherData,
} from './types'
import './dashboard.css'

type View = 'overview' | 'readings' | 'events' | 'ai' | 'simulation' | 'manual' | 'map'
type Notice = { message: string; kind: 'success' | 'error' }
type Column<T> = { label: string; render: (row: T) => ReactNode }
type DashboardData = {
  readings: SensorReading[]; alerts: AlertRecord[]; cleanings: CleaningRecord[]
  compactions: CompactionRecord[]; history: HistoryRecord[]; prediction: Prediction | null
  sources: DataSources | null; weather: WeatherData | null; topography: TopographyData | null
}

const INITIAL_DATA: DashboardData = { readings: [], alerts: [], cleanings: [], compactions: [], history: [], prediction: null, sources: null, weather: null, topography: null }
const DEFAULT_LOCATION: Coordinates = { lat: -23.5505, lon: -46.6333 }
const RISK_COLORS: Record<string, string> = { Baixo: '#39856e', Médio: '#cb983c', Alto: '#d16c48', Crítico: '#a84438' }
const TODAY_LABEL = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'full' }).format(new Date())
const NAVIGATION = [
  { id: 'overview' as const, label: 'Visão geral', icon: Gauge },
  { id: 'readings' as const, label: 'Leituras', icon: Activity },
  { id: 'events' as const, label: 'Alertas e eventos', icon: Layers3 },
  { id: 'ai' as const, label: 'IA e previsão', icon: BrainCircuit },
  { id: 'simulation' as const, label: 'Simulação', icon: Waves },
  { id: 'manual' as const, label: 'Inserção manual', icon: Wrench },
  { id: 'map' as const, label: 'Mapa e chamados SAC', icon: MapPinned },
]

function formatDate(value?: string | null) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'medium' }).format(date)
}

function formatTime(value?: string | null) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' }).format(date)
}

function cleaningConsistency(records: CleaningRecord[]) {
  const cutoff = Date.now() - 180 * 86400000
  const dates = [...new Set(records.map((row) => new Date(row.data_hora).getTime()).filter((stamp) => Number.isFinite(stamp) && stamp >= cutoff))].sort((a, b) => a - b)
  if (dates.length < 3) return { index: null, count: dates.length }
  const intervals = dates.slice(1).map((stamp, index) => (stamp - dates[index]) / 86400000)
  const mean = intervals.reduce((sum, value) => sum + value, 0) / intervals.length
  if (mean <= 0 || intervals.length < 2) return { index: null, count: dates.length }
  const variance = intervals.reduce((sum, value) => sum + (value - mean) ** 2, 0) / (intervals.length - 1)
  return { index: 100 / (1 + Math.sqrt(variance) / mean), count: dates.length }
}

function Table<T extends object>({ rows, columns, rowKey, empty }: {
  rows: T[]; columns: Column<T>[]; rowKey: (row: T, index: number) => string | number; empty: string
}) {
  if (!rows.length) return <div className="empty-state"><span>{empty}</span></div>
  return <div className="table-scroll"><table><thead><tr>{columns.map((column) => <th key={column.label}>{column.label}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={rowKey(row, index)}>{columns.map((column) => <td key={column.label}>{column.render(row)}</td>)}</tr>)}</tbody></table></div>
}

function RiskBadge({ risk }: { risk: string }) {
  return <span className="risk-badge" style={{ '--risk-color': RISK_COLORS[risk] ?? '#77827a' } as CSSProperties}>{risk}</span>
}

export default function Dashboard() {
  const [view, setView] = useState<View>('overview')
  const [coordinates, setCoordinates] = useState(DEFAULT_LOCATION)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)
  const [refreshing, setRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState<Notice | null>(null)
  const [data, setData] = useState(INITIAL_DATA)
  const [comparison, setComparison] = useState<Comparison | null>(null)
  const [comparisonBusy, setComparisonBusy] = useState(false)
  const [sampleCount, setSampleCount] = useState(3000)
  const [trainingBusy, setTrainingBusy] = useState(false)
  const [trainingResult, setTrainingResult] = useState<TrainingResult | null>(null)
  const [simulation, setSimulation] = useState<Simulation | null>(null)
  const [simulationBusy, setSimulationBusy] = useState(false)
  const [simulationInput, setSimulationInput] = useState({ distance: 350, rate: 25, minutes: 10 })
  const [manualTab, setManualTab] = useState<'reading' | 'alert' | 'cleaning' | 'compaction' | 'history'>('reading')
  const [manualBusy, setManualBusy] = useState(false)
  const [readingInput, setReadingInput] = useState({ value: 20, unit: 'cm', sensor: 1 })
  const [alertInput, setAlertInput] = useState({ readingId: '', description: 'Alerta manual de teste', level: 'baixo' })
  const [cleaningInput, setCleaningInput] = useState('iniciada')
  const [compactionInput, setCompactionInput] = useState(50)
  const [historyInput, setHistoryInput] = useState('Evento de teste manual')
  const { lat, lon } = coordinates

  useEffect(() => {
    let active = true
    async function load() {
      setRefreshing(true)
      const value = <T,>(result: PromiseSettledResult<T>, fallback: T) => result.status === 'fulfilled' ? result.value : fallback
      const core = await Promise.allSettled([
        apiRequest<SensorReading[]>('/sensores/leituras'),
        apiRequest<AlertRecord[]>('/alertas/'),
        apiRequest<CleaningRecord[]>('/limpeza/'),
        apiRequest<CompactionRecord[]>('/compactacao/'),
        apiRequest<HistoryRecord[]>('/historico/'),
        apiRequest<Prediction>('/ia/previsao', { params: { id_sensor: 1, lat, lon }, timeoutMs: 120000 }),
      ] as const)
      if (!active) return
      setData((current) => ({
        ...current,
        readings: value(core[0], []), alerts: value(core[1], []), cleanings: value(core[2], []),
        compactions: value(core[3], []), history: value(core[4], []), prediction: value(core[5], null),
      }))
      setError(core.every((result) => result.status === 'rejected') ? 'API indisponível. Verifique se a API e o banco estão ativos.' : '')
      setLastUpdated(new Date())
      setRefreshing(false)

      const external = await Promise.allSettled([
        apiRequest<DataSources>('/ia/fontes-dados', { timeoutMs: 65000 }),
        apiRequest<WeatherData>('/ia/clima-atual', { params: { lat, lon } }),
        apiRequest<TopographyData>('/ia/topografia-atual', { params: { lat, lon }, timeoutMs: 65000 }),
      ] as const)
      if (!active) return
      setData((current) => ({
        ...current,
        sources: value(external[0], current.sources),
        weather: value(external[1], current.weather),
        topography: value(external[2], current.topography),
      }))
    }
    void load()
    const timer = autoRefresh ? window.setInterval(() => void load(), 10000) : undefined
    return () => { active = false; if (timer !== undefined) window.clearInterval(timer) }
  }, [lat, lon, autoRefresh, refreshKey])

  useEffect(() => {
    if (!notice) return
    const timer = window.setTimeout(() => setNotice(null), 4200)
    return () => window.clearTimeout(timer)
  }, [notice])

  async function submit(endpoint: string, payload: unknown, message: string) {
    setManualBusy(true)
    try {
      await apiRequest(endpoint, { method: 'POST', body: payload })
      setNotice({ message, kind: 'success' })
      setRefreshKey((key) => key + 1)
    } catch (reason) {
      setNotice({ message: reason instanceof Error ? reason.message : 'Não foi possível salvar o registro.', kind: 'error' })
    } finally { setManualBusy(false) }
  }

  async function compareEngines() {
    setComparisonBusy(true)
    try { setComparison(await apiRequest<Comparison>('/ia/comparativo', { params: { id_sensor: 1, ...coordinates }, timeoutMs: 120000 })) }
    catch (reason) { setNotice({ message: reason instanceof Error ? reason.message : 'Falha ao executar a comparação.', kind: 'error' }) }
    finally { setComparisonBusy(false) }
  }

  async function trainModel() {
    setTrainingBusy(true)
    try {
      const result = await apiRequest<TrainingResult>('/ia/treinar-modelo-ml', { method: 'POST', params: { n_amostras: sampleCount }, timeoutMs: 120000 })
      setTrainingResult(result)
      setNotice({ message: `Modelo treinado com acurácia de ${(result.acuracia * 100).toFixed(1)}%.`, kind: 'success' })
    } catch (reason) { setNotice({ message: reason instanceof Error ? reason.message : 'Falha ao treinar o modelo.', kind: 'error' }) }
    finally { setTrainingBusy(false) }
  }

  async function runSimulation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSimulationBusy(true)
    try {
      setSimulation(await apiRequest<Simulation>('/ia/simular-cenario', { method: 'POST', body: {
        distancia_inicial_cm: simulationInput.distance,
        velocidade_subida_cm_min: simulationInput.rate,
        minutos_simulacao: simulationInput.minutes,
      } }))
    } catch (reason) { setNotice({ message: reason instanceof Error ? reason.message : 'Não foi possível executar a simulação.', kind: 'error' }) }
    finally { setSimulationBusy(false) }
  }

  const title = NAVIGATION.find((item) => item.id === view)?.label ?? 'Visão geral'
  const consistency = cleaningConsistency(data.cleanings)
  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="#inicio" onClick={(event) => { event.preventDefault(); setView('overview') }}><span className="brand-mark"><Waves size={20} /></span><span><strong>Bueiro</strong><small>INTELIGENTE · IoT</small></span></a>
      <div className="nav-caption">MONITORAMENTO</div>
      <nav className="primary-nav" aria-label="Navegação principal">{NAVIGATION.map(({ id, label, icon: Icon }) => <button key={id} type="button" className={`nav-link ${view === id ? 'is-active' : ''}`} onClick={() => setView(id)}><Icon size={18} /><span>{label}</span>{view === id && <ChevronRight className="nav-current" size={15} />}</button>)}</nav>
      <LocationControls coordinates={coordinates} onCoordinatesChange={setCoordinates} onNotice={(message, kind) => setNotice({ message, kind })} />
      <div className="sidebar-bottom"><span className={`connection-dot ${error ? 'is-offline' : ''}`} /><span>{error ? 'API indisponível' : 'Monitoramento conectado'}</span><span className="connection-help" title="Status da conexão com a API">i</span></div>
    </aside>

    <main className="main-area">
      <header className="topbar"><div className="mobile-brand"><span className="brand-mark"><Waves size={18} /></span><strong>Bueiro Inteligente</strong></div><div className="breadcrumb"><span>Operação</span><ChevronRight size={14} /><strong>{title}</strong></div><div className="topbar-actions"><label className="auto-toggle"><input type="checkbox" checked={autoRefresh} onChange={(event) => setAutoRefresh(event.target.checked)} /><span className="switch" />Atualização automática</label><span className="updated-at">{lastUpdated ? `Atualizado ${formatTime(lastUpdated.toISOString())}` : 'Aguardando dados'}</span><button className="icon-button" type="button" aria-label="Atualizar agora" title="Atualizar agora" disabled={refreshing} onClick={() => setRefreshKey((key) => key + 1)}><RefreshCw size={17} className={refreshing ? 'spin' : ''} /></button></div></header>
      <div className="page-content">
        {error && <div className="api-banner"><AlertTriangle size={17} /><span>{error}</span><button type="button" className="text-button" onClick={() => setRefreshKey((key) => key + 1)}>Tentar novamente</button></div>}
        <div className="page-heading"><div><div className="eyebrow">CENTRO DE OPERAÇÕES <span className="heading-rule" /></div><h1>{title}</h1><p>Acompanhamento de risco, sensores e manutenção da rede de drenagem.</p></div><div className="heading-date"><span>HOJE</span><strong>{TODAY_LABEL}</strong></div></div>
        {view === 'overview' && <OverviewView data={data} consistency={consistency} onNavigate={setView} />}
        {view === 'readings' && <ReadingsView readings={data.readings} />}
        {view === 'events' && <EventsView data={data} />}
        {view === 'ai' && <AiView data={data} comparison={comparison} comparisonBusy={comparisonBusy} onCompare={compareEngines} sampleCount={sampleCount} onSampleCount={setSampleCount} onTrain={trainModel} trainingBusy={trainingBusy} trainingResult={trainingResult} />}
        {view === 'simulation' && <SimulationView input={simulationInput} onInput={setSimulationInput} onSubmit={runSimulation} result={simulation} busy={simulationBusy} />}
        {view === 'manual' && <ManualView activeTab={manualTab} onTab={setManualTab} busy={manualBusy} data={data} reading={readingInput} onReading={setReadingInput} alert={alertInput} onAlert={setAlertInput} cleaning={cleaningInput} onCleaning={setCleaningInput} compaction={compactionInput} onCompaction={setCompactionInput} history={historyInput} onHistory={setHistoryInput} onSubmit={submit} />}
        {view === 'map' && <MapView coordinates={coordinates} />}
        <footer className="page-footer"><span>BUEIRO INTELIGENTE · IoT</span><span>Dados ambientais e operacionais integrados</span></footer>
      </div>
    </main>
    {notice && <div className={`toast toast-${notice.kind}`} role="status"><span>{notice.kind === 'success' ? <Check size={17} /> : <AlertTriangle size={17} />}{notice.message}</span><button type="button" aria-label="Fechar aviso" onClick={() => setNotice(null)}><X size={15} /></button></div>}
  </div>
}

function Metric({ label, value, detail, tone, icon: Icon }: { label: string; value: string; detail: string; tone: string; icon: typeof Gauge }) {
  return <div className={`metric-card metric-${tone}`}><div className="metric-top"><span>{label}</span><Icon size={17} /></div><strong>{value}</strong><small>{detail}</small></div>
}

function OverviewView({ data, consistency, onNavigate }: { data: DashboardData; consistency: { index: number | null; count: number }; onNavigate: (view: View) => void }) {
  const latest = data.readings[0]
  const prediction = data.prediction
  const risk = prediction?.nivel_risco ?? 'Baixo'
  const tone = risk === 'Crítico' ? 'critical' : risk === 'Alto' ? 'high' : risk === 'Médio' ? 'medium' : 'good'
  const chartRows = [...data.readings].reverse().slice(-50).map((row) => ({ ...row, timeLabel: formatTime(row.data_hora) }))
  return <>
    <div className="metric-grid"><Metric label="Última leitura" value={latest ? `${latest.valor_leitura.toFixed(1)} ${latest.unidade_medida}` : '—'} detail={latest ? `Sensor ${latest.id_sensor} · ${formatTime(latest.data_hora)}` : 'Sem leituras'} tone="teal" icon={Activity} /><Metric label="Risco de alagamento" value={prediction?.nivel_risco ?? '—'} detail="Análise multivariada atual" tone={tone} icon={AlertTriangle} /><Metric label="Probabilidade" value={prediction ? `${(prediction.probabilidade_entupimento * 100).toFixed(0)}%` : '—'} detail="Entupimento previsto" tone="blue" icon={Gauge} /><Metric label="Urgência de limpeza" value={prediction?.urgencia_limpeza ?? '—'} detail={prediction?.recomendacao_limpeza ?? 'Recomendação da IA'} tone="amber" icon={Wrench} /><Metric label="Alertas registrados" value={String(data.alerts.length)} detail="Eventos no sistema" tone="neutral" icon={Layers3} /></div>
    {prediction && <div className={`recommendation recommendation-${tone}`}><span className="recommendation-icon"><AlertTriangle size={20} /></span><div><span>{risk === 'Alto' || risk === 'Crítico' ? 'ATENÇÃO OPERACIONAL' : 'RECOMENDAÇÃO ATUAL'}</span><strong>{prediction.recomendacao}</strong>{prediction.recomendacao_limpeza && <p>{prediction.recomendacao_limpeza}</p>}</div><button type="button" className="text-button" onClick={() => onNavigate('ai')}>Ver análise <ArrowUpRight size={15} /></button></div>}
    <div className="content-grid overview-grid"><section className="panel chart-panel"><div className="panel-heading"><div><span className="eyebrow">TELEMETRIA</span><h2>Histórico do sensor</h2><p>Distância medida ao longo do tempo</p></div><span className="chart-unit">cm</span></div>{chartRows.length ? <div className="chart-area"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chartRows} margin={{ top: 12, right: 10, bottom: 0, left: -15 }}><defs><linearGradient id="reading-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#d88d66" stopOpacity={0.28} /><stop offset="100%" stopColor="#d88d66" stopOpacity={0.01} /></linearGradient></defs><CartesianGrid stroke="#e8e8e1" strokeDasharray="3 5" vertical={false} /><XAxis dataKey="timeLabel" tickLine={false} axisLine={false} tick={{ fill: '#777f78', fontSize: 11 }} minTickGap={36} /><YAxis tickLine={false} axisLine={false} tick={{ fill: '#777f78', fontSize: 11 }} /><Tooltip contentStyle={{ borderRadius: 6, borderColor: '#dfe2da', fontSize: 12 }} formatter={(value) => [`${Number(value).toFixed(1)} cm`, 'Distância']} /><ReferenceLine y={15} stroke="#aa493b" strokeDasharray="5 5" label={{ value: 'Limite crítico · 15 cm', fill: '#aa493b', fontSize: 10 }} /><Area type="monotone" dataKey="valor_leitura" stroke="#c47652" strokeWidth={2.5} fill="url(#reading-fill)" activeDot={{ r: 5 }} /></AreaChart></ResponsiveContainer></div> : <div className="empty-state tall">Nenhuma leitura registrada ainda.</div>}<button type="button" className="panel-link" onClick={() => onNavigate('readings')}>Abrir histórico completo <ArrowUpRight size={15} /></button></section>
      <section className="panel conditions-panel"><div className="panel-heading"><div><span className="eyebrow">CONDIÇÕES EXTERNAS</span><h2>Contexto do local</h2><p>Clima e relevo consultados pela IA</p></div><Compass size={18} /></div><div className="condition-row"><span className="condition-icon weather-icon"><CloudRain size={17} /></span><div><small>Clima atual</small><strong>{data.weather?.disponivel ? data.weather.descricao_clima : 'Fallback sazonal ativo'}</strong></div><span className="condition-value">{data.weather?.temperatura_c != null ? `${data.weather.temperatura_c}°` : '—'}</span></div><div className="condition-details"><span>Chuva <strong>{data.weather?.chuva_mm_h ?? '—'} mm/h</strong></span><span>Umidade <strong>{data.weather?.umidade_pct ?? '—'}%</strong></span></div><div className="condition-row"><span className="condition-icon terrain-icon"><MapPinned size={17} /></span><div><small>Topografia</small><strong>{data.topography?.disponivel ? data.topography.classificacao_risco : 'Cota padrão'}</strong></div><span className="condition-value">{data.topography?.altitude_metros != null ? `${data.topography.altitude_metros} m` : '—'}</span></div><div className="condition-details"><span>Declividade <strong>{data.topography?.declividade_pct ?? '—'}%</strong></span><span>Fundo de vale <strong>{data.topography?.eh_fundo_de_vale ? 'Sim' : 'Não'}</strong></span></div><div className="context-location"><MapPinned size={14} /> Coordenadas selecionadas <span>ponto ativo</span></div></section></div>
    <div className="bottom-summary"><div><div className="summary-heading"><Droplets size={17} /><strong>Constância da limpeza</strong></div><div className="summary-value">{consistency.index == null ? 'Dados insuficientes' : <>{consistency.index.toFixed(0)}<span>/100</span></>}</div><p>{consistency.count} registros nos últimos 180 dias. São necessários ao menos 3 registros.</p><a href="https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/coefvari.htm" target="_blank" rel="noreferrer">Método IC = 100 / (1 + CV) · referência NIST</a></div><div className="summary-separator" /><div><div className="summary-heading"><Layers3 size={17} /><strong>Atividade recente</strong></div><div className="activity-numbers"><span><b>{data.cleanings.length}</b>limpezas</span><span><b>{data.alerts.length}</b>alertas</span><span><b>{data.readings.length}</b>leituras</span></div><button type="button" className="panel-link" onClick={() => onNavigate('events')}>Consultar eventos <ArrowUpRight size={15} /></button></div></div>
  </>
}

function ReadingsView({ readings }: { readings: SensorReading[] }) {
  return <section className="panel data-panel"><div className="panel-heading"><div><span className="eyebrow">TELEMETRIA IoT</span><h2>Histórico completo de leituras</h2><p>{readings.length} registros retornados pelos sensores</p></div><Activity size={19} /></div><Table rows={readings} rowKey={(row) => row.id_leitura} empty="Nenhuma leitura registrada ainda." columns={[{ label: 'ID', render: (row) => `#${row.id_leitura}` }, { label: 'Sensor', render: (row) => row.id_sensor }, { label: 'Leitura', render: (row) => <strong>{row.valor_leitura.toFixed(1)} {row.unidade_medida}</strong> }, { label: 'Data e hora', render: (row) => formatDate(row.data_hora) }, { label: 'Risco', render: (row) => row.nivel_risco ? <RiskBadge risk={row.nivel_risco} /> : '—' }, { label: 'Acionamento', render: (row) => row.acionar_limpeza ? `${row.tempo_limpeza_segundos ?? 0} s` : 'Não' }]} /></section>
}

function EventPanel<T extends object>({ title, kicker, count, rows, rowKey, columns, empty }: { title: string; kicker: string; count: number; rows: T[]; rowKey: (row: T) => number; columns: Column<T>[]; empty: string }) {
  return <section className="panel data-panel"><div className="panel-heading"><div><span className="eyebrow">{kicker}</span><h2>{title}</h2></div><span className="count-badge">{count}</span></div><Table rows={rows} columns={columns} rowKey={(row) => rowKey(row)} empty={empty} /></section>
}

function EventsView({ data }: { data: DashboardData }) {
  return <div className="event-grid"><EventPanel title="Alertas" kicker="RISCO E OCORRÊNCIAS" count={data.alerts.length} empty="Nenhum alerta registrado." rows={data.alerts} rowKey={(row) => row.id_alerta} columns={[{ label: 'Descrição', render: (row) => row.descricao }, { label: 'Nível', render: (row) => row.nivel_criticidade }, { label: 'Data', render: (row) => formatDate(row.data_hora) }]} /><EventPanel title="Limpeza" kicker="MANUTENÇÃO" count={data.cleanings.length} empty="Nenhuma limpeza registrada." rows={data.cleanings} rowKey={(row) => row.id_limpeza} columns={[{ label: 'Status', render: (row) => row.status_limpeza }, { label: 'Data', render: (row) => formatDate(row.data_hora) }]} /><EventPanel title="Compactação" kicker="RESÍDUOS" count={data.compactions.length} empty="Nenhum registro de compactação." rows={data.compactions} rowKey={(row) => row.id_compactacao} columns={[{ label: 'Nível', render: (row) => `${row.nivel_residuo}%` }, { label: 'Data', render: (row) => formatDate(row.data_hora) }]} /><EventPanel title="Histórico do sistema" kicker="AUDITORIA" count={data.history.length} empty="Nenhum evento registrado." rows={data.history} rowKey={(row) => row.id_historico} columns={[{ label: 'Evento', render: (row) => row.descricao_evento }, { label: 'Data', render: (row) => formatDate(row.data_hora) }]} /></div>
}

function AiView({ data, comparison, comparisonBusy, onCompare, sampleCount, onSampleCount, onTrain, trainingBusy, trainingResult }: {
  data: DashboardData; comparison: Comparison | null; comparisonBusy: boolean; onCompare: () => void; sampleCount: number; onSampleCount: (value: number) => void; onTrain: () => void; trainingBusy: boolean; trainingResult: TrainingResult | null
}) {
  const scores = Object.entries(comparison?.motor_regressao.scores_detalhados ?? data.prediction?.scores_detalhados ?? {}).map(([name, score]) => ({ name, score }))
  const classes = Object.entries(comparison?.motor_machine_learning.classes_probabilidades ?? {}).map(([name, probability]) => ({ name, probability }))
  return <div className="ai-page"><section className="panel ai-action-panel"><div><span className="eyebrow">ANÁLISE PREDITIVA</span><h2>Comparativo dos motores</h2><p>Execute os dois modelos sobre as leituras mais recentes.</p></div><button className="button button-primary" type="button" onClick={onCompare} disabled={comparisonBusy}><BrainCircuit size={16} />{comparisonBusy ? 'Analisando…' : 'Rodar comparativo'}</button></section>
    {comparison ? <><div className="engine-grid"><section className="panel engine-panel"><div className="engine-heading"><span className="engine-number">01</span><div><span className="eyebrow">6 FONTES</span><h2>Motor multivariado</h2></div></div><div className="engine-result"><span>Risco</span><RiskBadge risk={comparison.motor_regressao.nivel_risco} /></div><div className="engine-result"><span>Probabilidade</span><strong>{(comparison.motor_regressao.probabilidade_entupimento * 100).toFixed(0)}%</strong></div><div className="engine-result"><span>Urgência de limpeza</span><strong>{comparison.motor_regressao.urgencia_limpeza ?? 'Rotina'}</strong></div><p className="engine-recommendation">{comparison.motor_regressao.recomendacao}</p><p className="engine-recommendation">{comparison.motor_regressao.recomendacao_limpeza}</p>{scores.length > 0 && <div className="mini-chart"><ResponsiveContainer width="100%" height={190}><BarChart data={scores} layout="vertical" margin={{ left: 12, right: 12 }}><CartesianGrid stroke="#ecece6" horizontal={false} /><XAxis type="number" domain={[0, 1]} tick={{ fontSize: 10 }} /><YAxis type="category" dataKey="name" width={110} tick={{ fontSize: 10 }} /><Tooltip formatter={(value) => [Number(value).toFixed(2), 'Score']} /><Bar dataKey="score" fill="#438d7c" radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer></div>}</section><section className="panel engine-panel"><div className="engine-heading"><span className="engine-number engine-number-amber">02</span><div><span className="eyebrow">CLASSIFICAÇÃO</span><h2>Machine Learning</h2></div></div><div className="engine-result"><span>Risco</span><RiskBadge risk={comparison.motor_machine_learning.nivel_risco} /></div><div className="engine-result"><span>Confiança</span><strong>{(comparison.motor_machine_learning.probabilidade_classe * 100).toFixed(0)}%</strong></div><div className="engine-result"><span>Modelo</span><strong>{comparison.motor_machine_learning.modelo_utilizado}</strong></div><p className="engine-recommendation">Probabilidades por nível de risco.</p>{classes.length > 0 && <div className="mini-chart"><ResponsiveContainer width="100%" height={190}><BarChart data={classes} margin={{ top: 10, right: 8, bottom: 0, left: -18 }}><CartesianGrid stroke="#ecece6" vertical={false} /><XAxis dataKey="name" tick={{ fontSize: 10 }} /><YAxis domain={[0, 1]} tickFormatter={(value) => `${Math.round(Number(value) * 100)}%`} tick={{ fontSize: 10 }} /><Tooltip formatter={(value) => [`${(Number(value) * 100).toFixed(1)}%`, 'Probabilidade']} /><Bar dataKey="probability" radius={[4, 4, 0, 0]}>{classes.map((entry) => <Cell key={entry.name} fill={RISK_COLORS[entry.name] ?? '#718078'} />)}</Bar></BarChart></ResponsiveContainer></div>}</section></div><div className={`convergence ${comparison.convergencia ? 'is-agree' : 'is-divergent'}`}><span>{comparison.convergencia ? <Check size={17} /> : <AlertTriangle size={17} />}</span><strong>{comparison.convergencia ? 'Motores convergentes' : 'Divergência entre motores'}</strong><p>{comparison.observacao}</p></div></> : <section className="panel ai-empty"><BrainCircuit size={30} /><strong>Análise comparativa pronta</strong><p>Execute os modelos para consultar risco, confiança e convergência.</p></section>}
    <div className="ai-subgrid"><section className="panel sources-panel"><div className="panel-heading"><div><span className="eyebrow">OBSERVABILIDADE</span><h2>Fontes de dados</h2><p>{data.sources?.total_ativas ?? '—'} de {data.sources?.total_fontes ?? 6} fontes ativas</p></div><Layers3 size={18} /></div><Table rows={data.sources?.fontes ?? []} rowKey={(row) => row.nome} empty="Status das fontes indisponível." columns={[{ label: 'Fonte', render: (row) => <strong>{row.nome}</strong> }, { label: 'Status', render: (row) => <span className={row.status === 'Ativo' ? 'source-on' : 'source-off'}>{row.status}</span> }, { label: 'Descrição', render: (row) => row.descricao }]} /></section><section className="panel source-details"><div className="panel-heading"><div><span className="eyebrow">SINAIS EXTERNOS</span><h2>Clima e topografia</h2></div><CloudRain size={18} /></div><div className="source-detail-block"><strong><CloudRain size={15} /> Clima</strong><span>{data.weather?.descricao_clima ?? 'Fallback sazonal ativo'}</span><small>Chuva {data.weather?.chuva_mm_h ?? '—'} mm/h · Umidade {data.weather?.umidade_pct ?? '—'}% · Previsão 3h {data.weather?.previsao_chuva_proximas_3h_mm ?? '—'} mm</small></div><div className="source-detail-block"><strong><MapPinned size={15} /> Relevo</strong><span>{data.topography?.disponivel ? `${data.topography.altitude_metros} m · ${data.topography.classificacao_risco}` : 'Cota padrão'}</span><small>Declividade {data.topography?.declividade_pct ?? '—'}% · Fundo de vale {data.topography?.eh_fundo_de_vale ? 'sim' : 'não'}</small></div></section></div>
    <section className="panel train-panel"><div><span className="eyebrow">CICLO DE TREINAMENTO</span><h2>Retreinar modelo ML</h2><p>Gere uma amostra sintética para avaliar o classificador.</p></div><div className="train-controls"><label htmlFor="sample-count">Amostras sintéticas <strong>{sampleCount.toLocaleString('pt-BR')}</strong><input id="sample-count" type="range" min="500" max="10000" step="500" value={sampleCount} onChange={(event) => onSampleCount(Number(event.target.value))} /></label><button className="button button-outline" type="button" onClick={onTrain} disabled={trainingBusy}><RefreshCw size={15} className={trainingBusy ? 'spin' : ''} />{trainingBusy ? 'Treinando…' : 'Treinar modelo'}</button></div>{trainingResult && <div className="training-result"><div><span>Acurácia</span><strong>{(trainingResult.acuracia * 100).toFixed(1)}%</strong></div><div><span>Amostras treino / teste</span><strong>{trainingResult.n_amostras_treino} / {trainingResult.n_amostras_teste}</strong></div><pre>{trainingResult.relatorio_classificacao}</pre></div>}</section>
  </div>
}

function SimulationView({ input, onInput, onSubmit, result, busy }: { input: { distance: number; rate: number; minutes: number }; onInput: (value: { distance: number; rate: number; minutes: number }) => void; onSubmit: (event: FormEvent<HTMLFormElement>) => void; result: Simulation | null; busy: boolean }) {
  return <div className="simulation-page"><section className="panel simulation-controls"><div className="panel-heading"><div><span className="eyebrow">CENÁRIO DE CHUVA</span><h2>Simular elevação da água</h2><p>Projeção baseada na distância e velocidade de subida.</p></div><Waves size={20} /></div><form onSubmit={onSubmit}><div className="form-grid-three"><label>Distância inicial (cm)<input type="number" min="0" step="1" value={input.distance} onChange={(event) => onInput({ ...input, distance: Number(event.target.value) })} /></label><label>Velocidade (cm/min)<input type="number" step="1" value={input.rate} onChange={(event) => onInput({ ...input, rate: Number(event.target.value) })} /></label><label>Duração (min)<input type="number" min="1" max="60" step="1" value={input.minutes} onChange={(event) => onInput({ ...input, minutes: Number(event.target.value) })} /></label></div><button className="button button-primary" disabled={busy}><Activity size={16} />{busy ? 'Calculando…' : 'Executar simulação'}</button></form></section>{result ? <><div className="simulation-summary"><span>Distância inicial <strong>{result.cenario.distancia_inicial_cm} cm</strong></span><span>Taxa de subida <strong>{result.cenario.velocidade_subida_cm_min} cm/min</strong></span><span>Tempo simulado <strong>{result.cenario.tempo_total_simulado_min} min</strong></span></div><section className="panel chart-panel"><div className="panel-heading"><div><span className="eyebrow">PROJEÇÃO</span><h2>Distância prevista no tempo</h2></div><span className="chart-unit">cm</span></div><div className="chart-area simulation-chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={result.projecoes} margin={{ top: 12, right: 18, bottom: 0, left: -15 }}><CartesianGrid stroke="#e8e8e1" strokeDasharray="3 5" vertical={false} /><XAxis dataKey="minuto" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} /><YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11 }} /><Tooltip formatter={(value) => [`${value} cm`, 'Distância prevista']} /><ReferenceLine y={15} stroke="#a84438" strokeDasharray="5 5" label={{ value: 'Limite crítico', fill: '#a84438', fontSize: 10 }} /><Line type="monotone" dataKey="distancia_prevista_cm" stroke="#c47652" strokeWidth={2.5} dot={false} activeDot={{ r: 5 }} /></LineChart></ResponsiveContainer></div></section><section className="panel data-panel"><Table rows={result.projecoes} rowKey={(row) => row.minuto} empty="Sem projeções." columns={[{ label: 'Minuto', render: (row) => row.minuto }, { label: 'Distância', render: (row) => `${row.distancia_prevista_cm.toFixed(1)} cm` }, { label: 'Probabilidade', render: (row) => `${(row.probabilidade_alagamento * 100).toFixed(0)}%` }, { label: 'Risco', render: (row) => <RiskBadge risk={row.nivel_risco} /> }]} /></section></> : <div className="empty-state tall">Configure o cenário e execute a simulação para ver a projeção.</div>}</div>
}

function ManualView({ activeTab, onTab, busy, data, reading, onReading, alert, onAlert, cleaning, onCleaning, compaction, onCompaction, history, onHistory, onSubmit }: {
  activeTab: 'reading' | 'alert' | 'cleaning' | 'compaction' | 'history'; onTab: (tab: 'reading' | 'alert' | 'cleaning' | 'compaction' | 'history') => void; busy: boolean; data: DashboardData
  reading: { value: number; unit: string; sensor: number }; onReading: (value: { value: number; unit: string; sensor: number }) => void
  alert: { readingId: string; description: string; level: string }; onAlert: (value: { readingId: string; description: string; level: string }) => void
  cleaning: string; onCleaning: (value: string) => void; compaction: number; onCompaction: (value: number) => void; history: string; onHistory: (value: string) => void
  onSubmit: (endpoint: string, payload: unknown, message: string) => Promise<void>
}) {
  const tabs = [{ id: 'reading' as const, label: 'Leitura de sensor' }, { id: 'alert' as const, label: 'Alerta' }, { id: 'cleaning' as const, label: 'Limpeza' }, { id: 'compaction' as const, label: 'Compactação' }, { id: 'history' as const, label: 'Histórico' }]
  const send = (event: FormEvent<HTMLFormElement>, endpoint: string, payload: unknown, message: string) => { event.preventDefault(); void onSubmit(endpoint, payload, message) }
  return <section className="panel manual-panel"><div className="panel-heading"><div><span className="eyebrow">ENTRADA OPERACIONAL</span><h2>Inserir dados manualmente</h2><p>Registre cenários de teste ou operações realizadas.</p></div><Wrench size={19} /></div><div className="manual-tabs" role="tablist">{tabs.map((tab) => <button type="button" role="tab" aria-selected={activeTab === tab.id} className={activeTab === tab.id ? 'is-active' : ''} key={tab.id} onClick={() => onTab(tab.id)}>{tab.label}</button>)}</div>
    {activeTab === 'reading' && <form className="manual-form" onSubmit={(event) => send(event, '/sensores/leitura', { valor_leitura: reading.value, unidade_medida: reading.unit, id_sensor: reading.sensor }, 'Leitura registrada e IA executada.')}><h3>Nova leitura de sensor</h3><div className="form-grid-three"><label>Distância<input type="number" min="0" step="0.1" value={reading.value} onChange={(event) => onReading({ ...reading, value: Number(event.target.value) })} /></label><label>Unidade<select value={reading.unit} onChange={(event) => onReading({ ...reading, unit: event.target.value })}><option>cm</option><option>mm</option><option>m</option></select></label><label>ID do sensor<input type="number" min="1" value={reading.sensor} onChange={(event) => onReading({ ...reading, sensor: Number(event.target.value) })} /></label></div><button className="button button-primary" disabled={busy}><Activity size={16} />Registrar leitura</button><div className="quick-scenarios"><span>Atalhos</span>{[{ value: 200, label: 'Normal · 200 cm' }, { value: 60, label: 'Moderado · 60 cm' }, { value: 8, label: 'Crítico · 8 cm' }].map((item) => <button type="button" key={item.value} onClick={() => void onSubmit('/sensores/leitura', { valor_leitura: item.value, unidade_medida: 'cm', id_sensor: reading.sensor }, `${item.label} enviado.`)}>{item.label}</button>)}</div></form>}
    {activeTab === 'alert' && <form className="manual-form" onSubmit={(event) => send(event, '/alertas/', { descricao: alert.description, nivel_criticidade: alert.level, id_leitura: Number(alert.readingId) }, 'Alerta registrado.')}><h3>Novo alerta manual</h3>{data.readings.length ? <><label>Leitura associada<select required value={alert.readingId} onChange={(event) => onAlert({ ...alert, readingId: event.target.value })}><option value="">Selecione uma leitura</option>{data.readings.slice(0, 20).map((row) => <option key={row.id_leitura} value={row.id_leitura}>{`#${row.id_leitura} · ${row.valor_leitura} ${row.unidade_medida} · ${formatDate(row.data_hora)}`}</option>)}</select></label><label>Descrição<input required maxLength={255} value={alert.description} onChange={(event) => onAlert({ ...alert, description: event.target.value })} /></label><label>Nível de criticidade<select value={alert.level} onChange={(event) => onAlert({ ...alert, level: event.target.value })}><option value="baixo">Baixo</option><option value="medio">Médio</option><option value="alto">Alto</option><option value="critico">Crítico</option></select></label><button className="button button-primary" disabled={busy}><Plus size={16} />Registrar alerta</button></> : <div className="inline-warning">Registre ao menos uma leitura antes de criar um alerta.</div>}</form>}
    {activeTab === 'cleaning' && <form className="manual-form" onSubmit={(event) => send(event, '/limpeza/', { status_limpeza: cleaning }, 'Limpeza registrada.')}><h3>Novo registro de limpeza</h3><label>Status<select value={cleaning} onChange={(event) => onCleaning(event.target.value)}>{['iniciada', 'em_andamento', 'concluida', 'falha'].map((item) => <option key={item}>{item}</option>)}</select></label><button className="button button-primary" disabled={busy}><Plus size={16} />Registrar limpeza</button></form>}
    {activeTab === 'compaction' && <form className="manual-form" onSubmit={(event) => send(event, '/compactacao/', { nivel_residuo: compaction }, 'Compactação registrada.')}><h3>Novo registro de compactação</h3><label>Nível de resíduo compactado <strong>{compaction}%</strong><input type="range" min="0" max="100" step="5" value={compaction} onChange={(event) => onCompaction(Number(event.target.value))} /></label><button className="button button-primary" disabled={busy}><Plus size={16} />Registrar compactação</button></form>}
    {activeTab === 'history' && <form className="manual-form" onSubmit={(event) => send(event, '/historico/', { descricao_evento: history }, 'Evento registrado no histórico.')}><h3>Novo evento do sistema</h3><label>Descrição do evento<input required maxLength={255} value={history} onChange={(event) => onHistory(event.target.value)} /></label><button className="button button-primary" disabled={busy}><Plus size={16} />Registrar evento</button></form>}
  </section>
}

function MapView({ coordinates }: { coordinates: Coordinates }) {
  const [sacLocations, setSacLocations] = useState<SacLocation[]>([])
  const [selectedSac, setSelectedSac] = useState('')
  useEffect(() => { void apiRequest<SacLocation[]>('/bueiros/locais-sac').then(setSacLocations).catch(() => setSacLocations([])) }, [])
  const selected = sacLocations.find((item) => item.id === selectedSac)
  return <div className="map-page"><div className="map-page-heading"><div><span className="eyebrow">INVENTÁRIO GEOESPACIAL</span><h2>Bueiros e chamados de limpeza</h2><p>Estruturas inventariadas e ocorrências do SAC próximas à localização ativa.</p></div><label className="field-inline">Local SAC<select value={selectedSac} onChange={(event) => setSelectedSac(event.target.value)}><option value="">Localização ativa</option>{sacLocations.map((item) => <option key={item.id} value={item.id}>{item.logradouro}, {item.numero} · {item.total_solicitacoes} chamados</option>)}</select></label></div><MapPanel key={selectedSac} coordinates={selected ? { lat: selected.latitude, lon: selected.longitude } : coordinates} /><p className="map-disclaimer">Os chamados FINALIZADOS indicam encerramento no SAC; não comprovam a execução física de uma limpeza.</p></div>
}