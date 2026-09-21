"""Validação cega do pipeline contra ground truth externo.

O arquivo de ground truth só é aberto depois de cada inferência. Assim os
valores reais nunca entram em segmentação, auditoria, geometria ou escala.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

try:
    from .pipeline import processar_foto
except ImportError:
    from pipeline import processar_foto


def validar(pasta: Path, saida: Path) -> dict[str, object]:
    contrato = json.loads((pasta / "ground_truth.json").read_text(encoding="utf-8"))
    inferencias: dict[str, dict[str, object]] = {}

    # Fase cega: nenhuma altura real foi carregada para a função de inferência.
    for item in contrato["fotos"]:
        arquivo = pasta / item["arquivo"]
        resultado = processar_foto(arquivo.read_bytes(), arquivo.name)
        inferencias[arquivo.name] = resultado

    linhas: list[dict[str, object]] = []
    erros: list[float] = []
    coberturas: list[bool] = []
    for item in contrato["fotos"]:
        medicao = inferencias[item["arquivo"]]["medicao_altura"]
        estimada = medicao["altura_cm"] if medicao["valido"] else None
        real = item.get("altura_real_cm")
        faixa = item.get("intervalo_real_cm")
        erro = abs(float(estimada) - float(real)) if estimada is not None and real is not None else None
        if erro is not None:
            erros.append(erro)
        dentro_faixa = bool(faixa[0] <= estimada <= faixa[1]) if estimada is not None and faixa else None
        if dentro_faixa is not None:
            coberturas.append(dentro_faixa)
        linhas.append({
            "arquivo": item["arquivo"], "cenario": item["cenario"],
            "altura_real_cm": real, "intervalo_real_cm": faixa,
            "altura_estimada_cm": estimada, "erro_cm": erro,
            "dentro_intervalo_real": dentro_faixa,
            "valido": medicao["valido"], "confianca": medicao["confianca"],
            "motivo": medicao["motivo"],
        })

    resumo = {
        "total": len(linhas),
        "medicoes_liberadas": sum(bool(x["valido"]) for x in linhas),
        "mae_cm": round(mean(erros), 2) if erros else None,
        "cobertura_intervalos_reais": round(sum(coberturas) / len(coberturas), 3) if coberturas else None,
        "ground_truth_usado_na_inferencia": False,
    }
    relatorio = {"resumo": resumo, "resultados": linhas}
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    return relatorio


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pasta", type=Path, default=Path(__file__).resolve().parent / "fotos" / "validacao-poco-x7-pro")
    parser.add_argument("--saida", type=Path, default=Path(__file__).resolve().parent / "fotos" / "validacao-poco-x7-pro" / "resultado-validacao.json")
    args = parser.parse_args()
    print(json.dumps(validar(args.pasta, args.saida)["resumo"], ensure_ascii=False))
