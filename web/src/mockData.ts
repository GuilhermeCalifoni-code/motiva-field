// Dado falso e único desta frente. Nenhum componente deve inventar dado inline.
// Quando o banco chegar, este arquivo é trocado por queries — nada mais muda.

export type Sentido = "Capital" | "Interior";
export type Margem = "direita" | "esquerda";
export type NivelRisco = "tranquilo" | "atencao" | "critico";

export interface Passagem {
  data: string; // ISO 8601
  alturaCm: number;
}

export interface PontoVegetacao {
  id: string;
  rodovia: string;
  km: number;
  sentido: Sentido;
  margem: Margem;
  latitude: number;
  longitude: number;
  alturaAtualCm: number;
  nivelRisco: NivelRisco;
  invadePista: boolean;
  cobrePlaca: boolean;
  historico: Passagem[];
}

// Escala de risco do produto: verde tranquilo, laranja atenção, amarelo/ouro crítico.
export const RISCO_LABEL: Record<NivelRisco, string> = {
  tranquilo: "Tranquilo",
  atencao: "Atenção",
  critico: "Crítico",
};

// As cores vivem em theme/tokens — aqui só mora o dado de domínio.

// Usado para ordenar a lista por risco decrescente (crítico primeiro).
export const RISCO_ORDEM: Record<NivelRisco, number> = {
  critico: 3,
  atencao: 2,
  tranquilo: 1,
};

// Altura, em cm, a partir da qual o ponto entra em cada nível. Bate com o
// nivelRisco já gravado em cada ponto abaixo.
export const LIMITE_ALTURA_CM: Record<NivelRisco, number> = {
  tranquilo: 0,
  atencao: 25,
  critico: 45,
};

export const ALTURA_CRITICA_CM = LIMITE_ALTURA_CM.critico;

export function nivelPorAltura(alturaCm: number): NivelRisco {
  if (alturaCm >= LIMITE_ALTURA_CM.critico) return "critico";
  if (alturaCm >= LIMITE_ALTURA_CM.atencao) return "atencao";
  return "tranquilo";
}

function paraDiasEpoch(dataIso: string): number {
  const [ano, mes, dia] = dataIso.split("-").map(Number);
  return Date.UTC(ano, mes - 1, dia) / (1000 * 60 * 60 * 24);
}

// Crescimento médio, em cm por mês, entre a primeira e a última passagem.
export function crescimentoMensalCm(historico: Passagem[]): number {
  const primeira = historico[0];
  const ultima = historico[historico.length - 1];
  const dias = paraDiasEpoch(ultima.data) - paraDiasEpoch(primeira.data);
  const meses = dias / 30.44;
  return (ultima.alturaCm - primeira.alturaCm) / meses;
}

// Crescimento médio do trecho inteiro, em cm por mês.
export function crescimentoMedioTrechoCm(pontos: PontoVegetacao[]): number {
  const soma = pontos.reduce((total, ponto) => total + crescimentoMensalCm(ponto.historico), 0);
  return soma / pontos.length;
}

export function contarPorRisco(pontos: PontoVegetacao[], nivelRisco: NivelRisco): number {
  return pontos.filter((ponto) => ponto.nivelRisco === nivelRisco).length;
}

// --- Projeção de crescimento ----------------------------------------------
//
// A regressão e a projeção vivem só aqui. Componente nenhum recalcula isso.

export const MS_POR_DIA = 1000 * 60 * 60 * 24;
const DIAS_POR_MES = 30.44;

// Escala de tempo usada pela projeção e pelo eixo X do gráfico de altura.
export function diaEpochDe(dataIso: string): number {
  return paraDiasEpoch(dataIso);
}

export function diaEpochHoje(agora: number = Date.now()): number {
  return agora / MS_POR_DIA;
}

