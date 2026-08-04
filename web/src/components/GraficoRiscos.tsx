import { RISCO_COR, RISCO_LABEL, contarPorRisco, type NivelRisco, type PontoVegetacao } from "../mockData";
import "./GraficoRiscos.css";

interface GraficoRiscosProps {
  pontos: PontoVegetacao[];
}

const NIVEIS: NivelRisco[] = ["critico", "atencao", "tranquilo"];

export default function GraficoRiscos({ pontos }: GraficoRiscosProps) {
  const contagens = NIVEIS.map((nivel) => ({
    nivel,
    total: contarPorRisco(pontos, nivel),
  }));
  const maior = Math.max(...contagens.map((item) => item.total), 1);

  return (
    <div className="grafico-riscos">
      {contagens.map(({ nivel, total }) => (
        <div key={nivel} className="grafico-riscos__linha">
          <span className="grafico-riscos__rotulo">{RISCO_LABEL[nivel]}</span>
          <div className="grafico-riscos__trilho">
            <div
              className="grafico-riscos__barra"
              style={{ width: `${(total / maior) * 100}%`, backgroundColor: RISCO_COR[nivel] }}
            />
          </div>
          <span className="grafico-riscos__total">{total}</span>
        </div>
      ))}
    </div>
  );
}
