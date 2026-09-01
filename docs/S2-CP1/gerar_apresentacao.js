/**
 * Gera o deck da aula tecnica do S2-CP01 (Tema 2).
 *
 *   cd docs/S2-CP1 && node gerar_apresentacao.js
 *
 * Formato pedido no enunciado: 10 min de aula + 5 de perguntas. Os slides
 * apoiam a fala, nao repetem o PDF. Cada slide tem nota de orador com o tempo
 * sugerido.
 */

const pptxgen = require("pptxgenjs");
const path = require("path");

// Identidade do projeto Motiva-Field.
const ROXO = "2E0854";
const ROXO_CLARO = "4B1F80";
const OURO = "F2B705";
const BRANCO = "FFFFFF";
const CINZA = "675E78";
const CINZA_CLARO = "F6F4FA";
const TEXTO = "201A2B";
const PERIGO = "D92D20";
const VERDE = "22C55E";

// PREENCHER ANTES DA APRESENTACAO
const TURMA = "2CCPO";
const INTEGRANTES = [
  { nome: "Bento Donato Garcia", rm: "561621", papel: "[participação no projeto]" },
  { nome: "Enzo Ribeiro Domingues Piazentin", rm: "564216", papel: "[participação no projeto]" },
  { nome: "Guilherme Domingues Califoni", rm: "565157", papel: "[participação no projeto]" },
  { nome: "Antonio Lucas Santana Tavares", rm: "565516", papel: "[participação no projeto]" },
  { nome: "Lucas M.", rm: "563667", papel: "[participação no projeto]" },
  { nome: "Gustavo Schimith", rm: "564800", papel: "[participação no projeto]" },
];

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5 pol
pres.author = "Grupo Motiva-Field";
pres.title = "S2-CP01 — Sensoriamento da vegetação e qualidade da medição";

const L = 0.7;            // margem esquerda
const LARG = 11.9;        // largura util

function tituloSlide(slide, texto, sobre) {
  if (sobre) {
    slide.addText(sobre.toUpperCase(), {
      x: L, y: 0.42, w: LARG, h: 0.3, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 12, bold: true, color: OURO, charSpacing: 2,
    });
  }
  slide.addText(texto, {
    x: L, y: sobre ? 0.72 : 0.55, w: LARG, h: 0.85, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 34, bold: true, color: ROXO,
  });
}

function cartao(slide, o) {
  slide.addShape(pres.ShapeType.roundRect, {
    x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.09,
    fill: { color: o.fundo || CINZA_CLARO },
    line: { color: o.borda || "E3DDEE", width: 1 },
  });
}

// ------------------------------------------------------------------ 1. CAPA
{
  const s = pres.addSlide();
  s.background = { color: ROXO };
  s.addText("S2-CP01 · PROJETO MOTIVA · TEMA 2", {
    x: L, y: 1.5, w: LARG, h: 0.35, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 14, bold: true, color: OURO, charSpacing: 3,
  });
  s.addText("Sensoriamento da vegetação\ne qualidade da medição", {
    x: L, y: 2.0, w: LARG, h: 1.9, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 46, bold: true, color: BRANCO, lineSpacing: 52,
  });
  s.addText(
    "Por que medir altura de mato em centímetros é mais difícil — e mais decisivo — do que parece",
    {
      x: L, y: 4.1, w: 10.5, h: 0.5, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 16, color: "D9C9F2", italic: true,
    });
  s.addShape(pres.ShapeType.rect, {
    x: L, y: 5.0, w: 1.4, h: 0.05, fill: { color: OURO }, line: { color: OURO },
  });
  s.addText(`Turma ${TURMA}  ·  FIAP  ·  CP1`, {
    x: L, y: 5.35, w: LARG, h: 0.4, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 14, color: "D9C9F2",
  });
  s.addNotes(
    "0:00-0:30 — Abrir dizendo o problema, nao o tema: 'nosso projeto promete " +
    "dizer que ha 38 cm de mato, nao que ha mato. Esta aula e sobre como se " +
    "mede esse numero e por que quase todo sensor erra.'");
}

