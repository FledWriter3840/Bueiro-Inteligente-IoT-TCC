import { lazy, Suspense } from 'react'
import type { Coordinates } from './LocationControls'

const MapPanel = lazy(() => import('./MapPanel').then((module) => ({ default: module.MapPanel })))

export function LazyMapPanel({ coordinates }: { coordinates: Coordinates }) {
  return (
    <Suspense fallback={<div className="map-frame map-loading">Carregando mapa…</div>}>
      <MapPanel coordinates={coordinates} />
    </Suspense>
  )
}