import { useDeferredValue, useEffect, useEffectEvent, useState } from 'react'
import { ChevronDown, Crosshair, MapPin, Plus, Save } from 'lucide-react'
import { apiRequest } from '../api'
import type { Bueiro, SacLocation } from '../types'

export type Coordinates = { lat: number; lon: number }

const PRESETS: Record<string, Coordinates> = {
  'São Paulo · Centro': { lat: -23.5505, lon: -46.6333 },
  'São Paulo · Marginal Tietê': { lat: -23.523, lon: -46.682 },
  'São Paulo · Marginal Pinheiros': { lat: -23.587, lon: -46.692 },
  'São Paulo · Ipiranga': { lat: -23.59, lon: -46.61 },
  'Rio de Janeiro · Centro': { lat: -22.9068, lon: -43.1729 },
  'Curitiba · Centro': { lat: -25.4284, lon: -49.2733 },
}
const TODAY = new Date().toISOString().slice(0, 10)

type Props = {
  coordinates: Coordinates
  onCoordinatesChange: (coordinates: Coordinates) => void
  onNotice: (message: string, kind: 'success' | 'error') => void
}

export function LocationControls({ coordinates, onCoordinatesChange, onNotice }: Props) {
  const [mode, setMode] = useState('preset')
  const [preset, setPreset] = useState(Object.keys(PRESETS)[0])
  const [roads, setRoads] = useState<string[]>([])
  const [road, setRoad] = useState('')
  const [inventory, setInventory] = useState<Bueiro[]>([])
  const [bueiroId, setBueiroId] = useState('')
  const [point, setPoint] = useState<'montante' | 'jusante'>('montante')
  const [sacLocations, setSacLocations] = useState<SacLocation[]>([])
  const [sacId, setSacId] = useState('')
  const [sacSearch, setSacSearch] = useState('')
  const [expanded, setExpanded] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    regional: 'Cadastro manual',
    elemento: 'Bueiro',
    rodovia: '',
    levantamento: TODAY,
    km: 0,
    tipo: 'Boca de lobo',
    extensao_m: '',
    dimensao_m: '',
    latitude_montante: coordinates.lat,
    longitude_montante: coordinates.lon,
    latitude_jusante: coordinates.lat,
    longitude_jusante: coordinates.lon,
  })

  useEffect(() => {
    void apiRequest<string[]>('/bueiros/rodovias').then((data) => {
      setRoads(data)
      setRoad((current) => current || data[0] || '')
    }).catch(() => setRoads([]))
    void apiRequest<SacLocation[]>('/bueiros/locais-sac').then((data) => {
      setSacLocations(data)
    }).catch(() => setSacLocations([]))
  }, [])

  const receiveInventory = useEffectEvent((data: Bueiro[]) => {
    setInventory(data)
    const selected = data.find((item) => String(item.id) === bueiroId) ?? data[0]
    setBueiroId(String(selected?.id ?? ''))
    if (!selected) return
    const next = { lat: selected[`latitude_${point}`], lon: selected[`longitude_${point}`] }
    onCoordinatesChange(next)
    setForm((current) => ({
      ...current,
      regional: selected.regional,
      elemento: selected.elemento,
      rodovia: selected.rodovia,
      km: selected.km,
      tipo: selected.tipo,
      extensao_m: selected.extensao_m == null ? '' : String(selected.extensao_m),
      dimensao_m: selected.dimensao_m == null ? '' : String(selected.dimensao_m),
      latitude_montante: next.lat,
      longitude_montante: next.lon,
      latitude_jusante: next.lat,
      longitude_jusante: next.lon,
    }))
  })

  useEffect(() => {
    if (!road || mode !== 'inventory') return
    void apiRequest<Bueiro[]>('/bueiros/', { params: { rodovia: road } }).then(receiveInventory).catch(() => setInventory([]))
  }, [mode, road])

  const selectedBueiro = inventory.find((item) => String(item.id) === bueiroId)
  const selectedSac = sacLocations.find((item) => item.id === sacId)
  const deferredSacSearch = useDeferredValue(sacSearch.trim().toLocaleLowerCase('pt-BR'))
  const filteredSacLocations = sacLocations
    .filter((item) => `${item.logradouro} ${item.numero}`.toLocaleLowerCase('pt-BR').includes(deferredSacSearch))
    .slice(0, 100)

  function updateForm<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  function applyCoordinates(next: Coordinates) {
    onCoordinatesChange(next)
    setForm((current) => ({
      ...current,
      latitude_montante: next.lat,
      longitude_montante: next.lon,
      latitude_jusante: next.lat,
      longitude_jusante: next.lon,
    }))
  }

  function selectBueiro(id: string) {
    setBueiroId(id)
    const selected = inventory.find((item) => String(item.id) === id)
    if (!selected) return
    setForm((current) => ({
      ...current,
      regional: selected.regional,
      elemento: selected.elemento,
      rodovia: selected.rodovia,
      km: selected.km,
      tipo: selected.tipo,
      extensao_m: selected.extensao_m == null ? '' : String(selected.extensao_m),
      dimensao_m: selected.dimensao_m == null ? '' : String(selected.dimensao_m),
    }))
    applyCoordinates({ lat: selected[`latitude_${point}`], lon: selected[`longitude_${point}`] })
  }

  function selectSac(id: string) {
    setSacId(id)
    const selected = sacLocations.find((item) => item.id === id)
    if (!selected) return
    setForm((current) => ({
      ...current,
      regional: 'Cadastro via SAC',
      elemento: 'Boca de lobo',
      rodovia: `${selected.logradouro}, ${selected.numero}`.replace(/, $/, ''),
      tipo: 'Boca de lobo (local do SAC)',
    }))
    applyCoordinates({ lat: selected.latitude, lon: selected.longitude })
  }

  async function submitBueiro(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    try {
      const result = await apiRequest<Bueiro>('/bueiros/', {
        method: 'POST',
        body: {
          ...form,
          km: Number(form.km),
          extensao_m: form.extensao_m ? Number(form.extensao_m) : null,
          dimensao_m: form.dimensao_m ? Number(form.dimensao_m) : null,
        },
      })
      onNotice(`Cadastro ${result.id} salvo no inventário.`, 'success')
      setMode('inventory')
      if (form.rodovia) setRoad(form.rodovia)
      const updated = await apiRequest<string[]>('/bueiros/rodovias')
      setRoads(updated)
    } catch (error) {
      onNotice(error instanceof Error ? error.message : 'Não foi possível salvar o cadastro.', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="location-controls" aria-label="Localização de referência">
      <div className="section-kicker"><MapPin size={15} /> LOCALIZAÇÃO DE REFERÊNCIA</div>
      <label className="field-label" htmlFor="location-mode">Origem do ponto</label>
      <select id="location-mode" value={mode} onChange={(event) => {
        const nextMode = event.target.value
        setMode(nextMode)
        if (nextMode === 'preset') applyCoordinates(PRESETS[preset])
        if (nextMode === 'inventory' && selectedBueiro) applyCoordinates({ lat: selectedBueiro[`latitude_${point}`], lon: selectedBueiro[`longitude_${point}`] })
        if (nextMode === 'sac' && selectedSac) applyCoordinates({ lat: selectedSac.latitude, lon: selectedSac.longitude })
      }}>
        <option value="preset">Locais predefinidos</option>
        <option value="inventory">Inventário rodoviário</option>
        <option value="sac">Local de chamado SAC</option>
        <option value="custom">Coordenadas próprias</option>
      </select>

      {mode === 'preset' && (
        <select aria-label="Local predefinido" value={preset} onChange={(event) => {
          setPreset(event.target.value)
          applyCoordinates(PRESETS[event.target.value])
        }}>
          {Object.keys(PRESETS).map((name) => <option key={name}>{name}</option>)}
        </select>
      )}
      {mode === 'inventory' && (
        <>
          <select aria-label="Rodovia do inventário" value={road} onChange={(event) => setRoad(event.target.value)}>
            {roads.map((name) => <option key={name}>{name}</option>)}
          </select>
          <select aria-label="Bueiro do inventário" value={bueiroId} onChange={(event) => selectBueiro(event.target.value)}>
            {inventory.map((item) => (
              <option key={item.id} value={item.id}>{`km ${item.km.toFixed(3)} · ${item.regional} · #${item.id}`}</option>
            ))}
          </select>
          <div className="segmented-control" role="group" aria-label="Ponto do bueiro">
            <button type="button" className={point === 'montante' ? 'is-active' : ''} onClick={() => { setPoint('montante'); if (selectedBueiro) applyCoordinates({ lat: selectedBueiro.latitude_montante, lon: selectedBueiro.longitude_montante }) }}>Montante</button>
            <button type="button" className={point === 'jusante' ? 'is-active' : ''} onClick={() => { setPoint('jusante'); if (selectedBueiro) applyCoordinates({ lat: selectedBueiro.latitude_jusante, lon: selectedBueiro.longitude_jusante }) }}>Jusante</button>
          </div>
        </>
      )}
      {mode === 'sac' && (
        <>
          <input aria-label="Buscar endereço SAC" type="search" placeholder="Buscar por rua ou endereço" value={sacSearch} onChange={(event) => setSacSearch(event.target.value)} />
          <select aria-label="Local de chamado SAC" value={sacId} onChange={(event) => selectSac(event.target.value)}>
            {filteredSacLocations.map((item) => (
              <option key={item.id} value={item.id}>{`${item.logradouro}, ${item.numero} · ${item.total_solicitacoes} chamado(s)`}</option>
            ))}
          </select>
          <span className="location-search-count">{filteredSacLocations.length} de {sacLocations.length} locais</span>
        </>
      )}

      {(mode === 'custom' || mode === 'inventory' || mode === 'sac') && (
        <div className="coordinate-fields">
          <label>Latitude<input type="number" min="-90" max="90" step="0.0000001" value={coordinates.lat} onChange={(event) => applyCoordinates({ ...coordinates, lat: Number(event.target.value) })} /></label>
          <label>Longitude<input type="number" min="-180" max="180" step="0.0000001" value={coordinates.lon} onChange={(event) => applyCoordinates({ ...coordinates, lon: Number(event.target.value) })} /></label>
        </div>
      )}

      <div className="location-readout">
        <Crosshair size={15} />
        <span>{coordinates.lat.toFixed(5)}, {coordinates.lon.toFixed(5)}</span>
        {selectedBueiro && <span className="readout-context">{selectedBueiro.rodovia} · km {selectedBueiro.km.toFixed(3)}</span>}
        {selectedSac && <span className="readout-context">{selectedSac.logradouro}, {selectedSac.numero}</span>}
      </div>

      <button className="disclosure-button" type="button" aria-expanded={expanded} onClick={() => setExpanded((value) => !value)}>
        <Plus size={16} /> Cadastrar ponto <ChevronDown className={expanded ? 'rotated' : ''} size={15} />
      </button>
      {expanded && (
        <form className="bueiro-form" onSubmit={submitBueiro}>
          <label>Regional<input required maxLength={80} value={form.regional} onChange={(event) => updateForm('regional', event.target.value)} /></label>
          <label>Elemento
            <select value={form.elemento} onChange={(event) => updateForm('elemento', event.target.value)}>
              {['Bueiro', 'Boca de lobo', 'Poço de visita', 'Outro'].map((value) => <option key={value}>{value}</option>)}
            </select>
          </label>
          <label>Rodovia ou logradouro<input required maxLength={80} value={form.rodovia} onChange={(event) => updateForm('rodovia', event.target.value)} /></label>
          <div className="coordinate-fields">
            <label>Km / referência<input type="number" min="0" step="0.1" value={form.km} onChange={(event) => updateForm('km', Number(event.target.value))} /></label>
            <label>Data do levantamento<input required type="date" value={form.levantamento} onChange={(event) => updateForm('levantamento', event.target.value)} /></label>
          </div>
          <label>Tipo / material<input required maxLength={160} value={form.tipo} onChange={(event) => updateForm('tipo', event.target.value)} /></label>
          <div className="coordinate-fields">
            <label>Extensão (m)<input type="number" min="0" step="0.1" value={form.extensao_m} onChange={(event) => updateForm('extensao_m', event.target.value)} /></label>
            <label>Dimensão (m)<input type="number" min="0" step="0.1" value={form.dimensao_m} onChange={(event) => updateForm('dimensao_m', event.target.value)} /></label>
          </div>
          <label>Coordenadas de montante</label>
          <div className="coordinate-fields">
            <input aria-label="Latitude de montante" type="number" min="-90" max="90" step="0.0000001" value={form.latitude_montante} onChange={(event) => updateForm('latitude_montante', Number(event.target.value))} />
            <input aria-label="Longitude de montante" type="number" min="-180" max="180" step="0.0000001" value={form.longitude_montante} onChange={(event) => updateForm('longitude_montante', Number(event.target.value))} />
          </div>
          <label>Coordenadas de jusante</label>
          <div className="coordinate-fields">
            <input aria-label="Latitude de jusante" type="number" min="-90" max="90" step="0.0000001" value={form.latitude_jusante} onChange={(event) => updateForm('latitude_jusante', Number(event.target.value))} />
            <input aria-label="Longitude de jusante" type="number" min="-180" max="180" step="0.0000001" value={form.longitude_jusante} onChange={(event) => updateForm('longitude_jusante', Number(event.target.value))} />
          </div>
          <button className="button button-primary button-wide" type="submit" disabled={saving}>
            <Save size={15} /> {saving ? 'Salvando…' : 'Salvar no inventário'}
          </button>
        </form>
      )}
    </section>
  )
}