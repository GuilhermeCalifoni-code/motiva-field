// Geometria do eixo da rodovia. O traçado vem de db/rodovias/, que é a tabela
// rodovias.eixo nascendo — por isso não é copiado para dentro do web/.
//
// Nas distâncias deste trecho (~2 km) tratar lat/lon como plano, corrigindo a
// longitude pelo cosseno da latitude, erra menos que a precisão do traçado.

import eixoBruto from "@db/rodovias/sp270-trecho.geojson?raw";
import { RISCO_COR, type PontoVegetacao } from "../mockData";

export interface Coordenada {
  latitude: number;
  longitude: number;
}

interface GeoJsonEixo {
  features: {
    properties: Record<string, unknown>;
    geometry: { type: string; coordinates: [number, number][] };
  }[];
}

function lerEixo(): Coordenada[] {
  const geo: GeoJsonEixo = JSON.parse(eixoBruto);
  const linha = geo.features.find((feature) => feature.geometry.type === "LineString");
  if (!linha) throw new Error("sp270-trecho.geojson sem LineString");
  // GeoJSON guarda [longitude, latitude], nesta ordem.
  return linha.geometry.coordinates.map(([longitude, latitude]) => ({ latitude, longitude }));
}

export const eixoTrecho: Coordenada[] = lerEixo();

const M_POR_GRAU_LAT = 111320;

function metrosPorGrauLon(latitude: number): number {
  return M_POR_GRAU_LAT * Math.cos((latitude * Math.PI) / 180);
}

// Ponto do segmento a-b mais próximo de p, junto da distância em metros.
function projetarNoSegmento(
  p: Coordenada,
  a: Coordenada,
  b: Coordenada,
): { ponto: Coordenada; distanciaM: number } {
  const escalaLon = metrosPorGrauLon(p.latitude);
  const ax = a.longitude * escalaLon;
  const ay = a.latitude * M_POR_GRAU_LAT;
  const bx = b.longitude * escalaLon;
  const by = b.latitude * M_POR_GRAU_LAT;
  const px = p.longitude * escalaLon;
  const py = p.latitude * M_POR_GRAU_LAT;

  const dx = bx - ax;
  const dy = by - ay;
  const comprimento2 = dx * dx + dy * dy;
  const t = comprimento2 === 0 ? 0 : Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / comprimento2));

  const projX = ax + t * dx;
  const projY = ay + t * dy;

  return {
    ponto: { latitude: projY / M_POR_GRAU_LAT, longitude: projX / escalaLon },
    distanciaM: Math.hypot(px - projX, py - projY),
  };
}

// Projeção do ponto sobre o eixo — é aí que o marcador é ancorado, para que
// nenhum ponto fique flutuando ao lado da estrada.
export function ancorarNoEixo(p: Coordenada, linha: Coordenada[] = eixoTrecho): Coordenada {
  let melhor = { ponto: p, distanciaM: Infinity };
  for (let i = 0; i < linha.length - 1; i += 1) {
    const candidato = projetarNoSegmento(p, linha[i], linha[i + 1]);
    if (candidato.distanciaM < melhor.distanciaM) melhor = candidato;
  }
  return melhor.ponto;
}

function distanciaM(a: Coordenada, b: Coordenada): number {
  const escalaLon = metrosPorGrauLon(a.latitude);
  return Math.hypot(
    (b.longitude - a.longitude) * escalaLon,
    (b.latitude - a.latitude) * M_POR_GRAU_LAT,
  );
}

export interface SegmentoEixo {
  coordenadas: [Coordenada, Coordenada];
  cor: string;
  pontoId: string;
}

// Cada segmento herda a cor do ponto de vegetação mais próximo do seu meio.
// É o que faz a própria estrada mostrar onde estão os trechos quentes.
export function segmentosPorRisco(
  pontos: PontoVegetacao[],
  linha: Coordenada[] = eixoTrecho,
): SegmentoEixo[] {
  if (pontos.length === 0) return [];

  const segmentos: SegmentoEixo[] = [];
  for (let i = 0; i < linha.length - 1; i += 1) {
    const inicio = linha[i];
    const fim = linha[i + 1];
    const meio: Coordenada = {
      latitude: (inicio.latitude + fim.latitude) / 2,
      longitude: (inicio.longitude + fim.longitude) / 2,
    };

    let maisProximo = pontos[0];
    let menorDistancia = Infinity;
    for (const ponto of pontos) {
      const distancia = distanciaM(meio, ancorarNoEixo(ponto, linha));
      if (distancia < menorDistancia) {
        menorDistancia = distancia;
        maisProximo = ponto;
      }
    }

    segmentos.push({
      coordenadas: [inicio, fim],
      cor: RISCO_COR[maisProximo.nivelRisco],
      pontoId: maisProximo.id,
    });
  }
  return segmentos;
}
