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

import json
import warnings
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

try:  # como pacote: python -m vision.calibracao
    from .graduacao import escala_por_graduacao
    from .segmentacao import mascara_vegetacao
except ImportError:  # direto de dentro de vision/: python teste_sintetico.py
    from graduacao import escala_por_graduacao
    from segmentacao import mascara_vegetacao

# Acima disso, a escala lida na graduacao e a derivada do comprimento digitado
# nao estao falando da mesma fita. Quase sempre e erro de digitacao.
DIVERGENCIA_MAXIMA_PCT = 15.0

# Abaixo disso a leitura da graduacao entra no resultado, mas com aviso.
CONFIANCA_GRADUACAO_MINIMA = 0.5

# --- Deteccao por cor (metodo principal) ------------------------------------
#
# Faixa HSV da trena, na convencao do OpenCV: H vai de 0 a 179, nao de 0 a 359.
#
# ESTES NUMEROS VALEM PARA TRENA AMARELA. Referencia de outra cor — laranja,
# branca, vermelha, fita metrica preta — NAO sera encontrada por aqui e vai cair
# no fallback geometrico, que so funciona em fundo limpo. Trocou a cor da
# referencia, ajuste esta faixa.
HSV_TRENA_MINIMO = (20, 140, 140)
HSV_TRENA_MAXIMO = (32, 255, 255)

# Fechamento com kernel vertical: costura as marcacoes, numeros e reflexos da
# trena num corpo unico, sem engordar a largura e estragar a razao.
KERNEL_FECHAMENTO_TRENA = (15, 7)  # (altura, largura) em pixels

# A trena e alta e estreita, mas menos exigente que o filtro geometrico: aqui a
# cor ja fez a maior parte da separacao.
RAZAO_MINIMA_COR = 3.0
FRACAO_ALTURA_MINIMA_COR = 0.10

# --- Fallback geometrico ----------------------------------------------------
#
# A haste e alta e estreita. Estes limites separam ela do chao, do horizonte e
# de placas — objetos largos ou baixos demais.
#
# So funciona em fundo limpo. Com ceu, predios ou carros no quadro, tudo que
# nao e vegetacao vira UM componente do tamanho da imagem e nada passa no
# filtro de largura. Foi por isso que a deteccao por cor virou o metodo
# principal.
RAZAO_ALTURA_LARGURA_MINIMA = 4.0
FRACAO_ALTURA_MINIMA = 0.10
FRACAO_LARGURA_MAXIMA = 0.20
ABERTURA_HASTE = 3

# Arquivo de calibracao persistida. Fica fora do git: e especifico de cada
# maquina, camera e montagem no veiculo.
CAMINHO_PADRAO_CALIBRACAO = Path(__file__).resolve().parent / "calibracao.json"

# Acima disso, carregar_calibracao avisa. A camera sai do lugar: batida de
# porta, manutencao, troca de veiculo. Calibracao velha mede errado calada.
IDADE_MAXIMA_DIAS = 7


class ReferenciaNaoEncontrada(Exception):
    """A haste de calibracao nao foi localizada na imagem."""


class CalibracaoInvalida(ValueError):
    """O arquivo de calibracao esta ausente, corrompido ou incompleto."""


class CalibracaoAntiga(UserWarning):
    """A calibracao carregada e velha demais para ser confiavel sem conferir."""


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


def _detectar_por_cor(imagem_bgr: np.ndarray) -> tuple[int, int, int, int] | None:
    """Acha a trena amarela por cor, que e o que ela tem de distintivo.

    Cor resolve o problema que a geometria nao resolve: num quadro com ceu,
    predios e carros, "o que nao e vegetacao" e a imagem inteira, e nenhum
    filtro de forma consegue recortar a trena de dentro disso. O amarelo
    saturado, por outro lado, quase nao aparece em cena de rodovia.

    Returns:
        `(x, y, largura, altura)` da maior mancha amarela que passa nos limites
        de forma, ou None se nada passar.
    """
    altura_imagem = imagem_bgr.shape[0]

    hsv = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2HSV)
    mascara = cv2.inRange(
        hsv,
        np.array(HSV_TRENA_MINIMO, dtype=np.uint8),
        np.array(HSV_TRENA_MAXIMO, dtype=np.uint8),
    )

    # Fechamento vertical: a trena tem marcacoes e numeros que quebram a mancha.
    elemento = np.ones(KERNEL_FECHAMENTO_TRENA, dtype=np.uint8)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, elemento)

    quantidade, _, estatisticas, _ = cv2.connectedComponentsWithStats(
        mascara, connectivity=8
    )
    if quantidade <= 1:
        return None

    indice = 1 + int(np.argmax(estatisticas[1:, cv2.CC_STAT_AREA]))
    x = int(estatisticas[indice, cv2.CC_STAT_LEFT])
    y = int(estatisticas[indice, cv2.CC_STAT_TOP])
    largura = int(estatisticas[indice, cv2.CC_STAT_WIDTH])
    altura = int(estatisticas[indice, cv2.CC_STAT_HEIGHT])

    if largura <= 0 or altura <= 0:
        return None
    if altura < FRACAO_ALTURA_MINIMA_COR * altura_imagem:
        return None
    if altura / largura < RAZAO_MINIMA_COR:
        return None

    return x, y, largura, altura


