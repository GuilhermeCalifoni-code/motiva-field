"""Testes do pipeline de foto: contrato JSON e recusa sem haste."""
from __future__ import annotations

import tempfile
from pathlib import Path

import cv2

from pipeline import FotoInvalida, processar_foto
from teste_sintetico import gerar_cena


def bytes_jpeg(imagem) -> bytes:
    ok, codificada = cv2.imencode(".jpg", imagem)
    assert ok, "não foi possível codificar a cena"
    return codificada.tobytes()


def executar() -> int:
    with tempfile.TemporaryDirectory() as pasta_temporaria:
        saida = Path(pasta_temporaria)
        cena = gerar_cena(altura_haste_px=400, altura_vegetacao_px=240)
        resultado = processar_foto(bytes_jpeg(cena), "teste.jpg", 100, saida)

        deteccao = resultado["deteccoes"][0]
        assert deteccao["unidade"] == "cm"
        assert abs(deteccao["metrica"] - 60.0) <= 3.0
        assert resultado["calibracao"]["pixels_por_cm"] > 0
        assert (saida / resultado["evidencias"]["imagem_anotada"]).is_file()
        assert (saida / resultado["evidencias"]["mascara"]).is_file()
        assert (saida / resultado["evidencias"]["json"]).is_file()
        print(f"ok — contrato: {deteccao['metrica']} cm; evidências gravadas")

        try:
            processar_foto(bytes_jpeg(gerar_cena(0, 200, com_haste=False)), "sem-haste.jpg", 100, saida)
        except FotoInvalida:
            print("ok — foto sem haste recusada")
        else:
            raise AssertionError("foto sem haste não foi recusada")

    return 0


if __name__ == "__main__":
    raise SystemExit(executar())
