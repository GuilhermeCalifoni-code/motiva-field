import { crescimentoMensalCm, projecao, type PontoVegetacao } from "../mockData";
import SeloPrazo from "./SeloPrazo";
import "./CartaoAcaoPonto.css";

interface CartaoAcaoPontoProps {
  ponto: PontoVegetacao;
  onGerarOrdem: (pontoId: string) => void;
  onAbrirNoMapa: (pontoId: string) => void;
}

// Substitui a tabela de crescimento: cada linha vira um cartão com a ação
// disponível ali mesmo, sem o gestor precisar procurar onde clicar.
export default function CartaoAcaoPonto({
  ponto,
  onGerarOrdem,
  onAbrirNoMapa,
}: CartaoAcaoPontoProps) {
  const previsao = projecao(ponto);
  const crescimento = crescimentoMensalCm(ponto.historico);

  return (
    <article className="cartao-acao">
      <button
        type="button"
        className="cartao-acao__identidade"
        onClick={() => onAbrirNoMapa(ponto.id)}
        title="Abrir este ponto no mapa"
      >
        <span className="cartao-acao__km">km {ponto.km.toFixed(2).replace(".", ",")}</span>
        <span className="cartao-acao__local">
          {ponto.sentido} · margem {ponto.margem}
        </span>
      </button>

      <div className="cartao-acao__medida">
        <span className="cartao-acao__crescimento">+{crescimento.toFixed(1)}</span>
        <span className="rotulo cartao-acao__medida-rotulo">cm/mês</span>
      </div>

      <div className="cartao-acao__prazo">
        <SeloPrazo projecao={previsao} comData />
      </div>

      <button
        type="button"
        className="cartao-acao__gerar"
        onClick={() => onGerarOrdem(ponto.id)}
      >
        Gerar OS
      </button>
    </article>
  );
}