// ------------------------------------------------------- 2. QUEM FALA O QUE
{
  const s = pres.addSlide();
  tituloSlide(s, "Quem somos e o que cada um fez", "Grupo");
  const y0 = 1.9, alt = 0.72, gap = 0.12;
  INTEGRANTES.forEach((m, i) => {
    const y = y0 + i * (alt + gap);
    cartao(s, { x: L, y: y, w: LARG, h: alt });
    s.addShape(pres.ShapeType.ellipse, {
      x: L + 0.22, y: y + 0.17, w: 0.44, h: 0.44,
      fill: { color: ROXO }, line: { color: ROXO },
    });
    s.addText(String(i + 1), {
      x: L + 0.22, y: y + 0.17, w: 0.44, h: 0.44, isTextBox: true, margin: 0,
      align: "center", valign: "middle", fontFace: "Calibri", fontSize: 15,
      bold: true, color: BRANCO,
    });
    s.addText(`${m.nome}   ·   RM ${m.rm}`, {
      x: L + 0.85, y: y + 0.12, w: 5.6, h: 0.3, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 15, bold: true, color: TEXTO,
    });
    s.addText(m.papel, {
      x: L + 0.85, y: y + 0.42, w: 5.6, h: 0.28, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 12.5, color: CINZA,
    });
  });
  s.addNotes(
    "0:30-1:30 — Cada um diz o nome e a frente em que atuou. Manter curto: " +
    "uma frase por pessoa. O enunciado exige que todos falem e informem a " +
    "participacao no projeto.");
}

// ------------------------------------------------ 3. O PROBLEMA (caso real)
{
  const s = pres.addSlide();
  tituloSlide(s, "O problema começa com um número plausível", "Por que este tema");

  cartao(s, { x: L, y: 1.9, w: 5.75, h: 2.5, fundo: "FEF3F2", borda: "FECDCA" });
  s.addText("MEDIÇÃO REAL DO GRUPO", {
    x: L + 0.35, y: 2.1, w: 5.0, h: 0.3, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 11, bold: true, color: "912018", charSpacing: 1.5,
  });
  s.addText("38,5 cm", {
    x: L + 0.35, y: 2.42, w: 5.0, h: 0.9, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 54, bold: true, color: PERIGO,
  });
  s.addText("reportados onde havia ~10 cm.\nO operador informou 50 cm de trena; a foto mostrava 13,5 cm.", {
    x: L + 0.35, y: 3.3, w: 5.1, h: 0.9, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 13.5, color: "912018",
  });

  cartao(s, { x: L + 6.15, y: 1.9, w: 5.75, h: 2.5 });
  s.addText("O QUE ISSO ENSINA", {
    x: L + 6.5, y: 2.1, w: 5.0, h: 0.3, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 11, bold: true, color: CINZA, charSpacing: 1.5,
  });
  s.addText(
    [{ text: "38,5 cm é uma altura perfeitamente crível para mato de beira de estrada.", options: { bullet: true, breakLine: true } },
     { text: "Nada na foto, na máscara ou no JSON denunciava o erro.", options: { bullet: true, breakLine: true } },
     { text: "Erro de escala multiplica tudo por uma constante — e preserva a aparência de normalidade.", options: { bullet: true } }],
    { x: L + 6.5, y: 2.45, w: 5.1, h: 1.8, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 14, color: TEXTO, paraSpaceAfter: 8 });

  s.addText(
    "Erro de ruído se vê. Erro de escala, não. É por isso que a escolha do sensor importa.",
    { x: L, y: 4.7, w: LARG, h: 0.5, isTextBox: true, margin: 0,
      fontFace: "Cambria", fontSize: 19, bold: true, italic: true, color: ROXO });
  s.addNotes(
    "1:30-3:00 — Este e o gancho da aula. Contar o caso real. Enfatizar: o " +
    "sistema nao 'quebrou', ele respondeu um numero bonito e errado. " +
    "Perguntar a turma: como voces detectariam isso? Ninguem detecta olhando o " +
    "resultado — so comparando com uma segunda fonte.");
}

