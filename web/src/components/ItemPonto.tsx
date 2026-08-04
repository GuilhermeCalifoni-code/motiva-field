import { crescimentoMensalCm, projecao, type PontoVegetacao } from "../mockData";
import SeloRisco from "./SeloRisco";
import SeloPrazo from "./SeloPrazo";
import "./ItemPonto.css";

interface ItemPontoProps {
  ponto: PontoVegetacao;
  selecionado: boolean;
  onSelecionar: (id: string) => void;
}

export default function ItemPonto({ ponto, selecionado, onSelecionar }: ItemPontoProps) {
  const crescimento = crescimentoMensalCm(ponto.historico);
  const previsao = projecao(ponto);

  return (
    <button
      type="button"
      className={`item-ponto${selecionado ? " item-ponto--selecionado" : ""}`}
      onClick={() => onSelecionar(ponto.id)}
    >
      <div className="item-ponto__topo">
        <span className="item-ponto__km">km {ponto.km.toFixed(2).replace(".", ",")}</span>
        <SeloRisco nivelRisco={ponto.nivelRisco} />
      </div>
      <div className="item-ponto__local">
        Sentido {ponto.sentido} · Margem {ponto.margem}
      </div>
      <div className="item-ponto__metricas">
        <span>
          <strong>{ponto.alturaAtualCm} cm</strong> altura atual
        </span>
        <span>
          <strong>+{crescimento.toFixed(1)} cm</strong> / mês
        </span>
      </div>
      <div className="item-ponto__prazo">
        <SeloPrazo projecao={previsao} comData />
      </div>
    </button>
  );
}
