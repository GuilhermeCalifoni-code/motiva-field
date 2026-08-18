"""Prova, com numero, que da para medir sem regua no quadro.

Recebe duas fotos do mesmo alvo, tiradas na mesma pose: uma com a trena
aparecendo, outra sem. Mede a primeira pelo metodo da haste no quadro e a
segunda pela calibracao salva, e compara.

Se as duas concordam, a calibracao persistida esta valendo naquela geometria.
Se divergem, alguma coisa mudou — camera fora do lugar, distancia diferente,
ou a calibracao envelheceu. Esse e exatamente o alerta que o pipeline sozinho
nao consegue dar.

Uso:
    python -m vision.conferir --com-trena a.jpg --sem-trena b.jpg \\
        --calibracao calibracao.json --referencia-cm 50

Sai com 0 se a divergencia for menor que o limite, 1 se for maior ou se
alguma das medicoes falhar. Nao abre janela.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:  # como pacote: python -m vision.conferir
    from .calibracao import (
        CAMINHO_PADRAO_CALIBRACAO,
        CalibracaoInvalida,
        carregar_calibracao,
    )
    from .pipeline import FotoInvalida, processar_foto
except ImportError:  # direto de dentro de vision/
    from calibracao import (
        CAMINHO_PADRAO_CALIBRACAO,
        CalibracaoInvalida,
        carregar_calibracao,
    )
    from pipeline import FotoInvalida, processar_foto

# Acima disso as duas vias nao estao medindo a mesma coisa.
DIVERGENCIA_MAXIMA_PCT = 10.0


def _medir(caminho: Path, **fonte_de_escala: object) -> float:
    """Roda o pipeline numa foto e devolve a altura em cm."""
    conteudo = caminho.read_bytes()
    resultado = processar_foto(conteudo, caminho.name, **fonte_de_escala)
    deteccoes = resultado.get("deteccoes") or []
    if not deteccoes:
        raise FotoInvalida(f"{caminho.name}: nenhuma vegetacao detectada")
    return float(deteccoes[0]["metrica"])


def executar(
    com_trena: Path,
    sem_trena: Path,
    caminho_calibracao: Path,
    referencia_cm: float,
    limite_pct: float = DIVERGENCIA_MAXIMA_PCT,
) -> int:
    print("Conferencia: haste no quadro x calibracao salva")
    print("=" * 68)

    for rotulo, caminho in (("--com-trena", com_trena), ("--sem-trena", sem_trena)):
        if not caminho.is_file():
            print(f"FALHOU: {rotulo} nao encontrado: {caminho}")
            return 1

    try:
        calibracao = carregar_calibracao(caminho_calibracao)
    except CalibracaoInvalida as erro:
        print(f"FALHOU: {erro}")
        return 1

    geometria = calibracao.get("geometria") or {}
    print(f"calibracao ......... {caminho_calibracao}")
    print(f"  pixels_por_cm .... {calibracao['pixels_por_cm']}")
    if geometria:
        print(
            f"  geometria ........ camera {geometria.get('altura_camera_cm')} cm, "
            f"alvo a {geometria.get('distancia_alvo_cm')} cm"
        )
    print()

    try:
        altura_haste = _medir(com_trena, referencia_cm=referencia_cm)
    except FotoInvalida as erro:
        print(f"FALHOU ao medir {com_trena.name} pela haste no quadro: {erro}")
        return 1

    try:
        altura_arquivo = _medir(sem_trena, calibracao=calibracao)
    except FotoInvalida as erro:
        print(f"FALHOU ao medir {sem_trena.name} pela calibracao salva: {erro}")
        return 1

    print(f"{'metodo':<28} {'foto':<24} altura")
    print("-" * 68)
    print(f"{'haste no quadro':<28} {com_trena.name:<24} {altura_haste:.1f} cm")
    print(f"{'calibracao salva':<28} {sem_trena.name:<24} {altura_arquivo:.1f} cm")
    print("-" * 68)

    if altura_haste <= 0:
        print("FALHOU: a medida de referencia veio zerada")
        return 1

    divergencia = abs(altura_arquivo - altura_haste) / altura_haste * 100.0
    print(f"divergencia ........ {divergencia:.2f}%  (limite {limite_pct:.0f}%)")
    print()

    if divergencia < limite_pct:
        print("OK — as duas vias concordam. Da para medir sem regua nesta geometria.")
        return 0

    print("DIVERGENCIA ACIMA DO LIMITE.")
    print("A calibracao salva nao esta valendo para esta foto. Causas comuns:")
    print("  - a camera mudou de altura, angulo ou distancia desde a calibracao")
    print("  - as duas fotos nao foram tiradas da mesma pose")
    print("  - a calibracao envelheceu; refaca com python -m vision.calibracao")
    return 1


def _principal(argumentos: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(
        prog="python -m vision.conferir",
        description=(
            "Compara a medida obtida pela haste no quadro com a obtida pela "
            "calibracao salva, nas mesmas condicoes."
        ),
    )
    analisador.add_argument("--com-trena", required=True, help="foto com a referencia no quadro")
    analisador.add_argument("--sem-trena", required=True, help="foto do mesmo alvo, sem referencia")
    analisador.add_argument(
        "--calibracao",
        default=str(CAMINHO_PADRAO_CALIBRACAO),
        help=f"arquivo de calibracao (padrao: {CAMINHO_PADRAO_CALIBRACAO.name})",
    )
    analisador.add_argument(
        "--referencia-cm", required=True, type=float, help="comprimento real da referencia, em cm"
    )
    analisador.add_argument(
        "--limite-pct",
        type=float,
        default=DIVERGENCIA_MAXIMA_PCT,
        help=f"divergencia maxima aceita (padrao: {DIVERGENCIA_MAXIMA_PCT:.0f}%%)",
    )
    opcoes = analisador.parse_args(argumentos)

    return executar(
        Path(opcoes.com_trena),
        Path(opcoes.sem_trena),
        Path(opcoes.calibracao),
        opcoes.referencia_cm,
        opcoes.limite_pct,
    )


if __name__ == "__main__":
    sys.exit(_principal())