// -------------------------------------------- 4. O QUE OS SENSORES MEDEM
{
  const s = pres.addSlide();
  tituloSlide(s, "Nenhum sensor mede altura", "Fundamentação");
  s.addText("Todos medem distância. Altura é uma diferença:", {
    x: L, y: 1.75, w: LARG, h: 0.35, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 16, color: CINZA });

  cartao(s, { x: L, y: 2.2, w: LARG, h: 1.0, fundo: ROXO, borda: ROXO });
  s.addText("h  =  d(solo)  −  d(dossel)", {
    x: L, y: 2.2, w: LARG, h: 1.0, isTextBox: true, margin: 0,
    align: "center", valign: "middle",
    fontFace: "Cambria", fontSize: 32, bold: true, color: OURO });

  const consequencias = [
    { t: "O erro se compõe", d: "Duas medidas com desvio σ dão σ√2 na altura — 41% pior.\nMedir o solo toda vez PIORA o resultado.", cor: PERIGO },
    { t: "“Topo do dossel” é ambíguo", d: "Vegetação é meio poroso, não superfície. O feixe reflete na folha,\natravessa o vão ou chega ao solo.", cor: ROXO_CLARO },
  ];
  consequencias.forEach((c, i) => {
    const x = L + i * 6.15;
    cartao(s, { x: x, y: 3.5, w: 5.75, h: 1.75 });
    s.addShape(pres.ShapeType.ellipse, {
      x: x + 0.3, y: 3.75, w: 0.38, h: 0.38,
      fill: { color: c.cor }, line: { color: c.cor } });
    s.addText(String(i + 1), {
      x: x + 0.3, y: 3.75, w: 0.38, h: 0.38, isTextBox: true, margin: 0,
      align: "center", valign: "middle", fontFace: "Calibri", fontSize: 14,
      bold: true, color: BRANCO });
    s.addText(c.t, {
      x: x + 0.82, y: 3.73, w: 4.7, h: 0.35, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 16, bold: true, color: TEXTO });
    s.addText(c.d, {
      x: x + 0.82, y: 4.12, w: 4.7, h: 1.0, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 13, color: CINZA });
  });
  s.addNotes(
    "3:00-4:00 — Ponto conceitual mais importante da aula. Escrever a formula " +
    "no quadro se ajudar. A consequencia (1) e contraintuitiva e vale " +
    "destacar: medir o solo a cada leitura parece mais seguro, mas degrada. " +
    "Dai vem a recomendacao de calibrar uma vez.");
}

// ------------------------------------- 5. ABERTURA DO FEIXE (o calculo)
{
  const s = pres.addSlide();
  tituloSlide(s, "A especificação que decide não é o alcance", "Cálculo");
  s.addText("É a abertura do feixe: ela define a área que o sensor integra numa leitura.", {
    x: L, y: 1.72, w: LARG, h: 0.35, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 15.5, color: CINZA });

  cartao(s, { x: L, y: 2.15, w: 3.5, h: 0.72, fundo: ROXO, borda: ROXO });
  s.addText("D = 2 · d · tan(θ/2)", {
    x: L, y: 2.15, w: 3.5, h: 0.72, isTextBox: true, margin: 0,
    align: "center", valign: "middle",
    fontFace: "Cambria", fontSize: 19, bold: true, color: OURO });

  const linhas = [
    ["Sensor", "θ", "D a 1 m", "Consequência"],
    ["HC-SR04 (ultrassom)", "< 15°", "26 cm", "Média de uma área grande — não resolve moita"],
    ["VL53L1X (ToF)", "27°", "48 cm", "Área ainda maior; mitigável por ROI"],
    ["TF-Luna (LiDAR)", "2,3°", "4 cm", "Resolve o alvo — mas amostra um só ponto"],
  ];
  s.addTable(
    linhas.map((r, i) => r.map((c) => ({
      text: c,
      options: {
        fontFace: "Calibri", fontSize: i === 0 ? 12.5 : 13.5,
        bold: i === 0, color: i === 0 ? BRANCO : TEXTO,
        fill: { color: i === 0 ? ROXO : (i % 2 ? BRANCO : CINZA_CLARO) },
        valign: "middle",
      },
    }))),
    { x: L, y: 3.1, w: LARG, colW: [3.0, 1.1, 1.4, 6.4], rowH: 0.46,
      border: { type: "solid", color: "E3DDEE", pt: 1 } });

  s.addText(
    "Compromisso real: feixe largo perde o alvo na média; feixe estreito cai no vão entre folhas. A saída é amostrar N vezes e usar a MEDIANA.",
    { x: L, y: 5.35, w: LARG, h: 0.6, isTextBox: true, margin: 0,
      fontFace: "Cambria", fontSize: 16, bold: true, italic: true, color: ROXO });
  s.addNotes(
    "4:00-5:15 — Fazer a conta no quadro para um caso: tan(7,5 graus)=0,132, " +
    "logo 2 x 1 m x 0,132 = 26 cm. Perguntar a turma o que acontece com uma " +
    "moita de 20 cm dentro de um circulo de 26 cm: ela vira media com o chao. " +
    "Fonte dos angulos: datasheets ST, Benewake e HC-SR04.");
}

