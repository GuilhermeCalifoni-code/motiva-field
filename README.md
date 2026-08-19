# MOTIVA-FIELD

Monitoramento de vegetação em rodovias por visão computacional.

Câmeras fotografam a faixa de domínio. O sistema mede a **altura da vegetação em
centímetros**, casa cada medição com um ponto fixo da via e projeta **quando
aquele trecho vai precisar de roçada**. O painel web mostra isso para a equipe
interna; o app mobile leva o operador até o local e comprova a execução.

Cliente: Motiva (CCR). Entrega de Sprint 2 da FIAP.
Apresentação de venda: primeira semana de novembro de 2026.

> **Comece por aqui:** [`CLAUDE.md`](CLAUDE.md) tem as regras do projeto que não
> se quebram. Leia antes de escrever código.

---

## O que faz o produto valer

Três ideias sustentam a venda. Se você só tiver tempo de entender uma coisa,
entenda estas:

**1. Medir em centímetros, não em "tem mato".** O número é o que vende. Para
existir número real, cada foto precisa de escala — e escala errada contamina
tudo silenciosamente.

**2. Projeção.** A partir do histórico de altura de cada ponto, uma regressão
linear estima **em quantos dias** aquele trecho cruza o limite crítico. Isso
transforma monitorar em antecipar; planilha nenhuma faz isso.

**3. Comprovação de execução.** Foto do antes, foto do depois e coordenada GPS
do momento do registro. Sem as três não há prova de que o serviço foi feito.

---

## Estrutura

Monorepo, uma frente por pasta:

| Pasta | O que é | Stack | Estado |
|---|---|---|---|
| [`web/`](web/) | Painel de operação interno | React + Vite + TypeScript + Leaflet | Funcional com dados mock |
| [`mobile/`](mobile/) | App do operador em campo | Flutter (Dart) | 4 telas, roda em iOS e Android |
| [`vision/`](vision/) | Medição de vegetação por foto | Python — OpenCV + TensorFlow | Mede por foto real; ver limites |
| [`db/`](db/) | Schema, migrations, geometria das vias | Supabase, PostgreSQL + PostGIS | Só o eixo da SP-270 |
| [`docs/`](docs/) | Contratos e protocolos | — | Contrato JSON e protocolo de captura |
| `shared/` | Contratos entre as frentes | — | Vazio |

### Divisão de trabalho

- **Bloco 1** — front-ends (`web/`, `mobile/`)
- **Bloco 2** — visão computacional e câmeras (`vision/`)
- **Bloco 3** — banco de dados e pipeline (`db/`)

**Contrato entre 2 e 3:** o `vision/` recebe imagem e devolve JSON de detecções,
sem conhecer o Supabase. Pipeline, casamento com ponto e escrita são do `db/`.
O formato está em [`docs/contrato-json-deteccoes.md`](docs/contrato-json-deteccoes.md)
— enquanto ele não mudar, os dois blocos trabalham em paralelo sem se travar.

---

## Rodando cada frente

### Painel web

```bash
cd web
npm install
npm run dev
```

Abre em `http://localhost:5173`. Precisa de Node LTS.
No Windows há o atalho `iniciar-painel.cmd` na raiz.

Três seções: **Visão geral** (KPIs, gráfico de risco, fila "atuar agora"),
**Mapa** (Leaflet com o eixo real da SP-270) e **Ordens de serviço** (kanban de
quatro estágios).

### App mobile

```bash
cd mobile
flutter pub get
flutter run
```

Precisa do Flutter SDK. Quatro telas: login, ordem ativa, navegação guiada e
comprovação de execução.

```bash
flutter analyze
flutter test
```

### Visão computacional

```bash
cd vision
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

No Linux e macOS, troque `.venv/Scripts/` por `.venv/bin/`.

Testes — todos passam e saem com código 0:

```bash
.venv/Scripts/python teste_sintetico.py
.venv/Scripts/python teste_pipeline.py
.venv/Scripts/python teste_classificacao.py
```

Interface local para testar com foto real, upload ou webcam:

```bash
.venv/Scripts/python app.py
```

Abre em `http://127.0.0.1:8766`. No Windows há o atalho `iniciar-visao.bat`.

---

## A regra mais importante do projeto

**Todo dado falso mora em um arquivo só:** `web/src/mockData.ts` e
`mobile/lib/mock_data.dart`.

