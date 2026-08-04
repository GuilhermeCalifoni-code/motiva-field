import { RISCO_ORDEM, type PontoVegetacao } from "../mockData";
import ItemPonto from "./ItemPonto";
import "./ListaPontos.css";

interface ListaPontosProps {
  pontos: PontoVegetacao[];
  pontoSelecionadoId: string | null;
  onSelecionar: (id: string) => void;
}

export default function ListaPontos({ pontos, pontoSelecionadoId, onSelecionar }: ListaPontosProps) {
  const pontosOrdenados = [...pontos].sort(
    (a, b) => RISCO_ORDEM[b.nivelRisco] - RISCO_ORDEM[a.nivelRisco] || b.alturaAtualCm - a.alturaAtualCm,
  );

  return (
    <div className="lista-pontos">
      <div className="lista-pontos__cabecalho">
        <h2>Pontos monitorados</h2>
        <span>{pontos.length} pontos · risco decrescente</span>
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
