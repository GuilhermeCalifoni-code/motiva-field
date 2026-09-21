import { useState } from "react";
import { FLUXO_STATUS, STATUS_LABEL, type OrdemServico, type Operador, type PontoVegetacao, type StatusOS } from "../mockData";
import CardOrdem from "./CardOrdem";
import "./ColunaKanban.css";

interface ColunaKanbanProps { status: StatusOS; ordens: OrdemServico[]; pontos: PontoVegetacao[]; operadores: Operador[]; agora: number; onMover: (id: string, status: StatusOS) => void; }

export default function ColunaKanban({ status, ordens, pontos, operadores, agora, onMover }: ColunaKanbanProps) {
  const [sobre, setSobre] = useState(false);
  function soltar(evento: React.DragEvent<HTMLDivElement>) {
    evento.preventDefault(); setSobre(false);
    const bruto = evento.dataTransfer.getData("application/motiva-os");
    if (!bruto) return;
    const ordem = JSON.parse(bruto) as { id: string; status: StatusOS };
    const origem = FLUXO_STATUS.indexOf(ordem.status), destino = FLUXO_STATUS.indexOf(status);
    if (Math.abs(destino - origem) !== 1) return;
    onMover(ordem.id, status);
  }
  return <section className={`coluna-kanban${sobre ? " coluna-kanban--sobre" : ""}`}>
    <header className="coluna-kanban__cabecalho"><h3>{STATUS_LABEL[status]}</h3><span className="coluna-kanban__contador">{ordens.length}</span></header>
    <div className="coluna-kanban__cards" onDragOver={(e) => { e.preventDefault(); setSobre(true); }} onDragLeave={() => setSobre(false)} onDrop={soltar}>
      {ordens.length === 0 && <p className="coluna-kanban__vazio">Arraste uma OS para esta etapa.</p>}
      {ordens.map((ordem) => <CardOrdem key={ordem.id} ordem={ordem} ponto={pontos.find((ponto) => ponto.id === ordem.pontoId)} operador={operadores.find((operador) => operador.id === ordem.operadorId)} agora={agora} />)}
    </div>
  </section>;
}
