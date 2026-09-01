"""Gera o PDF da documentacao tecnica do S2-CP01 (Tema 2).

Roda com o venv de vision/, que ja tem reportlab:
    cd docs/S2-CP1
    ../../vision/.venv/Scripts/python gerar_documentacao.py

O conteudo fica neste arquivo de proposito: o time edita texto e numeros aqui e
regera o PDF, sem depender de editor externo.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


class DocumentoComIndice(BaseDocTemplate):
    """Registra a pagina de cada secao, para o indice sair correto.

    O indice e montado em duas passagens: a primeira descobre onde cada secao
    caiu, a segunda escreve os numeros certos. Indice com pagina errada e
    exatamente o tipo de detalhe que derruba nota em organizacao.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.paginas_das_secoes: dict[str, int] = {}

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        nome = getattr(flowable.style, "name", "")
        if nome not in ("H1", "H2"):
            return
        texto = flowable.getPlainText().strip()
        numero = texto.split(" ", 1)[0].rstrip(".")
        if numero and (numero[0].isdigit()):
            self.paginas_das_secoes.setdefault(numero, self.page)

# Identidade visual do projeto.
ROXO = colors.HexColor("#2E0854")
ROXO_CLARO = colors.HexColor("#4B1F80")
OURO = colors.HexColor("#F2B705")
CINZA = colors.HexColor("#675E78")
BORDA = colors.HexColor("#CFC6E0")
FUNDO_SUAVE = colors.HexColor("#F6F4FA")
PERIGO = colors.HexColor("#D92D20")

SAIDA = Path(__file__).resolve().parent / "S2-CP1-Motiva-Tema2-Sensoriamento.pdf"

# --- PREENCHER ANTES DA ENTREGA ---------------------------------------------
TURMA = "2CCPO"
INTEGRANTES = [
    ("Bento Donato Garcia", "561621"),
    ("Enzo Ribeiro Domingues Piazentin", "564216"),
    ("Guilherme Domingues Califoni", "565157"),
    ("Antonio Lucas Santana Tavares", "565516"),
    ("Lucas M.", "563667"),
    ("Gustavo Schimith", "564800"),
]
# ----------------------------------------------------------------------------

estilos = getSampleStyleSheet()

E_TITULO_CAPA = ParagraphStyle(
    "TituloCapa", parent=estilos["Title"], fontSize=26, leading=32,
    textColor=ROXO, spaceAfter=6,
)
E_SUB_CAPA = ParagraphStyle(
    "SubCapa", parent=estilos["Normal"], fontSize=13, leading=18,
    textColor=CINZA, alignment=TA_CENTER,
)
E_H1 = ParagraphStyle(
    "H1", parent=estilos["Heading1"], fontSize=16, leading=20,
    textColor=ROXO, spaceBefore=18, spaceAfter=10,
)
E_H2 = ParagraphStyle(
    "H2", parent=estilos["Heading2"], fontSize=12.5, leading=16,
    textColor=ROXO_CLARO, spaceBefore=12, spaceAfter=6,
)
E_CORPO = ParagraphStyle(
    "Corpo", parent=estilos["Normal"], fontSize=10, leading=15,
    alignment=TA_JUSTIFY, spaceAfter=8,
)
E_LISTA = ParagraphStyle(
    "Lista", parent=E_CORPO, leftIndent=14, bulletIndent=4, spaceAfter=4,
)
E_TABELA = ParagraphStyle(
    "Tabela", parent=estilos["Normal"], fontSize=8.5, leading=11.5,
)
E_TABELA_CAB = ParagraphStyle(
    "TabelaCab", parent=E_TABELA, textColor=colors.white, fontName="Helvetica-Bold",
)
E_LEGENDA = ParagraphStyle(
    "Legenda", parent=estilos["Normal"], fontSize=8.5, leading=11,
    textColor=CINZA, spaceAfter=12,
)
E_REF = ParagraphStyle(
    "Ref", parent=estilos["Normal"], fontSize=9, leading=13,
    spaceAfter=7, leftIndent=16, firstLineIndent=-16,
)
E_DESTAQUE = ParagraphStyle(
    "Destaque", parent=E_CORPO, leftIndent=10, rightIndent=10,
    spaceBefore=6, spaceAfter=10, borderPadding=8,
    backColor=FUNDO_SUAVE, borderColor=BORDA, borderWidth=0.6,
)


def p(texto: str, estilo: ParagraphStyle = E_CORPO) -> Paragraph:
    return Paragraph(texto, estilo)


def item(texto: str) -> Paragraph:
    return Paragraph(texto, E_LISTA, bulletText="•")