export interface Projecao {
  // Taxa vinda da regressão linear sobre todas as passagens, não só do
  // primeiro contra o último ponto.
  taxaCmPorMes: number;
  // Altura projetada para hoje pela reta de regressão.
  alturaHojeCm: number;
  // Dia em que a reta cruza o limite crítico, em "YYYY-MM-DD".
  // null quando o ponto já é crítico ou quando não está crescendo.
  dataCritica: string | null;
  // 0 se o ponto já é crítico; null se não há crescimento que leve ao limite.
  diasRestantes: number | null;
}

interface Reta {
  inclinacaoCmPorDia: number;
  interceptoCm: number;
}

// Mínimos quadrados sobre (dia, altura) das passagens.
function regredir(historico: Passagem[]): Reta {
  const amostras = historico.map((passagem) => ({
    x: paraDiasEpoch(passagem.data),
    y: passagem.alturaCm,
  }));

  const mediaX = amostras.reduce((total, a) => total + a.x, 0) / amostras.length;
  const mediaY = amostras.reduce((total, a) => total + a.y, 0) / amostras.length;

  let numerador = 0;
  let denominador = 0;
  for (const amostra of amostras) {
    numerador += (amostra.x - mediaX) * (amostra.y - mediaY);
    denominador += (amostra.x - mediaX) ** 2;
  }

  const inclinacaoCmPorDia = denominador === 0 ? 0 : numerador / denominador;
  return {
    inclinacaoCmPorDia,
    interceptoCm: mediaY - inclinacaoCmPorDia * mediaX,
  };
}

function diaEpochParaIso(dia: number): string {
  return new Date(Math.round(dia) * MS_POR_DIA).toISOString().slice(0, 10);
}

export function projecao(ponto: PontoVegetacao, agora: number = Date.now()): Projecao {
  const reta = regredir(ponto.historico);
  const taxaCmPorMes = reta.inclinacaoCmPorDia * DIAS_POR_MES;
  const diaHoje = agora / MS_POR_DIA;
  const alturaHojeCm = reta.interceptoCm + reta.inclinacaoCmPorDia * diaHoje;

  if (ponto.alturaAtualCm >= ALTURA_CRITICA_CM) {
    return { taxaCmPorMes, alturaHojeCm, dataCritica: null, diasRestantes: 0 };
  }

  if (reta.inclinacaoCmPorDia <= 0) {
    return { taxaCmPorMes, alturaHojeCm, dataCritica: null, diasRestantes: null };
  }

  const diaCritico = (ALTURA_CRITICA_CM - reta.interceptoCm) / reta.inclinacaoCmPorDia;
  return {
    taxaCmPorMes,
    alturaHojeCm,
    dataCritica: diaEpochParaIso(diaCritico),
    diasRestantes: Math.max(0, Math.ceil(diaCritico - diaHoje)),
  };
}

export type UrgenciaPrazo = "vencido" | "urgente" | "atencao" | "neutro";

export const PRAZO_URGENTE_DIAS = 7;
export const PRAZO_ATENCAO_DIAS = 15;

export function urgenciaPrazo(dados: Projecao): UrgenciaPrazo {
  if (dados.diasRestantes === null) return "neutro";
  if (dados.diasRestantes === 0) return "vencido";
  if (dados.diasRestantes < PRAZO_URGENTE_DIAS) return "urgente";
  if (dados.diasRestantes < PRAZO_ATENCAO_DIAS) return "atencao";
  return "neutro";
}

// Prazos longos podem cair em outro ano — sem o sufixo, "08/10" seria lido
// como daqui a dois meses.
function diaMesDeIso(dataIso: string, anoReferencia: number): string {
  const [ano, mes, dia] = dataIso.split("-");
  return Number(ano) === anoReferencia ? `${dia}/${mes}` : `${dia}/${mes}/${ano.slice(2)}`;
}

// Data do cruzamento, curta: "12/08" ou "08/10/27".
export function dataPrazoCurta(dados: Projecao, agora: number = Date.now()): string | null {
  if (!dados.dataCritica) return null;
  return diaMesDeIso(dados.dataCritica, new Date(agora).getFullYear());
}

