import { useState, type FormEvent } from "react";
import {
  PRIORIDADE_LABEL,
  RISCO_LABEL,
  type Operador,
  type PontoVegetacao,
  type Prioridade,
} from "../mockData";
import "./ModalNovaOS.css";

interface ModalNovaOSProps {
  pontos: PontoVegetacao[];
  operadores: Operador[];
  onCriar: (pontoId: string, operadorId: string, prioridade: Prioridade) => void;
  onFechar: () => void;
}

const PRIORIDADES: Prioridade[] = ["alta", "media", "baixa"];

export default function ModalNovaOS({ pontos, operadores, onCriar, onFechar }: ModalNovaOSProps) {
  const [pontoId, setPontoId] = useState(pontos[0]?.id ?? "");
  const [operadorId, setOperadorId] = useState(operadores[0]?.id ?? "");
  const [prioridade, setPrioridade] = useState<Prioridade>("media");

  function enviar(evento: FormEvent) {
    evento.preventDefault();
    if (!pontoId || !operadorId) return;
    onCriar(pontoId, operadorId, prioridade);
  }

  return (
    <div className="modal-nova-os__fundo" onClick={onFechar}>
      <div
        className="modal-nova-os"
        role="dialog"
        aria-label="Nova ordem de serviço"
        onClick={(evento) => evento.stopPropagation()}
      >
        <div className="modal-nova-os__cabecalho">
          <h2>Nova ordem de serviço</h2>
          <button type="button" onClick={onFechar} aria-label="Fechar">
            ×
          </button>
        </div>

        <form className="modal-nova-os__form" onSubmit={enviar}>
          <label>
            Ponto
            <select value={pontoId} onChange={(evento) => setPontoId(evento.target.value)}>
              {pontos.map((ponto) => (
                <option key={ponto.id} value={ponto.id}>
                  km {ponto.km.toFixed(2).replace(".", ",")} · {ponto.sentido} ·{" "}
                  {RISCO_LABEL[ponto.nivelRisco]}
                </option>
              ))}
            </select>
          </label>

          <label>
            Operador
            <select value={operadorId} onChange={(evento) => setOperadorId(evento.target.value)}>
              {operadores.map((operador) => (
                <option key={operador.id} value={operador.id}>
                  {operador.nome}
                </option>
              ))}
            </select>
          </label>

          <label>
            Prioridade
            <select
              value={prioridade}
              onChange={(evento) => setPrioridade(evento.target.value as Prioridade)}
            >
              {PRIORIDADES.map((item) => (
                <option key={item} value={item}>
                  {PRIORIDADE_LABEL[item]}
                </option>
              ))}
            </select>
          </label>

          <div className="modal-nova-os__acoes">
            <button type="button" className="modal-nova-os__cancelar" onClick={onFechar}>
              Cancelar
            </button>
            <button type="submit" className="modal-nova-os__confirmar">
              Criar OS
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
