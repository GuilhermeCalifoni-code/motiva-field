import type { ReactNode } from "react";
import "./CardResumo.css";

interface CardResumoProps {
  rotulo: string;
  valor: string;
  unidade?: string;
  detalhe?: ReactNode;
  // Selo curto no canto (ex.: chuva acelerando o crescimento).
  selo?: ReactNode;
}

// Card neutro da faixa de topo. Sem cor própria: o destaque vem do tamanho do
// número, não de pintura.
export default function CardResumo({ rotulo, valor, unidade, detalhe, selo }: CardResumoProps) {
  return (
    <section className="card-resumo">
      <div className="card-resumo__topo">
        <span className="rotulo">{rotulo}</span>
        {selo}
      </div>

      <div className="card-resumo__numero">
        <span className="card-resumo__valor">{valor}</span>
        {unidade && <span className="card-resumo__unidade">{unidade}</span>}
      </div>

      {detalhe && <p className="card-resumo__detalhe">{detalhe}</p>}
    </section>
  );
}