def _detectar_por_geometria(imagem_bgr: np.ndarray) -> tuple[int, int, int, int] | None:
    """Fallback: acha a haste pela forma, sem depender da cor.

    Procedimento:

    1. Segmenta a vegetacao e a exclui — a haste nunca e verde.
    2. Dentro do que sobrou, separa claro de escuro por Otsu. A haste e pintada
       para contrastar com verde e marrom, entao cai num dos dois lados,
       enquanto o chao ocupa o outro.
    3. Mantem so componentes altas e estreitas.
    4. Escolhe a mais alta; empate desempata pela mais estreita.

    So funciona em fundo limpo. E o metodo original, mantido porque cobre
    referencia de qualquer cor — inclusive a haste cinza do teste sintetico.

    Returns:
        `(x, y, largura, altura)` da haste, ou None se nada passar.
    """
    altura_imagem, largura_imagem = imagem_bgr.shape[:2]

    vegetacao = mascara_vegetacao(imagem_bgr)
    nao_vegetacao = cv2.bitwise_not(vegetacao)

    cinza = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY)
    valores = cinza[nao_vegetacao > 0]
    if valores.size == 0:
        # A imagem inteira foi classificada como vegetacao.
        return None

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
        return None

    # Mais alta primeiro; entre alturas iguais, a mais estreita.
    altura, largura, x, y, _ = max(candidatos, key=lambda c: (c[0], -c[1]))
    return x, y, largura, altura


def detectar_referencia(
    imagem_bgr: np.ndarray,
) -> tuple[str, tuple[int, int, int, int]] | None:
    """Localiza a referencia, tentando cor e depois forma.

    Returns:
        `(metodo, (x, y, largura, altura))` com metodo em `"cor"` ou
        `"geometria"`, ou None se nenhuma das duas achar.
    """
    caixa = _detectar_por_cor(imagem_bgr)
    if caixa is not None:
        return "cor", caixa

    caixa = _detectar_por_geometria(imagem_bgr)
    if caixa is not None:
        return "geometria", caixa

    return None


