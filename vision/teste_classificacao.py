"""Prova o caminho da classificacao, quando o modelo existir.

O modelo ainda esta sendo retreinado. Ate o arquivo aparecer em
`vision/modelos/`, este teste PULA — nao falha. Assim ele pode entrar no
repositorio e no CI hoje, e passa a valer sozinho no dia em que o arquivo for
colocado na pasta, sem ninguem precisar lembrar de habilitar nada.

O que ele verifica quando roda:

    - o modelo carrega do caminho resolvido
    - o pre-processamento produz o formato e a faixa que o treino produzia
    - `classificar` devolve uma das classes configuradas
    - a confianca fica entre 0 e 1

Uso:
    python teste_classificacao.py

Sai com 0 quando passa ou quando pula; 1 quando falha. Nao abre janela.
"""

from __future__ import annotations

import sys

import numpy as np

from classificacao import (
    LADO_PADRAO,
    caminho_do_modelo,
    carregar_modelo,
    classes,
    classificar,
    modelo_disponivel,
    preprocessar,
)

# Faixa que a cadeia de treino produz. Vem da conta, nao de medicao:
#   passo 1: [0, 1]
#   passo 2: (0 - 0.485)/0.229 = -2.12  ate  (1 - 0.406)/0.225 = +2.64
#   passo 3: v*255/127.5 - 1 = 2v - 1   ->   -5.24 ate +4.28
# Se o resultado sair de [-1, 1] limpo, e sinal de que alguem "consertou" a
# dupla normalizacao e desalinhou a inferencia do treino.
FAIXA_ESPERADA = (-5.3, 4.3)


def recorte_sintetico(cor_bgr: tuple[int, int, int], lado: int = 96) -> np.ndarray:
    """Recorte chapado com ruido leve, no lugar de uma foto de mato."""
    imagem = np.full((lado, lado, 3), cor_bgr, dtype=np.uint8)
    gerador = np.random.default_rng(7)
    ruido = gerador.normal(0.0, 8.0, imagem.shape)
    return np.clip(imagem.astype(np.float64) + ruido, 0, 255).astype(np.uint8)


def testar_preprocessamento() -> list[str]:
    """Confere formato e faixa. Roda mesmo sem modelo."""
    falhas: list[str] = []
    recorte = recorte_sintetico((40, 160, 50))
    lote = preprocessar(recorte, LADO_PADRAO)

    esperado = (1, LADO_PADRAO, LADO_PADRAO, 3)
    if lote.shape != esperado:
        falhas.append(f"formato {lote.shape}, esperado {esperado}")
    else:
        print(f"    formato ................ {lote.shape}  ok")

    if lote.dtype != np.float32:
        falhas.append(f"dtype {lote.dtype}, esperado float32")
    else:
        print(f"    dtype .................. {lote.dtype}  ok")

    minimo, maximo = float(lote.min()), float(lote.max())
    limite_baixo, limite_alto = FAIXA_ESPERADA
    if minimo < limite_baixo or maximo > limite_alto:
        falhas.append(
            f"faixa [{minimo:.2f}, {maximo:.2f}] fora de "
            f"[{limite_baixo}, {limite_alto}]"
        )
    else:
        print(
            f"    faixa .................. [{minimo:.2f}, {maximo:.2f}]  ok "
            "(dupla normalizacao preservada)"
        )

    if maximo <= 1.0 and minimo >= -1.0:
        falhas.append(
            "a saida ficou dentro de [-1, 1]: a dupla normalizacao do treino "
            "parece ter sido removida, e a inferencia nao bate mais com o treino"
        )

    return falhas


def testar_classificacao() -> list[str]:
    """Carrega o modelo e classifica recortes sinteticos."""
    falhas: list[str] = []
    rotulos = classes()

    print(f"    carregando {caminho_do_modelo()} ...")
    modelo = carregar_modelo()
    print("    modelo carregado  ok")

    cenas = [
        ("verde vivo", (40, 160, 50)),
        ("verde seco", (60, 120, 110)),
        ("terra", (33, 67, 101)),
    ]

    for nome, cor in cenas:
        recorte = recorte_sintetico(cor)
        classe, confianca = classificar(recorte, modelo=modelo)

        problemas = []
        if classe not in rotulos:
            problemas.append(f"classe '{classe}' fora de {rotulos}")
        if not 0.0 <= confianca <= 1.0:
            problemas.append(f"confianca {confianca} fora de [0, 1]")

        if problemas:
            falhas.extend(problemas)
            print(f"    {nome:<12} FALHOU: {'; '.join(problemas)}")
        else:
            print(f"    {nome:<12} -> {classe} ({confianca:.1%})  ok")

    return falhas


def executar() -> int:
    print("Teste da classificacao")
    print("=" * 72)

    print("Pre-processamento (independe do modelo)")
    falhas = testar_preprocessamento()

    print()
    print("Classificacao")

    if not modelo_disponivel():
        print(f"    PULADO — modelo ausente em {caminho_do_modelo()}")
        print("    O teste passa a valer sozinho quando o arquivo aparecer ali.")
        print("=" * 72)
        if falhas:
            for falha in falhas:
                print(f"  FALHA: {falha}")
            return 1
        print("Pre-processamento ok; classificacao pulada por falta de modelo.")
        return 0

    falhas.extend(testar_classificacao())

    print("=" * 72)
    if falhas:
        for falha in falhas:
            print(f"  FALHA: {falha}")
        return 1

    print("Todos os testes passaram.")
    return 0


if __name__ == "__main__":
    sys.exit(executar())
