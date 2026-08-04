import type { Passagem } from "../mockData";
import "./GraficoAltura.css";

interface GraficoAlturaProps {
  historico: Passagem[];
}

const LARGURA = 320;
const ALTURA = 140;
const MARGEM = 24;

function formatarDataCurta(dataIso: string): string {
  const [, mes, dia] = dataIso.split("-");
  return `${dia}/${mes}`;
}

export default function GraficoAltura({ historico }: GraficoAlturaProps) {
  const alturas = historico.map((p) => p.alturaCm);
  const min = 0;
  const max = Math.max(...alturas) * 1.15;

  const largarUtil = LARGURA - MARGEM * 2;
  const alturaUtil = ALTURA - MARGEM * 2;

  const coordenadas = historico.map((passagem, indice) => {
    const x = MARGEM + (indice / (historico.length - 1)) * largarUtil;
    const y = MARGEM + alturaUtil - ((passagem.alturaCm - min) / (max - min)) * alturaUtil;
    return { x, y, passagem };
  });

  const pontosLinha = coordenadas.map((c) => `${c.x},${c.y}`).join(" ");

  return (
    <div className="grafico-altura">
      <svg viewBox={`0 0 ${LARGURA} ${ALTURA}`} role="img" aria-label="Altura da vegetação ao longo das passagens">
        <line
          x1={MARGEM}
          y1={MARGEM + alturaUtil}
          x2={LARGURA - MARGEM}
          y2={MARGEM + alturaUtil}
          className="grafico-altura__eixo"
        />
        <polyline points={pontosLinha} className="grafico-altura__linha" />
        {coordenadas.map(({ x, y, passagem }) => (
          <g key={passagem.data}>
            <circle cx={x} cy={y} r={4} className="grafico-altura__ponto" />
            <text x={x} y={y - 10} className="grafico-altura__valor" textAnchor="middle">
              {passagem.alturaCm}
            </text>
            <text x={x} y={ALTURA - 6} className="grafico-altura__data" textAnchor="middle">
              {formatarDataCurta(passagem.data)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