// -------------------------------------- 6. O TESTE NUMERICO (grafico)
{
  const s = pres.addSlide();
  tituloSlide(s, "Ultrassom aguenta a nossa faixa de decisão?", "Verificação");

  s.addChart(pres.ChartType.bar, [
    { name: "RMSE mínimo (cm)", labels: ["Trigo (dossel denso)", "Milho (dossel esparso)"], values: [3.7, 8.1] },
    { name: "RMSE máximo (cm)", labels: ["Trigo (dossel denso)", "Milho (dossel esparso)"], values: [4.7, 9.4] },
  ], {
    x: L, y: 1.85, w: 6.9, h: 3.7,
    barDir: "col", chartColors: [ROXO_CLARO, PERIGO],
    showTitle: true, title: "Erro medido após calibração (Zheng et al., 2024)",
    titleFontFace: "Calibri", titleFontSize: 13, titleColor: TEXTO,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 11,
    dataLabelColor: TEXTO, dataLabelFontFace: "Calibri",
    showLegend: true, legendPos: "b", legendFontSize: 10,
    catAxisLabelColor: CINZA, valAxisLabelColor: CINZA,
    catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
    valGridLine: { color: "E3DDEE", size: 1 },
    catGridLine: { style: "none" },
    valAxisTitle: "cm", showValAxisTitle: true, valAxisTitleFontSize: 10,
  });

  cartao(s, { x: L + 7.2, y: 1.85, w: 4.7, h: 1.65 });
  s.addText("NOSSO REQUISITO", {
    x: L + 7.5, y: 2.02, w: 4.1, h: 0.28, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 11, bold: true, color: CINZA, charSpacing: 1.5 });
  s.addText("σ ≤ 5 cm", {
    x: L + 7.5, y: 2.3, w: 4.1, h: 0.62, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 32, bold: true, color: ROXO });
  s.addText("Bandas de risco têm 20 cm\n(atenção 25 cm · crítico 45 cm)", {
    x: L + 7.5, y: 2.92, w: 4.1, h: 0.5, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12.5, color: CINZA });

  cartao(s, { x: L + 7.2, y: 3.7, w: 4.7, h: 1.85, fundo: "FEF3F2", borda: "FECDCA" });
  s.addText("Grama de 5–6 cm", {
    x: L + 7.5, y: 3.9, w: 4.1, h: 0.32, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 15, bold: true, color: "912018" });
  s.addText(
    "Com RMSE de 8–9 cm, o erro é MAIOR que a grandeza medida.\n\nUltrassom separa “tranquilo” de “crítico” em mato alto — não acompanha crescimento de grama baixa.",
    { x: L + 7.5, y: 4.22, w: 4.1, h: 1.25, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 12.5, color: "912018" });

  s.addNotes(
    "5:15-6:45 — Aqui esta o conteudo tecnico mais forte. Fonte revisada por " +
    "pares: Zheng et al. 2024, Frontiers in Plant Science, sensor industrial " +
    "ToughSonic, JA CALIBRADO. Se ate um sensor industrial calibrado erra 8-9 cm " +
    "em dossel esparso, um HC-SR04 de 20 reais nao vai fazer melhor. " +
    "Conclusao: ultrassom nao serve para o nosso alvo.");
}

