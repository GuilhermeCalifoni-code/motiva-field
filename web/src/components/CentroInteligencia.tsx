import { useEffect, useMemo, useRef, useState, type MouseEvent } from "react";
import "./CentroInteligencia.css";

type Nivel = "seguro" | "atencao" | "critico" | "nao_avaliavel";
type Tipo = "vegetacao_alta" | "invade_pista" | "cobre_placa";
type Modo = "medicao" | "risco" | "descricao" | "geometria";

interface Deteccao {
  tipo: Tipo;
  presente: boolean;
  nivel: Nivel;
  confianca: number;
  justificativa: string;
  cobertura_pct?: number | null;
}

interface Descricao {
  arquivo: string;
  origem: "gemini" | "demo_local";
  modelo: string;
  descricao: string;
  objeto_principal: string;
  confianca: number;
  detalhes_visuais: string[];
  avisos: string[];
}

interface AuditoriaGeometrica {
  arquivo: string;
  origem?: string;
  modelo?: string;
  decisao: "medir_com_regua" | "triagem_sem_medida" | "bloquear";
  geometria_candidata: boolean;
  alvo: { classe: string | null; roi_normalizada_0a1000: number[] | null; confianca: number; motivo: string };
  base_topo: { compativeis: boolean; base_visivel: boolean; topo_visivel: boolean; base_px_normalizado_0a1000?: number[] | null; topo_px_normalizado_0a1000?: number[] | null; motivo: string };
  referencias: { tipo: string; confianca: number; compatibilidade_espacial: number; utilizavel: boolean; ponto_superior_normalizado_0a1000?: number[] | null; ponto_inferior_normalizado_0a1000?: number[] | null; intervalo_observado_cm?: number | null; incerteza_descricao: string }[];
  plano_local: string | null;
  inclinacao_desconhecida: boolean;
  objetos_ignorados: string[];
  limitacoes: string[];
  proxima_captura: string;
}

interface MedicaoCompleta {
  arquivo: string;
  status: "medido" | "nao_mensuravel";
  altura_cm: number | null;
  valido: boolean;
  metodo: string | null;
  intervalo_cm?: number[] | null;
  confianca: number;
  escala?: {
    via_escala?: string;
    pixels_por_cm?: number;
    comprimento_visivel_cm?: number;
    intervalo_referencia_cm?: number;
  } | null;
  consenso?: {
    escalas_concordam: boolean;
    alturas_concordam: boolean;
    divergencia_escala_pct: number;
    divergencia_altura_pct: number;
  } | null;
  estimativa_assistida?: {
    altura_cm: number;
    intervalo_cm: number[];
    confianca: number;
    fonte: string;
    uso: "orientativo_nao_metrico";
  } | null;
  auditoria: AuditoriaGeometrica | null;
  avisos?: string[];
  pendencias?: string[];
  mensagem: string;
}

interface PontoAssistido {
  x: number;
  y: number;
}

interface MedicaoAssistida {
  arquivo: string;
  status: "medido_assistido";
  altura_cm: number;
  valido: true;
  nivel_validacao: "assistido_operador";
  apto_historico: false;
  intervalo_cm: number[];
  confianca: number;
  metodo: string;
  escala_px_por_cm: number;
  angulo_entre_segmentos_graus: number;
  referencia_cm: number;
  referencia_px: number;
  alvo_px_projetado: number;
  pontos: Record<string, PontoAssistido>;
  mensagem: string;
  avisos: string[];
  proveniencia: Record<string, string>;
}

interface Analise {
  arquivo: string;
  origem: "gemini" | "demo_local";
  modelo: string;
  resumo_operacional: string;
  deteccoes: Deteccao[];
  altura: { centimetros: number | null; fonte_escala: string | null; observacao: string };
  acao_recomendada: string;
  avisos: string[];
}

const ROTULOS: Record<Tipo, string> = {
  vegetacao_alta: "Vegetação alta",
  invade_pista: "Invasão de pista",
  cobre_placa: "Placa encoberta",
};

const API = import.meta.env.VITE_API_URL ?? "";
const API_OPERACAO = import.meta.env.VITE_MOTIVA_API_URL ?? "http://127.0.0.1:8000";
const ROTULOS_PONTOS = ["Início da referência", "Fim da referência", "Base da vegetação", "Topo da vegetação"];
const TEMPO_MINIMO_ANALISE_MS = 3000;

