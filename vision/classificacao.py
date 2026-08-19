"""Classificacao do recorte de vegetacao pelo modelo treinado.

Recebe o recorte que `segmentacao.maior_regiao` isolou e devolve a classe de
risco com a confianca. O modulo nao conhece o Supabase nem monta JSON — isso e
do passo seguinte, conforme docs/contrato-json-deteccoes.md.

O import do TensorFlow e adiado para dentro das funcoes: ele custa segundos e
nao deve pesar em quem so quer inspecionar constantes ou rodar a segmentacao.

Nada aqui abre janela: o modulo roda headless.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import cv2
import numpy as np

# Caminho padrao, relativo a este arquivo — nunca absoluto de maquina.
CAMINHO_PADRAO = Path(__file__).resolve().parent / "modelos" / "mobilenet_motiva.keras"
VARIAVEL_MODELO = "MOTIVA_MODELO"
VARIAVEL_CLASSES = "MOTIVA_CLASSES"

# ATENCAO — a ordem importa e precisa bater com o `class_indices` do gerador de
# treino, nao com o que parece logico aqui. O Keras ordena os diretorios de
# classe alfabeticamente, entao a ordem final depende de como as pastas foram
# nomeadas no notebook. Um desalinhamento aqui nao quebra nada: so troca os
# rotulos silenciosamente, e "Critico" vira "Seguro" sem ninguem perceber.
#
# Quando o modelo retreinado chegar, confira com:
#     print(train_generator.class_indices)
# e ajuste esta tupla ou defina MOTIVA_CLASSES="Seguro,Atencao,Critico".
CLASSES_PADRAO: tuple[str, ...] = ("Seguro", "Atenção", "Crítico")

# Estatisticas do ImageNet, em RGB.
MEDIA_IMAGENET = np.array([0.485, 0.456, 0.406], dtype=np.float32)
DESVIO_IMAGENET = np.array([0.229, 0.224, 0.225], dtype=np.float32)

LADO_PADRAO = 224

_modelo_em_cache: Any = None
_caminho_em_cache: Path | None = None


class ModeloNaoEncontrado(FileNotFoundError):
    """O arquivo do modelo nao existe no caminho resolvido."""


def caminho_do_modelo(caminho: str | os.PathLike[str] | None = None) -> Path:
    """Resolve qual arquivo de modelo usar.

    Precedencia: argumento explicito, depois a variavel de ambiente
    `MOTIVA_MODELO`, depois `vision/modelos/mobilenet_motiva.keras`.
    """
    if caminho is not None:
        return Path(caminho).expanduser().resolve()

    do_ambiente = os.environ.get(VARIAVEL_MODELO)
    if do_ambiente:
        return Path(do_ambiente).expanduser().resolve()

    return CAMINHO_PADRAO


def classes() -> tuple[str, ...]:
    """Rotulos na ordem das saidas do modelo.

    `MOTIVA_CLASSES` sobrescreve, separando por virgula — util para corrigir a
    ordem sem mexer no codigo quando o modelo for retreinado.
    """
    do_ambiente = os.environ.get(VARIAVEL_CLASSES)
    if do_ambiente:
        nomes = tuple(nome.strip() for nome in do_ambiente.split(",") if nome.strip())
        if nomes:
            return nomes
    return CLASSES_PADRAO


def modelo_disponivel(caminho: str | os.PathLike[str] | None = None) -> bool:
    """Se o arquivo do modelo existe. Permite pular teste sem falhar."""
    return caminho_do_modelo(caminho).is_file()


def carregar_modelo(caminho: str | os.PathLike[str] | None = None) -> Any:
    """Carrega o modelo Keras, com cache por caminho.

    Args:
        caminho: sobrescreve a variavel de ambiente e o padrao.

    Returns:
        Modelo Keras carregado.

    Raises:
        ModeloNaoEncontrado: com o caminho tentado e como apontar para outro.
    """
    global _modelo_em_cache, _caminho_em_cache

    destino = caminho_do_modelo(caminho)

    if _modelo_em_cache is not None and _caminho_em_cache == destino:
        return _modelo_em_cache

    if not destino.is_file():
        raise ModeloNaoEncontrado(
            f"modelo nao encontrado em {destino}. Coloque o arquivo treinado ali "
            f"ou aponte {VARIAVEL_MODELO} para outro caminho. O pipeline nao "
            "classifica sem modelo — nao ha fallback que invente classe."
        )

    # Import adiado: carregar o TensorFlow custa segundos.
    from tensorflow import keras  # noqa: PLC0415

    modelo = keras.models.load_model(destino)

    _modelo_em_cache = modelo
    _caminho_em_cache = destino
    return modelo


def _lado_esperado(modelo: Any) -> int:
    """Lado da entrada quadrada que o modelo espera, com queda para 224."""
    try:
        formato = modelo.input_shape
        if isinstance(formato, list):
            formato = formato[0]
        altura, largura = formato[1], formato[2]
        if altura and largura:
            return int(altura)
    except (AttributeError, IndexError, TypeError):
        pass
    return LADO_PADRAO


def preprocessar(recorte_bgr: np.ndarray, lado: int = LADO_PADRAO) -> np.ndarray:
    """Reproduz exatamente o pre-processamento usado no treino.

    A cadeia e esta, nesta ordem:

        1. x = imagem / 255                      -> [0, 1]
        2. x = (x - media_imagenet) / desvio     -> aproximadamente [-2.1, 2.6]
        3. x = preprocess_input(x * 255.0)       -> aproximadamente [-5.2, 4.2]

    Isto e uma DUPLA NORMALIZACAO e esta conceitualmente errado: o passo 2 ja
    padroniza, e o passo 3 volta a escalar como se a entrada ainda fosse
    [0, 255]. A faixa final estoura o [-1, 1] que o MobileNetV2 espera.

    Mesmo assim e o que fica. O modelo TREINOU com esta cadeia, entao os pesos
    aprenderam neste espaco de entrada deformado. Aplicar o pre-processamento
    "correto" na inferencia daria uma distribuicao diferente da vista no treino
    e a acuracia despencaria, silenciosamente — o modelo continuaria devolvendo
    tres probabilidades plausiveis, so que erradas.

    Consertar isso e retreinar, nao mexer aqui. Enquanto o treino nao mudar,
    inferencia e treino tem de errar igual.

    Args:
        recorte_bgr: recorte BGR, como o OpenCV entrega.
        lado: lado da entrada quadrada do modelo.

    Returns:
        Lote de 1 imagem, float32, formato `(1, lado, lado, 3)`.
    """
    if recorte_bgr is None:
        raise ValueError("recorte_bgr e None")
    if recorte_bgr.ndim != 3 or recorte_bgr.shape[2] != 3:
        raise ValueError(
            f"esperava recorte BGR de 3 canais, recebi shape {recorte_bgr.shape}"
        )
    if recorte_bgr.size == 0:
        raise ValueError("recorte_bgr esta vazio")

    # O MobileNetV2 foi treinado em RGB; o OpenCV entrega BGR.
    rgb = cv2.cvtColor(recorte_bgr, cv2.COLOR_BGR2RGB)
    redimensionado = cv2.resize(rgb, (lado, lado), interpolation=cv2.INTER_AREA)

    # Passo 1.
    x = redimensionado.astype(np.float32) / 255.0
    # Passo 2.
    x = (x - MEDIA_IMAGENET) / DESVIO_IMAGENET
    # Passo 3 — a funcao oficial, para nao divergir da versao do TensorFlow.
    from tensorflow.keras.applications.mobilenet_v2 import (  # noqa: PLC0415
        preprocess_input,
    )

    x = preprocess_input(x * 255.0)

    return np.expand_dims(x.astype(np.float32), axis=0)


def _para_probabilidades(vetor: np.ndarray) -> np.ndarray:
    """Garante que a saida seja distribuicao de probabilidade.

    Se a ultima camada ja tem softmax, devolve como esta. Se o modelo foi
    salvo emitindo logits, aplica softmax aqui — o contrato desta funcao e
    entregar confianca entre 0 e 1, e logit nao respeita isso.
    """
    dentro_do_intervalo = bool(np.all(vetor >= 0.0) and np.all(vetor <= 1.0))
    soma_um = bool(np.isclose(float(vetor.sum()), 1.0, atol=1e-3))
    if dentro_do_intervalo and soma_um:
        return vetor

    estavel = vetor - np.max(vetor)
    exponencial = np.exp(estavel)
    return exponencial / exponencial.sum()


def classificar(
    recorte_bgr: np.ndarray, modelo: Any = None
) -> tuple[str, float]:
    """Classifica o recorte em Seguro, Atencao ou Critico.

    Args:
        recorte_bgr: recorte BGR da vegetacao.
        modelo: modelo ja carregado. Quando omitido, usa `carregar_modelo()`,
            que mantem cache — passar explicitamente so ajuda em lote.

    Returns:
        `(classe, confianca)` com confianca entre 0 e 1.

    Raises:
        ModeloNaoEncontrado: se o arquivo do modelo nao existir.
        ValueError: se o recorte for invalido ou se o numero de saidas do
            modelo nao bater com o numero de classes configuradas.
    """
    if modelo is None:
        modelo = carregar_modelo()

    rotulos = classes()
    entrada = preprocessar(recorte_bgr, _lado_esperado(modelo))

    saida = modelo.predict(entrada, verbose=0)
    vetor = np.asarray(saida, dtype=np.float64).reshape(-1)

    if vetor.size != len(rotulos):
        raise ValueError(
            f"o modelo devolveu {vetor.size} saidas, mas ha {len(rotulos)} classes "
            f"configuradas {rotulos}. Ajuste CLASSES_PADRAO ou {VARIAVEL_CLASSES} "
            "para bater com o class_indices do treino."
        )

    probabilidades = _para_probabilidades(vetor)
    indice = int(np.argmax(probabilidades))

    return rotulos[indice], float(probabilidades[indice])
