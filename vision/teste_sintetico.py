"""Prova a medicao antes de existir foto real.

A conta que sustenta o produto e simples: altura_cm = altura_px / pixels_por_cm.
O risco nao esta na formula, esta em cada etapa que a alimenta — a segmentacao
pegar a moita errada, a calibracao medir a haste errada, o bbox vir torto.

Aqui a imagem e sintetica, entao a resposta certa e conhecida por construcao.
Se o pipeline erra numa figura de retangulos, nao vai acertar numa foto de
rodovia. Rodar isto e barato e falha cedo.

Uso:
    python teste_sintetico.py

Sai com codigo 0 se tudo passar, 1 se algo falhar. Nao abre janela.
"""

from __future__ import annotations

import sys

import cv2
import numpy as np

from calibracao import ReferenciaNaoEncontrada, pixels_por_cm
from segmentacao import altura_em_pixels, maior_regiao, mascara_vegetacao

# --- Aparencia da cena sintetica -------------------------------------------
# Cores em BGR, escolhidas para imitar o caso real: terra marrom, mato verde,
# haste clara. A haste contrasta com verde e marrom, como manda o protocolo.
COR_FUNDO = (33, 67, 101)      # marrom de terra batida
COR_VEGETACAO = (40, 160, 50)  # verde de mato
COR_HASTE = (170, 170, 170)    # cinza claro — cai no fallback geometrico
# Amarelo saturado, dentro da faixa HSV que calibracao.py procura. Serve para
# exercitar a deteccao por cor sem depender de foto real.
COR_TRENA_AMARELA = (0, 210, 230)

LARGURA_IMAGEM = 700
ALTURA_IMAGEM = 900
LINHA_DO_CHAO = 850

HASTE_X = 110
HASTE_LARGURA = 14
VEGETACAO_X1 = 300
VEGETACAO_X2 = 560

SIGMA_RUIDO = 5.0
TOLERANCIA = 0.05


