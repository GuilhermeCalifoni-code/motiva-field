import { useEffect, useReducer, useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import {
  PRIORIDADE_POR_RISCO,
  centroDoTrecho,
  chuvaAceleraCrescimento,
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
import CentroInteligencia from "./components/CentroInteligencia";
import "./App.css";
import { Icon } from "./components/atoms/Icon";
import LoginWeb from "./components/LoginWeb";
import Configuracoes from "./components/Configuracoes";
import { useClima } from "./hooks/useClima";

// Estado das OS vive só em memória. Sem localStorage: quando o banco chegar,
// isto vira mutação no Supabase e o mockData.ts sai de cena.
interface EstadoOrdens {
  ordens: OrdemServico[];
  sequencia: number;
}

type AcaoOrdens =
  | { tipo: "criar"; pontoId: string; operadorId: string; prioridade: Prioridade }
  | { tipo: "mover"; id: string; status: OrdemServico["status"] }
  | { tipo: "carregar"; ordens: OrdemServico[] };

type OrdemBanco = {
  id: string; rodovia: string | null; km_inicial: number | null; prioridade: number; status: string; created_at: string;
};

const API_OPERACAO = import.meta.env.VITE_MOTIVA_API_URL ?? "http://127.0.0.1:8000";

function ordemDoBanco(ordem: OrdemBanco): OrdemServico {
  const status: OrdemServico["status"] = ordem.status === "triagem" ? "pendente" : ordem.status === "em_campo" ? "no_local" :
    ["pendente", "programada", "em_deslocamento", "no_local", "validacao", "concluida"].includes(ordem.status)
      ? ordem.status as OrdemServico["status"] : "pendente";
  const ponto = pontosVegetacao.find((item) => item.rodovia === ordem.rodovia && Math.abs(item.km - (ordem.km_inicial ?? item.km)) < 3) ?? pontosVegetacao[0];
  return { id: ordem.id, pontoId: ponto.id, operadorId: operadores[0].id, prioridade: ordem.prioridade <= 1 ? "alta" : ordem.prioridade === 2 ? "media" : "baixa", status, criadaEm: ordem.created_at, transicoes: [] };
}

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
    case "mover": {
      return { ...estado, ordens: estado.ordens.map((ordem) => ordem.id !== acao.id ? ordem : { ...ordem, status: acao.status, transicoes: [...ordem.transicoes, { status: acao.status, em: new Date().toISOString() }] }) };
    }
    case "carregar":
      return { ...estado, ordens: acao.ordens };
  }
}

