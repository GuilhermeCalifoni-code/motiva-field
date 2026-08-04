# MOTIVA-FIELD

Monitoramento de vegetação em rodovias por visão computacional.
Cliente: Motiva (CCR). Também é a entrega de Sprint 2 da FIAP.
Apresentação de venda: primeira semana de novembro de 2026.

## O que o sistema faz

Câmeras montadas em veículo fotografam a rodovia. Um modelo detecta três coisas:
altura da vegetação, vegetação invadindo a pista, e vegetação cobrindo placas.
Cada detecção é casada com um ponto fixo da rodovia, o que permite acompanhar
crescimento ao longo do tempo e prever quando o trecho vai precisar de roçada.
O painel web mostra isso para a equipe interna. O app mobile leva o operador até
o local, registra a execução e comprova que foi feita.

## Estrutura

```
motiva-field/
├── vision/    Python — OpenCV/YOLO. Função pura: imagem entra, JSON sai.
├── mobile/    React Native + Expo — operador em campo
├── web/       React + Vite + Leaflet — painel interno
├── db/        Supabase, PostgreSQL + PostGIS, migrations
├── shared/    Tipos e contratos entre as frentes
└── docs/      ADRs e decisões de arquitetura
```

## Divisão de trabalho

- Bloco 1 — front-ends (web e mobile)
- Bloco 2 — visão computacional e câmeras
- Bloco 3 — banco de dados e pipeline

Contrato entre 2 e 3: o `vision/` não conhece o Supabase. Ele recebe imagem e
devolve JSON de detecções. Pipeline, casamento com ponto e escrita são do `db/`.

## Estado atual

O front-end vem primeiro; o schema será derivado das telas depois que elas
existirem. Decisão consciente do time — não sugerir inverter.

Por isso vale uma regra rígida:

**Todo dado falso mora em um arquivo só** (`web/src/mockData.ts`,
`mobile/src/mockData.ts`). Nenhum componente inventa dado inline. Quando o banco
chegar, troca-se aquele arquivo por queries e mais nada. Se você precisar de um
campo que não existe no mock, adicione lá — nunca no componente.

## Modelo de dados (rascunho, ver docs/)

Entidades centrais: `rodovias`, `passagens`, `frames`, `pontos`, `deteccoes`,
`operadores`, `ordens_servico`.

A distinção que sustenta o produto: `frames` é o que a câmera viu (efêmero),
`pontos` é o que existe na rodovia (permanente, acumula histórico). Uma detecção
nasce sem `ponto_id` e é casada depois por proximidade.

Status de OS tem mais de três estados: pendente, em deslocamento, no local,
concluída. Cada transição guarda horário.

Comprovação de execução exige foto do antes, foto do depois e coordenada GPS do
momento do registro — sem isso não há prova de que o serviço foi feito.

## Convenções

- Português nos nomes de tabela, coluna e domínio. Inglês em nomes de código.
- TypeScript nos dois fronts. Nada de JavaScript solto.
- Nenhum caminho absoluto, IP ou chave no código. Tudo por variável de ambiente.
- `.env` no `.gitignore` desde o primeiro commit.
- Sem acento nem espaço em nome de arquivo ou pasta.
- Commits em português, imperativo curto.

## Não faça

- Não use a `service_role key` do Supabase no mobile nem no bundle do web. Ela
  ignora RLS. Ela só existe no backend Python.
- Não crie um segundo backend. Um só, em Python, servindo web e mobile.
- Não espalhe dado falso pelos componentes.
- Não use localStorage para dado que precise sobreviver — ainda não há banco,
  mas isso não vira desculpa para persistir de qualquer jeito.
- Não instale nada dentro de pasta sincronizada por OneDrive ou Google Drive.

## Contexto extra

Documentação viva do projeto no Google Drive, em `1-PROJECTS/MOTIVA-FIELD/`,
sincronizada com Obsidian. O ADR do schema está em
`MOTIVA-FIELD-schema-v2.md`.
