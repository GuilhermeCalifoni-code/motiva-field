# MOTIVA FIELD — Sprint 4

> Plataforma para monitoramento inteligente de vegetação em rodovias, priorização de roçada e comprovação de execução em campo.

**Challenge FIAP 2026 · Motiva**  
**Entrega final — Sprint 4: versão final, APK e plano de negócio**

---

## Links da entrega

- **Repositório final:** https://github.com/GuilhermeCalifoni-code/motiva-field
- **APK Android:** https://github.com/GuilhermeCalifoni-code/motiva-field/releases/download/sprint4-final/motiva-field-sprint4.apk
- **Vídeo final (YouTube — não listado):** PENDENTE — inserir o link após a gravação
- **Plano de negócio:** [docs/PLANO-DE-NEGOCIO-SPRINT4.md](docs/PLANO-DE-NEGOCIO-SPRINT4.md)
- **Roteiro do pitch:** [docs/ROTEIRO-PITCH-SPRINT4.md](docs/ROTEIRO-PITCH-SPRINT4.md)

> O APK é gerado automaticamente pelo GitHub Actions a partir da pasta `mobile/`. O arquivo binário não é versionado no repositório.

---

## Integrantes

| Integrante | RM |
|---|---:|
| Bento Donato Garcia | 561621 |
| Enzo Ribeiro Domingues Piazentin | 564216 |
| Guilherme Domingues Califoni | 565157 |
| Antonio Lucas Santana Tavares | 565516 |
| Lucas M. | 563667 |
| Gustavo Schimith | 564800 |

---

## 1. Problema

A conservação da vegetação às margens das rodovias é uma atividade recorrente, distribuída por grandes extensões e sujeita a mudanças rápidas por clima e sazonalidade. Inspeções puramente manuais dificultam priorização, histórico, previsão e comprovação do serviço executado.

O desafio do **Motiva Field** é transformar imagens e dados de campo em informação operacional: **onde agir, quando agir e como comprovar que a intervenção foi concluída**.

A aderência ao contexto é direta: a Motiva informa administrar **5.044 km de rodovias, 13 concessionárias e 3.356 câmeras de monitoramento**, além de manter operações contínuas de conservação e roçada.

Fonte institucional: https://rodovias.motiva.com.br/

---

## 2. Proposta de solução

O Motiva Field combina quatro frentes:

1. **Visão computacional / inteligência por imagem** para identificar riscos relacionados à vegetação e apoiar medições.
2. **Painel web operacional** para visualizar pontos monitorados, níveis de risco, projeções e ordens de serviço.
3. **Aplicativo Flutter para Android** para orientar o operador em campo e registrar a execução.
4. **Backend e dados** para centralizar ordens, evidências e integração entre as interfaces.

O fluxo principal é:

```text
Imagem / captura
      ↓
Análise de vegetação
      ↓
Ponto georreferenciado + nível de risco
      ↓
Priorização / criação de ordem
      ↓
Operador recebe a ordem no app
      ↓
Deslocamento → execução
      ↓
Foto antes + foto depois + evidência de localização
      ↓
Validação e histórico operacional
```

---

## 3. Diferenciais

### Medição orientada por evidência

O projeto não pretende apenas responder “há vegetação”. A arquitetura foi pensada para associar a detecção a um ponto da rodovia e permitir histórico e evolução da altura ao longo do tempo.

### Priorização e projeção

O painel transforma medições históricas em apoio à decisão, indicando quais pontos exigem atenção primeiro e possibilitando antecipar intervenções.

### Comprovação da execução

O fluxo mobile exige evidências de campo antes do envio para validação. O objetivo é criar rastreabilidade entre alerta, ordem de serviço e execução.

### Operação conectada

Web, mobile, API e banco compartilham o mesmo domínio operacional. Se a API estiver indisponível durante a demonstração, o aplicativo possui modo local de contingência para preservar o fluxo principal.

---

## 4. Contexto real da Motiva

Em 2026, a Motiva Rodovias informa operar 13 concessionárias, 5.044 km de rodovias em 7 estados e 3.356 câmeras de monitoramento. Isso mostra que há escala para soluções baseadas em dados, imagens e priorização de conservação.

