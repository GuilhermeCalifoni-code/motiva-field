import "./CardAcaoImediata.css";

interface CardAcaoImediataProps {
  criticos: number;
  viramCriticos: number;
  janelaDias: number;
  onVerPontos: () => void;
}

// O único bloco vermelho do painel. Vermelho aqui significa "alguém precisa
// sair de casa hoje" — por isso nenhum outro card usa essa cor.
export default function CardAcaoImediata({
  criticos,
  viramCriticos,
  janelaDias,
  onVerPontos,
}: CardAcaoImediataProps) {
  const total = criticos + viramCriticos;
  const semAcao = total === 0;

  return (
    <section className={`card-acao${semAcao ? " card-acao--calmo" : ""}`}>
      <span className="rotulo card-acao__rotulo">Ação imediata</span>

      <div className="card-acao__numero">
        <span className="card-acao__valor">{total}</span>
        <span className="card-acao__unidade">
          {total === 1 ? "ponto" : "pontos"}
        </span>
      </div>

      <p className="card-acao__detalhe">
        {semAcao ? (
          <>Nenhum ponto exige roçada nos próximos {janelaDias} dias.</>
        ) : (
          <>
            <strong>{criticos}</strong> {criticos === 1 ? "já passou" : "já passaram"} do limite
            {viramCriticos > 0 && (
              <>
                {" · "}
                <strong>{viramCriticos}</strong>{" "}
                {viramCriticos === 1 ? "cruza" : "cruzam"} em até {janelaDias} dias
              </>
            )}
          </>
        )}
      </p>

      {!semAcao && (
        <button type="button" className="card-acao__botao" onClick={onVerPontos}>
          Ver pontos no mapa
        </button>
      )}
    </section>
  );
}
