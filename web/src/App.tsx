import { useReducer } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import {
  FLUXO_STATUS,
  PRIORIDADE_POR_RISCO,
  operadorMenosCarregado,
  operadores,
  ordensServicoIniciais,
  pontosVegetacao,
  type OrdemServico,
  type Prioridade,
} from "./mockData";
import NavegacaoLateral from "./components/NavegacaoLateral";
import VisaoGeral from "./components/VisaoGeral";
import SecaoMapa from "./components/SecaoMapa";
import QuadroOrdens from "./components/QuadroOrdens";
import "./App.css";

// Estado das OS vive só em memória. Sem localStorage: quando o banco chegar,
// isto vira mutação no Supabase e o mockData.ts sai de cena.
interface EstadoOrdens {
  ordens: OrdemServico[];
  sequencia: number;
}

type AcaoOrdens =
  | { tipo: "criar"; pontoId: string; operadorId: string; prioridade: Prioridade }
  | { tipo: "avancar"; id: string };

const ESTADO_INICIAL: EstadoOrdens = {
  ordens: ordensServicoIniciais,
  sequencia: ordensServicoIniciais.length + 1,
};

function reduzirOrdens(estado: EstadoOrdens, acao: AcaoOrdens): EstadoOrdens {
  switch (acao.tipo) {
    case "criar": {
      const nova: OrdemServico = {
        id: `os-${String(estado.sequencia).padStart(2, "0")}`,
        pontoId: acao.pontoId,
        operadorId: acao.operadorId,
        prioridade: acao.prioridade,
        status: "pendente",
        criadaEm: new Date().toISOString(),
        transicoes: [],
      };
      return { ordens: [nova, ...estado.ordens], sequencia: estado.sequencia + 1 };
    }
    case "avancar": {
      return {
        ...estado,
        ordens: estado.ordens.map((ordem) => {
          if (ordem.id !== acao.id) return ordem;
          const proximo = FLUXO_STATUS[FLUXO_STATUS.indexOf(ordem.status) + 1];
          if (!proximo) return ordem;
          // Cada transição guarda o horário em que aconteceu.
          return {
            ...ordem,
            status: proximo,
            transicoes: [...ordem.transicoes, { status: proximo, em: new Date().toISOString() }],
          };
        }),
      };
    }
  }
}

function App() {
  const [estado, despachar] = useReducer(reduzirOrdens, ESTADO_INICIAL);
  const navegar = useNavigate();

  function criarOrdem(pontoId: string, operadorId: string, prioridade: Prioridade) {
    despachar({ tipo: "criar", pontoId, operadorId, prioridade });
  }

  // Vem do painel de detalhe do mapa: sem tela de escolha, o sistema decide
  // prioridade pelo risco e responsável pela carga atual.
  function gerarOrdemDoPonto(pontoId: string) {
    const ponto = pontosVegetacao.find((item) => item.id === pontoId);
    if (!ponto) return;
    criarOrdem(
      pontoId,
      operadorMenosCarregado(estado.ordens, operadores),
      PRIORIDADE_POR_RISCO[ponto.nivelRisco],
    );
    navegar("/ordens");
  }

  return (
    <div className="app">
      <header className="app__cabecalho">
        <span className="app__marca">Motiva Field</span>
        <span className="app__subtitulo">SP-270 · Monitoramento de vegetação</span>
      </header>

      <div className="app__corpo">
        <NavegacaoLateral />
        <main className="app__conteudo">
          <Routes>
            <Route
              path="/"
              element={<VisaoGeral pontos={pontosVegetacao} ordens={estado.ordens} />}
            />
            <Route
              path="/mapa"
              element={<SecaoMapa pontos={pontosVegetacao} onGerarOrdem={gerarOrdemDoPonto} />}
            />
            <Route
              path="/ordens"
              element={
                <QuadroOrdens
                  ordens={estado.ordens}
                  pontos={pontosVegetacao}
                  operadores={operadores}
                  onCriar={criarOrdem}
                  onAvancar={(id) => despachar({ tipo: "avancar", id })}
                />
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default App;
