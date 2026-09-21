"""Calibração intrínseca real por fotos de tabuleiro xadrez.

Uso:
  python calibrar_camera.py --pasta fotos_tabuleiro --colunas 9 --linhas 6 --quadrado-mm 25

As dimensões são os cantos internos. O script grava fx/fy/cx/cy e distorção no
perfil_camera.json; não altera altura, pitch ou roll da montagem.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import cv2
import numpy as np
try:
    from .geometria import CAMINHO_PADRAO_PERFIL, carregar_perfil, salvar_perfil
except ImportError:
    from geometria import CAMINHO_PADRAO_PERFIL, carregar_perfil, salvar_perfil


def calibrar(pasta: Path, colunas: int, linhas: int, quadrado_mm: float) -> dict:
    padrao = (colunas, linhas)
    objeto = np.zeros((colunas * linhas, 3), np.float32)
    objeto[:, :2] = np.mgrid[0:colunas, 0:linhas].T.reshape(-1, 2) * quadrado_mm
    objetos, imagens, tamanho = [], [], None
    for caminho in sorted([*pasta.glob('*.jpg'), *pasta.glob('*.jpeg'), *pasta.glob('*.png')]):
        foto = cv2.imread(str(caminho))
        if foto is None: continue
        cinza = cv2.cvtColor(foto, cv2.COLOR_BGR2GRAY)
        achou, cantos = cv2.findChessboardCornersSB(cinza, padrao)
        if not achou: continue
        objetos.append(objeto)
        imagens.append(cantos)
        tamanho = cinza.shape[::-1]
    if len(objetos) < 12 or tamanho is None:
        raise ValueError(f"foram detectadas {len(objetos)} fotos úteis; use ao menos 12, em poses variadas")
    erro, k, dist, _, _ = cv2.calibrateCamera(objetos, imagens, tamanho, None, None)
    if erro > 1.0:
        raise ValueError(f"erro de reprojeção alto ({erro:.2f}px); refaça as fotos de calibração")
    perfil = carregar_perfil(CAMINHO_PADRAO_PERFIL)
    perfil.update({"fx_px": float(k[0,0]), "fy_px": float(k[1,1]), "cx_px": float(k[0,2]), "cy_px": float(k[1,2]), "distorcao": [float(v) for v in dist.ravel()[:5]], "erro_reprojecao_px": round(float(erro), 3), "calibration_resolution": [int(tamanho[0]), int(tamanho[1])], "camera_model": "POCO X7 Pro", "calibrado": True})
    salvar_perfil(perfil, CAMINHO_PADRAO_PERFIL)
    return perfil

if __name__ == '__main__':
    a=argparse.ArgumentParser(); a.add_argument('--pasta',type=Path,required=True); a.add_argument('--colunas',type=int,required=True); a.add_argument('--linhas',type=int,required=True); a.add_argument('--quadrado-mm',type=float,required=True)
    print(calibrar(**vars(a.parse_args())))
