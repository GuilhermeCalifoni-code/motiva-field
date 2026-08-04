import "./CardKpi.css";

interface CardKpiProps {
  rotulo: string;
  valor: string;
  detalhe?: string;
  cor?: string;
}

export default function CardKpi({ rotulo, valor, detalhe, cor }: CardKpiProps) {
  return (
    <div className="card-kpi">
      <span className="card-kpi__valor" style={cor ? { color: cor } : undefined}>
        {valor}
      </span>
      <span className="card-kpi__rotulo">{rotulo}</span>
      {detalhe && <span className="card-kpi__detalhe">{detalhe}</span>}
    </div>
  );
}
