import { centroDoTrecho, crescimentoMensalCm, ordemEstaAberta, projecao, RISCO_LABEL, RISCO_ORDEM, type OrdemServico, type PontoVegetacao } from "../mockData";
import { useClima } from "../hooks/useClima";
import { impactoNoCrescimento } from "../services/clima";
import MapaVegetacao from "./MapaVegetacao";
import "./VisaoGeral.css";

interface VisaoGeralProps { pontos: PontoVegetacao[]; ordens: OrdemServico[]; onGerarOrdem: (pontoId: string) => void; onAbrirNoMapa: (pontoId: string) => void; }

export default function VisaoGeral({ pontos, ordens, onGerarOrdem, onAbrirNoMapa }: VisaoGeralProps) {
  const centro = centroDoTrecho(pontos);
  const clima = useClima(centro.latitude, centro.longitude);
  const fila = [...pontos].sort((a,b) => RISCO_ORDEM[b.nivelRisco] - RISCO_ORDEM[a.nivelRisco] || (projecao(a).diasRestantes ?? 999) - (projecao(b).diasRestantes ?? 999)).slice(0,5);
  const criticos = pontos.filter((p) => p.nivelRisco === "critico");
  const abertas = ordens.filter(ordemEstaAberta).length;
  const emCampo = ordens.filter((o) => o.status === "no_local").length;
  const prioridade = fila[0];
  const climaPronto = clima.situacao === "pronto" ? clima.clima : null;

  return <div className="painel-decisao">
    <header className="painel-decisao__cabecalho"><div><p>Centro de decisão</p><h1>Operação do trecho</h1><span>SP-270 · km 98 a 100 · atualização operacional em tempo real</span></div><div className="painel-decisao__status"><i />Monitoramento ativo</div></header>
    <section className="painel-decisao__metricas"><article><span>Prioridades críticas</span><strong>{criticos.length}</strong><small>{criticos.length ? "exigem tratativa" : "sem atraso no trecho"}</small></article><article><span>Ordens no ciclo</span><strong>{abertas}</strong><small>{emCampo} equipe{emCampo === 1 ? "" : "s"} em campo</small></article><article><span>Clima no trecho</span><strong>{climaPronto ? `${climaPronto.temperaturaC.toFixed(0)}°` : "—"}</strong><small>{climaPronto ? climaPronto.condicao : "consultando condição atual"}</small></article></section>
    <section className="painel-decisao__prioridade"><div><span>Decisão recomendada</span><h2>{prioridade ? `${RISCO_LABEL[prioridade.nivelRisco]} no km ${prioridade.km.toFixed(2).replace(".", ",")}` : "Nenhuma prioridade aberta"}</h2><p>{prioridade ? `Vegetação em ${prioridade.alturaAtualCm.toFixed(0)} cm; crescimento de ${crescimentoMensalCm(prioridade.historico).toFixed(1)} cm/mês.` : "O trecho está dentro dos limites operacionais."}</p></div>{prioridade && <div className="painel-decisao__prioridade-acoes"><button onClick={() => onAbrirNoMapa(prioridade.id)}>Ver no mapa</button><button className="primario" onClick={() => onGerarOrdem(prioridade.id)}>Gerar ordem</button></div>}</section>
    <div className="painel-decisao__grade"><section className="painel-decisao__fila"><header><div><p>Fila operacional</p><h2>Onde atuar primeiro</h2></div><button onClick={() => prioridade && onAbrirNoMapa(prioridade.id)}>Abrir mapa</button></header><div className="painel-decisao__tabela"><div className="linha linha--titulo"><span>Trecho</span><span>Risco</span><span>Crescimento</span><span>Prazo</span><span /></div>{fila.map((ponto) => { const prazo = projecao(ponto).diasRestantes; return <div className="linha" key={ponto.id}><button onClick={() => onAbrirNoMapa(ponto.id)}>km {ponto.km.toFixed(2).replace(".", ",")}</button><span className={`risco risco--${ponto.nivelRisco}`}>{RISCO_LABEL[ponto.nivelRisco]}</span><span>+{crescimentoMensalCm(ponto.historico).toFixed(1)} cm/mês</span><span>{prazo === 0 ? "Vencido" : prazo === null ? "Sem previsão" : `${prazo} dias`}</span><button className="acao" onClick={() => onGerarOrdem(ponto.id)}>OS</button></div>;})}</div></section>
      <aside className="painel-decisao__lateral"><section className="painel-decisao__clima"><p>Clima e crescimento</p><h2>{climaPronto ? `${climaPronto.temperaturaC.toFixed(0)}°C · ${climaPronto.condicao}` : "Consultando clima"}</h2><span>{climaPronto ? `${climaPronto.chuva24hMm} mm nas últimas 24h` : "Aguardando fonte meteorológica"}</span><strong>{climaPronto ? impactoNoCrescimento(climaPronto).texto : "O impacto será exibido quando o clima carregar."}</strong></section><section className="painel-decisao__mapa"><header><span>Mapa-resumo</span><button onClick={() => prioridade && onAbrirNoMapa(prioridade.id)}>Expandir</button></header><MapaVegetacao pontos={pontos} pontoSelecionadoId={null} onSelecionar={onAbrirNoMapa} foco={{ centro:[centro.latitude, centro.longitude], zoom:14, mostrarTrecho:true, nome:"Motiva ViaOeste" }} /></section></aside></div>
  </div>;
}
