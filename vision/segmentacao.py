"""Segmentacao de vegetacao por indice de cor.

Sem modelo treinado e sem dependencia de foto real: o Excess Green separa
verde de marrom por aritmetica de canais, o que permite provar a medicao antes
de existir dataset. Quando o modelo entrar, ele substitui `mascara_vegetacao`
sem mexer no resto do pipeline.

Nada aqui abre janela: o modulo roda headless.
"""

from __future__ import annotations

import cv2
import numpy as np

# Lado do elemento estruturante da abertura morfologica, em pixels.
ABERTURA_PADRAO = 5


def exg(imagem_bgr: np.ndarray) -> np.ndarray:
    """Excess Green normalizado.

    Normaliza cada canal pela soma RGB antes de combinar, o que torna o indice
    razoavelmente estavel a mudanca de iluminacao — o mesmo mato ao sol e a
    sombra cai em valores proximos.

        ExG = 2*g - r - b,  com r = R/soma, g = G/soma, b = B/soma

    Faixa teorica: -1 (vermelho puro) a 2 (verde puro). Cinza da 0.

    Args:
        imagem_bgr: imagem BGR, como o OpenCV entrega.

    Returns:
        Array float32 do tamanho da imagem, um valor de indice por pixel.
    """
    if imagem_bgr is None:
        raise ValueError("imagem_bgr e None")
    if imagem_bgr.ndim != 3 or imagem_bgr.shape[2] != 3:
        raise ValueError(
            f"esperava imagem BGR de 3 canais, recebi shape {imagem_bgr.shape}"
        )

    bgr = imagem_bgr.astype(np.float64)
    azul, verde, vermelho = bgr[:, :, 0], bgr[:, :, 1], bgr[:, :, 2]
    soma = azul + verde + vermelho

    # Pixel preto puro nao tem cor definida. Divide por 1 e zera depois, em vez
    # de deixar NaN se espalhar pela mascara.
    divisor = np.where(soma == 0, 1.0, soma)
    indice = (2.0 * verde - vermelho - azul) / divisor
    indice[soma == 0] = 0.0

    return indice.astype(np.float32)


def mascara_vegetacao(
    imagem_bgr: np.ndarray, tamanho_abertura: int = ABERTURA_PADRAO
) -> np.ndarray:
    """Mascara binaria da vegetacao: ExG, limiar de Otsu e abertura.

    O limiar e escolhido por Otsu sobre o proprio ExG da imagem, entao nao ha
    constante magica de "quanto de verde e verde".

    Limitacao conhecida: Otsu sempre parte o histograma em dois. Numa imagem
    sem vegetacao nenhuma ele ainda devolve mascara, marcando o que houver de
    menos marrom. Quem consome precisa validar area minima antes de chamar
    aquilo de deteccao.

    Args:
        imagem_bgr: imagem BGR.
        tamanho_abertura: lado do elemento estruturante da abertura, em pixels.
            Abertura remove pontos isolados sem comer a silhueta da moita.

    Returns:
        Array uint8 com 0 (fundo) e 255 (vegetacao).
    """
    indice = exg(imagem_bgr)

    minimo = float(indice.min())
    maximo = float(indice.max())
    if maximo - minimo < 1e-9:
        # Imagem de cor uniforme: nao ha o que separar.
        return np.zeros(indice.shape, dtype=np.uint8)

    # Otsu exige uint8. O reescalonamento preserva a ordem dos valores, entao o
    # limiar encontrado equivale a um limiar sobre o ExG original.
    escalado = ((indice - minimo) / (maximo - minimo) * 255.0).astype(np.uint8)

    _, binaria = cv2.threshold(
        escalado, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    if tamanho_abertura > 1:
        elemento = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (tamanho_abertura, tamanho_abertura)
        )
        binaria = cv2.morphologyEx(binaria, cv2.MORPH_OPEN, elemento)

    return binaria


def maior_regiao(
    mascara: np.ndarray,
) -> tuple[tuple[int, int, int, int], np.ndarray] | None:
    """Maior componente conexa da mascara.

    A moita relevante e a maior mancha continua de verde. Componentes menores
    sao folha solta, capim no fundo, ruido.

    Args:
        mascara: array uint8 com 0 e 255.

    Returns:
        `(bbox, mascara_recortada)` onde bbox e `(x1, y1, x2, y2)` em pixels da
        imagem original — mesma convencao do contrato em docs/ — e
        `mascara_recortada` contem so aquela componente, ja cortada no bbox.

        `None` quando a mascara esta vazia. Ausencia de vegetacao e resultado
        valido, nao erro: o contrato admite `deteccoes: []`.
    """
    if mascara is None or mascara.size == 0:
        return None

    binaria = (mascara > 0).astype(np.uint8)
    quantidade, rotulos, estatisticas, _ = cv2.connectedComponentsWithStats(
        binaria, connectivity=8
    )

    # Rotulo 0 e sempre o fundo.
    if quantidade <= 1:
        return None

    indice = 1 + int(np.argmax(estatisticas[1:, cv2.CC_STAT_AREA]))

    x = int(estatisticas[indice, cv2.CC_STAT_LEFT])
    y = int(estatisticas[indice, cv2.CC_STAT_TOP])
    largura = int(estatisticas[indice, cv2.CC_STAT_WIDTH])
    altura = int(estatisticas[indice, cv2.CC_STAT_HEIGHT])

    recorte = rotulos[y : y + altura, x : x + largura] == indice
    mascara_recortada = (recorte.astype(np.uint8)) * 255

    return (x, y, x + largura, y + altura), mascara_recortada