// "crítico em ~9 dias", "já crítico", "sem crescimento".
export function rotuloPrazo(dados: Projecao): string {
  if (dados.diasRestantes === null) return "sem crescimento";
  if (dados.diasRestantes === 0) return "já crítico";
  return `crítico em ~${dados.diasRestantes} dias`;
}

// "roçar até 12/08".
export function rotuloDataPrazo(dados: Projecao, agora: number = Date.now()): string | null {
  const data = dataPrazoCurta(dados, agora);
  return data === null ? null : `roçar até ${data}`;
}

// Pontos que ainda não são críticos mas cruzam o limite dentro da janela.
export function viramCriticosEm(
  pontos: PontoVegetacao[],
  dias: number,
  agora: number = Date.now(),
): number {
  return pontos.filter((ponto) => {
    const dados = projecao(ponto, agora);
    return dados.diasRestantes !== null && dados.diasRestantes > 0 && dados.diasRestantes <= dias;
  }).length;
}

// Próximo ponto a cruzar o limite crítico. Ignora os que já são críticos:
// esses não têm prazo, têm atraso, e aparecem no bloco de acao imediata.
export function proximaRocada(
  pontos: PontoVegetacao[],
  agora: number = Date.now(),
): { ponto: PontoVegetacao; previsao: Projecao } | null {
  let melhor: { ponto: PontoVegetacao; previsao: Projecao } | null = null;
  for (const ponto of pontos) {
    const previsao = projecao(ponto, agora);
    if (previsao.diasRestantes === null || previsao.diasRestantes === 0) continue;
    if (melhor === null || previsao.diasRestantes < (melhor.previsao.diasRestantes ?? Infinity)) {
      melhor = { ponto, previsao };
    }
  }
  return melhor;
}

// Total que exige ação: os já críticos mais os que cruzam o limite na janela.
export function pontosQueExigemAcao(
  pontos: PontoVegetacao[],
  dias: number,
  agora: number = Date.now(),
): number {
  return contarPorRisco(pontos, "critico") + viramCriticosEm(pontos, dias, agora);
}

export type OrdenacaoPontos = "risco" | "prazo";

export const ORDENACAO_LABEL: Record<OrdenacaoPontos, string> = {
  risco: "Risco",
  prazo: "Prazo",
};

export function ordenarPontos(
  pontos: PontoVegetacao[],
  criterio: OrdenacaoPontos,
  agora: number = Date.now(),
): PontoVegetacao[] {
  if (criterio === "prazo") {
    // Sem crescimento vai para o fim da fila.
    const chave = (ponto: PontoVegetacao) => projecao(ponto, agora).diasRestantes ?? Infinity;
    return [...pontos].sort((a, b) => chave(a) - chave(b) || b.alturaAtualCm - a.alturaAtualCm);
  }
  return [...pontos].sort(
    (a, b) => RISCO_ORDEM[b.nivelRisco] - RISCO_ORDEM[a.nivelRisco] || b.alturaAtualCm - a.alturaAtualCm,
  );
}

// --- Efeito da chuva -------------------------------------------------------

// Acima disso, em mm por 24h, a equipe considera que o crescimento acelera.
export const CHUVA_ACELERA_MM = 1;

export function chuvaAceleraCrescimento(chuva24hMm: number, chuvaPrevista24hMm: number): boolean {
  return chuva24hMm >= CHUVA_ACELERA_MM || chuvaPrevista24hMm >= CHUVA_ACELERA_MM;
}

// Centro geográfico do trecho — usado para consultar o clima da região.
export function centroDoTrecho(pontos: PontoVegetacao[]): { latitude: number; longitude: number } {
  const soma = pontos.reduce(
    (total, ponto) => ({
      latitude: total.latitude + ponto.latitude,
      longitude: total.longitude + ponto.longitude,
    }),
    { latitude: 0, longitude: 0 },
  );
  return {
    latitude: soma.latitude / pontos.length,
    longitude: soma.longitude / pontos.length,
  };
}

