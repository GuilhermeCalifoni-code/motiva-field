import {
  ordenarPontos,
  projecao,
  rotuloPrazo,
  urgenciaPrazo,
  type PontoVegetacao,
} from "../mockData";
import "./ListaAtuarAgora.css";

interface ListaAtuarAgoraProps {
  pontos: PontoVegetacao[];
  onAbrirNoMapa: (pontoId: string) => void;
}

// Fila de trabalho: o mais urgente no topo. Cada item leva direto ao ponto no
// mapa, que é onde o gestor decide o que fazer.
export default function ListaAtuarAgora({ pontos, onAbrirNoMapa }: ListaAtuarAgoraProps) {
  const ordenados = ordenarPontos(pontos, "prazo");

  return (
    <ol className="lista-atuar">
      {ordenados.map((ponto, indice) => {
        const previsao = projecao(ponto);
        const urgencia = urgenciaPrazo(previsao);

        return (
          <li key={ponto.id}>
            <button
              type="button"
              className={`lista-atuar__item lista-atuar__item--${urgencia}`}
              onClick={() => onAbrirNoMapa(ponto.id)}
            >
              <span className="lista-atuar__posicao">{indice + 1}</span>

              <span className="lista-atuar__corpo">
                <span className="lista-atuar__km">
                  km {ponto.km.toFixed(2).replace(".", ",")}
                </span>
                <span className="lista-atuar__local">
                  {ponto.sentido} · {ponto.alturaAtualCm} cm
                </span>
              </span>

              <span className="lista-atuar__prazo">{rotuloPrazo(previsao)}</span>
            </button>
          </li>
        );
      })}
    </ol>
  );
}
