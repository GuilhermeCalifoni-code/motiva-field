import { useEffect, useState } from "react";
import "./IndicadorAoVivo.css";

interface IndicadorAoVivoProps {
  // Momento da última carga de dado externo (epoch ms), ou null enquanto carrega.
  atualizadoEm: number | null;
}

function descreverIntervalo(segundos: number): string {
  if (segundos < 60) return `há ${segundos}s`;
  const minutos = Math.floor(segundos / 60);
  if (minutos < 60) return `há ${minutos} min`;
  const horas = Math.floor(minutos / 60);
  return `há ${horas}h`;
}

export default function IndicadorAoVivo({ atualizadoEm }: IndicadorAoVivoProps) {
  const [agora, setAgora] = useState(() => Date.now());

  useEffect(() => {
    const id = setInterval(() => setAgora(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const segundos = atualizadoEm === null ? null : Math.max(0, Math.floor((agora - atualizadoEm) / 1000));

  return (
    <span className="indicador-ao-vivo">
      <span className="indicador-ao-vivo__ponto" aria-hidden="true" />
      <span className="indicador-ao-vivo__texto">
        ao vivo
        {segundos !== null && <> · atualizado {descreverIntervalo(segundos)}</>}
      </span>
    </span>
  );
}