function App() {
  const [autenticado, setAutenticado] = useState(() => sessionStorage.getItem("motiva-web-demo") === "ok");
  const [menuPerfilAberto, setMenuPerfilAberto] = useState(false);
  const [notificacoesAbertas, setNotificacoesAbertas] = useState(false);
  const [estado, despachar] = useReducer(reduzirOrdens, ESTADO_INICIAL);
  const [fonteOperacao, setFonteOperacao] = useState<"conectando" | "supabase" | "contingencia">("conectando");
  const centroClima = centroDoTrecho(pontosVegetacao);

  useEffect(() => {
    fetch(`${API_OPERACAO}/api/operacao/ordens`)
      .then(async (resposta) => {
        if (!resposta.ok) throw new Error("API indisponível");
        return resposta.json() as Promise<OrdemBanco[]>;
      })
      .then((ordens) => { despachar({ tipo: "carregar", ordens: ordens.map(ordemDoBanco) }); setFonteOperacao("supabase"); })
      .catch(() => setFonteOperacao("contingencia"));
  }, []);
  const clima = useClima(centroClima.latitude, centroClima.longitude);
  const navegar = useNavigate();

  function criarOrdem(pontoId: string, operadorId: string, prioridade: Prioridade) {
    despachar({ tipo: "criar", pontoId, operadorId, prioridade });
  }

  async function moverOrdem(id: string, status: OrdemServico["status"]) {
    const statusBanco = status === "pendente" ? "triagem" : status === "no_local" ? "em_campo" : status;
    const resposta = await fetch(`${API_OPERACAO}/api/operacao/ordens/${id}/status`, {
      method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: statusBanco }),
    });
    if (!resposta.ok) throw new Error("Não foi possível sincronizar a ordem.");
    despachar({ tipo: "mover", id, status });
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

  // A visão geral é uma tela de decisão: quase todo clique termina no mapa,
  // no ponto que motivou o clique.
  function abrirNoMapa(pontoId: string) {
    navegar(`/mapa?ponto=${encodeURIComponent(pontoId)}`);
  }

  if (!autenticado) return <LoginWeb onEntrar={() => { sessionStorage.setItem("motiva-web-demo", "ok"); setAutenticado(true); }} />;

  return (
    <div className="app">
      <header className="app__cabecalho">
        <div className="app__identidade"><span className="app__marca">MOTIVA<span>FIELD</span></span><span className="app__subtitulo">Operações de faixa de domínio · {fonteOperacao === "supabase" ? "dados compartilhados" : fonteOperacao === "contingencia" ? "contingência local" : "conectando banco"}</span></div>
        <div className="app__acoes"><div className="app__notificacoes"><button className="app__icone" aria-label="Notificações" onClick={() => setNotificacoesAbertas((aberto) => !aberto)}><Icon name="bell" size={17} /></button>{notificacoesAbertas && <div className="app__painel-notificacoes"><header><strong>Notificações</strong><span>{pontosVegetacao.filter((p) => p.nivelRisco === "critico").length + 1} novas</span></header><article><b>Prioridade de campo</b><p>{pontosVegetacao.filter((p) => p.nivelRisco === "critico").length} pontos críticos exigem tratativa.</p></article>{clima.situacao === "pronto" && <article><b>Clima no trecho</b><p>{clima.clima.temperaturaC.toFixed(0)}°C · {clima.clima.condicao}. {chuvaAceleraCrescimento(clima.clima.chuva24hMm, clima.clima.chuvaPrevista24hMm) ? "Chuva pode acelerar o crescimento; revise os próximos prazos." : "Sem aceleração climática imediata identificada."}</p></article>}<article><b>Validação de visão</b><p>Medição com régua transparente já está liberada por consenso. Fotos sem escala continuam em triagem até a calibração do POCO X7 Pro.</p></article></div>}</div><div className="app__perfil"><button className="app__usuario" onClick={() => setMenuPerfilAberto((aberto) => !aberto)} aria-expanded={menuPerfilAberto}><span>GC</span><div><strong>Operação SP-270</strong><small>Ambiente demonstrativo</small></div><Icon name="chevron" size={15} /></button>{menuPerfilAberto && <div className="app__menu-perfil"><button onClick={() => { setMenuPerfilAberto(false); navegar("/configuracoes"); }}>Configurações</button><button className="app__sair" onClick={() => { sessionStorage.removeItem("motiva-web-demo"); setAutenticado(false); }}>Sair da aplicação</button></div>}</div></div>
      </header>

      <div className="app__corpo">
        <NavegacaoLateral />
        <main className="app__conteudo">
          <Routes>
            <Route
              path="/"
              element={
                <VisaoGeral
                  pontos={pontosVegetacao}
                  ordens={estado.ordens}
                  onGerarOrdem={gerarOrdemDoPonto}
                  onAbrirNoMapa={abrirNoMapa}
                />
              }
            />
            <Route
              path="/mapa"
              element={<SecaoMapa pontos={pontosVegetacao} onGerarOrdem={gerarOrdemDoPonto} />}
            />
            <Route path="/inteligencia" element={<CentroInteligencia />} />
            <Route path="/configuracoes" element={<Configuracoes />} />
            <Route
              path="/ordens"
              element={
                <QuadroOrdens
                  ordens={estado.ordens}
                  pontos={pontosVegetacao}
                  operadores={operadores}
                  onCriar={criarOrdem}
                  onMover={(id, status) => { void moverOrdem(id, status).catch(() => window.alert("Não foi possível sincronizar a ordem com o banco.")); }}
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
