import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import type { PontoVegetacao } from "../mockData";
import MapaVegetacao from "./MapaVegetacao";
import ListaPontos from "./ListaPontos";
import PainelDetalhe from "./PainelDetalhe";
import "./SecaoMapa.css";
import { malhaMotiva } from "../malhaMotiva";
import { useClima } from "../hooks/useClima";
import { impactoNoCrescimento } from "../services/clima";

interface SecaoMapaProps {
  pontos: PontoVegetacao[];
  onGerarOrdem: (pontoId: string) => void;
}

function evidenciasDemonstrativas(concessao: typeof malhaMotiva[number], base: PontoVegetacao[]) {
  if (concessao.nome === "Motiva ViaOeste") return base;
  const deslocamentos = [[-.035,-.045],[-.018,-.016],[.004,.012],[.023,.036],[.042,.061]];
  return base.slice(0, 5).map((ponto, indice) => ({ ...ponto, id: `${concessao.nome}-${ponto.id}`, rodovia: concessao.rodovias.split(",")[0], latitude: concessao.centro[0] + deslocamentos[indice][0], longitude: concessao.centro[1] + deslocamentos[indice][1] }));
}

export default function SecaoMapa({ pontos, onGerarOrdem }: SecaoMapaProps) {
  const [parametros, definirParametros] = useSearchParams();
  const [pontoSelecionadoId, setPontoSelecionadoId] = useState<string | null>(null);
  const [concessaoSelecionada, setConcessaoSelecionada] = useState("Motiva ViaOeste");
  const concessao = malhaMotiva.find((item) => item.nome === concessaoSelecionada) ?? malhaMotiva[0];
  const rodoanelOficial = concessao.nome === "Motiva RodoAnel";

  // A visão geral chega aqui via /mapa?ponto=<id>. O parâmetro semeia a
  // seleção e sai da URL, para o botão voltar não reabrir o painel.
  useEffect(() => {
    const solicitado = parametros.get("ponto");
    if (!solicitado) return;
    if (pontos.some((ponto) => ponto.id === solicitado)) {
      setPontoSelecionadoId(solicitado);
    }
    definirParametros({}, { replace: true });
  }, [parametros, pontos, definirParametros]);

  const clima = useClima(concessao.centro[0], concessao.centro[1]);
  const evidenciasAtivas = evidenciasDemonstrativas(concessao, pontos);
  const pontoSelecionado = evidenciasAtivas.find((ponto) => ponto.id === pontoSelecionadoId) ?? null;
  const criticos = evidenciasAtivas.filter((ponto) => ponto.nivelRisco === "critico").length;
  const atencao = evidenciasAtivas.filter((ponto) => ponto.nivelRisco === "atencao").length;
  const tranquilos = evidenciasAtivas.filter((ponto) => ponto.nivelRisco === "tranquilo").length;

  return (
    <div className="secao-mapa__pagina">
      <header className="secao-mapa__cabecalho"><div><p>Inteligência territorial</p><h2>Mapa operacional</h2><span>Selecione uma concessão, consulte a malha e abra evidências do trecho.</span></div><div className="secao-mapa__acoes"><label><span>Concessão</span><select value={concessaoSelecionada} onChange={(e) => { setConcessaoSelecionada(e.target.value); setPontoSelecionadoId(null); }}>{malhaMotiva.map((item) => <option key={item.nome}>{item.nome}</option>)}</select></label><div className="secao-mapa__legenda"><b>{concessao.ufs}</b><small>{concessao.rodovias}{concessao.status === "detalhar" ? " · detalhe em atualização" : ""}</small></div></div></header>
      <section className="secao-mapa__faixa-alertas"><div><span>Rodovias da concessão</span><strong>{concessao.rodovias}</strong></div><div className="secao-mapa__clima">{rodoanelOficial ? <><b>Base oficial de roçada · SP-021</b><small>642 geometrias e 30 marcos km recebidos. Nível 3 (&gt;30 cm) caiu de 14,52% para 5,24% nos relatórios fornecidos.</small></> : clima.situacao === "pronto" ? <><b>{clima.clima.temperaturaC.toFixed(0)}°C · {clima.clima.condicao}</b><small>{clima.clima.chuva24hMm} mm nas últimas 24h · {impactoNoCrescimento(clima.clima).texto}</small></> : <><b>Clima local</b><small>{clima.situacao === "erro" ? "Indisponível no momento" : "Consultando condições atuais"}</small></>}</div><div className="secao-mapa__niveis">{rodoanelOficial ? <><span className="secao-mapa__oficial">camadas GIS oficiais</span><span className="secao-mapa__demo">ocorrências ainda demonstrativas</span></> : <><span className="nivel nivel--critico">{criticos} crítico{criticos === 1 ? "" : "s"}</span><span className="nivel nivel--atencao">{atencao} atenção</span><span className="nivel nivel--tranquilo">{tranquilos} tranquilo{tranquilos === 1 ? "" : "s"}</span><span className="secao-mapa__demo">dados demonstrativos</span></>}</div></section>
    <div className="secao-mapa">
      <section className="secao-mapa__mapa">
        <MapaVegetacao
          pontos={evidenciasAtivas}
          pontoSelecionadoId={pontoSelecionadoId}
          onSelecionar={setPontoSelecionadoId}
          foco={{ centro: concessao.centro, zoom: concessao.zoom, mostrarTrecho: concessao.nome === "Motiva ViaOeste", nome: concessao.nome, camadaRocadaOficial: rodoanelOficial }}
          camadaRocadaOficial={rodoanelOficial}
        />
      </section>
      <aside className="secao-mapa__lista">
        <ListaPontos
          pontos={evidenciasAtivas}
          pontoSelecionadoId={pontoSelecionadoId}
          onSelecionar={setPontoSelecionadoId}
        />
      </aside>

      {pontoSelecionado && (
        <PainelDetalhe
          ponto={pontoSelecionado}
          onFechar={() => setPontoSelecionadoId(null)}
          onGerarOrdem={() => {
            onGerarOrdem(pontoSelecionado.id);
            setPontoSelecionadoId(null);
          }}
        />
      )}
    </div>
    </div>
  );
}