// --- Ancoragem temporal das passagens ---------------------------------------
//
// As datas são calculadas a partir de hoje, não escritas à mão. Com datas
// absolutas o cenário envelhecia sozinho: conforme a projeção passava do prazo,
// o KPI "viram críticos em 15 dias" caía para zero e a demo passava a depender
// do dia em que rodasse.
//
// Só o ancoramento é relativo. Alturas e intervalos continuam sendo dado fixo,
// então as taxas de crescimento e os níveis de risco não mudam.
//
// Quando o banco chegar, isto some junto com o resto do mock: as passagens
// passam a ter data real de captura.

const INTERVALO_PASSAGENS_DIAS = 28;

// Distância da última passagem até hoje. Em 4 dias, o ponto do km 99,90 cruza
// o limite crítico daqui a ~9 dias — dentro da janela de 15 do KPI.
const DIAS_DESDE_ULTIMA_PASSAGEM = 4;

// Recebe as alturas medidas e devolve as passagens já datadas, da mais antiga
// para a mais recente.
function historicoDe(alturas: number[], agora: number = Date.now()): Passagem[] {
  const diaDaUltima = Math.floor(agora / MS_POR_DIA) - DIAS_DESDE_ULTIMA_PASSAGEM;
  return alturas.map((alturaCm, indice) => {
    const recuoDias = (alturas.length - 1 - indice) * INTERVALO_PASSAGENS_DIAS;
    return { data: diaEpochParaIso(diaDaUltima - recuoDias), alturaCm };
  });
}

export const pontosVegetacao: PontoVegetacao[] = [
  {
    id: "sp270-pv-01",
    rodovia: "SP-270",
    km: 98.2,
    sentido: "Capital",
    margem: "direita",
    latitude: -23.4692,
    longitude: -47.9581,
    alturaAtualCm: 32,
    nivelRisco: "atencao",
    invadePista: false,
    cobrePlaca: false,
    historico: historicoDe([12, 17, 22, 27, 32]),
  },
  {
    id: "sp270-pv-02",
    rodovia: "SP-270",
    km: 98.45,
    sentido: "Capital",
    margem: "esquerda",
    latitude: -23.4695,
    longitude: -47.9553,
    alturaAtualCm: 61,
    nivelRisco: "critico",
    invadePista: true,
    cobrePlaca: false,
    historico: historicoDe([25, 34, 43, 52, 61]),
  },
  {
    id: "sp270-pv-03",
    rodovia: "SP-270",
    km: 98.7,
    sentido: "Interior",
    margem: "direita",
    latitude: -23.4699,
    longitude: -47.9525,
    alturaAtualCm: 14,
    nivelRisco: "tranquilo",
    invadePista: false,
    cobrePlaca: false,
    historico: historicoDe([6, 8, 10, 12, 14]),
  },
  {
    id: "sp270-pv-04",
    rodovia: "SP-270",
    km: 98.95,
    sentido: "Interior",
    margem: "esquerda",
    latitude: -23.4703,
    longitude: -47.9497,
    alturaAtualCm: 50,
    nivelRisco: "critico",
    invadePista: false,
    cobrePlaca: true,
    historico: historicoDe([22, 29, 36, 43, 50]),
  },
  {
    id: "sp270-pv-05",
    rodovia: "SP-270",
    km: 99.3,
    sentido: "Capital",
    margem: "direita",
    latitude: -23.4708,
    longitude: -47.946,
    alturaAtualCm: 70,
    nivelRisco: "critico",
    invadePista: true,
    cobrePlaca: true,
    historico: historicoDe([30, 40, 50, 60, 70]),
  },
  {
    id: "sp270-pv-06",
    rodovia: "SP-270",
    km: 99.6,
    sentido: "Capital",
    margem: "esquerda",
    latitude: -23.4712,
    longitude: -47.9432,
    alturaAtualCm: 21,
    nivelRisco: "tranquilo",
    invadePista: false,
    cobrePlaca: false,
    historico: historicoDe([9, 12, 15, 18, 21]),
  },
  {
    id: "sp270-pv-07",
    rodovia: "SP-270",
    km: 99.9,
    sentido: "Interior",
    margem: "direita",
    latitude: -23.4716,
    longitude: -47.9404,
    alturaAtualCm: 42,
    nivelRisco: "atencao",
    invadePista: false,
    cobrePlaca: false,
    historico: historicoDe([19, 25, 31, 37, 42]),
  },
  {
    id: "sp270-pv-08",
    rodovia: "SP-270",
    km: 100.15,
    sentido: "Interior",
    margem: "esquerda",
    latitude: -23.4719,
    longitude: -47.938,
    alturaAtualCm: 29,
    nivelRisco: "atencao",
    invadePista: false,
    cobrePlaca: false,
    historico: historicoDe([13, 17, 21, 25, 29]),
  },
];