function aguardar(ms: number) {
  return new Promise<void>((resolver) => window.setTimeout(resolver, ms));
}

function ResultadoAssistido({ resultado }: { resultado: MedicaoAssistida }) {
  return <>
    <div className="centro-ia__resultado-topo">
      <div><p className="centro-ia__sobretitulo">Medição matemática assistida</p><h2>Altura calculada com referência física</h2></div>
      <span className="centro-ia__status centro-ia__status--assistido">Assistida pelo operador</span>
    </div>
    <div className="centro-ia__altura centro-ia__altura--assistida"><strong>{resultado.altura_cm.toFixed(1)}</strong><span>cm</span></div>
    <p className="centro-ia__medida">Intervalo conservador: <b>{resultado.intervalo_cm[0].toFixed(1)}–{resultado.intervalo_cm[1].toFixed(1)} cm</b></p>
    <div className="centro-ia__metadados">
      <div><span>Confiança geométrica</span><strong>{Math.round(resultado.confianca * 100)}%</strong></div>
      <div><span>Escala local</span><strong>{resultado.escala_px_por_cm.toFixed(2)} px/cm</strong></div>
      <div><span>Referência</span><strong>{resultado.referencia_cm.toFixed(1)} cm</strong></div>
      <div><span>Alinhamento</span><strong>{resultado.angulo_entre_segmentos_graus.toFixed(1)}°</strong></div>
      <div><span>Método</span><strong>4 pontos confirmados</strong></div>
    </div>
    <div className="centro-ia__checklist centro-ia__checklist--assistido">
      <header><div><span>Rastreabilidade</span><strong>4/4 entradas confirmadas</strong></div><b className="assistido">Revisão humana</b></header>
      <ul>
        {[
          "Comprimento físico da referência informado",
          "Início e fim da referência marcados",
          "Base e topo da vegetação marcados",
          "Coplanaridade confirmada pelo operador",
        ].map((item) => <li key={item} className="ok"><i>OK</i><span>{item}</span></li>)}
      </ul>
    </div>
    {resultado.avisos.length > 0 && <ul className="centro-ia__avisos">{resultado.avisos.map((aviso) => <li key={aviso}>{aviso}</li>)}</ul>}
    <div className="centro-ia__parecer centro-ia__parecer--assistido"><span>Parecer</span><strong>{resultado.mensagem}</strong><p>O resultado não é uma inferência autônoma e ainda não alimenta o histórico oficial.</p></div>
  </>;
}

