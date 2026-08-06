import { rotuloDataPrazo, rotuloPrazo, urgenciaPrazo, type Projecao } from "../mockData";
import { COR_URGENCIA } from "../theme/tokens";
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
    <span className={`selo-prazo selo-prazo--${urgencia}`} style={{ color: COR_URGENCIA[urgencia] }}>
      <span className="selo-prazo__dias">{rotuloPrazo(projecao)}</span>
      {comData && data && <span className="selo-prazo__data">{data}</span>}
    </span>
  );
}