// --- Operadores e ordens de serviço ---------------------------------------

export interface Operador {
  id: string;
  nome: string;
}

export const operadores: Operador[] = [
  { id: "op-01", nome: "Rafael Nogueira" },
  { id: "op-02", nome: "Camila Duarte" },
  { id: "op-03", nome: "Anderson Prado" },
  { id: "op-04", nome: "Juliana Freitas" },
];

export type StatusOS = "pendente" | "em_deslocamento" | "no_local" | "concluida";
export type Prioridade = "baixa" | "media" | "alta";

// Ordem das colunas do kanban — também define o avanço de status.
export const FLUXO_STATUS: StatusOS[] = ["pendente", "em_deslocamento", "no_local", "concluida"];

export const STATUS_LABEL: Record<StatusOS, string> = {
  pendente: "Pendente",
  em_deslocamento: "Em deslocamento",
  no_local: "No local",
  concluida: "Concluída",
};

export const PRIORIDADE_LABEL: Record<Prioridade, string> = {
  baixa: "Baixa",
  media: "Média",
  alta: "Alta",
};

// Ponto crítico gera OS de prioridade alta — regra do time de operação.
export const PRIORIDADE_POR_RISCO: Record<NivelRisco, Prioridade> = {
  critico: "alta",
  atencao: "media",
  tranquilo: "baixa",
};

export interface TransicaoStatus {
  status: StatusOS;
  em: string; // ISO 8601 com fuso
}

export interface OrdemServico {
  id: string;
  pontoId: string;
  operadorId: string;
  prioridade: Prioridade;
  status: StatusOS;
  criadaEm: string; // ISO 8601 com fuso
  // Transições ocorridas depois da criação, em ordem cronológica.
  transicoes: TransicaoStatus[];
}

// Mesma ancoragem das passagens, pelo mesmo motivo: com datas absolutas o KPI
// "OS concluídas nos últimos 30 dias" zerava sozinho e o "tempo em aberto" dos
// cards crescia até virar semanas.
//
// O dia é relativo a hoje; o horário é fixo. Assim o cenário acompanha o
// calendário sem que as OS apareçam abertas às três da manhã.
function diasAtrasAs(
  dias: number,
  hora: number,
  minuto: number,
  agora: number = Date.now(),
): string {
  const momento = new Date(agora);
  momento.setDate(momento.getDate() - dias);
  momento.setHours(hora, minuto, 0, 0);
  return momento.toISOString();
}

