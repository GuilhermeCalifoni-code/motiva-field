// Espelho em JavaScript dos tokens de cor definidos em tokens.css.
//
// Só existe porque alguns consumidores não são CSS: o Leaflet pinta SVG por
// atributo e alguns selos precisam de cor calculada em tempo de execução.
// Mantenha os valores em sincronia com tokens.css.

import type { NivelRisco, Prioridade, UrgenciaPrazo } from "../mockData";

export const COR_MARCA = {
  roxo: "#2e0854",
  roxoClaro: "#4b1f80",
  ouro: "#f2b705",
  branco: "#ffffff",
} as const;

// Escala de risco — codificação de dado, usada no mapa e nas barras.
export const COR_RISCO: Record<NivelRisco, string> = {
  tranquilo: "#22c55e",
  atencao: "#f97316",
  critico: "#f2b705",
};

// Semântica de ação — vermelho exige agora, laranja exige em breve.
export const COR_URGENCIA: Record<UrgenciaPrazo, string> = {
  vencido: "#d92d20",
  urgente: "#d92d20",
  atencao: "#f97316",
  neutro: "#675e78",
};

export const COR_PRIORIDADE: Record<Prioridade, string> = {
  baixa: "#22c55e",
  media: "#f97316",
  alta: "#e11d48",
};
