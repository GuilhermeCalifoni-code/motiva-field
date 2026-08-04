import "./SeloAlerta.css";

interface SeloAlertaProps {
  texto: string;
}

export default function SeloAlerta({ texto }: SeloAlertaProps) {
  return <span className="selo-alerta">{texto}</span>;
}
