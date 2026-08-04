import { useState } from "react";
import { ORDENACAO_LABEL, ordenarPontos, type OrdenacaoPontos, type PontoVegetacao } from "../mockData";
import ItemPonto from "./ItemPonto";
import "./ListaPontos.css";

interface ListaPontosProps {
  pontos: PontoVegetacao[];
  pontoSelecionadoId: string | null;
  onSelecionar: (id: string) => void;
}

const CRITERIOS: OrdenacaoPontos[] = ["risco", "prazo"];

export default function ListaPontos({ pontos, pontoSelecionadoId, onSelecionar }: ListaPontosProps) {
  const [criterio, setCriterio] = useState<OrdenacaoPontos>("risco");
  const pontosOrdenados = ordenarPontos(pontos, criterio);

  return (
    <div className="lista-pontos">
      <div className="lista-pontos__cabecalho">
        <h2>Pontos monitorados</h2>
        <span>{pontos.length} pontos</span>
        <div className="lista-pontos__ordenacao" role="group" aria-label="Ordenar por">
          {CRITERIOS.map((opcao) => (
            <button
              key={opcao}
              type="button"
              className={`lista-pontos__criterio${
                criterio === opcao ? " lista-pontos__criterio--ativo" : ""
              }`}
              aria-pressed={criterio === opcao}
              onClick={() => setCriterio(opcao)}
            >
              {ORDENACAO_LABEL[opcao]}
            </button>
          ))}
        </div>
      </div>
      <div className="lista-pontos__itens">
        {pontosOrdenados.map((ponto) => (
          <ItemPonto
            key={ponto.id}
            ponto={ponto}
            selecionado={ponto.id === pontoSelecionadoId}
            onSelecionar={onSelecionar}
          />
        ))}
      </div>
    </div>
  );
}
