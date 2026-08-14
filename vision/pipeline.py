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

from calibracao import ReferenciaNaoEncontrada, pixels_por_cm
from segmentacao import altura_em_pixels, maior_regiao, mascara_vegetacao

VERSAO_MODELO = "exg_haste_v1"


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


def _anotar(imagem: np.ndarray, bbox: tuple[int, int, int, int], altura_cm: float, escala: float) -> np.ndarray:
    resultado = imagem.copy()
    x1, y1, x2, y2 = bbox
    cv2.rectangle(resultado, (x1, y1), (x2, y2), (0, 215, 255), 3)
    cv2.putText(resultado, f"Vegetacao: {altura_cm:.1f} cm", (x1, max(30, y1 - 14)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 215, 255), 2, cv2.LINE_AA)
    cv2.putText(resultado, f"Escala: {escala:.2f} px/cm", (20, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
    return resultado


def processar_foto(
    conteudo: bytes,
    nome_arquivo: str,
    altura_haste_cm: float = 100.0,
    diretorio_saida: Path | None = None,
) -> dict[str, object]:
    """Processa uma foto e gera o contrato do Bloco 2 mais evidências visuais.

    A haste precisa estar inteira no quadro, vertical e no mesmo plano da
    vegetação. Sem ela a função falha explicitamente — nunca estima a escala.
    """
    if not conteudo:
        raise FotoInvalida("arquivo vazio")
    if altura_haste_cm <= 0:
        raise FotoInvalida("a altura da haste deve ser positiva")

    matriz = np.frombuffer(conteudo, dtype=np.uint8)
    imagem = cv2.imdecode(matriz, cv2.IMREAD_COLOR)
    if imagem is None:
        raise FotoInvalida("não foi possível ler a imagem; envie JPG, JPEG ou PNG")

    try:
        escala = pixels_por_cm(imagem, altura_haste_cm)
    except ReferenciaNaoEncontrada as erro:
        raise FotoInvalida(str(erro)) from erro

    mascara = mascara_vegetacao(imagem)
    regiao = maior_regiao(mascara)
    if regiao is None:
        raise FotoInvalida("nenhuma região de vegetação foi encontrada na imagem")

    bbox, _ = regiao
    altura_cm = altura_em_pixels(bbox) / escala
    cobertura_pct = float(np.count_nonzero(mascara) / mascara.size * 100)
    capturado_em, coordenadas = _data_e_coordenadas(conteudo)

    resultado: dict[str, object] = {
        "arquivo": Path(nome_arquivo).name,
        "capturado_em": capturado_em,
        "coordenadas": coordenadas,
        "modelo_versao": VERSAO_MODELO,
        "calibracao": {"referencia": f"haste_{altura_haste_cm:g}cm", "pixels_por_cm": round(escala, 4)},
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
        imagem_anotada = _anotar(imagem, bbox, altura_cm, escala)
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
