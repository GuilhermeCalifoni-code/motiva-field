import { useEffect, useState } from "react";
import { CircleMarker, GeoJSON, LayersControl, MapContainer, Polyline, TileLayer, Tooltip, useMap } from "react-leaflet";
import type { LatLngBoundsExpression } from "leaflet";
import type { Feature, GeoJsonObject } from "geojson";
import type { PontoVegetacao } from "../mockData";
import { COR_MARCA, COR_RISCO } from "../theme/tokens";
import { ancorarNoEixo, eixoTrecho } from "../services/eixo";
import EixoRodovia from "./EixoRodovia";
import "./MapaVegetacao.css";

interface MapaVegetacaoProps {
  pontos: PontoVegetacao[];
  pontoSelecionadoId: string | null;
  onSelecionar: (id: string) => void;
  foco?: { centro: [number, number]; zoom: number; mostrarTrecho: boolean; nome: string; camadaRocadaOficial?: boolean };
  camadaRocadaOficial?: boolean;
}

const CORES_ROCADA: Record<string, string> = {
  "Apenas manual": "#8b5cf6",
  "Spider, Giro-Zero ou Trator com trincheira": "#f59e0b",
  "Spider, com ancoragem": "#ef4444",
  "Trator com braço articulado": "#2563eb",
};

function corRocada(feature?: Feature) {
  return CORES_ROCADA[String(feature?.properties?.nome ?? "")] ?? "#64748b";
}

function CamadaRocadaOficial({ ativa }: { ativa: boolean }) {
  const [rocada, setRocada] = useState<GeoJsonObject | null>(null);
  const [marcos, setMarcos] = useState<GeoJsonObject | null>(null);

  useEffect(() => {
    if (!ativa || rocada) return;
    Promise.all([
      fetch("/dados-oficiais/classificacao-rocada-rodoanel.geojson").then((r) => r.json()),
      fetch("/dados-oficiais/marcos-km-rodoanel.geojson").then((r) => r.json()),
    ]).then(([camadaRocada, camadaMarcos]) => {
      setRocada(camadaRocada as GeoJsonObject);
      setMarcos(camadaMarcos as GeoJsonObject);
    }).catch(() => undefined);
  }, [ativa, rocada]);

  if (!ativa) return null;
  return <>
    {rocada && <LayersControl.Overlay checked name="Classificação de roçada · fonte oficial">
      <GeoJSON data={rocada} style={(feature) => ({ color: corRocada(feature), weight: 1, fillColor: corRocada(feature), fillOpacity: .34 })} />
    </LayersControl.Overlay>}
    {marcos && <LayersControl.Overlay checked name="Marcos quilométricos · fonte oficial">
      <GeoJSON data={marcos} />
    </LayersControl.Overlay>}
  </>;
}

function AjustarLimites({ foco }: { foco?: MapaVegetacaoProps["foco"] }) {
  const map = useMap();

  useEffect(() => {
    const limites: LatLngBoundsExpression = eixoTrecho.map((c) => [c.latitude, c.longitude]);
    const enquadrar = () => {
      map.invalidateSize();
      if (foco?.camadaRocadaOficial) map.setView([-23.52, -46.78], 11);
      else if (foco && !foco.mostrarTrecho) map.setView(foco.centro, foco.zoom);
      else map.fitBounds(limites, { padding: [48, 48] });
    };

    enquadrar();

    // O container só ganha largura depois do layout; sem reenquadrar aqui, o
    // zoom calculado no primeiro render fica errado.
    const observador = new ResizeObserver(enquadrar);
    observador.observe(map.getContainer());
    return () => observador.disconnect();
  }, [map, foco]);

  return null;
}

export default function MapaVegetacao({ pontos, pontoSelecionadoId, onSelecionar, foco, camadaRocadaOficial = false }: MapaVegetacaoProps) {
  return (
    <MapContainer
      className="mapa-vegetacao"
      center={[eixoTrecho[0].latitude, eixoTrecho[0].longitude]}
      zoom={15}
      scrollWheelZoom
    >
      <LayersControl position="topright">
        <LayersControl.BaseLayer checked name="Mapa operacional">
          <TileLayer attribution='&copy; OpenStreetMap &copy; CARTO' url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="Imagem de satélite">
          <TileLayer attribution="Tiles &copy; Esri" url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}" />
        </LayersControl.BaseLayer>
      </LayersControl>
      <AjustarLimites foco={foco} />
      <CamadaRocadaOficial ativa={camadaRocadaOficial} />
      {foco?.mostrarTrecho && <EixoRodovia pontos={pontos} />}
      {foco && !foco.mostrarTrecho && <Polyline positions={pontos.map((p) => [p.latitude, p.longitude] as [number, number])} pathOptions={{ color: "#5b1b8c", weight: 3, opacity: .75, dashArray: "7 8" }} />}

      {pontos.map((ponto) => {
        const selecionado = ponto.id === pontoSelecionadoId;
        // No trecho detalhado os pontos seguem o eixo calibrado; nas demais
        // malhas demonstrativas usamos a coordenada regional do próprio ponto.
        const ancora = foco?.mostrarTrecho ? ancorarNoEixo(ponto) : ponto;
        return (
          <CircleMarker
            key={ponto.id}
            center={[ancora.latitude, ancora.longitude]}
            radius={selecionado ? 11 : 8}
            pathOptions={{
              color: selecionado ? COR_MARCA.roxo : COR_MARCA.branco,
              weight: selecionado ? 3 : 2,
              fillColor: COR_RISCO[ponto.nivelRisco],
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
