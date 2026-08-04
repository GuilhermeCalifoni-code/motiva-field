import {
  URGENCIA_COR,
  rotuloDataPrazo,
  rotuloPrazo,
  urgenciaPrazo,
  type Projecao,
} from "../mockData";
import "./SeloPrazo.css";

interface SeloPrazoProps {
  projecao: Projecao;
  // Mostra também a data ("roçar até 12/08") abaixo do prazo em dias.
  comData?: boolean;
}

export default function SeloPrazo({ projecao, comData = false }: SeloPrazoProps) {
  const urgencia = urgenciaPrazo(projecao);
  const data = rotuloDataPrazo(projecao);

  return (
    <span className={`selo-prazo selo-prazo--${urgencia}`} style={{ color: URGENCIA_COR[urgencia] }}>
      <span className="selo-prazo__dias">{rotuloPrazo(projecao)}</span>
      {comData && data && <span className="selo-prazo__data">{data}</span>}
    </span>
  );
}
