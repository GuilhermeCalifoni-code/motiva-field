import { useEffect } from "react";
import { CircleMarker, MapContainer, TileLayer, Tooltip, useMap } from "react-leaflet";
import type { LatLngBoundsExpression } from "leaflet";
import { RISCO_COR, type PontoVegetacao } from "../mockData";
import { ancorarNoEixo, eixoTrecho } from "../services/eixo";
import EixoRodovia from "./EixoRodovia";
import "./MapaVegetacao.css";

interface MapaVegetacaoProps {
  pontos: PontoVegetacao[];
  pontoSelecionadoId: string | null;
  onSelecionar: (id: string) => void;
}

function AjustarLimites() {
  const map = useMap();

  useEffect(() => {
    // Enquadra o eixo inteiro, não só os pontos.
    const limites: LatLngBoundsExpression = eixoTrecho.map((c) => [c.latitude, c.longitude]);
    const enquadrar = () => {
      map.invalidateSize();
      map.fitBounds(limites, { padding: [40, 40] });
    };

    enquadrar();

    // O container só ganha largura depois do layout; sem reenquadrar aqui, o
    // zoom calculado no primeiro render fica errado.
    const observador = new ResizeObserver(enquadrar);
    observador.observe(map.getContainer());
    return () => observador.disconnect();
  }, [map]);

  return null;
}

export default function MapaVegetacao({ pontos, pontoSelecionadoId, onSelecionar }: MapaVegetacaoProps) {
  return (
    <MapContainer
      className="mapa-vegetacao"
      center={[eixoTrecho[0].latitude, eixoTrecho[0].longitude]}
      zoom={15}
      scrollWheelZoom
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <AjustarLimites />
      <EixoRodovia pontos={pontos} />

      {pontos.map((ponto) => {
        const selecionado = ponto.id === pontoSelecionadoId;
        // O marcador senta na projeção do ponto sobre o eixo, para não flutuar
        // ao lado da estrada.
        const ancora = ancorarNoEixo(ponto);
        return (
          <CircleMarker
            key={ponto.id}
            center={[ancora.latitude, ancora.longitude]}
            radius={selecionado ? 11 : 8}
            pathOptions={{
              color: selecionado ? "#2e0854" : "#ffffff",
              weight: selecionado ? 3 : 2,
              fillColor: RISCO_COR[ponto.nivelRisco],
              fillOpacity: 1,
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