def gerar_trena_graduada(
    pixels_por_cm: float,
    comprimento_cm: float,
    largura_fita_cm: float = 2.5,
    angulo_graus: float = 0.0,
    semente: int = 11,
) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Desenha uma trena amarela com graduacao, sobre fundo neutro.

    A hierarquia de marcas imita a fita real: milimetro curto e claro, meio
    centimetro medio, centimetro longo e escuro. E essa diferenca de tamanho
    que permite ao leitor de graduacao descobrir se o periodo dominante vale
    1 mm, 5 mm ou 1 cm.

    Args:
        pixels_por_cm: escala desejada, em px/cm.
        comprimento_cm: comprimento da fita desenhada.
        largura_fita_cm: largura fisica da fita, em cm. Fita real tem largura
            constante, entao em pixels ela ESCALA junto com pixels_por_cm — e e
            isso que permite desempatar a leitura da graduacao.
        angulo_graus: inclinacao aplicada a cena, para testar o endireitamento.
        semente: semente do ruido.

    Returns:
        `(imagem_bgr, bbox)` com bbox `(x, y, largura, altura)` da fita.
    """
    altura_fita = int(round(comprimento_cm * pixels_por_cm))
    largura_px = max(8, int(round(largura_fita_cm * pixels_por_cm)))
    margem = max(40, int(altura_fita * 0.18))
    altura_total = altura_fita + margem * 2
    largura_total = largura_px + margem * 2

    imagem = np.full((altura_total, largura_total, 3), (150, 150, 150), dtype=np.uint8)

    x0, y0 = margem, margem
    x1, y1 = x0 + largura_px, y0 + altura_fita
    cv2.rectangle(imagem, (x0, y0), (x1 - 1, y1 - 1), COR_TRENA_AMARELA, thickness=-1)

    # Marcas a cada milimetro; comprimento e cor dependem da hierarquia.
    milimetros = int(round(comprimento_cm * 10))
    pixels_por_mm = pixels_por_cm / 10.0
    for mm in range(milimetros + 1):
        posicao = int(round(y0 + mm * pixels_por_mm))
        if posicao >= y1:
            break
        if mm % 10 == 0:
            comprimento_marca, cor, espessura = int(largura_px * 0.75), (20, 20, 20), 2
        elif mm % 5 == 0:
            comprimento_marca, cor, espessura = int(largura_px * 0.50), (40, 40, 40), 1
        else:
            comprimento_marca, cor, espessura = int(largura_px * 0.28), (70, 70, 70), 1
        cv2.line(imagem, (x0, posicao), (x0 + comprimento_marca, posicao), cor, espessura)

    bbox = (x0, y0, largura_px, altura_fita)

    if abs(angulo_graus) > 1e-6:
        centro = (largura_total / 2.0, altura_total / 2.0)
        matriz = cv2.getRotationMatrix2D(centro, angulo_graus, 1.0)
        imagem = cv2.warpAffine(
            imagem, matriz, (largura_total, altura_total),
            flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE,
        )
        # A bbox passa a ser a do retangulo girado, que e o que o detector por
        # cor devolveria nessa foto.
        cantos = np.array(
            [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], dtype=np.float64
        )
        girados = cv2.transform(cantos.reshape(-1, 1, 2), matriz).reshape(-1, 2)
        gx, gy, gw, gh = cv2.boundingRect(girados.astype(np.int32))
        bbox = (gx, gy, gw, gh)

    gerador = np.random.default_rng(semente)
    ruido = gerador.normal(0.0, 3.0, imagem.shape)
    imagem = np.clip(imagem.astype(np.float64) + ruido, 0, 255).astype(np.uint8)

    return imagem, bbox


def gerar_cena(
    altura_haste_px: int,
    altura_vegetacao_px: int,
    com_haste: bool = True,
    semente: int = 42,
    cor_haste: tuple[int, int, int] = COR_HASTE,
) -> np.ndarray:
    """Monta a cena: fundo marrom, moita verde e haste.

    Tudo apoiado na mesma linha do chao, como na foto real, em que haste e mato
    ficam a mesma distancia da camera.

    Args:
        altura_haste_px: altura da haste em pixels.
        altura_vegetacao_px: altura do retangulo verde em pixels.
        com_haste: quando False, desenha a cena sem referencia — usado para
            provar que a calibracao falha em vez de chutar.
        semente: semente do ruido, para o teste ser reproduzivel.
        cor_haste: BGR da haste. O padrao cinza cai no fallback geometrico;
            passe COR_TRENA_AMARELA para exercitar a deteccao por cor.

    Returns:
        Imagem BGR uint8.
    """
    imagem = np.full((ALTURA_IMAGEM, LARGURA_IMAGEM, 3), COR_FUNDO, dtype=np.uint8)

    # cv2.rectangle preenche incluindo as duas bordas: para um retangulo de
    # altura H exata, a base fica em (chao - 1) e o topo em (chao - H).
    base = LINHA_DO_CHAO - 1

    cv2.rectangle(
        imagem,
        (VEGETACAO_X1, LINHA_DO_CHAO - altura_vegetacao_px),
        (VEGETACAO_X2, base),
        COR_VEGETACAO,
        thickness=-1,
    )

    if com_haste:
        cv2.rectangle(
            imagem,
            (HASTE_X, LINHA_DO_CHAO - altura_haste_px),
            (HASTE_X + HASTE_LARGURA, base),
            cor_haste,
            thickness=-1,
        )

    # Ruido leve: uma cena perfeitamente chapada provaria menos do que parece.
    gerador = np.random.default_rng(semente)
    ruido = gerador.normal(0.0, SIGMA_RUIDO, imagem.shape)
    return np.clip(imagem.astype(np.float64) + ruido, 0, 255).astype(np.uint8)


def medir_altura_cm(imagem_bgr: np.ndarray, altura_haste_cm: float) -> tuple[float, float]:
    """Roda o pipeline inteiro sobre a imagem.

    Returns:
        `(altura_vegetacao_cm, pixels_por_cm)`.

    Raises:
        ReferenciaNaoEncontrada: repassada da calibracao.
        AssertionError: se nenhuma vegetacao for encontrada na cena de teste.
    """
    razao = pixels_por_cm(imagem_bgr, altura_haste_cm)

    mascara = mascara_vegetacao(imagem_bgr)
    regiao = maior_regiao(mascara)
    assert regiao is not None, "nenhuma vegetacao encontrada na cena sintetica"

    bbox, _ = regiao
    return altura_em_pixels(bbox) / razao, razao


# --- Cenarios ---------------------------------------------------------------
# (nome, altura_haste_px, altura_vegetacao_px, altura_haste_cm)
CENARIOS: list[tuple[str, int, int, float]] = [
    ("mato baixo", 400, 150, 100.0),
    ("mato medio", 300, 240, 100.0),
    ("mato rasteiro", 500, 60, 100.0),
    ("haste de 150 cm", 360, 180, 150.0),
    ("haste curta, mato alto", 250, 300, 100.0),
]


def _linha(*colunas: str) -> str:
    larguras = (24, 12, 12, 10, 8)
    return "  ".join(texto.ljust(largura) for texto, largura in zip(colunas, larguras))


def executar() -> int:
    """Roda todos os cenarios. Returns: 0 se tudo passou, 1 caso contrario."""
    print("Teste sintetico do pipeline de medicao")
    print("=" * 72)
    print(_linha("cenario", "esperado", "medido", "erro", "veredito"))
    print("-" * 72)

    falhas = 0

    for nome, haste_px, vegetacao_px, haste_cm in CENARIOS:
        imagem = gerar_cena(haste_px, vegetacao_px)
        esperado_cm = vegetacao_px / (haste_px / haste_cm)

        try:
            medido_cm, razao = medir_altura_cm(imagem, haste_cm)
        except (ReferenciaNaoEncontrada, AssertionError) as erro:
            print(_linha(nome, f"{esperado_cm:.1f} cm", "-", "-", "FALHOU"))
            print(f"    {type(erro).__name__}: {erro}")
            falhas += 1
            continue

        erro_relativo = abs(medido_cm - esperado_cm) / esperado_cm
        passou = erro_relativo <= TOLERANCIA
        if not passou:
            falhas += 1

        print(
            _linha(
                nome,
                f"{esperado_cm:.1f} cm",
                f"{medido_cm:.1f} cm",
                f"{erro_relativo:.2%}",
                "ok" if passou else "FALHOU",
            )
        )
        razao_esperada = haste_px / haste_cm
        print(
            f"    pixels_por_cm: {razao:.4f} "
            f"(esperado {razao_esperada:.4f}, haste {haste_px} px / {haste_cm:.0f} cm)"
        )

    print("-" * 72)

    # Sem haste no quadro a calibracao tem de falhar. Devolver um numero
    # plausivel seria pior que falhar: contaminaria o historico do ponto.
    print("Cena sem haste: a calibracao deve recusar, nao estimar")
    imagem_sem_haste = gerar_cena(0, 200, com_haste=False)
    try:
        razao = pixels_por_cm(imagem_sem_haste, 100.0)
    except ReferenciaNaoEncontrada as erro:
        print(f"    ok — recusou: {str(erro)[:60]}...")
    else:
        print(f"    FALHOU — devolveu {razao:.4f} px/cm em vez de levantar excecao")
        falhas += 1

    print("=" * 72)
    if falhas == 0:
        print(f"Todos os {len(CENARIOS) + 1} testes passaram "
              f"(tolerancia de {TOLERANCIA:.0%}).")
        return 0

    print(f"{falhas} teste(s) falharam.")
    return 1


if __name__ == "__main__":
    sys.exit(executar())
