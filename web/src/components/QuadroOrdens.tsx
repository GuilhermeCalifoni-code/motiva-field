import { useState } from "react";
import {
  FLUXO_STATUS,
  type OrdemServico,
  type Operador,
  type PontoVegetacao,
  type Prioridade,
  type StatusOS,
} from "../mockData";
import ColunaKanban from "./ColunaKanban";
import ModalNovaOS from "./ModalNovaOS";
import "./QuadroOrdens.css";

interface QuadroOrdensProps {
  ordens: OrdemServico[];
  pontos: PontoVegetacao[];
  operadores: Operador[];
  onCriar: (pontoId: string, operadorId: string, prioridade: Prioridade) => void;
  onMover: (id: string, status: StatusOS) => void;
}

export default function QuadroOrdens({
  ordens,
  pontos,
  operadores,
  onCriar,
  onMover,
}: QuadroOrdensProps) {
  const [modalAberto, setModalAberto] = useState(false);
  const agora = Date.now();

  return (
    <div className="quadro-ordens">
      <header className="quadro-ordens__cabecalho">
        <div>
          <p className="quadro-ordens__eyebrow">Execução em campo</p>
          <h2>Ordens de serviço</h2>
          <span>{ordens.length} ordens no ciclo operacional</span>
        </div>
        <div className="quadro-ordens__acoes"><span className="quadro-ordens__resumo">{ordens.filter((ordem) => ordem.status === "no_local").length} equipes em campo</span><button type="button" className="quadro-ordens__nova" onClick={() => setModalAberto(true)}>+ Nova ordem</button></div>
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
            onMover={onMover}
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