// ------------------------------------------- 7. O SEGUNDO ERRO: PROFUNDIDADE
{
  const s = pres.addSlide();
  tituloSlide(s, "O segundo erro: 41,6 cm numa grama de 5–6 cm", "Caso Motiva");

  cartao(s, { x: L, y: 1.85, w: 5.75, h: 3.4 });
  s.addText("O que aconteceu", {
    x: L + 0.35, y: 2.05, w: 5.0, h: 0.32, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 16, bold: true, color: TEXTO });
  s.addText(
    [{ text: "Depois de corrigir a escala, o erro persistiu.", options: { bullet: true, breakLine: true } },
     { text: "A máscara de vegetação capturava a faixa de grama inteira — do pé da câmera ao horizonte.", options: { bullet: true, breakLine: true } },
     { text: "A extensão vertical dessa região não é a altura de planta nenhuma.", options: { bullet: true } }],
    { x: L + 0.35, y: 2.45, w: 5.1, h: 1.6, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 14, color: TEXTO, paraSpaceAfter: 9 });
  s.addText("Grama distante aparece mais alta no quadro sem ser mais alta.", {
    x: L + 0.35, y: 4.3, w: 5.1, h: 0.7, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 15, bold: true, italic: true, color: PERIGO });

  cartao(s, { x: L + 6.15, y: 1.85, w: 5.75, h: 3.4, fundo: ROXO, borda: ROXO });
  s.addText("Por que isso importa para o tema", {
    x: L + 6.5, y: 2.05, w: 5.1, h: 0.32, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 16, bold: true, color: OURO });
  s.addText(
    "Não é problema de segmentação.\nÉ falta de PROFUNDIDADE.",
    { x: L + 6.5, y: 2.5, w: 5.1, h: 0.8, isTextBox: true, margin: 0,
      fontFace: "Cambria", fontSize: 22, bold: true, color: BRANCO });
  s.addText(
    "Uma imagem RGB não sabe a distância de cada pixel. Segmentador melhor segmentaria a faixa perfeitamente — e ela continuaria sendo uma coisa só.\n\nUm sensor de distância fornece exatamente o dado que falta.",
    { x: L + 6.5, y: 3.35, w: 5.1, h: 1.7, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 13.5, color: "D9C9F2" });

  s.addNotes(
    "6:45-7:45 — Esta e a ponte entre o nosso projeto e a proposta. Deixar " +
    "claro que trocar de algoritmo NAO resolve; e limitacao de informacao, nao " +
    "de processamento. Se perguntarem: sim, existe profundidade monocular " +
    "(Depth Anything V2, Metric3D), mas custa modelo grande e GPU.");
}

// ------------------------------------------------------------- 8. PROPOSTA
{
  const s = pres.addSlide();
  tituloSlide(s, "Proposta: LiDAR de ponto único + câmera", "Recomendação do grupo");

  const razoes = [
    { n: "Sol pleno", d: "70 klux (TFmini-S) e operação acima de 100 klux (TF-Luna). Única categoria que sobrevive a céu aberto.", cor: OURO },
    { n: "Resolução", d: "Footprint de 4 cm a 1 m: resolve a moita em vez de mediar a faixa.", cor: VERDE },
    { n: "Profundidade", d: "Fornece a distância que falta à imagem — dispensa a trena no quadro.", cor: ROXO_CLARO },
  ];
  razoes.forEach((r, i) => {
    const x = L + i * 4.05;
    cartao(s, { x: x, y: 1.9, w: 3.8, h: 2.2 });
    s.addShape(pres.ShapeType.ellipse, {
      x: x + 0.3, y: 2.15, w: 0.42, h: 0.42,
      fill: { color: r.cor }, line: { color: r.cor } });
    s.addText(String(i + 1), {
      x: x + 0.3, y: 2.15, w: 0.42, h: 0.42, isTextBox: true, margin: 0,
      align: "center", valign: "middle", fontFace: "Calibri", fontSize: 15,
      bold: true, color: i === 0 ? TEXTO : BRANCO });
    s.addText(r.n, {
      x: x + 0.3, y: 2.7, w: 3.2, h: 0.32, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 16, bold: true, color: TEXTO });
    s.addText(r.d, {
      x: x + 0.3, y: 3.05, w: 3.2, h: 0.95, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 12.5, color: CINZA });
  });

  cartao(s, { x: L, y: 4.35, w: LARG, h: 1.15, fundo: "FFF8E1", borda: OURO });
  s.addText("Calibrar a geometria UMA vez, não a cada leitura", {
    x: L + 0.35, y: 4.5, w: 11.2, h: 0.32, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 15, bold: true, color: "7A5C00" });
  s.addText(
    "Medir o solo toda vez compõe erro (σ√2). Com montagem rígida, d(solo) é constante — o projeto já faz isso em vision/calibracao.json, que guarda a escala e a geometria e avisa após 7 dias.",
    { x: L + 0.35, y: 4.82, w: 11.2, h: 0.55, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 12.5, color: "7A5C00" });

  s.addNotes(
    "7:45-8:45 — Recomendacao objetiva e justificada, que e o que o criterio " +
    "'Aplicacao ao projeto' cobra. Amarrar com o slide anterior: o LiDAR entra " +
    "porque resolve o problema de profundidade que documentamos, nao porque e " +
    "a tecnologia mais nova.");
}