def medir_escala(
    imagem_bgr: np.ndarray, comprimento_referencia_cm: float | None = None
) -> dict[str, object]:
    """Deriva a escala da foto, por tres vias em ordem de preferencia.

    1. **Graduacao** (preferida): le as marcas impressas na trena e descobre a
       escala sozinha. Nao depende de ninguem digitar nada, e por isso e imune
       ao erro que motivou este caminho.
    2. **Comprimento informado**: usa o numero digitado, dividindo a altura da
       bbox pelo comprimento declarado.
    3. Falha com `ReferenciaNaoEncontrada`.

    Quando as duas primeiras estao disponiveis, calcula as duas e COMPARA. Uma
    divergencia grande quase sempre significa que a pessoa digitou o
    comprimento errado — e o sistema precisa dizer isso em voz alta, porque o
    erro escala tudo proporcionalmente sem deixar rastro no resultado.

    Args:
        imagem_bgr: foto com a referencia no quadro.
        comprimento_referencia_cm: comprimento declarado, em cm. Opcional.

    Returns:
        Dicionario com `pixels_por_cm`, `via`, `bbox_referencia`, `graduacao`,
        `comprimento_visivel_cm`, `divergencia_pct` e `avisos`.

    Raises:
        ValueError: se o comprimento informado nao for positivo.
        ReferenciaNaoEncontrada: se a referencia nao aparecer na foto.
    """
    if imagem_bgr is None:
        raise ValueError("imagem_bgr e None")
    if comprimento_referencia_cm is not None and comprimento_referencia_cm <= 0:
        raise ValueError(
            f"comprimento_referencia_cm deve ser positivo, recebi "
            f"{comprimento_referencia_cm}"
        )

    encontrado = detectar_referencia(imagem_bgr)
    if encontrado is None:
        raise ReferenciaNaoEncontrada(
            "referencia nao encontrada por nenhuma das duas vias. "
            f"Por cor: nenhuma mancha amarela em HSV {HSV_TRENA_MINIMO}-"
            f"{HSV_TRENA_MAXIMO} com altura >= {FRACAO_ALTURA_MINIMA_COR:.0%} da "
            f"imagem e razao altura/largura >= {RAZAO_MINIMA_COR:.0f}. "
            f"Por forma: nenhum objeto vertical estreito fora da vegetacao "
            f"(altura >= {FRACAO_ALTURA_MINIMA:.0%}, largura <= "
            f"{FRACAO_LARGURA_MAXIMA:.0%}, razao >= "
            f"{RAZAO_ALTURA_LARGURA_MINIMA:.0f}). "
            "Confira se a trena aparece inteira, na vertical e com a face "
            "amarela para a camera. Sem referencia nao ha como converter pixels "
            "em centimetros — a foto nao serve para medir."
        )

    metodo_deteccao, bbox = encontrado
    altura_px = bbox[3]

    graduacao = escala_por_graduacao(imagem_bgr, bbox)
    escala_informada = (
        float(altura_px) / float(comprimento_referencia_cm)
        if comprimento_referencia_cm
        else None
    )

    avisos: list[str] = []
    divergencia_pct: float | None = None

    if graduacao is not None and escala_informada is not None:
        escala_graduacao = float(graduacao["pixels_por_cm"])
        divergencia_pct = (
            abs(escala_graduacao - escala_informada) / escala_graduacao * 100.0
        )
        if divergencia_pct > DIVERGENCIA_MAXIMA_PCT:
            avisos.append(
                f"as duas vias de escala divergem {divergencia_pct:.0f}%: a "
                f"graduacao da trena indica {escala_graduacao:.2f} px/cm "
                f"(fita visivel de {graduacao['comprimento_visivel_cm']:.1f} cm), "
                f"mas o comprimento informado de {comprimento_referencia_cm:.1f} cm "
                f"daria {escala_informada:.2f} px/cm. Quase sempre isso e o "
                "comprimento digitado errado — confira quanto da fita aparece "
                "na foto."
            )

    if graduacao is not None:
        confianca = float(graduacao["confianca"])
        if confianca < CONFIANCA_GRADUACAO_MINIMA:
            avisos.append(
                f"a leitura da graduacao saiu com confianca baixa "
                f"({confianca:.2f} < {CONFIANCA_GRADUACAO_MINIMA}). As marcas "
                "podem estar borradas ou pequenas demais para esta resolucao."
            )
        via = "graduacao"
        escala = float(graduacao["pixels_por_cm"])
        comprimento_visivel_cm = float(graduacao["comprimento_visivel_cm"])
    elif escala_informada is not None:
        via = "comprimento_informado"
        escala = escala_informada
        comprimento_visivel_cm = float(comprimento_referencia_cm)
        avisos.append(
            "nao foi possivel ler a graduacao da trena; a escala veio do "
            "comprimento informado. Se esse numero estiver errado, a medida "
            "inteira sai errada na mesma proporcao."
        )
    else:
        raise ReferenciaNaoEncontrada(
            "a referencia foi localizada na foto, mas a graduacao nao pode ser "
            "lida e nenhum comprimento foi informado. Sem uma das duas nao ha "
            "escala. Informe quantos centimetros da fita aparecem no quadro, ou "
            "refaca a foto com a graduacao legivel."
        )

    return {
        "pixels_por_cm": round(float(escala), 4),
        "via": via,
        "metodo_deteccao": metodo_deteccao,
        "bbox_referencia": [int(v) for v in bbox],
        "graduacao": graduacao,
        "comprimento_visivel_cm": round(comprimento_visivel_cm, 2),
        "comprimento_informado_cm": (
            float(comprimento_referencia_cm) if comprimento_referencia_cm else None
        ),
        "pixels_por_cm_informado": (
            round(escala_informada, 4) if escala_informada is not None else None
        ),
        "divergencia_pct": (
            round(divergencia_pct, 1) if divergencia_pct is not None else None
        ),
        "avisos": avisos,
    }


def pixels_por_cm(
    imagem_bgr: np.ndarray, altura_referencia_cm: float | None = None
) -> float:
    """Quantos pixels valem um centimetro. Atalho para `medir_escala`.

    Mantida com esta assinatura porque e o que o resto do codigo e os testes ja
    chamam. O comprimento passou a ser opcional: sem ele, a escala sai da
    graduacao.
    """
    return float(medir_escala(imagem_bgr, altura_referencia_cm)["pixels_por_cm"])


