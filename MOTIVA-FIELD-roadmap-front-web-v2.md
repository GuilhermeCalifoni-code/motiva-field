# MOTIVA-FIELD — Roadmap do painel web (v2)

> Atualizado 2026-08-04 | para Enzo e Bento
> Contexto: [[MOTIVA-FIELD-HUB]] | Schema: [[MOTIVA-FIELD-schema-v2]]
> Substitui a v1 do roadmap

---

## Onde estamos

O painel web roda com navegação lateral e três seções: visão geral, mapa e
kanban de OS. Já entregue além do básico: projeção de crescimento por regressão
(prazo até virar crítico) e o eixo real da rodovia desenhado no mapa, com os
pontos ancorados na linha e segmentos coloridos por risco. Clima real via
Open-Meteo. Repositório git com dois commits, indo para o GitHub como privado.

Todo dado de domínio vem de um arquivo único, `mockData.ts`. Quando o banco
chegar, troca-se esse arquivo por queries e nada mais.

## A virada desta fase: de "funciona" para "impressiona"

A lógica ficou profissional antes da aparência. O diagnóstico honesto: hoje
todos os elementos têm o mesmo peso visual, então o gestor não sabe para onde
olhar. O conserto não é mais informação — é hierarquia.

Dois princípios que passam a valer no painel inteiro:

1. **Cor é semântica, não decoração.** Vermelho só para o que exige ação agora,
   laranja para atenção próxima, neutro para o resto.
2. **Hierarquia por tamanho e peso.** Números grandes, rótulos pequenos e
   apagados. O que importa é grande; o contexto é discreto.

Para isso nasce um tema central de tokens em `web/src/theme/` — cores,
espaçamentos e tipografia num lugar só. Nenhum componente usa cor hexadecimal
solta. Isso também prepara o mobile: os dois fronts passam a beber da mesma
identidade.

## Fases, em ordem de valor

**Fase 1 — Projeção + eixo** ✓ concluída
Projeção de crescimento e eixo real da rodovia no mapa.

**Fase 2 — Visão executiva + tema de tokens** (em andamento)
Faixa de topo com card de "ação imediata" em destaque e três cards de contexto;
abaixo, coluna "atuar agora" com os pontos ordenados por urgência. Tema central
de tokens aplicado a todo o painel.

**Fase 3 — Backend Python (FastAPI)**
Vem logo após a pele executiva. Os endpoints nascem das telas que já existem —
o `mockData.ts` já descreve o que o backend precisa servir. É o método do time
funcionando: o banco e a API derivados do que a interface provou precisar, sem
gambiarra. O front troca o mock por chamadas reais sem reescrever componente.

**Fase 4 — Mapa enriquecido**
Basemap mais sóbrio para os dados saltarem, selo de km por ponto, legenda,
clima sobreposto, voo até o ponto ao clicar.

**Fase 5 — OS contando a própria história**
Detalhe da OS com timeline das transições e slots de evidência (foto antes,
foto depois, GPS). KPI de tempo médio de resposta.

**Fase 6 — Demo ao vivo e acabamento**
Botão "simular passagem" para a reunião; filtros, busca, exportar PDF.

## O que fica para depois do banco

Autenticação, permissões e notificações. Feitos agora, seriam retrabalho —
ganham forma com o Supabase Auth.

## O maior "uau" que ainda falta

Não está no front nem no backend: é a primeira foto real de vegetação da SP-270
dentro do detalhe do ponto. Uma tarde de captura resolve, e o dataset começa a
render sozinho enquanto o resto é construído.

---
Voltar: [[MOTIVA-FIELD-HUB]] | [[🧠 Cerebro 2]]
