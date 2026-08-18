"""Le a graduacao impressa na trena e deriva a escala sozinho.

Por que isto existe: enquanto a escala depender de alguem digitar quantos
centimetros da fita estao esticados, um numero errado escala TUDO
proporcionalmente e nada percebe. Na primeira medicao real foram informados
~50 cm onde a fita mostrava ~13,5 cm, e a vegetacao saiu 38,5 cm em vez de
~10 cm. O resultado parecia perfeitamente plausivel.

A trena ja carrega a resposta impressa nela. Este modulo le as marcas.

Resolucao — leia antes de confiar
---------------------------------
Na foto real a escala fica em torno de 29 px/cm, entao 1 mm ~= 2,9 px. Isso e o
limite do que da para resolver: duas marcas de milimetro ocupam menos de 6 px
e qualquer desfoque as funde. O metodo NAO depende de enxergar milimetro. Ele
acha a periodicidade dominante — seja ela de 1 mm, 5 mm ou 1 cm — e so entao
descobre o que aquele periodo significa, testando as tres hipoteses.

Em foto de baixa resolucao o normal e o fundamental detectado ser 5 mm ou
1 cm. Isso e esperado e continua dando a escala certa.

Quando nao houver periodicidade limpa, devolve None. Preferir falhar e cair na
via manual e melhor do que devolver numero errado.

Nada aqui abre janela: o modulo roda headless.
"""

from __future__ import annotations

import cv2
import numpy as np

# Faixa de periodos considerada, em pixels. Abaixo de 2 px nao existe
# periodicidade resolvivel; acima de 200 px a "marca" seria maior que a fita.
LAG_MINIMO = 2
LAG_MAXIMO = 200

# Fracao central da largura da fita usada para o perfil. As bordas trazem o
# contorno da trena e o fundo, que sujam o sinal.
FRACAO_CENTRAL = 0.6

# Grau do polinomio removido do perfil para tirar a iluminacao desigual.
#
# Escolhido no lugar da media movel: para preservar um periodo de 1 cm (que a
# 50 px/cm ocupa 50 px) a janela precisaria passar de 100 px, e num perfil de
# 300-400 px isso vira praticamente a media global — nao removeria gradiente
# nenhum. Um polinomio de grau 3 tira o gradiente lento sem tocar nas marcas.
GRAU_TENDENCIA = 3

# Autocorrelacao minima no pico para a leitura ser considerada.
CONFIANCA_MINIMA = 0.35

# Amplitude minima do perfil, em niveis de cinza, para existir marca alguma.
#
# E a guarda mais importante do modulo. Sem ela, uma barra LISA com ruido chega
# a produzir periodicidade aparente: a mascara segmenta ruido, a rotacao
# resultante interpola e a interpolacao cria correlacao onde nao havia marca
# nenhuma. Medido no sintetico: trena graduada da 39 a 60; barra lisa da 1,0.
# O corte em 6 tem margem larga dos dois lados.
AMPLITUDE_MINIMA_PERFIL = 6.0

# Fracao do pico maximo que um lag menor precisa atingir para ser considerado o
# FUNDAMENTAL. Sem isso o metodo trava num harmonico: numa fita de marcas de
# 1 cm, os picos em 1, 2 e 3 cm tem altura parecida, e basta o ruido inflar o de
# 2 cm para a escala sair pela metade. O fundamental e o MENOR periodo forte,
# nao o mais alto.
FATOR_FUNDAMENTAL = 0.80

# Largura fisica da trena, em cm. E o desempate: cada hipotese (1mm, 5mm, 1cm)
# implica uma escala, e a escala implica uma largura para a fita. So uma delas
# bate com a fita que esta na mao.
#
# Por que isto e melhor que digitar o comprimento esticado: a largura e uma
# constante do equipamento — mede-se uma vez com uma regua e nunca mais muda.
# O comprimento esticado muda a cada foto, e foi justamente ele que produziu o
# erro de 50 cm informados para uma fita de 13,5 cm.
#
# Ajuste para a trena do time. Fitas comuns: 12,5 / 16 / 19 / 25 / 32 mm.
LARGURA_FITA_ESPERADA_CM = 2.5

# Tolerancia em torno da largura esperada. Cobre perspectiva, sombra e a borda
# que a deteccao inclui a mais.
TOLERANCIA_LARGURA = 0.45

# A hipotese vencedora precisa estar este tanto mais perto da largura esperada
# que a segunda colocada. Sem essa folga e empate — e empate vira None, porque
# escolher no par ou impar reintroduz exatamente o erro que este modulo existe
# para eliminar.
MARGEM_DESEMPATE_LARGURA = 1.6

