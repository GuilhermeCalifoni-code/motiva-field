import { RISCO_LABEL, type NivelRisco } from "../mockData";
import { COR_RISCO } from "../theme/tokens";
import "./SeloRisco.css";

interface SeloRiscoProps {
  nivelRisco: NivelRisco;
}

export default function SeloRisco({ nivelRisco }: SeloRiscoProps) {
  return (
    <span className="selo-risco" style={{ backgroundColor: COR_RISCO[nivelRisco] }}>
      {RISCO_LABEL[nivelRisco]}
    </span>
  );
}
