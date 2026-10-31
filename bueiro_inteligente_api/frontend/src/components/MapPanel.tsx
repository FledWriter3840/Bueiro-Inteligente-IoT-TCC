import { useEffect, useState, type CSSProperties } from 'react'
import { Circle, CircleMarker, MapContainer, Popup, TileLayer, useMap, ZoomControl } from 'react-leaflet'
import { apiRequest } from '../api'
import type { Bueiro, Prediction, RiskLevel, SacSearch } from '../types'
import type { Coordinates } from './LocationControls'

type Props = { coordinates: Coordinates }

function MapRecenter({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap()
  useEffect(() => { map.setView(center, zoom) }, [center, map, zoom])
  return null
}

export function MapPanel({ coordinates }: Props) {
  const [roads, setRoads] = useState<string[]>([])
  const [road, setRoad] = useState('')
  const [bueiros, setBueiros] = useState<Bueiro[]>([])
  const [sac, setSac] = useState<SacSearch | null>(null)
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [radius, setRadius] = useState(500)
  const [error, setError] = useState('')

  useEffect(() => {
    let current = true
    void apiRequest<Prediction>('/ia/previsao', {
      params: { id_sensor: 1, lat: coordinates.lat, lon: coordinates.lon },
      timeoutMs: 120000,
    }).then((result) => {
      if (current) {
        setPrediction(result)
        setError('')
      }
    }).catch((reason) => {
      if (current) {
        setPrediction(null)
        setError(reason instanceof Error ? reason.message : 'Falha ao consultar previsão de entupimento.')
      }
    })
    return () => { current = false }
  }, [coordinates.lat, coordinates.lon])

  useEffect(() => {
    void apiRequest<string[]>('/bueiros/rodovias').then((data) => {
      setRoads(data)
      setRoad((current) => current || data[0] || '')
    }).catch((reason) => setError(reason instanceof Error ? reason.message : 'Falha ao consultar o inventário.'))
  }, [])

  useEffect(() => {
    if (!road) return
    void apiRequest<Bueiro[]>('/bueiros/', { params: { rodovia: road } }).then(setBueiros)
      .catch((reason) => setError(reason instanceof Error ? reason.message : 'Falha ao consultar bueiros.'))
  }, [road])

  useEffect(() => {
    let current = true
    void apiRequest<SacSearch>('/bueiros/solicitacoes-limpeza', {
      params: { lat: coordinates.lat, lon: coordinates.lon, raio_m: radius },
    }).then((result) => {
      if (current) {
        setSac(result)
        setError('')
      }
    }).catch((reason) => {
      if (current) setError(reason instanceof Error ? reason.message : 'Falha ao consultar chamados SAC.')
    })
    return () => { current = false }
  }, [coordinates.lat, coordinates.lon, radius])

  const mapCenter: [number, number] = [coordinates.lat, coordinates.lon]
  const zoom = radius <= 500 ? 14 : radius <= 1500 ? 12 : 10
  const riskColors: Record<RiskLevel, string> = {
    Baixo: '#2f8a63',
    'Médio': '#d2a321',
    Alto: '#e77832',
    'Crítico': '#c43d3d',
  }
  const riskColor = prediction ? riskColors[prediction.nivel_risco] : undefined

  return (
    <div className="map-workspace">
      <div className="map-toolbar">
        <label className="field-inline">Rodovia do inventário
          <select value={road} onChange={(event) => setRoad(event.target.value)}>
            {roads.map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
        <label className="field-inline">Raio SAC <strong>{radius.toLocaleString('pt-BR')} m</strong>
          <input type="range" min="100" max="5000" step="100" value={radius} onChange={(event) => setRadius(Number(event.target.value))} />
        </label>
      </div>
      {error && <div className="inline-error" role="alert">{error}</div>}
      <div className="map-frame">
        <MapContainer center={mapCenter} zoom={zoom} scrollWheelZoom zoomControl={false}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapRecenter center={mapCenter} zoom={zoom} />
          <ZoomControl position="bottomright" />
          {prediction && riskColor && (
            <Circle
              center={mapCenter}
              radius={radius}
              pathOptions={{ color: riskColor, fillColor: riskColor, fillOpacity: 0.13, opacity: 0.9, weight: 3 }}
            >
              <Popup>
                Região analisada · risco {prediction.nivel_risco}<br />
                Probabilidade de entupimento: {(prediction.probabilidade_entupimento * 100).toFixed(0)}%
              </Popup>
            </Circle>
          )}
          <CircleMarker center={mapCenter} radius={8} pathOptions={{ color: '#a74631', fillColor: '#d27655', fillOpacity: 0.95, weight: 3 }}>
            <Popup>
              Local analisado · {coordinates.lat.toFixed(5)}, {coordinates.lon.toFixed(5)}
              {prediction && <><br />Risco {prediction.nivel_risco} · {(prediction.probabilidade_entupimento * 100).toFixed(0)}%</>}
            </Popup>
          </CircleMarker>
          {bueiros.flatMap((bueiro) => ([
            <CircleMarker key={`${bueiro.id}-montante`} center={[bueiro.latitude_montante, bueiro.longitude_montante]} radius={5} pathOptions={{ color: '#176f68', fillColor: '#49a99b', fillOpacity: 0.9, weight: 2 }}>
              <Popup>{bueiro.rodovia} · km {bueiro.km.toFixed(3)}<br />Montante · {bueiro.tipo}</Popup>
            </CircleMarker>,
            <CircleMarker key={`${bueiro.id}-jusante`} center={[bueiro.latitude_jusante, bueiro.longitude_jusante]} radius={5} pathOptions={{ color: '#176f68', fillColor: '#86c8b9', fillOpacity: 0.9, weight: 2 }}>
              <Popup>{bueiro.rodovia} · km {bueiro.km.toFixed(3)}<br />Jusante · {bueiro.tipo}</Popup>
            </CircleMarker>,
          ]))}
          {(sac?.solicitacoes ?? []).map((request) => (
            <CircleMarker
              key={`sac-${request.id}`}
              center={[request.latitude, request.longitude]}
              radius={request.situacao === 'FINALIZADA' ? 5 : 6}
              pathOptions={{ color: request.situacao === 'FINALIZADA' ? '#397d9d' : '#c89732', fillOpacity: 0.8, weight: 2 }}
            >
              <Popup>{request.logradouro}, {request.numero}<br />{request.situacao}<br />{request.distancia_m} m</Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
      <div className="map-legend" aria-label="Legenda do mapa">
        <span><i className="legend-dot location-dot" /> Local analisado</span>
        <span><i className="legend-dot inventory-dot" /> Inventário</span>
        <span><i className="legend-dot sac-dot" /> Chamados SAC</span>
        <span><i className="legend-dot risk-low" /> Baixo</span>
        <span><i className="legend-dot risk-medium" /> Médio</span>
        <span><i className="legend-dot risk-high" /> Alto</span>
        <span><i className="legend-dot risk-critical" /> Crítico</span>
      </div>
      <div className="risk-region-summary" style={{ '--region-color': riskColor ?? '#8a958e' } as CSSProperties}>
        <span className="risk-region-indicator" />
        <div>
          <strong>{prediction ? `Região analisada · risco ${prediction.nivel_risco}` : 'Previsão de entupimento indisponível'}</strong>
          <span>{prediction
            ? `Probabilidade de entupimento: ${(prediction.probabilidade_entupimento * 100).toFixed(0)}% · Área delimitada pelo raio SAC de ${radius.toLocaleString('pt-BR')} m.`
            : 'Não foi possível gerar o contorno de risco para este local.'}</span>
        </div>
      </div>
      <div className="map-summary-grid">
        <div><span>Estruturas na rodovia</span><strong>{bueiros.length}</strong></div>
        <div><span>Chamados próximos</span><strong>{sac?.total_encontradas ?? '—'}</strong></div>
        <div><span>Finalizados no SAC</span><strong>{sac?.total_finalizadas ?? '—'}</strong></div>
        <div><span>Cancelados no SAC</span><strong>{sac?.total_canceladas ?? '—'}</strong></div>
      </div>
      <div className="sac-history-summary">
        <div><span className="eyebrow">RECORRÊNCIA NO SAC</span><strong>{sac?.indice_constancia_chamados == null ? 'Dados insuficientes' : `${sac.indice_constancia_chamados.toFixed(0)}/100`}</strong></div>
        <p>{sac?.intervalo_medio_dias == null
          ? 'São necessários ao menos três chamados finalizados com data de parecer para calcular a regularidade.'
          : `Intervalo médio entre pareceres finalizados: ${sac.intervalo_medio_dias.toFixed(1)} dias. Período: ${sac.periodo_inicio?.slice(0, 10) ?? '—'} a ${sac.periodo_fim?.slice(0, 10) ?? '—'}.`}</p>
      </div>
      {sac?.solicitacoes.length ? (
        <div className="panel sac-requests-panel">
          <div className="panel-heading"><div><span className="eyebrow">ATÉ 20 MAIS PRÓXIMOS</span><h2>Solicitações georreferenciadas</h2></div><span className="count-badge">{sac.solicitacoes.length}</span></div>
          <div className="table-scroll"><table><thead><tr><th>Chamado</th><th>Endereço</th><th>Situação</th><th>Data do parecer</th><th>Distância</th></tr></thead><tbody>
            {sac.solicitacoes.slice(0, 20).map((request) => <tr key={request.id}><td>#{request.id}</td><td>{request.logradouro}{request.numero ? `, ${request.numero}` : ''}</td><td>{request.situacao}</td><td>{request.data_parecer || '—'}</td><td>{request.distancia_m.toFixed(1)} m</td></tr>)}
          </tbody></table></div>
        </div>
      ) : null}
      <p className="map-disclaimer">Fonte: sac_limpeza_bueiro.csv (2020–2021). FINALIZADA indica encerramento da solicitação no SAC, não comprova isoladamente a execução da limpeza.</p>
    </div>
  )
}