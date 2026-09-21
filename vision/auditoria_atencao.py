"""Ponte segura entre a auditoria visual e a geometria determinística.

A auditoria pode vir do Gemini ou de uma seleção humana. Ela nunca mede
centímetros: só autoriza uma ROI explícita a seguir para validação de câmera,
plano e Monte Carlo.
"""
from __future__ import annotations
from typing import Any


def _ponto(valor: object) -> bool:
    return isinstance(valor, list) and len(valor) == 2 and all(isinstance(v, (int, float)) and 0 <= v <= 1000 for v in valor)


def validar_auditoria(auditoria: dict[str, Any] | None, largura: int, altura: int) -> dict[str, Any]:
    if not isinstance(auditoria, dict):
        return {"aprovada": False, "roi_px": None, "motivos": ["attention_audit_required"]}

    alvo = auditoria.get("alvo") if isinstance(auditoria.get("alvo"), dict) else {}
    base_topo = auditoria.get("base_topo") if isinstance(auditoria.get("base_topo"), dict) else {}
    roi = alvo.get("roi_normalizada_0a1000")
    motivos: list[str] = []
    if not auditoria.get("geometria_candidata", False):
        motivos.append("visual_geometry_not_candidate")
    if auditoria.get("decisao") == "bloquear":
        motivos.append("visual_audit_blocked")
    if not (isinstance(roi, list) and len(roi) == 4 and all(isinstance(v, (int, float)) and 0 <= v <= 1000 for v in roi)):
        motivos.append("roi_not_supplied")
    elif roi[2] <= roi[0] or roi[3] <= roi[1]:
        motivos.append("roi_invalid")
    if float(alvo.get("confianca", 0) or 0) < .65:
        motivos.append("target_confidence_low")
    if not base_topo.get("compativeis", False):
        motivos.append("base_top_not_compatible")
    if not base_topo.get("base_visivel", False):
        motivos.append("base_not_visually_confirmed")
    if not base_topo.get("topo_visivel", False):
        motivos.append("top_not_visually_confirmed")

    if motivos:
        return {"aprovada": False, "roi_px": None, "motivos": motivos}
    x1, y1, x2, y2 = (int(round(float(v) / 1000 * (largura if i % 2 == 0 else altura))) for i, v in enumerate(roi))
    return {"aprovada": True, "roi_px": (max(0, x1), max(0, y1), min(largura, x2), min(altura, y2)), "motivos": []}