def tabela(dados: list[list[str]], larguras: list[float], destaque_linha: int | None = None) -> Table:
    corpo = [[Paragraph(c, E_TABELA_CAB if i == 0 else E_TABELA) for c in linha]
             for i, linha in enumerate(dados)]
    t = Table(corpo, colWidths=larguras, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), ROXO),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDA),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FUNDO_SUAVE]),
    ]
    if destaque_linha is not None:
        estilo += [
            ("BACKGROUND", (0, destaque_linha), (-1, destaque_linha), colors.HexColor("#FFF4CC")),
            ("BOX", (0, destaque_linha), (-1, destaque_linha), 1.2, OURO),
        ]
    t.setStyle(TableStyle(estilo))
    return t


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(BORDA)
    canvas.setLineWidth(0.5)
    canvas.line(2.2 * cm, 1.6 * cm, A4[0] - 2.2 * cm, 1.6 * cm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(CINZA)
    canvas.drawString(2.2 * cm, 1.15 * cm,
                      "S2-CP01 — Projeto Motiva | Tema 2: Sensoriamento da vegetação e qualidade da medição")
    canvas.drawRightString(A4[0] - 2.2 * cm, 1.15 * cm, f"{doc.page}")
    canvas.restoreState()


def construir(paginas: dict[str, int] | None = None) -> dict[str, int]:
    paginas = paginas or {}
    doc = DocumentoComIndice(
        str(SAIDA), pagesize=A4,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm,
        topMargin=2.0 * cm, bottomMargin=2.2 * cm,
        title="S2-CP01 Projeto Motiva — Tema 2",
        author="Grupo Motiva-Field",
    )
    quadro = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="corpo")
    doc.addPageTemplates([PageTemplate(id="padrao", frames=[quadro], onPage=rodape)])

    h: list = []

    # ---------------------------------------------------------------- CAPA --
    h.append(Spacer(1, 3.2 * cm))
    h.append(p("S2-CP01 — PROJETO MOTIVA",
               ParagraphStyle("eyebrow", parent=E_SUB_CAPA, fontSize=10,
                              textColor=OURO, spaceAfter=10)))
    h.append(p("Sensoriamento da vegetação<br/>e qualidade da medição", E_TITULO_CAPA))
    h.append(Spacer(1, 0.3 * cm))
    h.append(p("Tema 2 — Comparação entre infravermelho, ultrassom, "
               "Time-of-Flight e LiDAR<br/>para medir altura de vegetação em faixa de "
               "domínio rodoviária", E_SUB_CAPA))
    h.append(Spacer(1, 2.2 * cm))

    linhas = [["Integrante", "RM"]] + [[n, r] for n, r in INTEGRANTES]
    h.append(tabela(linhas, [10.5 * cm, 4.5 * cm]))
    h.append(Spacer(1, 0.8 * cm))
    h.append(p(f"Turma: {TURMA}", E_SUB_CAPA))
    h.append(Spacer(1, 1.6 * cm))
    h.append(p("Documentação técnica — FIAP — CP1", E_SUB_CAPA))
    h.append(PageBreak())

    # -------------------------------------------------------------- ÍNDICE --
    h.append(p("Índice", E_H1))
    indice = [
        ("1.", "Introdução", "3"),
        ("2.", "Fundamentação técnica", "3"),
        ("2.1", "O que significa “medir altura de vegetação”", "3"),
        ("2.2", "Ultrassom", "4"),
        ("2.3", "Infravermelho por triangulação", "4"),
        ("2.4", "Time-of-Flight (ToF) de estado sólido", "4"),
        ("2.5", "LiDAR de ponto único", "5"),
        ("2.6", "Abertura do feixe: o parâmetro que decide", "5"),
        ("3.", "Comparação de alternativas", "6"),
        ("4.", "Aplicação ao projeto Motiva", "7"),
        ("4.1", "A faixa de medição que importa", "7"),
        ("4.2", "O erro que cometemos e o que ele ensina", "7"),
        ("4.3", "Verificação numérica de adequação", "8"),
        ("5.", "Proposta técnica do grupo", "9"),
        ("5.1", "Arquitetura de medição", "9"),
        ("5.2", "Fluxo de decisão embarcado", "10"),
        ("5.3", "Regras de qualidade do dado", "10"),
        ("6.", "Conclusão", "11"),
        ("7.", "Referências", "11"),
    ]
    dados = [["", "Seção", "Pág."]]
    for n, titulo, _ in indice:
        chave = n.rstrip(".")
        dados.append([n, titulo, str(paginas.get(chave, "—"))])
    h.append(tabela(dados, [1.4 * cm, 12.1 * cm, 1.5 * cm]))
    h.append(PageBreak())

    # --------------------------------------------------------- INTRODUÇÃO --
    h.append(p("1. Introdução", E_H1))
    h.append(p(
        "O projeto Motiva-Field monitora vegetação na faixa de domínio de rodovias "
        "para prever quando cada trecho precisará de roçada. O valor comercial do "
        "sistema não está em detectar que “há mato”, e sim em afirmar que "
        "<b>há 38 cm de mato</b> — porque é o número que permite projetar "
        "crescimento, priorizar equipes e comprovar serviço."))
    h.append(p(
        "Toda a cadeia do produto depende, portanto, de uma única grandeza física: a "
        "<b>altura da vegetação em centímetros</b>. Se essa medida for imprecisa "
        "ou, pior, sistematicamente enviesada, o erro se propaga silenciosamente para a "
        "projeção de crescimento e para o planejamento de roçada. Um número "
        "errado não parece errado: ele apenas produz uma decisão errada meses depois."))
    h.append(p(
        "Este documento investiga as tecnologias de sensoriamento aplicáveis a essa "
        "medição — infravermelho, ultrassom, Time-of-Flight e LiDAR — "
        "compara seus limites reais com base em datasheets de fabricantes e literatura "
        "revisada por pares, e propõe uma arquitetura de medição justificada "
        "para o protótipo. A análise é ancorada em <b>medições reais "
        "já realizadas pelo grupo</b>, incluindo um erro de escala que ilustra "
        "exatamente o risco descrito acima."))

    # ------------------------------------------------------ FUNDAMENTAÇÃO --
    h.append(p("2. Fundamentação técnica", E_H1))

    h.append(p("2.1 O que significa “medir altura de vegetação”", E_H2))
    h.append(p(
        "Nenhum dos sensores estudados mede altura. Todos medem <b>distância até "
        "uma superfície refletora</b>. A altura é obtida por diferença:"))
    h.append(p(
        "<b>h = d<sub>solo</sub> − d<sub>dossel</sub></b>", ParagraphStyle(
            "formula", parent=E_CORPO, alignment=TA_CENTER, fontSize=12,
            spaceBefore=6, spaceAfter=6, textColor=ROXO)))
    h.append(p(
        "onde d<sub>solo</sub> é a distância do sensor ao solo nu e "
        "d<sub>dossel</sub> a distância ao topo da vegetação. Essa formulação "
        "traz duas consequências que orientam todo o resto deste documento."))
    h.append(item(
        "<b>O erro se compõe.</b> Se as duas distâncias forem medidas com desvio "
        "σ, o desvio da altura é σ<sub>h</sub> = σ·√2 — "
        "cerca de 41% pior que o do sensor isolado. Medir o solo a cada leitura "
        "<i>degrada</i> o resultado."))
    h.append(item(
        "<b>“Topo do dossel” é ambíguo.</b> Vegetação não "
        "é superfície sólida: é um meio poroso. O feixe pode refletir na "
        "primeira folha, atravessar o vão entre folhas e atingir o solo, ou retornar "
        "de um ponto intermediário. A leitura depende da densidade da vegetação "
        "e do ângulo de observação."))
    h.append(p(
        "Zheng <i>et al.</i> (2024) confirmam experimentalmente o segundo ponto: em ensaio "
        "com milho e trigo, <b>ângulo de observação e densidade de plantio "
        "afetaram significativamente</b> (p &lt; 0,05) a medição ultrassônica, "
        "enquanto altura de observação, horário e velocidade da plataforma "
        "tiveram efeito desprezível [5]."))

    h.append(p("2.2 Ultrassom", E_H2))
    h.append(p(
        "Emite pulso acústico (40 kHz no HC-SR04) e mede o tempo de retorno. A "
        "distância sai de d = v·t/2, com v ≈ 330–343 m/s. O módulo "
        "HC-SR04 cobre 2–400 cm com resolução declarada de 3 mm e ângulo "
        "efetivo menor que 15° [3]."))
    h.append(p(
        "<b>Limitação crítica:</b> a velocidade do som varia com a temperatura "
        "(aproximadamente +0,6 m/s por °C). Entre 0 °C e 40 °C a variação "
        "chega a ~7%, que a 1 m de distância representa 7 cm de erro sistemático se "
        "não houver compensação térmica. Vento e chuva também "
        "perturbam o meio de propagação."))

    h.append(p("2.3 Infravermelho por triangulação", E_H2))
    h.append(p(
        "Sensores como o Sharp GP2Y0A21YK0F combinam um LED infravermelho, um detector "
        "sensível à posição (PSD) e circuito de processamento. O alcance "
        "útil é de 10 a 80 cm e a saída é uma tensão analógica "
        "<b>não linear</b>: aproximadamente linear em relação ao "
        "<i>inverso</i> da distância, exigindo linearização em software [4]."))
    h.append(p(
        "A triangulação torna a leitura relativamente robusta a variações "
        "de refletividade do alvo e de temperatura [4]. Em contrapartida, o alcance curto "
        "e a sensibilidade à luz solar direta limitam severamente o uso em rodovia a "
        "céu aberto."))

    h.append(p("2.4 Time-of-Flight (ToF) de estado sólido", E_H2))
    h.append(p(
        "O VL53L1X integra emissor laser de 940 nm (Classe 1), matriz receptora SPAD e "
        "filtros ópticos. Alcance de até 4 m, distância mínima de 4 cm e "
        "campo de visão de 27° com todos os 265 elementos ativos. Possui "
        "<b>região de interesse programável</b>, que permite reduzir o FoV ou "
        "dividi-lo em zonas [2]."))
    h.append(p(
        "<b>Limitação crítica:</b> o modo de longa distância alcança "
        "4 m mas é <b>significativamente afetado por luz ambiente</b>; o modo curto "
        "é praticamente imune à luz ambiente, porém limita o alcance a "
        "cerca de 1,3 m [2]. Em rodovia sob sol pleno, essa é uma restrição "
        "de projeto, não um detalhe."))

    h.append(p("2.5 LiDAR de ponto único", E_H2))
    h.append(p(
        "Módulos como o Benewake TF-Luna e o TFmini-S usam o mesmo princípio ToF, "
        "mas com óptica colimada e maior potência óptica. O TFmini-S resiste a "
        "luz ambiente de até <b>70 klux</b> com acurácia de ± 6 cm na faixa "
        "de 0,1 a 6 m [6]. O TF-Luna tem ângulo de aceitação de apenas "
        "<b>2,3°</b>; sob sol de verão acima de 100 klux, o alcance efetivo cai "
        "para 3 m [7]."))
    h.append(p(
        "A tolerância a luz ambiente na casa das dezenas de klux é o que separa "
        "esta categoria das demais para uso a céu aberto: a irradiância solar em "
        "dia claro fica tipicamente entre 32 e 100 klux."))

    h.append(p("2.6 Abertura do feixe: o parâmetro que decide", E_H2))
    h.append(p(
        "A especificação mais determinante para medir vegetação não "
        "é alcance nem resolução, e sim a <b>abertura angular</b>. Ela define "
        "a área que o sensor integra numa única leitura. O diâmetro dessa "
        "área a uma distância d é:"))
    h.append(p("<b>D = 2 · d · tan(θ / 2)</b>", ParagraphStyle(
        "formula2", parent=E_CORPO, alignment=TA_CENTER, fontSize=12,
        spaceBefore=6, spaceAfter=8, textColor=ROXO)))
    h.append(tabela([
        ["Sensor", "Abertura θ", "D a 1 m", "D a 2 m", "Leitura resultante"],
        ["HC-SR04 (ultrassom)", "&lt; 15°", "26 cm", "53 cm",
         "Média sobre uma área grande; não resolve moita isolada"],
        ["VL53L1X (ToF)", "27°", "48 cm", "96 cm",
         "Área ainda maior; mitigável via ROI programável"],
        ["TF-Luna (LiDAR)", "2,3°", "4,0 cm", "8,0 cm",
         "Praticamente pontual; resolve o alvo, mas amostra um único ponto"],
    ], [3.6 * cm, 2.0 * cm, 1.7 * cm, 1.7 * cm, 6.0 * cm]))
    h.append(p(
        "Tabela 1 — Footprint do feixe calculado a partir das aberturas declaradas nos "
        "datasheets [2][3][7]. Valores arredondados.", E_LEGENDA))
    h.append(KeepTogether([p(
        "Há aqui um <b>compromisso genuíno</b>, e não uma escolha óbvia. "
        "Feixe largo mede a média de uma área — útil para dossel "
        "homogêneo, inútil para uma touceira de 30 cm. Feixe estreito resolve o "
        "alvo, mas uma única leitura pode cair no vão entre folhas e retornar a "
        "distância do solo. A solução não é escolher a abertura "
        "“certa”, e sim <b>amostrar várias vezes e tratar estatisticamente</b>.")]))

    # -------------------------------------------------------- COMPARAÇÃO --
    h.append(p("3. Comparação de alternativas", E_H1))
    h.append(tabela([
        ["Critério", "IR triangulação<br/>(GP2Y0A21)", "Ultrassom<br/>(HC-SR04)",
         "ToF<br/>(VL53L1X)", "LiDAR<br/>(TF-Luna)"],
        ["Faixa de medição", "10–80 cm", "2–400 cm", "4 cm–4 m", "0,2–8 m"],
        ["Abertura do feixe", "Estreita (PSD)", "&lt; 15°", "27° (ROI ajustável)", "2,3°"],
        ["Acurácia declarada", "Não linear; exige<br/>linearização", "± 3 mm (alvo rígido)",
         "mm em curta dist.", "± 6 cm (TFmini-S)"],
        ["Sol pleno<br/>(32–100 klux)", "Ruim", "Indiferente (acústico)",
         "Modo longo degrada;<br/>modo curto ≤ 1,3 m", "70–100 klux;<br/>3 m sob sol forte"],
        ["Chuva / poeira", "Degrada (óptico)", "Degrada (meio acústico)",
         "Degrada (óptico)", "Degrada (óptico)"],
        ["Temperatura", "Pouco sensível", "<b>Crítico:</b> v<sub>som</sub><br/>varia ~7% de 0–40 °C",
         "Pouco sensível", "Pouco sensível"],
        ["Custo relativo", "Muito baixo", "Muito baixo", "Baixo", "Médio"],
        ["Adequação ao<br/>cenário Motiva", "Inadequado:<br/>alcance e sol", "Limitado: ver §4.3",
         "Parcial: conflito<br/>alcance x luz", "<b>Recomendado</b>"],
    ], [2.9 * cm, 2.9 * cm, 3.1 * cm, 3.1 * cm, 3.0 * cm], destaque_linha=8))
    h.append(p(
        "Tabela 2 — Comparação consolidada. Dados de faixa, abertura e "
        "tolerância a luz ambiente extraídos dos datasheets [2][3][4][6][7]; "
        "avaliação de adequação é análise do grupo.", E_LEGENDA))

    h.append(KeepTogether([
        p("Critérios de escolha adotados", E_H2),
        p("Ordenados por peso na decisão, dado o cenário de rodovia a céu aberto:"),
        item("<b>Sobrevivência ao sol pleno.</b> Elimina qualquer sensor óptico "
             "sem tolerância declarada em dezenas de klux."),
        item("<b>Resolução espacial compatível com o alvo.</b> O footprint "
             "precisa ser menor que a moita medida."),
        item("<b>Incerteza compatível com a faixa de decisão.</b> Detalhado "
             "numericamente na seção 4.3."),
        item("<b>Estabilidade térmica.</b> Rodovia opera de 0 a 45 °C sem "
             "controle ambiental."),
    ]))

    h.append(PageBreak())

    # --------------------------------------------------------- APLICAÇÃO --
    h.append(p("4. Aplicação ao projeto Motiva", E_H1))

    h.append(p("4.1 A faixa de medição que importa", E_H2))
    h.append(p(
        "O software do projeto já define os limiares de decisão operacional, "
        "implementados em <font face='Courier'>vision/segmentacao.py</font>:"))
    h.append(tabela([
        ["Nível de risco", "Altura da vegetação", "Ação operacional"],
        ["Tranquilo", "&lt; 25 cm", "Apenas monitorar"],
        ["Atenção", "25 a 45 cm", "Programar roçada"],
        ["Crítico", "≥ 45 cm", "Roçada prioritária"],
    ], [4.0 * cm, 4.5 * cm, 6.5 * cm]))
    h.append(p("Tabela 3 — Limiares de decisão do projeto.", E_LEGENDA))
    h.append(p(
        "As bandas têm <b>20 cm de largura</b>. Esse número é o requisito "
        "quantitativo que o sensor precisa atender — e é contra ele que a "
        "seção 4.3 verifica cada tecnologia."))

    h.append(p("4.2 O erro que cometemos e o que ele ensina", E_H2))
    h.append(p(
        "Na primeira medição real, o grupo mediu vegetação por fotografia "
        "usando uma trena como referência de escala. O operador informou que "
        "aproximadamente 50 cm de fita estavam esticados, quando na foto apareciam cerca "
        "de 13,5 cm. O sistema reportou <b>38,5 cm de vegetação onde havia "
        "aproximadamente 10 cm</b>."))
    h.append(p(
        "O ponto pedagógico não é o erro de digitação. É que "
        "<b>o resultado permaneceu plausível</b>: 38,5 cm é uma altura "
        "perfeitamente crível para mato de beira de estrada. Nada na foto, na "
        "máscara de vegetação ou no JSON denunciava o problema. Um erro de "
        "escala multiplica <i>toda</i> a medição por um fator constante e "
        "preserva a aparência de normalidade.", E_DESTAQUE))
    h.append(p(
        "Duas consequências foram incorporadas ao projeto e valem como recomendação "
        "para qualquer arquitetura de sensoriamento:"))
    h.append(item(
        "<b>Nunca estimar escala.</b> Quando a referência não é encontrada, "
        "o sistema levanta exceção em vez de retornar um valor padrão. "
        "Recusar medir é melhor que medir errado em silêncio."))
    h.append(item(
        "<b>Redundância com comparação explícita.</b> Quando duas vias "
        "de escala estão disponíveis, ambas são calculadas e comparadas; "
        "divergência acima de 15% gera aviso identificando o valor de cada via."))
    h.append(p(
        "Um segundo episódio reforça o argumento. Após corrigir a escala, o "
        "sistema ainda reportou <b>41,6 cm para uma grama de 5 a 6 cm</b>. A causa foi "
        "diferente: a máscara de vegetação capturava a faixa de grama "
        "inteira, do pé da câmera até o horizonte, e a extensão vertical "
        "dessa região não corresponde à altura de nenhuma planta. <b>Grama "
        "distante aparece mais alta no quadro sem ser mais alta.</b>"))
    h.append(p(
        "Esse segundo erro é exatamente o que um sensor de distância resolve: ele "
        "fornece a <b>profundidade</b> que uma única imagem RGB não contém. "
        "É a justificativa central da proposta da seção 5."))

    h.append(p("4.3 Verificação numérica de adequação", E_H2))
    h.append(p(
        "Para classificar corretamente em bandas de 20 cm, a incerteza da medição "
        "precisa ser pequena frente à banda. Adotando o critério de que o intervalo "
        "de 95% de confiança (≈ 2σ) deve caber na metade da banda, chega-se ao "
        "requisito <b>σ ≤ 5 cm</b>."))
    h.append(p(
        "Zheng <i>et al.</i> (2024) mediram, com sensor ultrassônico industrial "
        "(ToughSonic TSPC-15) e <b>após calibração</b>, RMSE de 81,4 a "
        "93,6 mm em milho e 37,1 a 47,2 mm em trigo [5]. Aplicando ao nosso caso:"))
    h.append(tabela([
        ["Cenário", "RMSE (σ)", "Intervalo 2σ", "Cabe em banda de 20 cm?"],
        ["Trigo (dossel denso, homogêneo)", "3,7–4,7 cm", "± 7,4 a 9,4 cm",
         "Marginal"],
        ["Milho (dossel esparso, irregular)", "8,1–9,4 cm", "± 16,2 a 18,8 cm",
         "<b>Não</b>"],
        ["Grama de 5–6 cm (nosso caso)", "8,1–9,4 cm", "± 16,2 a 18,8 cm",
         "<b>Erro maior que o alvo</b>"],
    ], [5.2 * cm, 2.6 * cm, 3.2 * cm, 4.0 * cm], destaque_linha=3))
    h.append(p(
        "Tabela 4 — Confronto entre a incerteza medida na literatura [5] e o requisito "
        "do projeto. A última linha aplica o RMSE de dossel esparso ao caso de grama "
        "baixa observado em campo.", E_LEGENDA))
    h.append(p(
        "A conclusão é dura e precisa ser dita: para vegetação rasteira "
        "de 5 a 6 cm, <b>a incerteza típica de um sensor ultrassônico calibrado "
        "é maior que a própria grandeza medida</b>. Ultrassom serve para "
        "distinguir “tranquilo” de “crítico” em vegetação "
        "alta; não serve para acompanhar crescimento de grama baixa, que é "
        "justamente onde a projeção do produto precisa de resolução.",
        E_DESTAQUE))

    h.append(PageBreak())

    # ----------------------------------------------------------- PROPOSTA --
    h.append(p("5. Proposta técnica do grupo", E_H1))

    h.append(p("5.1 Arquitetura de medição", E_H2))
    h.append(p(
        "Recomendamos <b>LiDAR de ponto único (Benewake TF-Luna ou TFmini-S) "
        "solidário à câmera</b>, com montagem rígida e geometria "
        "calibrada uma única vez. A justificativa é tripla:"))
    h.append(item(
        "<b>É a única categoria com tolerância declarada a sol pleno</b> "
        "(70 klux no TFmini-S, operação especificada acima de 100 klux no "
        "TF-Luna) [6][7]. O ToF de estado sólido perde alcance sob luz ambiente e o "
        "IR não sobrevive."))
    h.append(item(
        "<b>Footprint de 4 cm a 1 m</b> (Tabela 1) é menor que a moita alvo, "
        "permitindo resolver vegetação individual em vez de uma média da faixa."))
    h.append(item(
        "<b>Fornece a profundidade que falta à câmera.</b> Com a distância "
        "conhecida, a conversão pixel→centímetro passa a ser geométrica, "
        "dispensando a trena no quadro — exatamente o mecanismo que falhou na "
        "seção 4.2."))

    h.append(p("<b>Calibração da referência de solo.</b> Como demonstrado em 2.1, "
               "medir o solo a cada leitura degrada a incerteza em √2. Recomendamos "
               "medir d<sub>solo</sub> <b>uma única vez</b>, com o suporte instalado, e "
               "persistir o valor junto com a geometria (altura e ângulo da câmera). "
               "O projeto já adota esse padrão em "
               "<font face='Courier'>vision/calibracao.json</font>, que armazena "
               "<font face='Courier'>pixels_por_cm</font> e a geometria de captura, e "
               "emite alerta quando a calibração passa de 7 dias."))

    h.append(p("5.2 Fluxo de decisão embarcado", E_H2))
    fluxo = [
        ("1", "Acordar", "Timer ou gatilho de posição (ponto cadastrado da rodovia)."),
        ("2", "Amostrar", "N = 15 leituras de distância a ~100 Hz sobre o mesmo alvo."),
        ("3", "Filtrar", "Descartar leituras fora de [d<sub>solo</sub> − 200 cm, d<sub>solo</sub>]; "
                         "aplicar <b>mediana</b>, não média — mediana rejeita o "
                         "vão entre folhas, que é outlier assimétrico."),
        ("4", "Avaliar<br/>dispersão", "Se o desvio interquartil exceder o limiar, a leitura "
                                          "é <b>recusada</b> e sinalizada. Não se reporta "
                                          "número de baixa confiança."),
        ("5", "Converter", "h = d<sub>solo</sub> − mediana(d<sub>dossel</sub>)."),
        ("6", "Decidir", "Transmitir apenas se h cruzar limiar (25 ou 45 cm) com histérese, "
                         "ou se decorrido o intervalo máximo de reporte."),
    ]
    h.append(tabela(
        [["#", "Etapa", "Descrição"]] + [[a, b, c] for a, b, c in fluxo],
        [1.0 * cm, 2.6 * cm, 11.4 * cm]))
    h.append(p("Tabela 5 — Fluxo proposto para a lógica embarcada de medição.",
               E_LEGENDA))
    h.append(p(
        "A histérese na etapa 6 evita oscilação de estado quando a altura "
        "flutua em torno de um limiar: recomenda-se margem de 2 cm, de modo que a "
        "transição para “crítico” ocorra em 45 cm e o retorno "
        "apenas abaixo de 43 cm."))

    h.append(p("5.3 Regras de qualidade do dado", E_H2))
    h.append(p(
        "Derivadas diretamente dos erros documentados na seção 4.2 e já "
        "implementadas no pipeline do projeto:"))
    h.append(KeepTogether([tabela([
        ["Regra", "Justificativa"],
        ["Nunca estimar escala; falhar com erro claro",
         "Valor padrão silencioso contamina o histórico do ponto"],
        ["Comparar vias redundantes e avisar se divergirem &gt; 15%",
         "Foi o que teria detectado o erro dos 50 cm informados"],
        ["Sinalizar altura acima de 200 cm",
         "Implausível para faixa de domínio; indica escala errada"],
        ["Sinalizar altura maior que 3× a referência visível",
         "Medir algo muito maior que a régua é suspeito"],
        ["Alertar quando a calibração passar de 7 dias",
         "Câmera e sensor saem de posição; a medida erra sem avisar"],
    ], [7.0 * cm, 8.0 * cm]),
        p("Tabela 6 — Guardas de qualidade e sua origem empírica.", E_LEGENDA)]))

    h.append(PageBreak())

    # ---------------------------------------------------------- CONCLUSÃO --
    h.append(p("6. Conclusão", E_H1))
    h.append(p("<b>Principais aprendizados</b>", E_H2))
    h.append(item(
        "Sensor algum mede altura: todos medem distância. A altura é uma "
        "diferença, e diferenças compõem erro — o que torna a "
        "calibração única do solo uma decisão de projeto, não "
        "uma conveniência."))
    h.append(item(
        "A abertura do feixe, e não o alcance, é o parâmetro que decide a "
        "aplicabilidade: 15° integram 26 cm de terreno a 1 m de distância."))
    h.append(item(
        "A literatura revisada por pares mostra que ultrassom calibrado atinge RMSE de "
        "3,7 a 9,4 cm em dossel agrícola [5] — incerteza da mesma ordem, ou "
        "maior, que a vegetação rasteira que precisamos acompanhar."))
    h.append(item(
        "Erro de escala é mais perigoso que erro de ruído, porque preserva a "
        "plausibilidade do resultado. Guardas explícitas e redundância "
        "comparada são a única defesa."))

    h.append(p("<b>Decisões recomendadas</b>", E_H2))
    h.append(tabela([
        ["Decisão", "Justificativa resumida"],
        ["Adotar LiDAR de ponto único (TF-Luna / TFmini-S)",
         "Única categoria com tolerância a sol pleno e footprint compatível com o alvo"],
        ["Descartar ultrassom como sensor primário",
         "RMSE de 8–9 cm em dossel esparso excede a resolução necessária"],
        ["Fundir LiDAR com a câmera já existente",
         "O sensor fornece a profundidade ausente na imagem RGB e dispensa a trena"],
        ["Calibrar a geometria uma vez e persistir",
         "Evita compor erro e permite auditar em que condições a medida vale"],
        ["Manter a regra de recusar em vez de estimar",
         "Validada empiricamente por dois erros de campo documentados"],
    ], [6.2 * cm, 8.8 * cm]))
    h.append(p("Tabela 7 — Síntese das recomendações.", E_LEGENDA))

    h.append(p(
        "<b>Limitação assumida.</b> As recomendações derivam de "
        "datasheets, literatura e dos ensaios do grupo com medição por imagem. "
        "<b>Não houve ensaio próprio com LiDAR ou ultrassom</b> — a "
        "validação em bancada, comparando cada sensor contra medição "
        "manual em vegetação real, é o próximo passo necessário "
        "antes de fixar a arquitetura.", E_DESTAQUE))

    # -------------------------------------------------------- REFERÊNCIAS --
    h.append(p("7. Referências", E_H1))
    refs = [
        "[1] MOTIVA-FIELD. <i>Repositório do projeto: documentação técnica, "
        "contrato JSON de detecções e protocolo de captura SP-270.</i> 2026.",
        "[2] STMICROELECTRONICS. <i>VL53L1X: a long distance ranging Time-of-Flight sensor "
        "based on ST FlightSense technology — Datasheet DS13088.</i> "
        "Disponível em: https://www.st.com/resource/en/datasheet/vl53l1x.pdf",
        "[3] HANDSON TECHNOLOGY. <i>HC-SR04 Ultrasonic Sensor Module — User Guide.</i> "
        "Disponível em: https://www.handsontec.com/dataspecs/HC-SR04-Ultrasonic.pdf",
        "[4] SHARP CORPORATION. <i>GP2Y0A21YK0F — Distance Measuring Sensor Unit, "
        "Datasheet.</i> Disponível em: "
        "https://global.sharp/products/device/lineup/data/pdf/datasheet/gp2y0a21yk_e.pdf",
        "[5] ZHENG, H.; HUI, S.; CAI, S.; WANG, X.; WANG, J.; MA, Q.; YAN, Z. "
        "<i>Calibrating ultrasonic sensor measurements of crop canopy heights: a case "
        "study of maize and wheat.</i> Frontiers in Plant Science, v. 15, 2024. "
        "DOI: 10.3389/fpls.2024.1354359",
        "[6] BENEWAKE. <i>TFmini-S Micro LiDAR Module — Product Specification.</i> "
        "Disponível em: https://en.benewake.com/TFminiS/index.html",
        "[7] BENEWAKE. <i>TF-Luna LiDAR Module (Short-range distance sensor) — "
        "Datasheet SJ-GU-TF-Luna-A01.</i> Disponível em: "
        "https://en.benewake.com/TFLuna/index.html",
        "[8] POLOLU CORPORATION. <i>VL53L1X Time-of-Flight Distance Sensor Carrier — "
        "Product documentation.</i> Disponível em: https://www.pololu.com/product/3415",
    ]
    for r in refs:
        h.append(p(r, E_REF))

    h.append(Spacer(1, 0.6 * cm))
    h.append(p(
        "Datasheets consultados nas páginas oficiais de fabricante; artigo [5] "
        "revisado por pares e acessível em texto completo via PubMed Central "
        "(PMC11188359). Tabelas 1 e 4 são cálculos do grupo a partir dos "
        "parâmetros publicados nessas fontes.", E_LEGENDA))

    doc.build(h)
    return doc.paginas_das_secoes


if __name__ == "__main__":
    # Passagem 1: descobre onde cada secao caiu. Passagem 2: escreve o indice.
    mapa = construir()
    construir(mapa)
    print(f"PDF gerado: {SAIDA}")
    print(f"tamanho: {SAIDA.stat().st_size / 1024:.0f} KB")
    print(f"secoes mapeadas: {len(mapa)}")
