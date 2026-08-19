# MOTIVA-FIELD

Monitoramento de vegetação em rodovias por visão computacional.

Câmeras montadas em veículo fotografam a rodovia. Um modelo detecta vegetação
alta, invasão de pista e placas encobertas. Cada detecção é casada com um ponto
fixo da via, o que permite acompanhar o crescimento ao longo do tempo e prever
quando cada trecho vai precisar de roçada. O painel web mostra isso para a
equipe interna; o app mobile leva o operador até o local e comprova a execução.

Cliente: Motiva (CCR). Projeto de Sprint 2 da FIAP.

## Estrutura

Monorepo com uma frente por pasta:

| Pasta | O que é | Stack |
|---|---|---|
| `web/` | Painel de operação interno | React + Vite + TypeScript + Leaflet |
| `mobile/` | App do operador em campo | Flutter (Dart) |
| `vision/` | Detecção de vegetação | Python — OpenCV/YOLO |
| `db/` | Schema, migrations, geometria das vias | Supabase, PostgreSQL + PostGIS |
| `docs/` | Decisões de arquitetura (ADRs) | — |
| `shared/` | Contratos entre as frentes | — |

## Divisão de trabalho

- **Bloco 1** — front-ends (`web/`, `mobile/`)
- **Bloco 2** — visão computacional e câmeras (`vision/`)
- **Bloco 3** — banco de dados e pipeline (`db/`)

Contrato entre visão e banco: o `vision/` recebe imagem e devolve JSON de
detecções, sem conhecer o Supabase. Pipeline, casamento com ponto e escrita
são do `db/`.

Contrato entre front e backend: a fonte da verdade dos tipos é a API. Quando o
backend Python existir, ele expõe o schema OpenAPI e o Flutter deriva os
modelos dele. Até lá, cada front tem seu mock local espelhando o outro.

## Rodando o painel web

```bash
cd web
npm install
npm run dev
```

Abre em `http://localhost:5173`. Precisa de Node LTS.

Variáveis de ambiente em `web/.env` (ver `web/.env.example`). O `.env` nunca é
versionado.

## Rodando o mobile

```bash
cd mobile
flutter pub get
flutter run
```

Precisa do Flutter SDK instalado. Roda em iOS e Android.

## Estado atual

O front-end vem primeiro; o schema do banco é derivado das telas depois que
elas existem. Decisão consciente do time. Todo dado de domínio de cada front
mora num único arquivo de mock, trocado por chamadas reais quando o backend
chegar.

Documentação viva do projeto no Google Drive, em `1-PROJECTS/MOTIVA-FIELD/`,
sincronizada com Obsidian.

## Convenções

- Português em nomes de domínio (tabela, coluna, tipo). Inglês em nomes de
  código de bibliotecas.
- Nenhum caminho absoluto, IP ou chave no código — tudo por variável de
  ambiente. `.env` no `.gitignore`.
- Sem acento nem espaço em nome de arquivo ou pasta.
- Commits em português, imperativo curto.