export const ordensServicoIniciais: OrdemServico[] = [
  {
    id: "os-01",
    pontoId: "sp270-pv-05",
    operadorId: "op-01",
    prioridade: "alta",
    status: "pendente",
    criadaEm: diasAtrasAs(2, 7, 40),
    transicoes: [],
  },
  {
    id: "os-02",
    pontoId: "sp270-pv-02",
    operadorId: "op-02",
    prioridade: "alta",
    status: "pendente",
    criadaEm: diasAtrasAs(3, 14, 10),
    transicoes: [],
  },
  {
    id: "os-03",
    pontoId: "sp270-pv-04",
    operadorId: "op-03",
    prioridade: "alta",
    status: "em_deslocamento",
    criadaEm: diasAtrasAs(1, 6, 20),
    transicoes: [{ status: "em_deslocamento", em: diasAtrasAs(1, 8, 5) }],
  },
  {
    id: "os-04",
    pontoId: "sp270-pv-07",
    operadorId: "op-04",
    prioridade: "media",
    status: "no_local",
    criadaEm: diasAtrasAs(2, 9, 0),
    transicoes: [
      { status: "em_deslocamento", em: diasAtrasAs(1, 7, 15) },
      { status: "no_local", em: diasAtrasAs(1, 8, 40) },
    ],
  },
  {
    id: "os-05",
    pontoId: "sp270-pv-01",
    operadorId: "op-01",
    prioridade: "media",
    status: "concluida",
    criadaEm: diasAtrasAs(15, 8, 0),
    transicoes: [
      { status: "em_deslocamento", em: diasAtrasAs(14, 7, 10) },
      { status: "no_local", em: diasAtrasAs(14, 8, 25) },
      { status: "concluida", em: diasAtrasAs(14, 11, 50) },
    ],
  },
  {
    id: "os-06",
    pontoId: "sp270-pv-08",
    operadorId: "op-02",
    prioridade: "baixa",
    status: "concluida",
    criadaEm: diasAtrasAs(25, 10, 30),
    transicoes: [
      { status: "em_deslocamento", em: diasAtrasAs(22, 9, 5) },
      { status: "no_local", em: diasAtrasAs(22, 10, 40) },
      { status: "concluida", em: diasAtrasAs(22, 15, 20) },
    ],
  },
];

export function ordemEstaAberta(ordem: OrdemServico): boolean {
  return ordem.status !== "concluida";
}

export function contarPorStatus(ordens: OrdemServico[], status: StatusOS): number {
  return ordens.filter((ordem) => ordem.status === status).length;
}

// Momento em que a OS foi concluída, ou null se ainda estiver aberta.
export function concluidaEm(ordem: OrdemServico): string | null {
  const transicao = ordem.transicoes.find((item) => item.status === "concluida");
  return transicao ? transicao.em : null;
}

export function concluidasNosUltimosDias(ordens: OrdemServico[], dias: number, agora: number): number {
  const limite = agora - dias * 24 * 60 * 60 * 1000;
  return ordens.filter((ordem) => {
    const fim = concluidaEm(ordem);
    return fim !== null && new Date(fim).getTime() >= limite;
  }).length;
}

// Tempo entre a criação e a conclusão — ou até agora, se ainda estiver aberta.
export function tempoEmAberto(ordem: OrdemServico, agora: number): string {
  const fim = concluidaEm(ordem);
  const fimMs = fim ? new Date(fim).getTime() : agora;
  const totalMinutos = Math.max(0, Math.round((fimMs - new Date(ordem.criadaEm).getTime()) / 60000));
  const dias = Math.floor(totalMinutos / (60 * 24));
  const horas = Math.floor((totalMinutos % (60 * 24)) / 60);
  const minutos = totalMinutos % 60;

  if (dias > 0) return `${dias}d ${horas}h`;
  if (horas > 0) return `${horas}h ${minutos}min`;
  return `${minutos}min`;
}

// Operador com menos OS em aberto — usado quando a OS nasce do painel de
// detalhe do mapa, onde não há tela para escolher responsável.
export function operadorMenosCarregado(ordens: OrdemServico[], equipe: Operador[]): string {
  const carga = new Map<string, number>(equipe.map((operador) => [operador.id, 0]));
  for (const ordem of ordens) {
    if (!ordemEstaAberta(ordem)) continue;
    const atual = carga.get(ordem.operadorId);
    if (atual !== undefined) carga.set(ordem.operadorId, atual + 1);
  }
  return equipe.reduce((melhor, operador) =>
    (carga.get(operador.id) ?? 0) < (carga.get(melhor.id) ?? 0) ? operador : melhor,
  ).id;
}

export function formatarDataHora(dataIso: string): string {
  const data = new Date(dataIso);
  const doisDigitos = (valor: number) => String(valor).padStart(2, "0");
  return `${doisDigitos(data.getDate())}/${doisDigitos(data.getMonth() + 1)} ${doisDigitos(data.getHours())}:${doisDigitos(data.getMinutes())}`;
}
