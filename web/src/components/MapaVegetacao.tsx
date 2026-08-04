import { useEffect } from "react";
import { CircleMarker, MapContainer, TileLayer, Tooltip, useMap } from "react-leaflet";
import type { LatLngBoundsExpression } from "leaflet";
import { RISCO_COR, type PontoVegetacao } from "../mockData";
import "./MapaVegetacao.css";

interface MapaVegetacaoProps {
  pontos: PontoVegetacao[];
  pontoSelecionadoId: string | null;
  onSelecionar: (id: string) => void;
}

function AjustarLimites({ pontos }: { pontos: PontoVegetacao[] }) {
  const map = useMap();

  useEffect(() => {
    const limites: LatLngBoundsExpression = pontos.map((ponto) => [ponto.latitude, ponto.longitude]);
    map.fitBounds(limites, { padding: [40, 40] });
  }, [map, pontos]);

  return null;
}

export default function MapaVegetacao({ pontos, pontoSelecionadoId, onSelecionar }: MapaVegetacaoProps) {
  return (
    <MapContainer
      className="mapa-vegetacao"
      center={[pontos[0].latitude, pontos[0].longitude]}
      zoom={15}
      scrollWheelZoom
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <AjustarLimites pontos={pontos} />
      {pontos.map((ponto) => {
        const selecionado = ponto.id === pontoSelecionadoId;
        return (
          <CircleMarker
            key={ponto.id}
            center={[ponto.latitude, ponto.longitude]}
            radius={selecionado ? 13 : 10}
            pathOptions={{
              color: selecionado ? "#2e0854" : "#ffffff",
              weight: selecionado ? 3 : 2,
              fillColor: RISCO_COR[ponto.nivelRisco],
              fillOpacity: 0.9,
            }}
            eventHandlers={{ click: () => onSelecionar(ponto.id) }}
          >
            <Tooltip direction="top" offset={[0, -8]}>
              km {ponto.km.toFixed(2).replace(".", ",")} · {ponto.sentido}
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
