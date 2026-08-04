import { useEffect, useState } from "react";
import { chuvaAceleraCrescimento } from "../mockData";
import { buscarClima, type Clima } from "../services/clima";
import "./CardClima.css";

interface CardClimaProps {
  latitude: number;
  longitude: number;
}

type Estado =
  | { situacao: "carregando" }
  | { situacao: "pronto"; clima: Clima }
  | { situacao: "erro" };

export default function CardClima({ latitude, longitude }: CardClimaProps) {
  const [estado, setEstado] = useState<Estado>({ situacao: "carregando" });

  useEffect(() => {
    const controle = new AbortController();
    setEstado({ situacao: "carregando" });

    buscarClima(latitude, longitude, controle.signal)
      .then((clima) => setEstado({ situacao: "pronto", clima }))
      .catch(() => {
        // O cleanup do efeito aborta a chamada — isso não é falha da API.
        if (controle.signal.aborted) return;
        setEstado({ situacao: "erro" });
      });

    return () => controle.abort();
  }, [latitude, longitude]);

  return (
    <div className="card-clima">
      <div className="card-clima__cabecalho">
        <h3>Clima no trecho</h3>
        <span>chuva acelera o crescimento</span>
      </div>

      {estado.situacao === "carregando" && (
        <p className="card-clima__aviso">Consultando previsão…</p>
      )}

      {estado.situacao === "erro" && (
        <p className="card-clima__aviso card-clima__aviso--erro">
          Não foi possível consultar o clima agora. O restante do painel segue atualizado.
        </p>
      )}

      {estado.situacao === "pronto" && (
        <div className="card-clima__dados">
          <span className="card-clima__temperatura">{Math.round(estado.clima.temperaturaC)}°C</span>
          <span className="card-clima__condicao">{estado.clima.condicao}</span>
          <span className="card-clima__chuva">
            <strong>{estado.clima.chuva24hMm.toFixed(1).replace(".", ",")} mm</strong> nas últimas
            24h · <strong>{estado.clima.chuvaPrevista24hMm.toFixed(1).replace(".", ",")} mm</strong>{" "}
            previstos
          </span>
          {chuvaAceleraCrescimento(estado.clima.chuva24hMm, estado.clima.chuvaPrevista24hMm) && (
            <span className="card-clima__acelera">Chuva no trecho — crescimento tende a acelerar</span>
          )}
        </div>
      )}
    </div>
  );
}
