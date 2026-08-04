import { useState } from "react";
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
  const [pontoSelecionadoId, setPontoSelecionadoId] = useState<string | null>(null);
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
