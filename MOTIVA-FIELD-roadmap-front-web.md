# MOTIVA-FIELD — Roadmap do painel web

> 2026-08-03 | para Enzo e Bento
> Contexto: [[MOTIVA-FIELD-HUB]] | Schema: [[MOTIVA-FIELD-schema-v2]]

---

## Onde estamos

O painel web já roda com navegação lateral e três seções: visão geral com
KPIs, mapa Leaflet do trecho da SP-270, e kanban de ordens de serviço com os
quatro estágios (pendente, em deslocamento, no local, concluída). Clima real
via Open-Meteo. Todo dado de domínio vem de um arquivo único, `mockData.ts` —
regra que a gente segue à risca: quando o banco chegar, troca-se esse arquivo
por queries e nada mais.

Stack: React + Vite + TypeScript + Leaflet, tudo em `web/`.

## Princípio que guia o roadmap

O que faz a Motiva comprar não é quantidade de widget. São duas ideias que
mudam o que o painel É:

1. **Projeção** transforma monitorar em antecipar. Planilha nenhuma faz isso.
2. **Eixo real da rodovia** transforma maquete em produto.

O resto é acabamento em cima dessas duas. Autenticação, permissões e
notificações ficam para depois do banco — feitas agora, seriam retrabalho.

## Fases, em ordem de valor

**Fase 1 — Projeção + eixo (em andamento)**
- Projeção de crescimento por regressão sobre o histórico de cada ponto:
  prazo estimado até o limite crítico, em dias. Vira coluna na lista, linha
  pontilhada no gráfico e um KPI de "viram críticos em 15 dias".
- Chuva da Open-Meteo passa a influenciar o aviso de aceleração.
- Eixo do trecho desenhado como polyline; pontos ancorados na linha;
  segmentos coloridos pelo risco. O traçado mora em
  `db/rodovias/sp270-trecho.geojson` — é a tabela `rodovias.eixo` nascendo.

**Fase 2 — OS contando a própria história**
- Tela de detalhe da OS com timeline das transições e duração de cada etapa.
- Slots de evidência: foto antes, foto depois, coordenada do registro
  (placeholder até o mobile existir).
- KPI de tempo médio de resposta por prioridade.

**Fase 3 — Demo ao vivo**
- Botão (só em dev) "simular nova passagem" que injeta leituras novas e faz o
  painel inteiro reagir na frente do cliente.

**Fase 4 — Acabamento profissional**
- Filtros e busca na lista e no mapa (risco, sentido, faixa de km).
- Estados vazios bem resolvidos.
- Exportar a visão geral em PDF para o gestor levar à reunião dele.

## Onde o front satura

A partir da fase 4, o próximo salto do produto não está mais no front. Está em
foto real de vegetação da SP-270 dentro do painel (dataset, Bloco 2) e no banco
(Bloco 3). A primeira imagem real no detalhe do ponto vale mais que qualquer
feature acima.

## Como isso alimenta o banco

Cada campo que o front inventa no `mockData.ts` é um campo que a tabela vai ter.
Ao final da fase 2, o mock descreve o schema quase inteiro, e o DDL sai
derivado das telas — sem gambiarra, que era a meta do time.

---
Voltar: [[MOTIVA-FIELD-HUB]] | [[🧠 Cerebro 2]]
