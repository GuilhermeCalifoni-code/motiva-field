import {
  PRAZO_ATENCAO_DIAS,
  centroDoTrecho,
  chuvaAceleraCrescimento,
  contarPorRisco,
  contarPorStatus,
  crescimentoMedioTrechoCm,
  crescimentoMensalCm,
  dataPrazoCurta,
  ordemEstaAberta,
  proximaRocada,
  viramCriticosEm,
  type OrdemServico,
  type PontoVegetacao,
} from "../mockData";
import { useClima } from "../hooks/useClima";
import CardAcaoImediata from "./CardAcaoImediata";
import CardResumo from "./CardResumo";
import IndicadorAoVivo from "./IndicadorAoVivo";
import GraficoRiscos from "./GraficoRiscos";
import CartaoAcaoPonto from "./CartaoAcaoPonto";
import ListaAtuarAgora from "./ListaAtuarAgora";
import "./VisaoGeral.css";

interface VisaoGeralProps {
  pontos: PontoVegetacao[];
  ordens: OrdemServico[];
  onGerarOrdem: (pontoId: string) => void;
  onAbrirNoMapa: (pontoId: string) => void;
}

const TOP_CRESCIMENTO = 5;

export default function VisaoGeral({
  pontos,
  ordens,
  onGerarOrdem,
  onAbrirNoMapa,
}: VisaoGeralProps) {
  const agora = Date.now();
  const centro = centroDoTrecho(pontos);
  const clima = useClima(centro.latitude, centro.longitude);

  const criticos = contarPorRisco(pontos, "critico");
  const viramCriticos = viramCriticosEm(pontos, PRAZO_ATENCAO_DIAS, agora);
  const proxima = proximaRocada(pontos, agora);
  const abertas = ordens.filter(ordemEstaAberta).length;
  const noLocal = contarPorStatus(ordens, "no_local");
  const crescimentoMedio = crescimentoMedioTrechoCm(pontos);

  const chovendo =
    clima.situacao === "pronto" &&
    chuvaAceleraCrescimento(clima.clima.chuva24hMm, clima.clima.chuvaPrevista24hMm);

  const maioresCrescimentos = [...pontos]
    .sort((a, b) => crescimentoMensalCm(b.historico) - crescimentoMensalCm(a.historico))
    .slice(0, TOP_CRESCIMENTO);

  // O primeiro ponto da fila é o destino do botão do card vermelho.
  const maisUrgente = criticos > 0 || viramCriticos > 0 ? pontos : [];

  return (
    <div className="visao-geral">
      <header className="visao-geral__cabecalho">
        <div>
          <h1 className="visao-geral__titulo">Visão geral</h1>
          <p className="visao-geral__subtitulo">SP-270 · km 98 a 100 · {pontos.length} pontos monitorados</p>
        </div>
        <IndicadorAoVivo
          atualizadoEm={clima.situacao === "pronto" ? clima.carregadoEm : null}
        />
      </header>

      <section className="visao-geral__faixa">
        <CardAcaoImediata
          criticos={criticos}
          viramCriticos={viramCriticos}
          janelaDias={PRAZO_ATENCAO_DIAS}
          onVerPontos={() => {
            const alvo = maisUrgente[0];
            if (alvo) onAbrirNoMapa(alvo.id);
          }}
        />

        <div className="visao-geral__resumos">
          <CardResumo
            rotulo="Próxima roçada"
            valor={proxima ? (dataPrazoCurta(proxima.previsao, agora) ?? "—") : "—"}
            detalhe={
              proxima ? (
                <>
                  km {proxima.ponto.km.toFixed(2).replace(".", ",")} · em{" "}
                  {proxima.previsao.diasRestantes} dias
                </>
              ) : (
                <>Nenhum ponto com prazo aberto.</>
              )
            }
          />

          <CardResumo
            rotulo="Frentes ativas"
            valor={String(abertas)}
            unidade={abertas === 1 ? "OS aberta" : "OS abertas"}
            detalhe={
              <>
                {noLocal} {noLocal === 1 ? "equipe" : "equipes"} no local agora
              </>
            }
          />

          <CardResumo
            rotulo="Crescimento médio"
            valor={crescimentoMedio.toFixed(1)}
            unidade="cm/mês"
            selo={chovendo ? <span className="visao-geral__selo-chuva">chuva</span> : undefined}
            detalhe={
              clima.situacao === "erro" ? (
                <>Clima indisponível agora.</>
              ) : chovendo ? (
                <>Chuva no trecho — tende a acelerar.</>
              ) : (
                <>No trecho inteiro.</>
              )
            }
          />
        </div>
      </section>

      <div className="visao-geral__colunas">
        <div className="visao-geral__coluna-principal">
          <section className="visao-geral__bloco">
            <h2 className="rotulo visao-geral__bloco-titulo">Pontos por nível de risco</h2>
            <GraficoRiscos pontos={pontos} />
          </section>

          <section className="visao-geral__bloco">
            <h2 className="rotulo visao-geral__bloco-titulo">Maior crescimento mensal</h2>
            <div className="visao-geral__cartoes">
              {maioresCrescimentos.map((ponto) => (
                <CartaoAcaoPonto
                  key={ponto.id}
                  ponto={ponto}
                  onGerarOrdem={onGerarOrdem}
                  onAbrirNoMapa={onAbrirNoMapa}
                />
              ))}
            </div>
          </section>
        </div>

        <aside className="visao-geral__bloco visao-geral__coluna-lateral">
          <h2 className="rotulo visao-geral__bloco-titulo">Atuar agora</h2>
          <p className="visao-geral__ajuda">Ordenado por dias até o limite crítico.</p>
          <ListaAtuarAgora pontos={pontos} onAbrirNoMapa={onAbrirNoMapa} />
        </aside>
      </div>
    </div>
  );
}