def altura_em_pixels(bbox: tuple[int, int, int, int]) -> int:
    """Altura vertical do bbox `(x1, y1, x2, y2)`."""
    _, y1, _, y2 = bbox
    return int(y2 - y1)


# --- Medicao da altura -------------------------------------------------------
#
# Medir o bbox da maior mancha verde do quadro NAO e medir altura de planta.
# Numa foto de rodovia a maior mancha e a faixa de grama inteira, que vai do pe
# da camera ate o horizonte; a extensao vertical desse bbox mistura vegetacao a
# 1 m e a 30 m. Grama distante aparece mais alta no quadro sem ser mais alta.
#
# O protocolo de captura ja resolve isso: a trena fica encostada no chao, ao
# lado da vegetacao, na mesma distancia da camera. Logo a base da trena e a
# linha do chao, e o que interessa e a moita ao lado dela.

# Meia-largura da banda de interesse, em multiplos da largura da trena.
FATOR_BANDA_LATERAL = 4.0

# Quao perto do chao a base da moita precisa estar, em fracao da altura da
# imagem. Planta nasce do chao; mancha verde solta no alto do quadro e arvore,
# barranco ou fundo.
FRACAO_TOLERANCIA_CHAO = 0.05


def medir_altura_vegetacao(
    mascara: np.ndarray,
    bbox_referencia: tuple[int, int, int, int] | None,
    fator_banda: float = FATOR_BANDA_LATERAL,
) -> tuple[int, tuple[int, int, int, int]] | None:
    """Altura da vegetacao em pixels, medida do chao para cima.

    Usa a trena como referencia geometrica: a base dela e a linha do chao, e a
    moita que interessa e a que esta ao lado, dentro de uma banda lateral.

    Args:
        mascara: mascara binaria de vegetacao, uint8 com 0 e 255.
        bbox_referencia: `(x, y, largura, altura)` da trena. Quando None, cai no
            comportamento antigo (maior componente do quadro), que so faz
            sentido em cena controlada.
        fator_banda: meia-largura da banda, em multiplos da largura da trena.

    Returns:
        `(altura_px, bbox)` com bbox `(x1, y1, x2, y2)` da moita medida, ou None
        quando nao ha vegetacao qualificada.
    """
    if mascara is None or mascara.size == 0:
        return None

    if bbox_referencia is None:
        regiao = maior_regiao(mascara)
        if regiao is None:
            return None
        bbox, _ = regiao
        return altura_em_pixels(bbox), bbox

    altura_img, largura_img = mascara.shape[:2]
    rx, ry, rw, rh = (int(v) for v in bbox_referencia)
    linha_do_chao = min(altura_img, ry + rh)

    # Banda lateral centrada na trena.
    centro_x = rx + rw / 2.0
    meia = max(rw * fator_banda, rw + 1.0)
    x_inicio = max(0, int(round(centro_x - meia)))
    x_fim = min(largura_img, int(round(centro_x + meia)))
    if x_fim - x_inicio < 3 or linha_do_chao < 3:
        return None

    # So o que esta na banda e acima do chao.
    recorte = np.zeros_like(mascara)
    recorte[:linha_do_chao, x_inicio:x_fim] = mascara[:linha_do_chao, x_inicio:x_fim]

    # A propria trena nao e vegetacao, mas se o verde vazar por cima dela o
    # componente pode encostar; remover a coluna dela evita medir a fita.
    recorte[:, rx : rx + rw] = 0

    quantidade, rotulos, estatisticas, _ = cv2.connectedComponentsWithStats(
        (recorte > 0).astype(np.uint8), connectivity=8
    )
    if quantidade <= 1:
        return None

    tolerancia = max(3, int(altura_img * FRACAO_TOLERANCIA_CHAO))

    melhor = None
    melhor_area = 0
    for indice in range(1, quantidade):
        x = int(estatisticas[indice, cv2.CC_STAT_LEFT])
        y = int(estatisticas[indice, cv2.CC_STAT_TOP])
        largura = int(estatisticas[indice, cv2.CC_STAT_WIDTH])
        altura = int(estatisticas[indice, cv2.CC_STAT_HEIGHT])
        area = int(estatisticas[indice, cv2.CC_STAT_AREA])

        base = y + altura
        # Planta nasce do chao: a base tem de chegar perto da linha da trena.
        if abs(base - linha_do_chao) > tolerancia:
            continue
        if area > melhor_area:
            melhor_area = area
            melhor = (x, y, largura, altura)

    if melhor is None:
        return None

    x, y, largura, altura = melhor
    altura_px = max(0, linha_do_chao - y)
    return altura_px, (x, y, x + largura, linha_do_chao)
