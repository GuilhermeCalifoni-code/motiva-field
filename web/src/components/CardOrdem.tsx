import { PRIORIDADE_LABEL, formatarDataHora, tempoEmAberto, type OrdemServico, type Operador, type PontoVegetacao } from "../mockData";
import { COR_PRIORIDADE } from "../theme/tokens";
import "./CardOrdem.css";

interface CardOrdemProps { ordem: OrdemServico; ponto: PontoVegetacao | undefined; operador: Operador | undefined; agora: number; }

export default function CardOrdem({ ordem, ponto, operador, agora }: CardOrdemProps) {
  return <article className="card-ordem" draggable onDragStart={(e) => { e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("application/motiva-os", JSON.stringify({ id: ordem.id, status: ordem.status })); }}>
    <div className="card-ordem__topo"><span className="card-ordem__ponto">{ponto ? `km ${ponto.km.toFixed(2).replace(".", ",")}` : "ponto removido"}</span><span className="card-ordem__prioridade" style={{ backgroundColor: COR_PRIORIDADE[ordem.prioridade] }}>{PRIORIDADE_LABEL[ordem.prioridade]}</span></div>
    <p className="card-ordem__sentido">{ponto ? `Sentido ${ponto.sentido}` : "—"}</p>
    <dl className="card-ordem__campos"><div><dt>Operador</dt><dd>{operador ? operador.nome : "não atribuído"}</dd></div><div><dt>Criada em</dt><dd>{formatarDataHora(ordem.criadaEm)}</dd></div><div><dt>{ordem.status === "concluida" ? "Tempo até concluir" : "Tempo em aberto"}</dt><dd>{tempoEmAberto(ordem, agora)}</dd></div></dl>
    <p className="card-ordem__arrastar">Arraste para a etapa anterior ou seguinte</p>
  </article>;
}
