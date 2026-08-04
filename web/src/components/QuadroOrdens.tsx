import { useState } from "react";
import {
  FLUXO_STATUS,
  type OrdemServico,
  type Operador,
  type PontoVegetacao,
  type Prioridade,
} from "../mockData";
import ColunaKanban from "./ColunaKanban";
import ModalNovaOS from "./ModalNovaOS";
import "./QuadroOrdens.css";

interface QuadroOrdensProps {
  ordens: OrdemServico[];
  pontos: PontoVegetacao[];
  operadores: Operador[];
  onCriar: (pontoId: string, operadorId: string, prioridade: Prioridade) => void;
  onAvancar: (id: string) => void;
}

export default function QuadroOrdens({
  ordens,
  pontos,
  operadores,
  onCriar,
  onAvancar,
}: QuadroOrdensProps) {
  const [modalAberto, setModalAberto] = useState(false);
  const agora = Date.now();

  return (
    <div className="quadro-ordens">
      <header className="quadro-ordens__cabecalho">
        <div>
          <h2>Ordens de serviço</h2>
          <span>{ordens.length} no total</span>
        </div>
        <button type="button" className="quadro-ordens__nova" onClick={() => setModalAberto(true)}>
          Nova OS
        </button>
      </header>

      <div className="quadro-ordens__colunas">
        {FLUXO_STATUS.map((status) => (
          <ColunaKanban
            key={status}
            status={status}
            ordens={ordens.filter((ordem) => ordem.status === status)}
            pontos={pontos}
            operadores={operadores}
            agora={agora}
            onAvancar={onAvancar}
          />
        ))}
      </div>

      {modalAberto && (
        <ModalNovaOS
          pontos={pontos}
          operadores={operadores}
          onCriar={(pontoId, operadorId, prioridade) => {
            onCriar(pontoId, operadorId, prioridade);
            setModalAberto(false);
          }}
          onFechar={() => setModalAberto(false)}
        />
      )}
    </div>
  );
}