Além disso, iniciativas públicas da própria Motiva reforçam a aderência do tema:

- o Rodoanel já divulgou uso de inteligência artificial e base georreferenciada para monitoramento de áreas verdes;
- a Motiva Sorocabana adotou equipamento especializado para aumentar segurança e eficiência em roçadas;
- concessionárias do grupo publicam cronogramas recorrentes de roçada, capina e conservação.

O Motiva Field se posiciona como **camada operacional de decisão e evidência**, complementando tecnologias de captura e equipamentos de execução.

Fontes:
- https://rodovias.motiva.com.br/
- https://rodovias.motiva.com.br/rodoanel/noticias/2025/dezembro/rodoanel-utiliza-inteligencia-artificial-para-elevar-padrao-de-m/
- https://rodovias.motiva.com.br/sorocabana/noticias/2026/agosto/motiva-sorocabana-aposta-em-inovacao-para-tornar-rocada-as-marge/

---

## 5. Stack

| Camada | Tecnologia |
|---|---|
| Mobile | Flutter + Dart |
| Web | React + Vite + TypeScript |
| API | Python + FastAPI |
| Visão computacional | Python + OpenCV + TensorFlow |
| IA assistida | Gemini via backend |
| Banco | Supabase + PostgreSQL + PostGIS |
| Mapa web | Leaflet |
| Clima | Open-Meteo |
| CI / APK | GitHub Actions |

---

## 6. Estrutura do repositório

```text
motiva-field/
├── api/       Backend FastAPI e integração de inteligência
├── db/        Banco, migrations e dados geoespaciais
├── docs/      Documentação técnica e Sprint 4
├── mobile/    Aplicativo Flutter
├── shared/    Contratos compartilhados
├── vision/    Pipeline de visão computacional
└── web/       Painel operacional React
```

---

## 7. Aplicativo Android

### Fluxos cobertos

O aplicativo possui:

- login demonstrativo;
- visão geral da operação;
- consulta da ordem ativa;
- fluxo de programação e deslocamento;
- indicação de chegada ao local;
- comprovação de execução;
- captura/seleção de imagem para inteligência;
- mapa operacional;
- sincronização com API quando disponível;
- contingência local quando o backend estiver indisponível.

Os testes automatizados do projeto cobrem login, navegação para o centro operacional e o fluxo de evidências da ordem de serviço.

### Instalação do APK

1. Baixe o APK pelo link desta página.
2. No Android, autorize a instalação de aplicativos provenientes do navegador ou gerenciador de arquivos utilizado.
3. Abra `motiva-field-sprint4.apk`.
4. Confirme **Instalar**.
5. Abra **Motiva Field**.
6. Conceda as permissões de câmera e localização quando solicitadas para demonstrar a comprovação de campo.

> O APK da entrega acadêmica é uma distribuição direta para demonstração e avaliação. Publicação em loja exigiria gestão de chave privada de assinatura e processo específico de distribuição.

### Gerar localmente

```bash
cd mobile
flutter pub get
flutter analyze
flutter test
flutter build apk --release
```

Saída esperada:

```text
mobile/build/app/outputs/flutter-apk/app-release.apk
```

---

## 8. Build automatizado

O workflow `.github/workflows/build-apk.yml` executa:

1. checkout do código;
2. configuração de Java 17;
3. configuração do Flutter estável;
4. `flutter pub get`;
5. `flutter analyze`;
6. `flutter test`;
7. `flutter build apk --release`;
8. upload do APK como artefato;
9. na branch `main`, publicação/atualização da release **sprint4-final**.

Isso garante que o APK disponibilizado seja gerado a partir do código do próprio repositório.

---

## 9. Plano de negócio

O modelo proposto é **B2B SaaS + implantação assistida**, voltado a concessionárias de rodovias.

### Resumo

- **Cliente:** áreas de Operações, Conservação, Engenharia e gestão de contratos.
- **Usuários:** gestores operacionais, inspetores, supervisores e equipes de campo.
- **Receita:** implantação/piloto + assinatura mensal por concessão/faixa de quilometragem.
- **Valor:** reduzir inspeção manual repetitiva, priorizar recursos, antecipar roçadas e criar evidência auditável.
- **Escala:** arquitetura preparada para múltiplos trechos e concessionárias.

