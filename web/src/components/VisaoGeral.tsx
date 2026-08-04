import {
  PRAZO_ATENCAO_DIAS,
  RISCO_COR,
  URGENCIA_COR,
  centroDoTrecho,
  concluidasNosUltimosDias,
  contarPorRisco,
  crescimentoMedioTrechoCm,
  ordemEstaAberta,
  viramCriticosEm,
  type OrdemServico,
  type PontoVegetacao,
} from "../mockData";
import CardKpi from "./CardKpi";
import GraficoRiscos from "./GraficoRiscos";
import TabelaCrescimento from "./TabelaCrescimento";
import CardClima from "./CardClima";
import "./VisaoGeral.css";

interface VisaoGeralProps {
  pontos: PontoVegetacao[];
  ordens: OrdemServico[];
}

export default function VisaoGeral({ pontos, ordens }: VisaoGeralProps) {
  const agora = Date.now();
  const criticos = contarPorRisco(pontos, "critico");
  const emAtencao = contarPorRisco(pontos, "atencao");
  const abertas = ordens.filter(ordemEstaAberta).length;
  const concluidas30d = concluidasNosUltimosDias(ordens, 30, agora);
  const crescimentoMedio = crescimentoMedioTrechoCm(pontos);
  const viramCriticos = viramCriticosEm(pontos, PRAZO_ATENCAO_DIAS, agora);
  const centro = centroDoTrecho(pontos);

  return (
    <div className="visao-geral">
      <div className="visao-geral__kpis">
        <CardKpi
          rotulo="Pontos críticos"
          valor={String(criticos)}
          detalhe="roçada urgente"
          cor={RISCO_COR.critico}
        />
        <CardKpi
          rotulo="Pontos em atenção"
          valor={String(emAtencao)}
          detalhe="monitorar de perto"
          cor={RISCO_COR.atencao}
        />
        <CardKpi
          rotulo={`Viram críticos em ${PRAZO_ATENCAO_DIAS} dias`}
          valor={String(viramCriticos)}
          detalhe="pela projeção do histórico"
          cor={viramCriticos > 0 ? URGENCIA_COR.atencao : undefined}
        />
        <CardKpi rotulo="OS abertas" valor={String(abertas)} detalhe="em qualquer estágio" />
        <CardKpi
          rotulo="OS concluídas"
          valor={String(concluidas30d)}
          detalhe="últimos 30 dias"
        />
        <CardKpi
          rotulo="Crescimento médio"
          valor={`${crescimentoMedio.toFixed(1)} cm`}
          detalhe="por mês, no trecho"
        />
      </div>

      <div className="visao-geral__colunas">
        <section className="visao-geral__bloco">
          <h2>Pontos por nível de risco</h2>
          <GraficoRiscos pontos={pontos} />
        </section>

        <CardClima latitude={centro.latitude} longitude={centro.longitude} />
      </div>

      <section className="visao-geral__bloco">
        <h2>Maior crescimento mensal</h2>
        <TabelaCrescimento pontos={pontos} limite={5} />
      </section>
    </div>
  );
}