# --- Calibracao persistida --------------------------------------------------
#
# Em producao a camera fica fixa no veiculo, com altura e angulo constantes, e
# nao ha regua dentro de cada foto. Calibra-se UMA vez, com a trena no quadro, e
# reusa-se a escala.
#
# O preco disso e que a escala passa a valer so para aquela geometria. Por isso
# a geometria viaja junto no dicionario e reaparece no JSON de saida: quem ler o
# resultado depois consegue auditar de onde veio o centimetro.


def calibrar_de_foto(
    caminho_imagem: str | Path,
    comprimento_referencia_cm: float | None,
    altura_camera_cm: float,
    distancia_alvo_cm: float,
) -> dict[str, object]:
    """Deriva a calibracao de uma foto com a referencia no quadro.

    A deteccao e a mesma de `pixels_por_cm`: procura o objeto alto e estreito
    fora da vegetacao. A trena precisa aparecer **na vertical** — deitada no
    chao ela nao e reconhecida.

    Args:
        caminho_imagem: foto contendo a referencia inteira no quadro.
        comprimento_referencia_cm: comprimento real da referencia, em cm.
        altura_camera_cm: altura da camera em relacao ao solo, em cm.
        distancia_alvo_cm: distancia da camera ate o alvo, em cm.

    Returns:
        Dicionario de calibracao pronto para `salvar_calibracao`.

    Raises:
        FileNotFoundError: se a foto nao existir.
        CalibracaoInvalida: se a foto nao puder ser lida ou os numeros da
            geometria nao forem positivos.
        ReferenciaNaoEncontrada: se a referencia nao aparecer na foto.
    """
    caminho = Path(caminho_imagem)
    if not caminho.is_file():
        raise FileNotFoundError(f"foto de calibracao nao encontrada: {caminho}")

    # O comprimento da referencia virou opcional: quando a graduacao e legivel,
    # a escala sai dela. A geometria continua obrigatoria — e ela que registra
    # em que condicoes a calibracao vale.
    for nome, valor in (
        ("altura_camera_cm", altura_camera_cm),
        ("distancia_alvo_cm", distancia_alvo_cm),
    ):
        if valor is None or float(valor) <= 0:
            raise CalibracaoInvalida(f"{nome} deve ser positivo, recebi {valor}")

    if comprimento_referencia_cm is not None and float(comprimento_referencia_cm) <= 0:
        raise CalibracaoInvalida(
            f"comprimento_referencia_cm deve ser positivo, recebi "
            f"{comprimento_referencia_cm}"
        )

    imagem = cv2.imread(str(caminho))
    if imagem is None:
        raise CalibracaoInvalida(
            f"nao foi possivel ler a imagem {caminho.name}; use JPG, JPEG ou PNG"
        )

    medicao = medir_escala(
        imagem,
        float(comprimento_referencia_cm) if comprimento_referencia_cm else None,
    )

    return {
        "pixels_por_cm": round(float(medicao["pixels_por_cm"]), 4),
        "geometria": {
            "altura_camera_cm": float(altura_camera_cm),
            "distancia_alvo_cm": float(distancia_alvo_cm),
        },
        "origem": {
            "foto": caminho.name,
            "via": medicao["via"],
            "referencia_cm": (
                float(comprimento_referencia_cm) if comprimento_referencia_cm else None
            ),
            "comprimento_visivel_cm": medicao["comprimento_visivel_cm"],
            "graduacao": medicao["graduacao"],
            "criado_em": datetime.now().astimezone().isoformat(timespec="seconds"),
        },
        "avisos": medicao["avisos"],
    }


def _validar_estrutura(dados: object) -> dict[str, object]:
    """Confere que o dicionario tem o minimo para ser usado como escala."""
    if not isinstance(dados, dict):
        raise CalibracaoInvalida("a calibracao precisa ser um objeto JSON")

    escala = dados.get("pixels_por_cm")
    if not isinstance(escala, (int, float)) or escala <= 0:
        raise CalibracaoInvalida(
            f"pixels_por_cm ausente ou nao positivo: {escala!r}"
        )

    geometria = dados.get("geometria")
    if not isinstance(geometria, dict):
        raise CalibracaoInvalida(
            "bloco 'geometria' ausente. Sem altura da camera e distancia do "
            "alvo nao da para auditar em que condicoes a escala vale."
        )

    return dados


