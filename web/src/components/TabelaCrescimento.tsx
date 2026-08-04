import { crescimentoMensalCm, projecao, type PontoVegetacao } from "../mockData";
import SeloRisco from "./SeloRisco";
import SeloPrazo from "./SeloPrazo";
import "./TabelaCrescimento.css";

interface TabelaCrescimentoProps {
  pontos: PontoVegetacao[];
  limite: number;
}

export default function TabelaCrescimento({ pontos, limite }: TabelaCrescimentoProps) {
  const maiores = [...pontos]
    .sort((a, b) => crescimentoMensalCm(b.historico) - crescimentoMensalCm(a.historico))
    .slice(0, limite);

  return (
    <table className="tabela-crescimento">
      <thead>
        <tr>
          <th>km</th>
          <th>Sentido</th>
          <th>Margem</th>
          <th>Altura</th>
          <th>Crescimento</th>
          <th>Prazo</th>
          <th>Risco</th>
        </tr>
      </thead>
      <tbody>
        {maiores.map((ponto) => (
          <tr key={ponto.id}>
            <td className="tabela-crescimento__km">{ponto.km.toFixed(2).replace(".", ",")}</td>
            <td>{ponto.sentido}</td>
            <td>{ponto.margem}</td>
            <td>{ponto.alturaAtualCm} cm</td>
            <td className="tabela-crescimento__destaque">
              +{crescimentoMensalCm(ponto.historico).toFixed(1)} cm/mês
            </td>
            <td>
              <SeloPrazo projecao={projecao(ponto)} comData />
            </td>
            <td>
              <SeloRisco nivelRisco={ponto.nivelRisco} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
