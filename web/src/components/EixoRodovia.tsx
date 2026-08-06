import { Polyline } from "react-leaflet";
import type { PontoVegetacao } from "../mockData";
import { COR_MARCA } from "../theme/tokens";
import { eixoTrecho, segmentosPorRisco } from "../services/eixo";

interface EixoRodoviaProps {
  pontos: PontoVegetacao[];
}

// Duas camadas: o eixo roxo cheio marca a via; por cima, cada segmento ganha a
// cor do risco mais próximo, e é isso que mostra onde estão os trechos quentes.
export default function EixoRodovia({ pontos }: EixoRodoviaProps) {
  const tracado = eixoTrecho.map((coordenada) => [coordenada.latitude, coordenada.longitude] as [number, number]);
  const segmentos = segmentosPorRisco(pontos);

  return (
    <>
      <Polyline
        positions={tracado}
        pathOptions={{ color: COR_MARCA.roxo, weight: 9, opacity: 0.85, lineCap: "round", lineJoin: "round" }}
      />
      {segmentos.map((segmento, indice) => (
        <Polyline
          key={`${segmento.pontoId}-${indice}`}
          positions={segmento.coordenadas.map((c) => [c.latitude, c.longitude] as [number, number])}
          pathOptions={{
            color: segmento.cor,
            weight: 4,
            opacity: 0.95,
            lineCap: "butt",
          }}
        />
      ))}
    </>
  );
}
