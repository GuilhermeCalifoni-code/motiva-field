import {
  STATUS_LABEL,
  type OrdemServico,
  type Operador,
  type PontoVegetacao,
  type StatusOS,
} from "../mockData";
import CardOrdem from "./CardOrdem";
import "./ColunaKanban.css";

interface ColunaKanbanProps {
  status: StatusOS;
  ordens: OrdemServico[];
  pontos: PontoVegetacao[];
  operadores: Operador[];
  agora: number;
  onAvancar: (id: string) => void;
}

export default function ColunaKanban({
  status,
  ordens,
  pontos,
  operadores,
  agora,
  onAvancar,
}: ColunaKanbanProps) {
  return (
    <section className="coluna-kanban">
      <header className="coluna-kanban__cabecalho">
        <h3>{STATUS_LABEL[status]}</h3>
        <span className="coluna-kanban__contador">{ordens.length}</span>
      </header>

      <div className="coluna-kanban__cards">
        {ordens.length === 0 && <p className="coluna-kanban__vazio">Nenhuma OS aqui.</p>}
        {ordens.map((ordem) => (
          <CardOrdem
            key={ordem.id}
            ordem={ordem}
            ponto={pontos.find((ponto) => ponto.id === ordem.pontoId)}
            operador={operadores.find((operador) => operador.id === ordem.operadorId)}
            agora={agora}
            onAvancar={onAvancar}
          />
        ))}
      </div>
    </section>
  );
}