function ChecklistMedicao({ medicao }: { medicao: MedicaoCompleta }) {
  const referenciaValida = medicao.auditoria?.referencias.some(
    (referencia) => referencia.utilizavel && referencia.compatibilidade_espacial >= 0.9,
  ) ?? false;
  const itens = [
    { rotulo: "Auditoria visual concluída", ok: Boolean(medicao.auditoria) },
    {
      rotulo: "Base e topo pertencem ao mesmo alvo",
      ok: Boolean(
        medicao.auditoria?.base_topo.compativeis
        && medicao.auditoria.base_topo.base_visivel
        && medicao.auditoria.base_topo.topo_visivel,
      ),
    },
    {
      rotulo: "Escala métrica ou câmera calibrada",
      ok: referenciaValida || medicao.valido,
    },
    {
      rotulo: "Detectores independentes em consenso",
      ok: medicao.valido && medicao.mensagem.toLowerCase().includes("consenso"),
    },
    { rotulo: "Centímetros autorizados para operação", ok: medicao.valido },
  ];

  return (
    <div className="centro-ia__checklist">
      <header>
        <div>
          <span>Checklist de aprovação</span>
          <strong>{itens.filter((item) => item.ok).length}/{itens.length} evidências</strong>
        </div>
        <b className={medicao.valido ? "aprovado" : "pendente"}>{medicao.valido ? "Aprovado" : "Pendente"}</b>
      </header>
      <ul>
        {itens.map((item) => (
          <li key={item.rotulo} className={item.ok ? "ok" : "nao"}>
            <i>{item.ok ? "OK" : "—"}</i>
            <span>{item.rotulo}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function CentroInteligencia() {
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [modo, setModo] = useState<Modo>("medicao");
  const [medicao, setMedicao] = useState<MedicaoCompleta | null>(null);
  const [analise, setAnalise] = useState<Analise | null>(null);
  const [descricao, setDescricao] = useState<Descricao | null>(null);
  const [auditoria, setAuditoria] = useState<AuditoriaGeometrica | null>(null);
  const [erro, setErro] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [filaStatus, setFilaStatus] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [assistidoAtivo, setAssistidoAtivo] = useState(false);
  const [pontosAssistidos, setPontosAssistidos] = useState<PontoAssistido[]>([]);
  const [dimensoesImagem, setDimensoesImagem] = useState({ largura: 1, altura: 1 });
  const [referenciaCm, setReferenciaCm] = useState(20);
  const [coplanarConfirmado, setCoplanarConfirmado] = useState(false);
  const [medicaoAssistida, setMedicaoAssistida] = useState<MedicaoAssistida | null>(null);
  const imagemAssistidaRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (!arquivo) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(arquivo);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [arquivo]);

  const fonte = useMemo(() => {
    if (medicaoAssistida) return "Matemática determinística + pontos confirmados";
    if (medicao?.auditoria?.origem === "gemini" || auditoria?.origem === "gemini" || analise?.origem === "gemini" || descricao?.origem === "gemini") return "Gemini + validação determinística";
    if (analise?.origem === "demo_local" || descricao?.origem === "demo_local") return "Modo demonstração local";
    return null;
  }, [analise, auditoria, descricao, medicao, medicaoAssistida]);

  function selecionarArquivo(novoArquivo: File | null) {
    setArquivo(novoArquivo);
    setMedicao(null);
    setAnalise(null);
    setDescricao(null);
    setAuditoria(null);
    setMedicaoAssistida(null);
    setPontosAssistidos([]);
    setCoplanarConfirmado(false);
    setAssistidoAtivo(false);
    setFilaStatus(null);
    setErro("");
  }

  async function carregarSugestoesIa() {
    const audit = medicao?.auditoria;
    const referencia = audit?.referencias.find((item) =>
      item.utilizavel
      && item.ponto_superior_normalizado_0a1000
      && item.ponto_inferior_normalizado_0a1000
      && item.intervalo_observado_cm,
    );
    const base = audit?.base_topo.base_px_normalizado_0a1000;
    const topo = audit?.base_topo.topo_px_normalizado_0a1000;
    if (!previewUrl || !referencia || !base || !topo) {
      setErro("A IA não produziu quatro pontos completos; marque-os manualmente.");
      return;
    }
    const imagem = new Image();
    imagem.src = previewUrl;
    await imagem.decode();
    const converter = (ponto: number[]) => ({ x: ponto[0] / 1000 * imagem.naturalWidth, y: ponto[1] / 1000 * imagem.naturalHeight });
    setDimensoesImagem({ largura: imagem.naturalWidth, altura: imagem.naturalHeight });
    setPontosAssistidos([
      converter(referencia.ponto_superior_normalizado_0a1000!),
      converter(referencia.ponto_inferior_normalizado_0a1000!),
      converter(base),
      converter(topo),
    ]);
    setReferenciaCm(Number(referencia.intervalo_observado_cm));
    setAssistidoAtivo(true);
    setCoplanarConfirmado(false);
    setMedicaoAssistida(null);
    setErro("");
  }

  function marcarPontoAssistido(evento: MouseEvent<HTMLDivElement>) {
    if (pontosAssistidos.length >= 4 || !imagemAssistidaRef.current) return;
    const imagem = imagemAssistidaRef.current;
    const limites = imagem.getBoundingClientRect();
    const x = Math.max(0, Math.min(imagem.naturalWidth - 1, (evento.clientX - limites.left) / limites.width * imagem.naturalWidth));
    const y = Math.max(0, Math.min(imagem.naturalHeight - 1, (evento.clientY - limites.top) / limites.height * imagem.naturalHeight));
    setPontosAssistidos((atuais) => [...atuais, { x, y }]);
    setMedicaoAssistida(null);
  }

  async function calcularAssistida() {
    if (!arquivo || pontosAssistidos.length !== 4) {
      setErro("Marque os quatro pontos antes de calcular.");
      return;
    }
    if (!coplanarConfirmado) {
      setErro("Confirme que a referência e a vegetação estão no mesmo plano físico.");
      return;
    }
    setCarregando(true);
    setErro("");
    const dados = new FormData();
    dados.append("imagem", arquivo);
    dados.append("comprimento_referencia_cm", String(referenciaCm));
    const campos = ["referencia_inicio", "referencia_fim", "base", "topo"];
    pontosAssistidos.forEach((ponto, indice) => {
      dados.append(`${campos[indice]}_x`, String(ponto.x));
      dados.append(`${campos[indice]}_y`, String(ponto.y));
    });
    dados.append("coplanar_confirmado", "true");
    try {
      const resposta = await fetch(`${API}/api/medicoes-assistidas`, { method: "POST", body: dados });
      const corpo = await resposta.json();
      if (!resposta.ok) throw new Error(corpo.detail ?? "A medição assistida não pôde ser calculada.");
      setMedicaoAssistida(corpo as MedicaoAssistida);
      setMedicao(null);
      setAnalise(null);
      setDescricao(null);
      setAuditoria(null);
    } catch (causa) {
      setErro(causa instanceof Error ? causa.message : "Falha ao calcular a medição assistida.");
    } finally {
      setCarregando(false);
    }
  }

  async function analisar() {
    if (!arquivo) {
      setErro("Selecione uma foto de campo para analisar.");
      return;
    }
    const inicio = performance.now();
    setCarregando(true);
    setErro("");
    setMedicaoAssistida(null);
    const dadosFila = new FormData();
    dadosFila.append("imagem", arquivo);
    const dados = new FormData();
    dados.append("imagem", arquivo);
    let filaId: string | null = null;
    try {
      const recebimento = await fetch(`${API_OPERACAO}/api/operacao/fila-imagens`, { method: "POST", body: dadosFila });
      const registro = await recebimento.json();
      if (!recebimento.ok) throw new Error(registro.detail ?? "Não foi possível registrar a evidência no Supabase.");
      filaId = registro.fila?.id ?? null;
      setFilaStatus(filaId ? `Evidência registrada na fila · ${filaId.slice(0, 8)}` : "Evidência registrada na fila");

      const endpoint = modo === "medicao"
        ? "/api/medicoes-altura"
        : modo === "risco"
          ? "/api/analises"
          : modo === "descricao"
            ? "/api/descricoes"
            : "/api/auditorias-geometricas";
      const resposta = await fetch(`${API}${endpoint}`, { method: "POST", body: dados });
      const corpo = await resposta.json();
      if (!resposta.ok) throw new Error(corpo.detail ?? "A análise não pôde ser concluída.");
      await aguardar(Math.max(0, TEMPO_MINIMO_ANALISE_MS - (performance.now() - inicio)));
      if (filaId) {
        const resumo = modo === "medicao"
          ? { estado: "analise_concluida", modo, altura_cm: corpo.altura_cm, valido: corpo.valido, confianca: corpo.confianca }
          : { estado: "analise_concluida", modo };
        const conclusao = await fetch(`${API_OPERACAO}/api/operacao/fila-imagens/${filaId}`, {
          method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ resultado_resumo: resumo }),
        });
        if (!conclusao.ok) throw new Error("A análise terminou, mas a fila não pôde ser atualizada.");
        setFilaStatus(`Processamento concluído · ${filaId.slice(0, 8)}`);
      }
      setMedicao(modo === "medicao" ? corpo as MedicaoCompleta : null);
      setAnalise(modo === "risco" ? corpo as Analise : null);
      setDescricao(modo === "descricao" ? corpo as Descricao : null);
      setAuditoria(modo === "geometria" ? corpo as AuditoriaGeometrica : null);
    } catch (causa) {
      setErro(causa instanceof Error ? causa.message : "Falha inesperada ao analisar a imagem.");
    } finally {
      await aguardar(Math.max(0, TEMPO_MINIMO_ANALISE_MS - (performance.now() - inicio)));
      setCarregando(false);
    }
  }

  return (
    <section className="centro-ia">
      <header className="centro-ia__cabecalho">
        <div>
          <p className="centro-ia__sobretitulo">Central de inteligência</p>
          <h1>Da evidência de campo à decisão</h1>
          <p>Triagem visual, medição rastreável e justificativa pronta para aprovação.</p>
        </div>
        {fonte && <span className="centro-ia__fonte centro-ia__fonte--gemini">{fonte}</span>}
      </header>

      <div className="centro-ia__grade">
        <article className="centro-ia__card centro-ia__entrada">
          <p className="centro-ia__sobretitulo">Nova passagem</p>
          <h2>Enviar foto de campo</h2>
          <p className="centro-ia__texto">Use a câmera principal 1× e uma régua no mesmo plano da vegetação. Se a automação falhar, confirme a geometria com quatro pontos.</p>
          <label className="centro-ia__campo">
            <span>Tipo de análise</span>
            <select value={modo} onChange={(evento) => setModo(evento.target.value as Modo)}>
              <option value="medicao">Análise completa + altura validada</option>
              <option value="risco">Somente triagem de risco</option>
              <option value="geometria">Auditoria da evidência</option>
              <option value="descricao">Descrição automática</option>
            </select>
          </label>

          <label className={`centro-ia__arquivo${previewUrl ? " centro-ia__arquivo--com-preview" : ""}`}>
            {previewUrl ? (
              <><img src={previewUrl} alt="Prévia da foto selecionada" /><span>Trocar imagem</span></>
            ) : (
              <><strong>Selecionar imagem</strong><span>JPG, PNG ou WEBP</span></>
            )}
            <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(evento) => selecionarArquivo(evento.target.files?.[0] ?? null)} />
          </label>
          {arquivo && <p className="centro-ia__arquivo-nome">{arquivo.name}</p>}
          <button className="centro-ia__botao" type="button" disabled={carregando} onClick={analisar}>
            {carregando ? "Auditando percepção, escala e geometria..." : modo === "medicao" ? "Analisar e validar altura" : modo === "risco" ? "Analisar risco" : modo === "geometria" ? "Auditar evidência" : "Descrever imagem"}
          </button>
          {assistidoAtivo && previewUrl && <div className="centro-ia__assistido">
            <header><div><span>Fallback matemático</span><strong>Confirme a geometria na imagem</strong></div><b>{pontosAssistidos.length}/4 pontos</b></header>
            <label className="centro-ia__campo"><span>Intervalo físico marcado na régua (cm)</span><input type="number" min="1" max="200" step="0.1" value={referenciaCm} onChange={(evento) => setReferenciaCm(Number(evento.target.value))} /></label>
            <div className="centro-ia__marcador" onClick={marcarPontoAssistido} role="button" tabIndex={0} aria-label="Marcar pontos na imagem">
              <img ref={imagemAssistidaRef} src={previewUrl} alt="Imagem para medição assistida" draggable={false} onLoad={(evento) => setDimensoesImagem({ largura: evento.currentTarget.naturalWidth, altura: evento.currentTarget.naturalHeight })} />
              <svg viewBox={`0 0 ${dimensoesImagem.largura} ${dimensoesImagem.altura}`} preserveAspectRatio="none" aria-hidden="true">
                {pontosAssistidos.length >= 2 && <line x1={pontosAssistidos[0].x} y1={pontosAssistidos[0].y} x2={pontosAssistidos[1].x} y2={pontosAssistidos[1].y} className="linha-referencia" />}
                {pontosAssistidos.length >= 4 && <line x1={pontosAssistidos[2].x} y1={pontosAssistidos[2].y} x2={pontosAssistidos[3].x} y2={pontosAssistidos[3].y} className="linha-alvo" />}
                {pontosAssistidos.map((ponto, indice) => <g key={`${ponto.x}-${ponto.y}`}><circle cx={ponto.x} cy={ponto.y} r={Math.max(10, dimensoesImagem.largura / 90)} className={indice < 2 ? "ponto-referencia" : "ponto-alvo"} /><text x={ponto.x + dimensoesImagem.largura / 70} y={ponto.y - dimensoesImagem.largura / 90}>{indice + 1}</text></g>)}
              </svg>
            </div>
            <ol className="centro-ia__passos-pontos">{ROTULOS_PONTOS.map((rotulo, indice) => <li key={rotulo} className={pontosAssistidos.length > indice ? "concluido" : pontosAssistidos.length === indice ? "atual" : ""}><i>{indice + 1}</i><span>{rotulo}</span></li>)}</ol>
            <label className="centro-ia__confirmacao"><input type="checkbox" checked={coplanarConfirmado} onChange={(evento) => setCoplanarConfirmado(evento.target.checked)} /><span>Confirmo que a régua e a vegetação estão lado a lado no mesmo plano físico.</span></label>
            <div className="centro-ia__acoes-assistidas"><button type="button" onClick={() => { setPontosAssistidos((atuais) => atuais.slice(0, -1)); setMedicaoAssistida(null); }} disabled={!pontosAssistidos.length}>Desfazer</button><button type="button" onClick={() => { setPontosAssistidos([]); setMedicaoAssistida(null); }}>Recomeçar</button></div>
            <button className="centro-ia__botao centro-ia__botao--assistido" type="button" disabled={carregando || pontosAssistidos.length !== 4 || !coplanarConfirmado || referenciaCm <= 0} onClick={calcularAssistida}>{carregando ? "Calculando geometria..." : "Calcular medida assistida"}</button>
          </div>}
          {filaStatus && <p className="centro-ia__fila-status">{filaStatus}</p>}
          {erro && <p className="centro-ia__erro">{erro}</p>}
          <div className="centro-ia__regra">
            <strong>Regra de segurança</strong>
            <p>Se percepção, escala, base/topo e detectores independentes não concordarem, o retorno será <code>null</code>.</p>
          </div>
        </article>

        <article className="centro-ia__card centro-ia__resultado">
          {carregando ? (
            <div className="centro-ia__vazio"><strong>Analisando a foto...</strong><span>Verificando evidência, escala, geometria e consenso.</span></div>
          ) : !medicaoAssistida && !medicao && !analise && !descricao && !auditoria ? (
            <div className="centro-ia__vazio"><strong>Aguardando uma foto</strong><span>A análise e seu checklist aparecerão aqui.</span></div>
          ) : medicaoAssistida ? (
            <ResultadoAssistido resultado={medicaoAssistida} />
          ) : medicao ? (
            <>
              <div className="centro-ia__resultado-topo">
                <div><p className="centro-ia__sobretitulo">Medição operacional</p><h2>{medicao.valido ? "Altura validada" : medicao.estimativa_assistida ? "Estimativa assistida disponível" : "Medição bloqueada com segurança"}</h2></div>
                <span className={`centro-ia__status ${medicao.valido ? "centro-ia__status--ok" : "centro-ia__status--pendente"}`}>{medicao.valido ? "Apta para aprovação" : medicao.estimativa_assistida ? "Orientativa" : "Somente triagem"}</span>
              </div>

              {medicao.altura_cm !== null ? (
                <><div className="centro-ia__altura"><strong>{medicao.altura_cm.toFixed(1)}</strong><span>cm</span></div>{medicao.intervalo_cm && <p className="centro-ia__medida">Intervalo validado: <b>{medicao.intervalo_cm[0].toFixed(1)}–{medicao.intervalo_cm[1].toFixed(1)} cm</b></p>}</>
              ) : medicao.estimativa_assistida ? (
                <><div className="centro-ia__estimativa"><span>Estimativa assistida · não validada</span><div><strong>{medicao.estimativa_assistida.altura_cm.toFixed(1)}</strong><b>cm</b></div><p>Faixa orientativa {medicao.estimativa_assistida.intervalo_cm[0].toFixed(1)}–{medicao.estimativa_assistida.intervalo_cm[1].toFixed(1)} cm · confiança {Math.round(medicao.estimativa_assistida.confianca * 100)}% · fonte {medicao.estimativa_assistida.fonte.replaceAll("_", " ")}</p></div><p className="centro-ia__oficial-null">Valor oficial: altura_cm = null até consenso independente.</p></>
              ) : <div className="centro-ia__sem-medida"><strong>altura_cm = null</strong><p>{medicao.mensagem}</p></div>}

              <div className="centro-ia__metadados">
                <div><span>Confiança métrica</span><strong>{Math.round(medicao.confianca * 100)}%</strong></div>
                <div><span>Confiança visual</span><strong>{medicao.auditoria ? `${Math.round(medicao.auditoria.alvo.confianca * 100)}%` : "indisponível"}</strong></div>
                <div><span>Método</span><strong>{medicao.metodo?.replaceAll("_", " ") ?? "não liberado"}</strong></div>
                <div><span>Escala</span><strong>{medicao.escala?.pixels_por_cm ? `${medicao.escala.pixels_por_cm.toFixed(2)} px/cm` : "não confirmada"}</strong></div>
                <div><span>Consenso</span><strong>{medicao.consenso ? `escala ${medicao.consenso.divergencia_escala_pct.toFixed(1)}% · altura ${medicao.consenso.divergencia_altura_pct.toFixed(1)}%` : "não confirmado"}</strong></div>
              </div>

              <ChecklistMedicao medicao={medicao} />

              {medicao.auditoria && <div className={`centro-ia__risco centro-ia__risco--${medicao.valido ? "seguro" : "atencao"}`}><div><strong>{medicao.auditoria.alvo.classe ?? "Alvo não definido"}</strong><span>confiança visual {Math.round(medicao.auditoria.alvo.confianca * 100)}%</span></div><p>{medicao.auditoria.base_topo.motivo}</p></div>}
              {medicao.pendencias && medicao.pendencias.length > 0 && <ul className="centro-ia__avisos">{medicao.pendencias.map((item) => <li key={item}>{item}</li>)}</ul>}
              {!medicao.valido && medicao.auditoria?.geometria_candidata && <button className="centro-ia__sugestoes" type="button" onClick={carregarSugestoesIa}>Usar pontos sugeridos pela IA e confirmar</button>}
              <div className={`centro-ia__parecer ${medicao.valido ? "centro-ia__parecer--ok" : ""}`}><span>Parecer para aprovação</span><strong>{medicao.valido ? "A medição possui referência rastreável e consenso independente." : "A imagem não sustenta centímetros automáticos; confirme pontos ou use somente para priorização."}</strong></div>
            </>
          ) : auditoria ? (
            <>
              <p className="centro-ia__sobretitulo">Auditoria geométrica</p>
              <h2>{auditoria.decisao === "medir_com_regua" ? "Evidência adequada para medir com régua" : auditoria.decisao === "triagem_sem_medida" ? "Aprovar apenas para triagem" : "Bloquear medição em centímetros"}</h2>
              <div className={`centro-ia__risco centro-ia__risco--${auditoria.decisao === "medir_com_regua" ? "seguro" : auditoria.decisao === "triagem_sem_medida" ? "atencao" : "nao_avaliavel"}`}><div><strong>{auditoria.alvo.classe ?? "Alvo não definido"}</strong><span>confiança visual {Math.round(auditoria.alvo.confianca * 100)}%</span></div><p>{auditoria.alvo.motivo}</p></div>
              <div className="centro-ia__acao"><span>Base e topo</span><strong>{auditoria.base_topo.compativeis ? "Compatíveis" : "Não comprovados como o mesmo alvo"}</strong><p>{auditoria.base_topo.motivo}</p></div>
              <ul className="centro-ia__avisos">{auditoria.referencias.map((referencia) => <li key={`${referencia.tipo}-${referencia.incerteza_descricao}`}>{referencia.tipo}: {referencia.utilizavel ? "utilizável" : "não utilizável"} · compatibilidade espacial {Math.round(referencia.compatibilidade_espacial * 100)}% · {referencia.incerteza_descricao}</li>)}{auditoria.limitacoes.map((limitacao) => <li key={limitacao}>{limitacao}</li>)}</ul>
              <p className="centro-ia__medida">{auditoria.geometria_candidata ? "ROI/base/topo podem seguir para a validação determinística." : "A fórmula geométrica não deve receber esta imagem."}</p><p className="centro-ia__medida">Próxima captura: {auditoria.proxima_captura}</p>
            </>
          ) : descricao ? (
            <><p className="centro-ia__sobretitulo">Descrição automática</p><h2>{descricao.objeto_principal}</h2><p>{descricao.descricao}</p><p className="centro-ia__medida">Confiança visual: {Math.round(descricao.confianca * 100)}%</p><ul className="centro-ia__avisos">{descricao.detalhes_visuais.map((detalhe) => <li key={detalhe}>{detalhe}</li>)}</ul></>
          ) : analise ? (
            <><p className="centro-ia__sobretitulo">Resultado operacional</p><h2>{analise.resumo_operacional}</h2><div className="centro-ia__riscos">{analise.deteccoes.map((deteccao) => <div key={deteccao.tipo} className={`centro-ia__risco centro-ia__risco--${deteccao.nivel}`}><div><strong>{ROTULOS[deteccao.tipo]}</strong><span>{deteccao.presente ? deteccao.nivel.replace("_", " ") : "não identificado"}</span></div><b>{Math.round(deteccao.confianca * 100)}%</b><p>{deteccao.justificativa}</p></div>)}</div><div className="centro-ia__acao"><span>Próxima ação</span><strong>{analise.acao_recomendada}</strong></div><p className="centro-ia__medida">{analise.altura.centimetros !== null ? `${analise.altura.centimetros.toFixed(1)} cm — ${analise.altura.fonte_escala}` : analise.altura.observacao}</p>{analise.avisos.length > 0 && <ul className="centro-ia__avisos">{analise.avisos.map((aviso) => <li key={aviso}>{aviso}</li>)}</ul>}</>
          ) : null}
        </article>
      </div>
    </section>
  );
}
