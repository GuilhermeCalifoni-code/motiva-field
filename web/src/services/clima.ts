// Única chamada de rede do painel. Dado de domínio (pontos, OS, operadores)
// continua vindo do mockData.ts.
//
// Open-Meteo é aberta e não exige chave. O endereço fica em variável de
// ambiente para não amarrar o código a um host.

const URL_BASE = import.meta.env.VITE_OPEN_METEO_URL ?? "https://api.open-meteo.com/v1/forecast";

export interface Clima {
  temperaturaC: number;
  condicao: string;
  chuva24hMm: number;
}

interface RespostaOpenMeteo {
  current?: {
    time?: string;
    temperature_2m?: number;
    weather_code?: number;
  };
  hourly?: {
    time?: string[];
    precipitation?: number[];
  };
}

// Códigos WMO devolvidos pela Open-Meteo.
const CONDICAO_POR_CODIGO: Record<number, string> = {
  0: "Céu limpo",
  1: "Predominantemente limpo",
  2: "Parcialmente nublado",
  3: "Nublado",
  45: "Névoa",
  48: "Névoa com geada",
  51: "Garoa fraca",
  53: "Garoa moderada",
  55: "Garoa forte",
  56: "Garoa congelante fraca",
  57: "Garoa congelante forte",
  61: "Chuva fraca",
  63: "Chuva moderada",
  65: "Chuva forte",
  66: "Chuva congelante fraca",
  67: "Chuva congelante forte",
  71: "Neve fraca",
  73: "Neve moderada",
  75: "Neve forte",
  77: "Grãos de neve",
  80: "Pancadas de chuva fracas",
  81: "Pancadas de chuva moderadas",
  82: "Pancadas de chuva fortes",
  85: "Pancadas de neve fracas",
  86: "Pancadas de neve fortes",
  95: "Tempestade",
  96: "Tempestade com granizo",
  99: "Tempestade com granizo forte",
};

function descreverCondicao(codigo: number | undefined): string {
  if (codigo === undefined) return "Condição indisponível";
  return CONDICAO_POR_CODIGO[codigo] ?? "Condição indisponível";
}

// Soma a precipitação das 24 horas que antecedem o horário atual.
function somarChuva24h(hourly: RespostaOpenMeteo["hourly"], horaAtual: string | undefined): number {
  const horarios = hourly?.time;
  const precipitacoes = hourly?.precipitation;
  if (!horarios || !precipitacoes || !horaAtual) return 0;

  let indiceAtual = -1;
  for (let i = 0; i < horarios.length; i += 1) {
    if (horarios[i] <= horaAtual) indiceAtual = i;
  }
  if (indiceAtual < 0) return 0;

  const inicio = Math.max(0, indiceAtual - 23);
  let total = 0;
  for (let i = inicio; i <= indiceAtual; i += 1) {
    total += precipitacoes[i] ?? 0;
  }
  return Math.round(total * 10) / 10;
}

export async function buscarClima(
  latitude: number,
  longitude: number,
  signal?: AbortSignal,
): Promise<Clima> {
  const parametros = new URLSearchParams({
    latitude: String(latitude),
    longitude: String(longitude),
    current: "temperature_2m,weather_code",
    hourly: "precipitation",
    past_days: "1",
    forecast_days: "1",
    timezone: "America/Sao_Paulo",
  });

  const resposta = await fetch(`${URL_BASE}?${parametros}`, { signal });
  if (!resposta.ok) {
    throw new Error(`Open-Meteo respondeu ${resposta.status}`);
  }

  const dados: RespostaOpenMeteo = await resposta.json();
  const temperatura = dados.current?.temperature_2m;
  if (typeof temperatura !== "number") {
    throw new Error("Resposta da Open-Meteo sem temperatura");
  }

  return {
    temperaturaC: temperatura,
    condicao: descreverCondicao(dados.current?.weather_code),
    chuva24hMm: somarChuva24h(dados.hourly, dados.current?.time),
  };
}
