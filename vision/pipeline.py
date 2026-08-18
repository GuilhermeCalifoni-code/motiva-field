"""Pipeline de foto real: imagem entra, JSON e evidências visuais saem."""
from __future__ import annotations

import json
from datetime import datetime
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
from PIL import Image

try:  # como pacote: python -m vision.conferir
    from .calibracao import ReferenciaNaoEncontrada, medir_escala
    from .segmentacao import altura_em_pixels, maior_regiao, mascara_vegetacao
except ImportError:  # direto de dentro de vision/
    from calibracao import ReferenciaNaoEncontrada, medir_escala
    from segmentacao import altura_em_pixels, maior_regiao, mascara_vegetacao

VERSAO_MODELO = "exg_haste_v1"

# --- Guardas de plausibilidade ----------------------------------------------
#
# Nenhuma delas impede o resultado. Elas acompanham o JSON, porque o erro que
# motivou tudo isto — escala proporcionalmente errada — produz um numero que
# parece perfeitamente normal. Quem le decide.
ALTURA_IMPLAUSIVEL_CM = 200.0
FATOR_MAXIMO_SOBRE_REFERENCIA = 3.0

# Valores de calibracao.referencia no JSON de saida. Existem para
# rastreabilidade: quem ler o resultado depois sabe como o centimetro foi
# obtido, sem precisar adivinhar.
VIA_ARQUIVO = "arquivo"
VIA_HASTE = "haste_no_quadro"


class FotoInvalida(ValueError):
    """A imagem não atende às condições mínimas para uma medição confiável."""


def _data_e_coordenadas(conteudo: bytes) -> tuple[str, dict[str, float] | None]:
    """Extrai data EXIF quando disponível; GPS é opcional nesta primeira versão."""
    agora = datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        imagem = Image.open(BytesIO(conteudo))
        exif = imagem.getexif()
        data = exif.get(36867) or exif.get(306)  # DateTimeOriginal / DateTime
        if data:
            data_parseada = datetime.strptime(str(data), "%Y:%m:%d %H:%M:%S")
            return data_parseada.replace(tzinfo=datetime.now().astimezone().tzinfo).isoformat(), None
    except Exception:
        pass
    return agora, None


