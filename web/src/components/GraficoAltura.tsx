import {
  ALTURA_CRITICA_CM,
  dataPrazoCurta,
  diaEpochDe,
  urgenciaPrazo,
  type Passagem,
  type Projecao,
} from "../mockData";
import { COR_URGENCIA } from "../theme/tokens";
import "./GraficoAltura.css";

interface GraficoAlturaProps {
  historico: Passagem[];
  projecao: Projecao;
}

const LARGURA = 340;
const ALTURA = 168;
const MARGEM_X = 26;
const MARGEM_TOPO = 22;
const MARGEM_BASE = 30;

// Até onde a projeção é desenhada. Pontos que só ficam críticos daqui a um ano
// esmagariam o histórico contra a lateral esquerda do gráfico.
const HORIZONTE_DIAS = 120;

function formatarDataCurta(dataIso: string): string {
  const [, mes, dia] = dataIso.split("-");
  return `${dia}/${mes}`;
}

export default function GraficoAltura({ historico, projecao }: GraficoAlturaProps) {
  const diaPrimeira = diaEpochDe(historico[0].data);
  const diaUltima = diaEpochDe(historico[historico.length - 1].data);
  const alturaUltima = historico[historico.length - 1].alturaCm;

  const diaCritico = projecao.dataCritica ? diaEpochDe(projecao.dataCritica) : null;
  const diaLimiteGrafico = diaUltima + HORIZONTE_DIAS;
  // Se o cruzamento cai depois do horizonte, a linha pontilhada só aponta a
  // direção — sem marcar uma data que ficaria ilegível.
  const cruzamentoVisivel = diaCritico !== null && diaCritico <= diaLimiteGrafico;
  const diaFim = cruzamentoVisivel ? diaCritico : diaCritico !== null ? diaLimiteGrafico : diaUltima;

  const alturaMaxima = Math.max(...historico.map((p) => p.alturaCm), ALTURA_CRITICA_CM);
  const topoEscala = alturaMaxima * 1.12;

  const larguraUtil = LARGURA - MARGEM_X * 2;
  const alturaUtil = ALTURA - MARGEM_TOPO - MARGEM_BASE;
  const spanDias = Math.max(1, diaFim - diaPrimeira);

  const x = (dia: number) => MARGEM_X + ((dia - diaPrimeira) / spanDias) * larguraUtil;
  const y = (altura: number) => MARGEM_TOPO + alturaUtil - (altura / topoEscala) * alturaUtil;

  const coordenadas = historico.map((passagem) => ({
    x: x(diaEpochDe(passagem.data)),
    y: y(passagem.alturaCm),
    passagem,
  }));

  // Altura que a reta de regressão alcança na borda direita, quando o
  // cruzamento fica fora do horizonte desenhado.
  const alturaNoFim = cruzamentoVisivel
    ? ALTURA_CRITICA_CM
    : alturaUltima +
      ((ALTURA_CRITICA_CM - alturaUltima) * (diaFim - diaUltima)) /
        Math.max(1, (diaCritico ?? diaFim) - diaUltima);

  const corProjecao = COR_URGENCIA[urgenciaPrazo(projecao)];
  const yLimite = y(ALTURA_CRITICA_CM);

  return (
    <div className="grafico-altura">
      <svg
        viewBox={`0 0 ${LARGURA} ${ALTURA}`}
        role="img"
        aria-label="Altura da vegetação nas passagens e projeção até o limite crítico"
      >
        <line
          x1={MARGEM_X}
          y1={MARGEM_TOPO + alturaUtil}
          x2={LARGURA - MARGEM_X}
          y2={MARGEM_TOPO + alturaUtil}
          className="grafico-altura__eixo"
        />

        <line
          x1={MARGEM_X}
          y1={yLimite}
          x2={LARGURA - MARGEM_X}
          y2={yLimite}
          className="grafico-altura__limite"
        />
        <text x={LARGURA - MARGEM_X} y={yLimite - 4} className="grafico-altura__limite-rotulo" textAnchor="end">
          limite {ALTURA_CRITICA_CM} cm
        </text>

        {diaCritico !== null && (
          <line
            x1={x(diaUltima)}
            y1={y(alturaUltima)}
            x2={x(diaFim)}
            y2={y(alturaNoFim)}
            className="grafico-altura__projecao"
            style={{ stroke: corProjecao }}
          />
        )}

        {cruzamentoVisivel && projecao.dataCritica && (
          <g>
            <circle cx={x(diaFim)} cy={yLimite} r={4.5} className="grafico-altura__alvo" style={{ fill: corProjecao }} />
            <text
              x={x(diaFim)}
              y={yLimite - 10}
              className="grafico-altura__alvo-rotulo"
              textAnchor="end"
              style={{ fill: corProjecao }}
            >
              {dataPrazoCurta(projecao)}
            </text>
          </g>
        )}

        <polyline points={coordenadas.map((c) => `${c.x},${c.y}`).join(" ")} className="grafico-altura__linha" />

        {coordenadas.map(({ x: cx, y: cy, passagem }) => (
          <g key={passagem.data}>
            <circle cx={cx} cy={cy} r={4} className="grafico-altura__ponto" />
            <text x={cx} y={cy - 10} className="grafico-altura__valor" textAnchor="middle">
              {passagem.alturaCm}
            </text>
            <text x={cx} y={ALTURA - 12} className="grafico-altura__data" textAnchor="middle">
              {formatarDataCurta(passagem.data)}
            </text>
          </g>
        ))}
      </svg>
      {!cruzamentoVisivel && projecao.dataCritica && (
        <p className="grafico-altura__nota">
          Cruza o limite só em {dataPrazoCurta(projecao)} — fora da janela do gráfico.
        </p>
      )}
    </div>
  );
}
