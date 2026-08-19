import { useEffect, useState } from "react";
import { buscarClima, type Clima } from "../services/clima";

export type EstadoClima =
  | { situacao: "carregando" }
  | { situacao: "pronto"; clima: Clima; carregadoEm: number }
  | { situacao: "erro" };

// Busca o clima do trecho uma vez por par de coordenadas. Se a API falhar, o
// estado vira "erro" e cabe a quem consome seguir sem o dado — o painel
// inteiro continua funcionando.
export function useClima(latitude: number, longitude: number): EstadoClima {
  const [estado, setEstado] = useState<EstadoClima>({ situacao: "carregando" });

  useEffect(() => {
    const controle = new AbortController();
    setEstado({ situacao: "carregando" });

    buscarClima(latitude, longitude, controle.signal)
      .then((clima) => setEstado({ situacao: "pronto", clima, carregadoEm: Date.now() }))
      .catch(() => {
        // O cleanup do efeito aborta a chamada — isso não é falha da API.
        if (controle.signal.aborted) return;
        setEstado({ situacao: "erro" });
      });

    return () => controle.abort();
  }, [latitude, longitude]);

  return estado;
}