INTERPRETACOES = {
    # nome: quantos milimetros vale um periodo
    "1mm": 1.0,
    "5mm": 5.0,
    "10mm": 10.0,
}


def _mascara_da_fita(recorte_bgr: np.ndarray) -> np.ndarray | None:
    """Isola a fita dentro do recorte, sem depender das constantes de cor.

    Usa Otsu na saturacao: a trena e um corpo saturado sobre fundo lavado.
    Fica aqui, e nao em calibracao.py, para este modulo nao importar aquele —
    o sentido da dependencia e calibracao -> graduacao.
    """
    if recorte_bgr.size == 0:
        return None

    hsv = cv2.cvtColor(recorte_bgr, cv2.COLOR_BGR2HSV)
    saturacao = hsv[:, :, 1]

    if int(saturacao.max()) - int(saturacao.min()) < 10:
        # Recorte de saturacao uniforme: usa a area toda.
        return np.full(saturacao.shape, 255, dtype=np.uint8)

    _, mascara = cv2.threshold(
        saturacao, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    quantidade, rotulos, estatisticas, _ = cv2.connectedComponentsWithStats(
        mascara, connectivity=8
    )
    if quantidade <= 1:
        return None

    indice = 1 + int(np.argmax(estatisticas[1:, cv2.CC_STAT_AREA]))
    return ((rotulos == indice).astype(np.uint8)) * 255


def _endireitar(
    recorte_bgr: np.ndarray, mascara: np.ndarray
) -> tuple[np.ndarray, np.ndarray] | None:
    """Rotaciona o recorte para a fita ficar vertical.

    A foto de campo raramente tem a trena perfeitamente a prumo. Alguns graus
    de inclinacao borram as marcas ao tirar a media por linha, e a periodicidade
    some. Endireitar antes resolve.
    """
    pontos = cv2.findNonZero(mascara)
    if pontos is None or len(pontos) < 5:
        return None

    (centro, (largura, altura), angulo) = cv2.minAreaRect(pontos)

    # minAreaRect devolve o angulo do lado "largura". Se a fita esta deitada
    # nessa convencao, soma 90 para o eixo maior virar o vertical.
    if largura > altura:
        angulo += 90.0

    altura_img, largura_img = mascara.shape[:2]
    matriz = cv2.getRotationMatrix2D(centro, angulo, 1.0)

    recorte_reto = cv2.warpAffine(
        recorte_bgr, matriz, (largura_img, altura_img),
        flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE,
    )
    mascara_reta = cv2.warpAffine(
        mascara, matriz, (largura_img, altura_img), flags=cv2.INTER_NEAREST
    )

    # Recorta na fita endireitada, para o perfil não pegar fundo.
    pontos_retos = cv2.findNonZero(mascara_reta)
    if pontos_retos is None:
        return None
    x, y, largura_fita, altura_fita = cv2.boundingRect(pontos_retos)
    if largura_fita < 3 or altura_fita < 3 * LAG_MINIMO:
        return None

    return (
        recorte_reto[y : y + altura_fita, x : x + largura_fita],
        mascara_reta[y : y + altura_fita, x : x + largura_fita],
    )


def _perfil_de_intensidade(fita_bgr: np.ndarray) -> np.ndarray | None:
    """Media de cinza por linha, numa faixa central estreita da largura."""
    altura, largura = fita_bgr.shape[:2]
    if altura < 3 * LAG_MINIMO or largura < 1:
        return None

    cinza = cv2.cvtColor(fita_bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)

    margem = int(largura * (1.0 - FRACAO_CENTRAL) / 2.0)
    inicio = min(margem, max(0, largura // 2 - 1))
    fim = max(largura - margem, inicio + 1)

    return cinza[:, inicio:fim].mean(axis=1)


def _remover_tendencia(perfil: np.ndarray) -> np.ndarray:
    """Tira o gradiente lento de iluminacao, preservando as marcas."""
    n = len(perfil)
    if n <= GRAU_TENDENCIA + 1:
        return perfil - perfil.mean()

    x = np.arange(n, dtype=np.float64)
    coeficientes = np.polyfit(x, perfil, GRAU_TENDENCIA)
    return perfil - np.polyval(coeficientes, x)


def _autocorrelacao(sinal: np.ndarray) -> np.ndarray | None:
    """Autocorrelacao normalizada e SEM VIES, com r[0] = 1.

    A divisao por (n - lag) e essencial aqui, nao um detalhe. A autocorrelacao
    enviesada decai com o lag so porque sobra menos sobreposicao, e esse
    decaimento imita estrutura: r(2p) sai maior que r(3p) mesmo numa fita de
    marcas todas iguais. O teste de harmonicos leria isso como "existe marca
    especial em 2p" e dobraria a escala.
    """
    centrado = sinal - sinal.mean()
    desvio = centrado.std()
    if desvio < 1e-9:
        return None

    normalizado = centrado / desvio
    n = len(normalizado)
    completa = np.correlate(normalizado, normalizado, mode="full")
    metade = completa[n - 1 :].astype(np.float64)

    sobreposicao = np.arange(n, 0, -1, dtype=np.float64)
    sem_vies = metade / sobreposicao

    if sem_vies[0] <= 0:
        return None
    return sem_vies / sem_vies[0]


def _refinar_pico(r: np.ndarray, lag: int) -> float:
    """Interpolacao parabolica no pico, para o periodo sair sub-pixel."""
    if lag <= 0 or lag >= len(r) - 1:
        return float(lag)
    anterior, atual, proximo = r[lag - 1], r[lag], r[lag + 1]
    denominador = anterior - 2.0 * atual + proximo
    if abs(denominador) < 1e-12:
        return float(lag)
    ajuste = 0.5 * (anterior - proximo) / denominador
    if abs(ajuste) > 1.0:
        return float(lag)
    return float(lag) + float(ajuste)


def _valor_em(r: np.ndarray, lag: float) -> float | None:
    """Autocorrelacao no lag pedido, tolerando +-1 px de imprecisao."""
    indice = int(round(lag))
    if indice < 1 or indice >= len(r):
        return None
    janela = r[max(1, indice - 1) : min(len(r), indice + 2)]
    return float(janela.max()) if janela.size else None


def _lag_fundamental(
    r: np.ndarray, lag_minimo: int, lag_maximo: int, pico_maximo: float
) -> int | None:
    """Menor lag que ja e um pico forte — o fundamental, nao um harmonico.

    Numa fita com marcas de 1 cm, a autocorrelacao tem picos parecidos em 1, 2 e
    3 cm. Pegar o mais alto e sorte: basta o ruido inflar o de 2 cm para a
    escala sair pela metade, que foi o que aconteceu no sintetico a 25, 29 e
    35 px/cm. O periodo verdadeiro e o MENOR que ja atinge quase o maximo.
    """
    limiar = FATOR_FUNDAMENTAL * pico_maximo
    for lag in range(lag_minimo, lag_maximo + 1):
        if r[lag] < limiar:
            continue
        # Precisa ser maximo local, para nao pegar a subida de um pico vizinho.
        anterior = r[lag - 1] if lag - 1 >= 1 else -np.inf
        proximo = r[lag + 1] if lag + 1 < len(r) else -np.inf
        if r[lag] >= anterior and r[lag] >= proximo:
            return lag
    return None


def _escolher_interpretacao(
    r: np.ndarray, periodo: float, largura_fita_px: float
) -> tuple[str, float] | None:
    """Descobre se o periodo detectado vale 1 mm, 5 mm ou 1 cm.

    A decisao e FISICA, pela largura da fita. Cada hipotese implica uma escala;
    a escala implica uma largura para a trena; so uma bate com a fita real.

    Nao uso mais o teste de harmonicos como criterio. Ele foi implementado e
    medido: numa trena sintetica de marcas 1mm/5mm/1cm, `r(2p)` fica acima de
    `r(p)` por arredondamento sub-pixel das marcas, nao por estrutura. Isso faz
    a hipotese "5mm" ganhar indevidamente e dobra a escala — foi o que produziu
    5,31 px/cm onde o correto era ~29. Autocorrelacao sozinha nao separa 5 mm de
    1 cm, porque as duas hipoteses geram o mesmo pente.

    Returns:
        `(interpretacao, pixels_por_cm)`, ou None quando nenhuma hipotese cabe
        na largura esperada ou quando duas ficam igualmente perto. Devolver None
        e o comportamento seguro: a via manual assume.
    """
    if largura_fita_px <= 0 or LARGURA_FITA_ESPERADA_CM <= 0:
        return None

    limite_baixo = LARGURA_FITA_ESPERADA_CM * (1.0 - TOLERANCIA_LARGURA)
    limite_alto = LARGURA_FITA_ESPERADA_CM * (1.0 + TOLERANCIA_LARGURA)

    candidatas: list[tuple[str, float, float]] = []
    for nome, milimetros in INTERPRETACOES.items():
        escala = periodo * 10.0 / milimetros
        if escala <= 0:
            continue
        largura_cm = largura_fita_px / escala
        if not (limite_baixo <= largura_cm <= limite_alto):
            continue
        # Erro relativo em relacao a largura esperada: menor e melhor.
        erro = abs(largura_cm - LARGURA_FITA_ESPERADA_CM) / LARGURA_FITA_ESPERADA_CM
        candidatas.append((nome, escala, erro))

    if not candidatas:
        return None

    candidatas.sort(key=lambda item: item[2])
    if len(candidatas) > 1:
        melhor, segunda = candidatas[0], candidatas[1]
        # Empate: a segunda esta quase tao perto quanto a primeira.
        if segunda[2] < melhor[2] * MARGEM_DESEMPATE_LARGURA:
            return None

    return candidatas[0][0], candidatas[0][1]


def escala_por_graduacao(
    imagem_bgr: np.ndarray, bbox_referencia: tuple[int, int, int, int]
) -> dict[str, object] | None:
    """Deriva pixels_por_cm lendo a graduacao impressa na trena.

    Args:
        imagem_bgr: foto inteira, BGR.
        bbox_referencia: `(x, y, largura, altura)` da trena, como
            `calibracao.detectar_referencia` devolve.

    Returns:
        Dicionario com `pixels_por_cm`, `periodo_px`, `interpretacao`,
        `confianca` e `comprimento_visivel_cm`; ou None quando nao ha
        periodicidade clara. None e resultado legitimo: melhor cair na via
        manual do que inventar escala.
    """
    if imagem_bgr is None or imagem_bgr.size == 0:
        return None

    x, y, largura, altura = (int(v) for v in bbox_referencia)
    if largura <= 0 or altura <= 0:
        return None

    altura_img, largura_img = imagem_bgr.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(largura_img, x + largura), min(altura_img, y + altura)
    if x1 - x0 < 3 or y1 - y0 < 3 * LAG_MINIMO:
        return None

    recorte = imagem_bgr[y0:y1, x0:x1]

    mascara = _mascara_da_fita(recorte)
    if mascara is None:
        return None

    endireitado = _endireitar(recorte, mascara)
    if endireitado is None:
        return None
    fita, _ = endireitado

    perfil = _perfil_de_intensidade(fita)
    if perfil is None:
        return None

    sinal = _remover_tendencia(perfil)

    # Sem contraste nao ha marca. Barra lisa cai aqui, antes de a
    # autocorrelacao ter chance de achar padrao no ruido.
    if float(sinal.std()) < AMPLITUDE_MINIMA_PERFIL:
        return None

    r = _autocorrelacao(sinal)
    if r is None:
        return None

    lag_maximo = min(LAG_MAXIMO, len(r) - 1, len(sinal) // 2)
    if lag_maximo <= LAG_MINIMO:
        return None

    faixa = r[LAG_MINIMO : lag_maximo + 1]
    if faixa.size == 0:
        return None

    pico_maximo = float(faixa.max())
    if pico_maximo < CONFIANCA_MINIMA:
        return None

    melhor_lag = _lag_fundamental(r, LAG_MINIMO, lag_maximo, pico_maximo)
    if melhor_lag is None:
        return None
    confianca = float(np.clip(r[melhor_lag], 0.0, 1.0))

    periodo = _refinar_pico(r, melhor_lag)
    if periodo < LAG_MINIMO:
        return None

    largura_fita_px = float(fita.shape[1])
    escolha = _escolher_interpretacao(r, periodo, largura_fita_px)
    if escolha is None:
        # Nenhuma hipotese sobreviveu, ou duas empataram. Devolver uma delas
        # seria adivinhar; a via manual assume.
        return None
    interpretacao, pixels_por_cm = escolha
    if pixels_por_cm <= 0:
        return None

    # A altura da bbox original e o comprimento visivel: e ela que denuncia
    # quando alguem digita 50 cm para uma fita que mostra 13,5 cm.
    comprimento_visivel_cm = float(altura) / pixels_por_cm

    return {
        "pixels_por_cm": round(float(pixels_por_cm), 4),
        "periodo_px": round(float(periodo), 3),
        "interpretacao": interpretacao,
        "confianca": round(confianca, 3),
        "comprimento_visivel_cm": round(comprimento_visivel_cm, 2),
        "largura_fita_cm": round(largura_fita_px / pixels_por_cm, 2),
    }
