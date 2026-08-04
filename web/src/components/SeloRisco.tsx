import { RISCO_COR, RISCO_LABEL, type NivelRisco } from "../mockData";
import "./SeloRisco.css";

interface SeloRiscoProps {
  nivelRisco: NivelRisco;
}

export default function SeloRisco({ nivelRisco }: SeloRiscoProps) {
  return (
    <span className="selo-risco" style={{ backgroundColor: RISCO_COR[nivelRisco] }}>
      {RISCO_LABEL[nivelRisco]}
    </span>
  );
}