def _anotar(
    imagem: np.ndarray,
    bbox: tuple[int, int, int, int],
    altura_cm: float,
    escala: float,
    bbox_referencia: list[int] | None = None,
    comprimento_referencia_cm: float | None = None,
) -> np.ndarray:
    resultado = imagem.copy()
    x1, y1, x2, y2 = bbox
    cv2.rectangle(resultado, (x1, y1), (x2, y2), (0, 215, 255), 3)
    cv2.putText(resultado, f"Vegetacao: {altura_cm:.1f} cm", (x1, max(30, y1 - 14)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 215, 255), 2, cv2.LINE_AA)
    cv2.putText(resultado, f"Escala: {escala:.2f} px/cm", (20, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

    # A trena tambem entra no overlay, com o comprimento que o sistema leu. E a
    # conferencia visual mais rapida que existe: se a caixa cobre meio metro de
    # fita e o rotulo diz 13 cm, da para ver o erro sem abrir o JSON.
    if bbox_referencia is not None and len(bbox_referencia) == 4:
        rx, ry, rw, rh = (int(v) for v in bbox_referencia)
        cv2.rectangle(resultado, (rx, ry), (rx + rw, ry + rh), (255, 120, 0), 3)
        if comprimento_referencia_cm is not None:
            cv2.putText(
                resultado,
                f"Trena: {comprimento_referencia_cm:.1f} cm",
                (rx, max(30, ry - 12)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 120, 0), 2, cv2.LINE_AA,
            )
    return resultado


def processar_foto(
    conteudo: bytes,
    nome_arquivo: str,
    referencia_cm: float | None = None,
    diretorio_saida: Path | None = None,
    *,
    calibracao: dict[str, object] | None = None,
) -> dict[str, object]:
    """Processa uma foto e gera o contrato do Bloco 2 mais evidências visuais.

    A escala vem por uma de duas fontes, nesta precedência:

    1. `calibracao`: dicionário lido de `vision/calibracao.json`. Mede sem
       nenhuma referência no quadro — é o modo de produção, com a câmera fixa
       no veículo.
    2. Referência na própria foto: lê a graduação da trena e, se não conseguir,
       usa o `referencia_cm` informado. É o modo de conferência.

    `referencia_cm` é OPCIONAL: quando a graduação é legível, a escala sai
    dela, sem ninguém digitar nada. Sem nenhuma fonte utilizável a função
    levanta `FotoInvalida`. Não existe valor padrão de escala: medir errado em
    silêncio é pior do que não medir, porque o número errado entra no histórico
    do ponto e só aparece meses depois, como uma projeção de roçada furada.
    """
    if not conteudo:
        raise FotoInvalida("arquivo vazio")

    if calibracao is None and referencia_cm is not None and referencia_cm <= 0:
        raise FotoInvalida("o comprimento da referência deve ser positivo")

    matriz = np.frombuffer(conteudo, dtype=np.uint8)
    imagem = cv2.imdecode(matriz, cv2.IMREAD_COLOR)
    if imagem is None:
        raise FotoInvalida("não foi possível ler a imagem; envie JPG, JPEG ou PNG")

    medicao: dict[str, object] | None = None

    if calibracao is not None:
        escala = float(calibracao.get("pixels_por_cm", 0) or 0)
        if escala <= 0:
            raise FotoInvalida(
                "a calibração informada não tem pixels_por_cm positivo; "
                "regenere com python -m vision.calibracao"
            )
        geometria = calibracao.get("geometria")
        bloco_calibracao: dict[str, object] = {
            "referencia": VIA_ARQUIVO,
            "pixels_por_cm": round(escala, 4),
            "geometria": geometria if isinstance(geometria, dict) else {},
        }
    else:
        try:
            medicao = medir_escala(imagem, referencia_cm)
        except (ReferenciaNaoEncontrada, ValueError) as erro:
            raise FotoInvalida(str(erro)) from erro
        escala = float(medicao["pixels_por_cm"])
        bloco_calibracao = {
            "referencia": VIA_HASTE,
            "pixels_por_cm": round(escala, 4),
            "via_escala": medicao["via"],
            "comprimento_visivel_cm": medicao["comprimento_visivel_cm"],
            "graduacao": medicao["graduacao"],
            "divergencia_pct": medicao["divergencia_pct"],
        }

    mascara = mascara_vegetacao(imagem)
    regiao = maior_regiao(mascara)
    if regiao is None:
        raise FotoInvalida("nenhuma região de vegetação foi encontrada na imagem")

    bbox, _ = regiao
    altura_cm = altura_em_pixels(bbox) / escala
    cobertura_pct = float(np.count_nonzero(mascara) / mascara.size * 100)
    capturado_em, coordenadas = _data_e_coordenadas(conteudo)

    # Avisos vindos da medicao de escala (divergencia entre vias, confianca
    # baixa da graduacao) mais as guardas de plausibilidade da medida.
    avisos: list[str] = list(medicao["avisos"]) if medicao is not None else []
    comprimento_referencia_cm = (
        float(medicao["comprimento_visivel_cm"]) if medicao is not None else None
    )

    if altura_cm > ALTURA_IMPLAUSIVEL_CM:
        avisos.append(
            f"altura medida de {altura_cm:.0f} cm acima do plausivel "
            f"({ALTURA_IMPLAUSIVEL_CM:.0f} cm) para vegetacao de faixa de "
            "dominio. Confira a escala antes de aceitar."
        )

    if (
        comprimento_referencia_cm
        and altura_cm > comprimento_referencia_cm * FATOR_MAXIMO_SOBRE_REFERENCIA
    ):
        avisos.append(
            f"a vegetacao medida ({altura_cm:.0f} cm) e mais de "
            f"{FATOR_MAXIMO_SOBRE_REFERENCIA:.0f}x maior que a referencia visivel "
            f"({comprimento_referencia_cm:.1f} cm). Medir algo muito maior que a "
            "regua e suspeito: a escala pode estar errada."
        )

    resultado: dict[str, object] = {
        "arquivo": Path(nome_arquivo).name,
        "capturado_em": capturado_em,
        "coordenadas": coordenadas,
        "modelo_versao": VERSAO_MODELO,
        "calibracao": bloco_calibracao,
        "avisos": avisos,
        "deteccoes": [{
            "classe": "vegetacao_alta",
            "confianca": 1.0,
            "metrica": round(altura_cm, 1),
            "unidade": "cm",
            "bbox": list(bbox),
            "cobertura_pct": round(cobertura_pct, 1),
        }],
    }

    if diretorio_saida is not None:
        diretorio_saida.mkdir(parents=True, exist_ok=True)
        identificador = uuid4().hex[:10]
        imagem_anotada = _anotar(
            imagem, bbox, altura_cm, escala,
            bbox_referencia=medicao["bbox_referencia"] if medicao is not None else None,
            comprimento_referencia_cm=comprimento_referencia_cm,
        )
        mascara_visual = cv2.cvtColor(mascara, cv2.COLOR_GRAY2BGR)
        mascara_visual[mascara > 0] = (40, 160, 50)
        anotada = diretorio_saida / f"{identificador}-anotada.jpg"
        mascara_path = diretorio_saida / f"{identificador}-mascara.png"
        contrato = diretorio_saida / f"{identificador}.json"
        cv2.imwrite(str(anotada), imagem_anotada)
        cv2.imwrite(str(mascara_path), mascara_visual)
        contrato.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        resultado["evidencias"] = {"imagem_anotada": anotada.name, "mascara": mascara_path.name, "json": contrato.name}

    return resultado