def salvar_calibracao(
    dados: dict[str, object], caminho: str | Path = CAMINHO_PADRAO_CALIBRACAO
) -> Path:
    """Grava a calibracao em JSON. Returns: o caminho escrito."""
    _validar_estrutura(dados)
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return destino


def idade_em_dias(dados: dict[str, object], agora: datetime | None = None) -> float | None:
    """Idade da calibracao em dias, ou None se a origem nao tiver data."""
    origem = dados.get("origem")
    if not isinstance(origem, dict):
        return None
    criado_em = origem.get("criado_em")
    if not isinstance(criado_em, str):
        return None
    try:
        marca = datetime.fromisoformat(criado_em)
    except ValueError:
        return None
    referencia = agora or datetime.now().astimezone()
    if marca.tzinfo is None:
        marca = marca.replace(tzinfo=referencia.tzinfo)
    return (referencia - marca).total_seconds() / 86400.0


def carregar_calibracao(
    caminho: str | Path = CAMINHO_PADRAO_CALIBRACAO,
) -> dict[str, object]:
    """Le a calibracao do disco e avisa quando ela esta velha.

    O aviso e `CalibracaoAntiga` via warnings — nao interrompe, porque uma
    calibracao velha ainda pode estar correta. Mas precisa aparecer: a camera
    sai do lugar e nada no resultado denuncia isso sozinho.

    Raises:
        CalibracaoInvalida: se o arquivo nao existir, nao for JSON valido ou
            estiver incompleto.
    """
    origem = Path(caminho)
    if not origem.is_file():
        raise CalibracaoInvalida(
            f"calibracao nao encontrada em {origem}. Gere com: "
            "python -m vision.calibracao --foto FOTO --referencia-cm N "
            "--altura-camera-cm N --distancia-cm N"
        )

    try:
        dados = json.loads(origem.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise CalibracaoInvalida(f"{origem.name} nao e JSON valido: {erro}") from erro

    _validar_estrutura(dados)

    idade = idade_em_dias(dados)
    if idade is not None and idade > IDADE_MAXIMA_DIAS:
        warnings.warn(
            f"calibracao de {origem.name} tem {idade:.0f} dias (limite "
            f"{IDADE_MAXIMA_DIAS}). Ela so vale para a geometria em que foi "
            "feita; se a camera saiu do lugar, a medida sai errada sem avisar. "
            "Refaca a calibracao ou confira com python -m vision.conferir.",
            CalibracaoAntiga,
            stacklevel=2,
        )

    return dados


def _principal(argumentos: list[str] | None = None) -> int:
    """CLI: gera e grava a calibracao a partir de uma foto com a referencia."""
    import argparse

    analisador = argparse.ArgumentParser(
        prog="python -m vision.calibracao",
        description=(
            "Gera a calibracao pixel/cm a partir de uma foto com trena no "
            "quadro. A escala resultante vale so para esta geometria de camera."
        ),
    )
    analisador.add_argument("--foto", required=True, help="foto com a referencia no quadro")
    analisador.add_argument(
        "--referencia-cm", required=True, type=float, help="comprimento real da referencia, em cm"
    )
    analisador.add_argument(
        "--altura-camera-cm", required=True, type=float, help="altura da camera ao solo, em cm"
    )
    analisador.add_argument(
        "--distancia-cm", required=True, type=float, help="distancia da camera ao alvo, em cm"
    )
    analisador.add_argument(
        "--saida",
        default=str(CAMINHO_PADRAO_CALIBRACAO),
        help=f"arquivo de destino (padrao: {CAMINHO_PADRAO_CALIBRACAO.name})",
    )
    opcoes = analisador.parse_args(argumentos)

    try:
        dados = calibrar_de_foto(
            opcoes.foto,
            opcoes.referencia_cm,
            opcoes.altura_camera_cm,
            opcoes.distancia_cm,
        )
    except (FileNotFoundError, CalibracaoInvalida, ReferenciaNaoEncontrada) as erro:
        print(f"FALHOU: {erro}")
        return 1

    destino = salvar_calibracao(dados, opcoes.saida)

    print("Calibracao gravada.")
    print(f"  arquivo ............ {destino}")
    print(f"  pixels_por_cm ...... {dados['pixels_por_cm']}")
    geometria = dados["geometria"]
    print(f"  altura da camera ... {geometria['altura_camera_cm']:.0f} cm")
    print(f"  distancia do alvo .. {geometria['distancia_alvo_cm']:.0f} cm")
    print(f"  origem ............. {dados['origem']['foto']}")
    print()
    print("Vale so para esta geometria. Mudou altura, angulo ou distancia,")
    print("refaca — a medida sai errada e nada avisa.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_principal())