Nenhum componente inventa dado inline. Quando o banco chegar, troca-se aquele
arquivo por queries e mais nada. Se você precisar de um campo que não existe no
mock, **adicione lá** — nunca no componente.

Isso não é preciosismo: é o que permite o front-end vir primeiro e o schema ser
derivado das telas depois. Foi decisão consciente do time.

---

## Onde estamos e o que falta

### Funciona hoje

- Painel web com projeção de crescimento, eixo real da rodovia desenhado no
  mapa, kanban de OS e clima real via Open-Meteo.
- App mobile com o fluxo do operador e a trava de comprovação: o botão de
  concluir só habilita depois das duas fotos e do GPS.
- Medição por foto: detecta a trena por cor, lê a graduação impressa e deriva a
  escala **sem ninguém digitar número**.

### Não funciona ainda — leia antes de confiar

**A altura medida sai maior que a real quando a grama é contínua.** Numa cena
sintética com verdade de 6,0 cm, o método mede 14,6 cm. A causa não é
segmentação: é **profundidade**. A faixa de grama vai do pé da câmera ao
horizonte e é uma coisa só; separar o que está a 1 m do que está a 30 m exige
saber a distância de cada pixel. Segmentador melhor não resolve isso.

Caminhos: profundidade métrica monocular (Depth Anything V2, Metric3D) ou, muito
mais barato, **enquadrar a foto de perto**, com a moita ocupando o quadro.

**O modelo de classificação não existe.** `vision/classificacao.py` está pronto
e testado, mas `modelos/mobilenet_motiva.keras` nunca foi exportado do Colab —
ficou no `/content`, que é volátil. O teste **pula sozinho** enquanto o arquivo
não aparecer, e passa a valer no momento em que ele for colocado na pasta.

**A largura da trena está chutada.** `LARGURA_FITA_ESPERADA_CM = 2.5` em
`vision/graduacao.py`. É o que desempata a leitura da graduação entre 1 mm,
5 mm e 1 cm. Meça a trena de vocês e ajuste. Com o valor errado o sistema
**recusa medir** em vez de errar — seguro, mas inútil.

**Não há backend.** O front consome mock. O plano é um backend Python (FastAPI)
único, servindo web e mobile, com os endpoints derivados das telas que já
existem.

---

## Como o time trabalha

### Branches

`main` é a integração. Cada frente tem a sua:

| Branch | Bloco | Escopo |
|---|---|---|
| `frente-web` | 1 | `web/` |
| `frente-mobile` | 1 | `mobile/` |
| `frente-vision` | 2 | `vision/` |
| `frente-db` | 3 | `db/`, backend |

Fluxo: saia da `main` atualizada, trabalhe na sua branch, abra PR para a `main`.

```bash
git checkout main && git pull
git checkout frente-web
git merge main
```

Antes de abrir PR, rode o que a sua frente tem: `npm run build` no web,
`flutter analyze && flutter test` no mobile, os três `teste_*.py` na visão.

### Convenções

- Português em nomes de domínio (tabela, coluna, tipo). Inglês em nomes de
  bibliotecas.
- TypeScript no web, Dart no mobile, Python na visão. Nada de JavaScript solto.
- **Nenhum caminho absoluto, IP ou chave no código.** Tudo por variável de
  ambiente; `.env` no `.gitignore`.
- Sem acento nem espaço em nome de arquivo ou pasta.
- Commits em português, imperativo curto.

### O que não fazer

- Não usar a `service_role key` do Supabase no mobile nem no bundle do web —
  ela ignora RLS. Ela só existe no backend Python.
- Não criar um segundo backend. Um só, em Python.
- Não espalhar dado falso pelos componentes.
- Não instalar nada dentro de pasta sincronizada por OneDrive ou Google Drive.

---

## Documentos

| Arquivo | Para quê |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Regras do projeto. Leia primeiro |
| [`docs/contrato-json-deteccoes.md`](docs/contrato-json-deteccoes.md) | Formato entre visão e banco |
| [`docs/protocolo-captura-sp270.md`](docs/protocolo-captura-sp270.md) | Como fotografar em campo |
| [`vision/README.md`](vision/README.md) | Como a medição funciona e onde ela falha |
| [`MOTIVA-FIELD-roadmap-front-web-v2.md`](MOTIVA-FIELD-roadmap-front-web-v2.md) | Roadmap do painel |

Documentação viva no Google Drive, em `1-PROJECTS/MOTIVA-FIELD/`.