// -------------------------------------------------- 9. FLUXO EMBARCADO
{
  const s = pres.addSlide();
  tituloSlide(s, "Como a leitura vira decisão", "Fluxo proposto");

  const etapas = [
    { n: "1", t: "Amostrar", d: "15 leituras\na ~100 Hz" },
    { n: "2", t: "Filtrar", d: "Descarta fora\nda janela válida" },
    { n: "3", t: "Mediana", d: "Rejeita o vão\nentre folhas" },
    { n: "4", t: "Dispersão", d: "Alta? RECUSA\ne sinaliza" },
    { n: "5", t: "Converter", d: "h = d(solo)\n− mediana" },
    { n: "6", t: "Decidir", d: "Cruzou limiar?\nTransmite" },
  ];
  const larg = 1.82, gap = 0.19;
  etapas.forEach((e, i) => {
    const x = L + i * (larg + gap);
    const destaque = e.n === "4";
    cartao(s, {
      x: x, y: 2.15, w: larg, h: 2.1,
      fundo: destaque ? "FEF3F2" : CINZA_CLARO,
      borda: destaque ? "FECDCA" : "E3DDEE",
    });
    s.addShape(pres.ShapeType.ellipse, {
      x: x + larg / 2 - 0.21, y: 2.35, w: 0.42, h: 0.42,
      fill: { color: destaque ? PERIGO : ROXO }, line: { color: destaque ? PERIGO : ROXO } });
    s.addText(e.n, {
      x: x + larg / 2 - 0.21, y: 2.35, w: 0.42, h: 0.42, isTextBox: true, margin: 0,
      align: "center", valign: "middle", fontFace: "Calibri", fontSize: 14,
      bold: true, color: BRANCO });
    s.addText(e.t, {
      x: x, y: 2.9, w: larg, h: 0.3, isTextBox: true, margin: 0, align: "center",
      fontFace: "Calibri", fontSize: 14, bold: true,
      color: destaque ? "912018" : TEXTO });
    s.addText(e.d, {
      x: x + 0.1, y: 3.22, w: larg - 0.2, h: 0.9, isTextBox: true, margin: 0,
      align: "center", fontFace: "Calibri", fontSize: 11.5,
      color: destaque ? "912018" : CINZA });
  });

  s.addText(
    "Mediana, não média: o vão entre folhas é outlier assimétrico — média o absorve, mediana o rejeita.",
    { x: L, y: 4.55, w: LARG, h: 0.4, isTextBox: true, margin: 0,
      fontFace: "Cambria", fontSize: 16, bold: true, italic: true, color: ROXO });
  s.addText(
    "Etapa 4 é a regra que vale mais que todas: sem confiança, não se reporta número. Recusar medir é melhor que medir errado em silêncio.",
    { x: L, y: 5.0, w: LARG, h: 0.4, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 14, color: CINZA });

  s.addNotes(
    "8:45-9:30 — Explicar por que mediana e nao media (pergunta provavel do " +
    "professor). Destacar a etapa 4: e a licao que veio dos nossos dois erros " +
    "de campo, e ja esta implementada no pipeline.");
}

