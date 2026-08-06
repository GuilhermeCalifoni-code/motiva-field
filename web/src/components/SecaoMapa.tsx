import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import type { PontoVegetacao } from "../mockData";
import MapaVegetacao from "./MapaVegetacao";
import ListaPontos from "./ListaPontos";
import PainelDetalhe from "./PainelDetalhe";
import "./SecaoMapa.css";

interface SecaoMapaProps {
  pontos: PontoVegetacao[];
  onGerarOrdem: (pontoId: string) => void;
}

export default function SecaoMapa({ pontos, onGerarOrdem }: SecaoMapaProps) {
  const [parametros, definirParametros] = useSearchParams();
  const [pontoSelecionadoId, setPontoSelecionadoId] = useState<string | null>(null);

  // A visão geral chega aqui via /mapa?ponto=<id>. O parâmetro semeia a
  // seleção e sai da URL, para o botão voltar não reabrir o painel.
  useEffect(() => {
    const solicitado = parametros.get("ponto");
    if (!solicitado) return;
    if (pontos.some((ponto) => ponto.id === solicitado)) {
      setPontoSelecionadoId(solicitado);
    }
    definirParametros({}, { replace: true });
  }, [parametros, pontos, definirParametros]);

  const pontoSelecionado = pontos.find((ponto) => ponto.id === pontoSelecionadoId) ?? null;

  return (
    <div className="secao-mapa">
      <section className="secao-mapa__mapa">
        <MapaVegetacao
          pontos={pontos}
          pontoSelecionadoId={pontoSelecionadoId}
          onSelecionar={setPontoSelecionadoId}
        />
      </section>
      <aside className="secao-mapa__lista">
        <ListaPontos
          pontos={pontos}
          pontoSelecionadoId={pontoSelecionadoId}
          onSelecionar={setPontoSelecionadoId}
        />
      </aside>

      {pontoSelecionado && (
        <PainelDetalhe
          ponto={pontoSelecionado}
          onFechar={() => setPontoSelecionadoId(null)}
          onGerarOrdem={() => {
            onGerarOrdem(pontoSelecionado.id);
            setPontoSelecionadoId(null);
          }}
        />
      )}
    </div>
  );
}