O documento completo está em [docs/PLANO-DE-NEGOCIO-SPRINT4.md](docs/PLANO-DE-NEGOCIO-SPRINT4.md).

---

## 10. Evolução por Sprint

### Sprint 1 — definição do problema

- compreensão do desafio de conservação de vegetação;
- definição da proposta inicial;
- desenho do fluxo de captura, análise e visualização;
- decisão de separar visão, interfaces e dados.

### Sprint 2 — arquitetura e protótipos funcionais

- evolução da visão computacional;
- estruturação do painel web;
- base do aplicativo mobile;
- definição de contratos de dados e pontos monitorados;
- consolidação do monorepo.

### Sprint 3 — protótipo funcional completo

- fluxos principais e alternativos navegáveis;
- dados mockados de sucesso, erro e contingência;
- painel com mapa, riscos e ordens;
- fluxo mobile completo de ordem de serviço;
- testes automatizados e validações manuais;
- evolução da API e integração operacional.

### Sprint 4 — versão final e negócio

- consolidação da documentação;
- versão mobile 1.0;
- pipeline automatizado de qualidade e APK;
- plano de negócio aderente à Motiva;
- roteiro de pitch e demonstração;
- disponibilização do APK por GitHub Release;
- README transformado em documento-âncora da entrega.

---

## 11. Decisão pelo Flutter

A frente mobile foi consolidada em **Flutter** durante a evolução do projeto.

A decisão foi baseada em:

- geração nativa de APK Android;
- bom suporte a câmera e recursos do dispositivo;
- desenvolvimento multiplataforma;
- composição de interface consistente;
- facilidade para testes de widgets e fluxos.

Foram reaproveitados da evolução anterior os **requisitos, fluxos, regras de negócio, contratos de dados, identidade visual e arquitetura funcional**. A camada mobile final foi consolidada em Dart/Flutter.

---

## 12. Testes e critérios de aceite

Antes da entrega final, o grupo deve validar:

- [ ] APK instala em pelo menos um Android físico.
- [ ] Aplicativo abre sem erro crítico.
- [ ] Login funciona.
- [ ] Abas Resumo, Ordem, Mapa e IA abrem.
- [ ] Fluxo da ordem chega até comprovação.
- [ ] Evidências bloqueiam o envio enquanto incompletas.
- [ ] Câmera/galeria abre no dispositivo.
- [ ] Modo de contingência não derruba o app se a API estiver fora do ar.
- [ ] Link do APK está público.
- [ ] Link do YouTube está como **não listado**.
- [ ] Vídeo possui no máximo 5 minutos.
- [ ] Todos os integrantes aparecem ou têm protagonismo real no pitch.
- [ ] `ENTREGA-SPRINT4.txt` contém os links finais sem placeholders.

---

## 13. Limites e próximos passos

O projeto é um protótipo acadêmico avançado, não um sistema de segurança crítica em produção.

Antes de implantação operacional real seriam necessários:

- calibração e validação de campo em escala;
- dataset representativo das concessões;
- autenticação corporativa;
- assinatura e distribuição corporativa do aplicativo;
- observabilidade, SLA e recuperação de falhas;
- política de retenção das imagens;
- validação de segurança e LGPD;
- homologação com as equipes de conservação.

Essa transparência faz parte da proposta: o Motiva Field demonstra o produto e sua viabilidade, sem transformar resultados de laboratório em promessas não validadas.

---

## 14. Como executar

### Mobile

```bash
cd mobile
flutter pub get
flutter run
```

### Web

```bash
cd web
npm install
npm run dev
```

### API

```bash
cd api
copy .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### Visão computacional

```bash
cd vision
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

---

## Documentação complementar

- [Plano de negócio da Sprint 4](docs/PLANO-DE-NEGOCIO-SPRINT4.md)
- [Roteiro do pitch final](docs/ROTEIRO-PITCH-SPRINT4.md)
- [Contrato JSON de detecções](docs/contrato-json-deteccoes.md)
- [Protocolo de captura](docs/protocolo-captura-sp270.md)
- [Documentação da visão computacional](vision/README.md)