// ----------------------------------------------------------- 10. CONCLUSAO
{
  const s = pres.addSlide();
  s.background = { color: ROXO };
  s.addText("O QUE FICA", {
    x: L, y: 0.75, w: LARG, h: 0.35, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 13, bold: true, color: OURO, charSpacing: 2.5 });
  s.addText("Decisões recomendadas", {
    x: L, y: 1.1, w: LARG, h: 0.7, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 36, bold: true, color: BRANCO });

  const decisoes = [
    ["Adotar LiDAR de ponto único", "Única categoria com tolerância a sol pleno e footprint compatível"],
    ["Descartar ultrassom como primário", "RMSE de 8–9 cm excede a resolução que a nossa faixa exige"],
    ["Fundir o sensor com a câmera", "Ele entrega a profundidade que a imagem RGB não tem"],
    ["Calibrar a geometria uma vez", "Evita compor erro e deixa a medição auditável"],
    ["Recusar em vez de estimar", "Validado por dois erros de campo documentados"],
  ];
  decisoes.forEach((d, i) => {
    const y = 2.15 + i * 0.66;
    s.addShape(pres.ShapeType.ellipse, {
      x: L, y: y + 0.05, w: 0.3, h: 0.3,
      fill: { color: OURO }, line: { color: OURO } });
    s.addText(d[0], {
      x: L + 0.5, y: y, w: 4.9, h: 0.36, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 15, bold: true, color: BRANCO });
    s.addText(d[1], {
      x: L + 5.5, y: y + 0.02, w: 6.4, h: 0.36, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 13, color: "D9C9F2" });
  });

  s.addText(
    "Limitação assumida: não ensaiamos LiDAR nem ultrassom. Bancada contra medição manual é o próximo passo.",
    { x: L, y: 5.7, w: LARG, h: 0.4, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 13, italic: true, color: OURO });

  s.addNotes(
    "9:30-10:00 — Fechar com as decisoes, nao com resumo. A ultima linha e " +
    "deliberada: admitir o que nao foi testado da credibilidade e antecipa a " +
    "pergunta obvia do professor.");
}

// --------------------------------------------------------- 11. REFERENCIAS
{
  const s = pres.addSlide();
  tituloSlide(s, "Referências", "Fontes");
  const refs = [
    ["[2] STMicroelectronics", "VL53L1X Datasheet DS13088 — alcance, FoV 27°, modos de distância e luz ambiente"],
    ["[3] Handson Technology", "HC-SR04 Ultrasonic Sensor Module — User Guide (2–400 cm, ângulo < 15°)"],
    ["[4] Sharp Corporation", "GP2Y0A21YK0F Datasheet — 10–80 cm, saída não linear por triangulação"],
    ["[5] Zheng, H. et al. (2024)", "Calibrating ultrasonic sensor measurements of crop canopy heights.\nFrontiers in Plant Science, v. 15. DOI: 10.3389/fpls.2024.1354359"],
    ["[6] Benewake", "TFmini-S Product Specification — 70 klux, ± 6 cm em 0,1–6 m"],
    ["[7] Benewake", "TF-Luna Datasheet SJ-GU-TF-Luna-A01 — ângulo 2,3°, 0,2–8 m"],
  ];
  refs.forEach((r, i) => {
    const y = 1.85 + i * 0.68;
    s.addText(r[0], {
      x: L, y: y, w: 3.1, h: 0.36, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 13.5, bold: true, color: ROXO });
    s.addText(r[1], {
      x: L + 3.2, y: y, w: 8.7, h: 0.6, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 12.5, color: CINZA });
  });
  s.addText(
    "Datasheets consultados nas páginas oficiais dos fabricantes. [5] é revisado por pares (PMC11188359). Tabelas de footprint e de adequação são cálculos do grupo a partir desses parâmetros.",
    { x: L, y: 6.0, w: LARG, h: 0.5, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 11.5, italic: true, color: CINZA });
  s.addNotes("Slide de apoio para as perguntas. Nao apresentar linha a linha.");
}

const destino = path.join(__dirname, "S2-CP1-Motiva-Tema2-Aula.pptx");
pres.writeFile({ fileName: destino }).then(() => {
  console.log("Deck gerado:", destino);
});
