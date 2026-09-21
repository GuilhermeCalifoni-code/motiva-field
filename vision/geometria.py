"""Medição monocular determinística sobre plano local.

Convenção: mundo em metros, X à direita, Y à frente e Z para cima. A câmera está
em (0, 0, altura_camera_m). Pitch positivo aponta a lente para baixo.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import math
from typing import Any

import cv2
import numpy as np

CAMINHO_PADRAO_PERFIL = Path(__file__).resolve().parent / "perfil_camera.json"

PERFIL_PADRAO: dict[str, Any] = {
    "versao": "monocular_plano_local_v1",
    "altura_camera_m": 1.82,
    "pitch_graus": 45.0,
    "roll_graus": 0.0,
    "yaw_graus": 0.0,
    # Estes valores são aproximação inicial para uma imagem 1920x1080. Devem
    # ser substituídos por calibração de tabuleiro antes de uso operacional.
    "fx_px": 1500.0, "fy_px": 1500.0, "cx_px": 960.0, "cy_px": 540.0,
    "distorcao": [0.0, 0.0, 0.0, 0.0, 0.0],
    "incerteza_altura_m": 0.05,
    "incerteza_pitch_graus": 2.0,
    "incerteza_pixel_px": 3.0,
    "calibrado": False,
}


class GeometriaInsuficiente(ValueError):
    pass


def carregar_perfil(caminho: str | Path = CAMINHO_PADRAO_PERFIL) -> dict[str, Any]:
    destino = Path(caminho)
    if not destino.exists():
        salvar_perfil(PERFIL_PADRAO, destino)
    dados = json.loads(destino.read_text(encoding="utf-8"))
    obrigatorios = ("altura_camera_m", "pitch_graus", "fx_px", "fy_px", "cx_px", "cy_px")
    if any(not isinstance(dados.get(k), (int, float)) for k in obrigatorios):
        raise GeometriaInsuficiente("perfil de câmera incompleto")
    if dados["altura_camera_m"] <= 0 or dados["fx_px"] <= 0 or dados["fy_px"] <= 0:
        raise GeometriaInsuficiente("altura, fx e fy devem ser positivos")
    return dados


def salvar_perfil(dados: dict[str, Any], caminho: str | Path = CAMINHO_PADRAO_PERFIL) -> Path:
    destino = Path(caminho)
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def _rotacao(perfil: dict[str, Any]) -> np.ndarray:
    p, r, y = (math.radians(float(perfil[k])) for k in ("pitch_graus", "roll_graus", "yaw_graus"))
    # câmera: x direita, y baixo, z frente -> mundo sem yaw/roll
    base = np.array([[1, 0, 0], [0, -math.sin(p), math.cos(p)], [0, -math.cos(p), -math.sin(p)]], dtype=float)
    rz = np.array([[math.cos(y), -math.sin(y), 0], [math.sin(y), math.cos(y), 0], [0, 0, 1]], dtype=float)
    # roll em torno do eixo óptico, antes da transformação ao mundo
    roll = np.array([[math.cos(r), -math.sin(r), 0], [math.sin(r), math.cos(r), 0], [0, 0, 1]], dtype=float)
    return rz @ base @ roll


def _raio(pixel: tuple[float, float], perfil: dict[str, Any]) -> np.ndarray:
    k = np.array([[perfil["fx_px"], 0, perfil["cx_px"]], [0, perfil["fy_px"], perfil["cy_px"]], [0, 0, 1]], dtype=float)
    dist = np.array(perfil.get("distorcao", [0, 0, 0, 0, 0]), dtype=float)
    und = cv2.undistortPoints(np.array([[pixel]], dtype=np.float64), k, dist)[0, 0]
    raio_camera = np.array([und[0], und[1], 1.0], dtype=float)
    raio_mundo = _rotacao(perfil) @ (raio_camera / np.linalg.norm(raio_camera))
    return raio_mundo / np.linalg.norm(raio_mundo)


@dataclass
class ResultadoGeometrico:
    valido: bool
    altura_cm: float | None
    incerteza_cm: float | None
    confianca: float
    motivo: str | None
    base_px: list[float]
    topo_px: list[float]
    base_mundo_m: list[float] | None
    metodo: str = "geometria_monocular_plano_local"

    def json(self) -> dict[str, Any]:
        return asdict(self)


def medir_altura(top: tuple[float, float], base: tuple[float, float], perfil: dict[str, Any]) -> ResultadoGeometrico:
    """Calcula H pelo plano z=0 e pela vertical que passa na base.

    O raio da base deve cruzar o plano local. O raio do topo é projetado nessa
    vertical; discrepância lateral alta denuncia que topo/base não pertencem ao
    mesmo objeto ou que a hipótese de plano local não se sustenta.
    """
    hcam = float(perfil["altura_camera_m"])
    rb, rt = _raio(base, perfil), _raio(top, perfil)
    if rb[2] >= -0.015:
        raise GeometriaInsuficiente("a base não aponta para o solo; distância indeterminada")
    lam_base = hcam / -rb[2]
    pbase = np.array([lam_base * rb[0], lam_base * rb[1], 0.0])
    horizontal = rt[:2]
    den = float(horizontal @ horizontal)
    if den < 1e-9:
        raise GeometriaInsuficiente("raio do topo degenerado")
    lam_top = float((pbase[:2] @ horizontal) / den)
    if lam_top <= 0:
        raise GeometriaInsuficiente("topo está atrás da câmera")
    ptop = lam_top * rt + np.array([0.0, 0.0, hcam])
    residual = float(np.linalg.norm(ptop[:2] - pbase[:2]))
    distancia = float(np.linalg.norm(pbase[:2]))
    # Aceita até 15% da distância (ou 20 cm); além disso a vertical não fecha.
    if residual > max(0.20, distancia * 0.15):
        raise GeometriaInsuficiente("topo e base não fecham na mesma vertical local")
    altura = float(ptop[2])
    if not 0.01 <= altura <= 3.0:
        raise GeometriaInsuficiente("altura geométrica fora da faixa plausível")

    # Propagação conservadora por perturbações dos parâmetros mais sensíveis.
    valores: list[float] = []
    for dh, dp, dv in ((float(perfil.get("incerteza_altura_m", .05)), 0, 0), (0, float(perfil.get("incerteza_pitch_graus", 2)), 0), (0, 0, float(perfil.get("incerteza_pixel_px", 3)))):
        if not (dh or dp or dv): continue
        alterado = dict(perfil); alterado["altura_camera_m"] = hcam + dh; alterado["pitch_graus"] = float(perfil["pitch_graus"]) + dp
        try:
            # chamada interna sem propagar incerteza para evitar recursão
            alterado.update({"incerteza_altura_m": 0, "incerteza_pitch_graus": 0, "incerteza_pixel_px": 0})
            valores.append(medir_altura((top[0], top[1]-dv), (base[0], base[1]+dv), alterado).altura_cm / 100)
        except (GeometriaInsuficiente, TypeError):
            pass
    sigma = max(0.02, float(np.std([altura, *valores])) if valores else 0.10)
    confianca = float(np.clip((1 - residual / max(.20, distancia*.15)) * (1 - min(.75, sigma / altura)), 0, 1))
    return ResultadoGeometrico(True, round(altura * 100, 1), round(sigma * 100, 1), round(confianca, 2), None, list(base), list(top), [round(float(x), 3) for x in pbase])


def monte_carlo_horizontal(top: tuple[float,float], base: tuple[float,float], perfil: dict[str,Any], amostras: int=160, seed: int=7) -> dict[str,Any]:
    """Propaga incertezas; só é aplicável quando plano horizontal foi validado externamente."""
    rng=np.random.default_rng(seed); valores=[]
    for _ in range(amostras):
        p=dict(perfil); p["altura_camera_m"]=float(perfil["altura_camera_m"])+rng.normal(0,float(perfil.get("incerteza_altura_m",.05)))
        p["pitch_graus"]=float(perfil["pitch_graus"])+rng.normal(0,float(perfil.get("incerteza_pitch_graus",7)))
        p["roll_graus"]=float(perfil.get("roll_graus",0))+rng.normal(0,float(perfil.get("incerteza_roll_graus",3)))
        e=float(perfil.get("incerteza_pixel_px",3)); t=(top[0]+rng.normal(0,e),top[1]+rng.normal(0,e)); b=(base[0]+rng.normal(0,e),base[1]+rng.normal(0,e))
        p.update({"incerteza_altura_m":0,"incerteza_pitch_graus":0,"incerteza_pixel_px":0})
        try: valores.append(medir_altura(t,b,p).altura_cm)
        except GeometriaInsuficiente: pass
    if len(valores)<amostras*.8: return {"estavel":False,"score":0.0,"amostras_validas":len(valores),"intervalo_cm":None}
    a=np.array(valores); intervalo=[round(float(np.percentile(a,5)),1),round(float(np.percentile(a,95)),1)]; dispersao=float(np.std(a))
    return {"estavel":dispersao<=max(5,float(np.median(a))*.20),"score":round(float(np.clip(1-dispersao/max(5,float(np.median(a))*.20),0,1)),2),"amostras_validas":len(valores),"mediana_cm":round(float(np.median(a)),1),"intervalo_cm":intervalo,"desvio_cm":round(dispersao,1)}
