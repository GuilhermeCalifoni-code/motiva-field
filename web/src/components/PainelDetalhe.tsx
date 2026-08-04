import { projecao, type PontoVegetacao } from "../mockData";
import SeloRisco from "./SeloRisco";
import SeloAlerta from "./SeloAlerta";
import SeloPrazo from "./SeloPrazo";
import GraficoAltura from "./GraficoAltura";
import "./PainelDetalhe.css";

interface PainelDetalheProps {
  ponto: PontoVegetacao;
  onFechar: () => void;
  onGerarOrdem: () => void;
}

export default function PainelDetalhe({ ponto, onFechar, onGerarOrdem }: PainelDetalheProps) {
  const previsao = projecao(ponto);

  return (
    <div className="painel-detalhe__fundo" onClick={onFechar}>
      <aside className="painel-detalhe" onClick={(evento) => evento.stopPropagation()}>
        <div className="painel-detalhe__cabecalho">
          <div>
            <h2>km {ponto.km.toFixed(2).replace(".", ",")}</h2>
            <p>{ponto.rodovia} · Sentido {ponto.sentido} · Margem {ponto.margem}</p>
          </div>
          <button type="button" className="painel-detalhe__fechar" onClick={onFechar} aria-label="Fechar">
            ×
          </button>
        </div>

        <div className="painel-detalhe__selos">
          <SeloRisco nivelRisco={ponto.nivelRisco} />
          {ponto.invadePista && <SeloAlerta texto="Invade a pista" />}
          {ponto.cobrePlaca && <SeloAlerta texto="Cobre placa" />}
        </div>

        <div className="painel-detalhe__metricas">
          <div>
            <span className="painel-detalhe__metrica-valor">{ponto.alturaAtualCm} cm</span>
            <span className="painel-detalhe__metrica-rotulo">altura atual</span>
          </div>
          <div>
            <span className="painel-detalhe__metrica-valor">+{previsao.taxaCmPorMes.toFixed(1)} cm</span>
            <span className="painel-detalhe__metrica-rotulo">projeção / mês</span>
          </div>
          <div>
            <SeloPrazo projecao={previsao} comData />
            <span className="painel-detalhe__metrica-rotulo">prazo estimado</span>
          </div>
        </div>

        <div className="painel-detalhe__grafico">
          <h3>Altura nas últimas {ponto.historico.length} passagens</h3>
          <GraficoAltura historico={ponto.historico} projecao={previsao} />
        </div>

        <button type="button" className="painel-detalhe__acao" onClick={onGerarOrdem}>
          Gerar ordem de serviço
        </button>
      </aside>
    </div>
  );
}
