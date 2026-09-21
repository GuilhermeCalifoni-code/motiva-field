"""Guardas auditáveis para estimativa monocular; não fabrica evidência métrica."""
from __future__ import annotations
from typing import Any
import cv2
import numpy as np

PESOS = {"imagem": .12, "camera": .18, "orientacao": .14, "terreno": .22, "atencao": .14, "segmentacao": .08, "monte_carlo": .12}

def qualidade_imagem(imagem: np.ndarray) -> dict[str, Any]:
    h, w = imagem.shape[:2]
    cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    brilho, blur = float(cinza.mean()), float(cv2.Laplacian(cinza, cv2.CV_64F).var())
    sat = float(np.mean((cinza <= 3) | (cinza >= 252)))
    problemas=[]
    if min(h,w) < 720: problemas.append("invalid_resolution")
    if blur < 45: problemas.append("excessive_blur")
    if brilho < 25 or brilho > 235: problemas.append("exposure_inadequate")
    if sat > .12: problemas.append("saturation_excessive")
    score=float(np.clip(min(1, blur/180) * (1-sat) * (1 if not problemas else .65),0,1))
    return {"score":round(score,2),"resolucao":[w,h],"blur_laplaciano":round(blur,1),"brilho":round(brilho,1),"saturacao":round(sat,3),"problemas":problemas}

def validar(perfil: dict[str,Any], qualidade: dict[str,Any], regiao: dict[str,Any]|None, plano: dict[str,Any]|None=None, orientacao: dict[str,Any]|None=None, mc: dict[str,Any]|None=None, auditoria: dict[str,Any]|None=None) -> dict[str,Any]:
    motivos=[]
    resolucao=qualidade["resolucao"]
    if not perfil.get("calibrado"): motivos.append("camera_not_calibrated")
    if perfil.get("calibration_resolution") and perfil["calibration_resolution"] != resolucao: motivos.append("invalid_resolution")
    if qualidade["problemas"]: motivos.extend(qualidade["problemas"])
    if not regiao: motivos.append("base_not_detected")
    if not auditoria or not auditoria.get("aprovada"): motivos.extend((auditoria or {}).get("motivos", ["attention_audit_required"]))
    if not orientacao or not orientacao.get("confiavel"): motivos.append("orientation_uncertain")
    if not plano or not plano.get("confiavel"): motivos.append("insufficient_ground_evidence")
    if mc and not mc.get("estavel"): motivos.append("height_solution_unstable")
    fatores={"imagem":qualidade["score"],"camera":1.0 if perfil.get("calibrado") else 0.0,"orientacao":(orientacao or {}).get("score",0.0),"terreno":(plano or {}).get("score",0.0),"atencao":1.0 if (auditoria or {}).get("aprovada") else 0.0,"segmentacao":1.0 if regiao else 0.0,"monte_carlo":(mc or {}).get("score",0.0)}
    score=sum(PESOS[k]*fatores[k] for k in PESOS)
    return {"valido":not motivos and score>=.60,"confianca":round(score,2),"motivos":list(dict.fromkeys(motivos)),"fatores_confianca":fatores}
