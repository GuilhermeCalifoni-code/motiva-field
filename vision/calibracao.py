"""Calibracao pixel/cm a partir da haste de referencia.

O protocolo de captura manda encostar uma haste vertical de altura conhecida
ao lado da vegetacao, na mesma distancia da camera. Achar essa haste na imagem
e o que transforma "tem mato" em "tem 62 cm de mato".

Regra que nao se quebra, vinda de docs/contrato-json-deteccoes.md: se a
referencia nao for encontrada, isto levanta excecao. Nunca devolve um valor
chutado — um pixels_por_cm inventado contamina todo o historico do ponto.

Nada aqui abre janela: o modulo roda headless.
"""

from __future__ import annotations

import cv2
import numpy as np

from segmentacao import mascara_vegetacao

# A haste e alta e estreita. Estes limites separam ela do chao, do horizonte e
# de placas — objetos largos ou baixos demais.
RAZAO_ALTURA_LARGURA_MINIMA = 4.0
FRACAO_ALTURA_MINIMA = 0.10
FRACAO_LARGURA_MAXIMA = 0.20
ABERTURA_HASTE = 3


class ReferenciaNaoEncontrada(Exception):
    """A haste de calibracao nao foi localizada na imagem."""


def _componentes_verticais(
    mascara: np.ndarray, formato: tuple[int, int]
) -> list[tuple[int, int, int, int, int]]:
    """Componentes da mascara que parecem uma haste.

    Returns:
        Lista de `(altura, largura, x, y, area)`, so dos candidatos aprovados.
    """
    altura_imagem, largura_imagem = formato

    if ABERTURA_HASTE > 1:
        elemento = cv2.getStructuringElement(
            cv2.MORPH_RECT, (ABERTURA_HASTE, ABERTURA_HASTE)
        )
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, elemento)

    quantidade, _, estatisticas, _ = cv2.connectedComponentsWithStats(
        (mascara > 0).astype(np.uint8), connectivity=8
    )

    aprovados: list[tuple[int, int, int, int, int]] = []
    for indice in range(1, quantidade):
        x = int(estatisticas[indice, cv2.CC_STAT_LEFT])
        y = int(estatisticas[indice, cv2.CC_STAT_TOP])
        largura = int(estatisticas[indice, cv2.CC_STAT_WIDTH])
        altura = int(estatisticas[indice, cv2.CC_STAT_HEIGHT])
        area = int(estatisticas[indice, cv2.CC_STAT_AREA])

        if largura <= 0 or altura <= 0:
            continue
        # Baixa demais para ser a haste de referencia.
        if altura < FRACAO_ALTURA_MINIMA * altura_imagem:
            continue
        # Larga demais: e o chao, o ceu ou o quadro inteiro.
        if largura > FRACAO_LARGURA_MAXIMA * largura_imagem:
            continue
        # Nao e vertical o bastante.
        if altura / largura < RAZAO_ALTURA_LARGURA_MINIMA:
            continue

        aprovados.append((altura, largura, x, y, area))

    return aprovados


def pixels_por_cm(imagem_bgr: np.ndarray, altura_referencia_cm: float) -> float:
    """Quantos pixels valem um centimetro, medido pela haste de referencia.

    Procedimento:

    1. Segmenta a vegetacao e a exclui — a haste nunca e verde.
    2. Dentro do que sobrou, separa claro de escuro por Otsu. A haste e pintada
       para contrastar com verde e marrom, entao cai num dos dois lados,
       enquanto o chao ocupa o outro.
    3. Mantem so componentes altas e estreitas.
    4. Escolhe a mais alta; empate desempata pela mais estreita.

    Args:
        imagem_bgr: imagem BGR contendo a haste inteira no quadro.
        altura_referencia_cm: altura real da haste, em cm (100.0 no piloto).

    Returns:
        Razao pixels por centimetro, sempre > 0.

    Raises:
        ValueError: se `altura_referencia_cm` nao for positiva.
        ReferenciaNaoEncontrada: se nenhuma haste plausivel aparecer. O chamador
            deve tratar como falha da foto, nao estimar um valor.
    """
    if imagem_bgr is None:
        raise ValueError("imagem_bgr e None")
    if altura_referencia_cm <= 0:
        raise ValueError(
            f"altura_referencia_cm deve ser positiva, recebi {altura_referencia_cm}"
        )

    altura_imagem, largura_imagem = imagem_bgr.shape[:2]

    vegetacao = mascara_vegetacao(imagem_bgr)
    nao_vegetacao = cv2.bitwise_not(vegetacao)

    cinza = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY)
    valores = cinza[nao_vegetacao > 0]
    if valores.size == 0:
        raise ReferenciaNaoEncontrada(
            "a imagem inteira foi classificada como vegetacao: nao sobrou regiao "
            "onde procurar a haste de referencia. Refaca a foto enquadrando a "
            "haste conforme docs/protocolo-captura-sp270.md."
        )

    # Otsu sobre o que nao e vegetacao: separa a haste pintada do chao.
    limiar, _ = cv2.threshold(
        valores.reshape(-1, 1), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    fora_da_vegetacao = nao_vegetacao > 0
    claros = ((cinza > limiar) & fora_da_vegetacao).astype(np.uint8) * 255
    escuros = ((cinza <= limiar) & fora_da_vegetacao).astype(np.uint8) * 255

    candidatos: list[tuple[int, int, int, int, int]] = []
    for mascara in (claros, escuros):
        candidatos.extend(
            _componentes_verticais(mascara, (altura_imagem, largura_imagem))
        )

    if not candidatos:
        raise ReferenciaNaoEncontrada(
            "nenhum objeto vertical alto e estreito foi encontrado fora da "
            f"vegetacao (exigido: altura >= {FRACAO_ALTURA_MINIMA:.0%} da imagem, "
            f"largura <= {FRACAO_LARGURA_MAXIMA:.0%} e razao altura/largura >= "
            f"{RAZAO_ALTURA_LARGURA_MINIMA:.0f}). Sem a haste no quadro nao ha "
            "como converter pixels em centimetros — a foto nao serve para medir."
        )

    # Mais alta primeiro; entre alturas iguais, a mais estreita.
    altura_haste_px, _, _, _, _ = max(
        candidatos, key=lambda c: (c[0], -c[1])
    )

    return float(altura_haste_px) / float(altura_referencia_cm)
