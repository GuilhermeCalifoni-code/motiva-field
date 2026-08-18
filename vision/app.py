"""Servidor local para testar a visão com upload ou webcam no Chrome."""
from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

try:  # como pacote: python -m vision.app
    from .calibracao import (
        CAMINHO_PADRAO_CALIBRACAO,
        CalibracaoInvalida,
        ReferenciaNaoEncontrada,
        calibrar_de_foto,
        carregar_calibracao,
        idade_em_dias,
        salvar_calibracao,
    )
    from .pipeline import FotoInvalida, processar_foto
except ImportError:  # direto de dentro de vision/: python app.py
    from calibracao import (
        CAMINHO_PADRAO_CALIBRACAO,
        CalibracaoInvalida,
        ReferenciaNaoEncontrada,
        calibrar_de_foto,
        carregar_calibracao,
        idade_em_dias,
        salvar_calibracao,
    )
    from pipeline import FotoInvalida, processar_foto

def _cm_opcional(bruto: str | None) -> float | None:
    """Le um comprimento do formulario. Vazio vira None, e nao um padrao.

    Com a leitura da graduacao, digitar o comprimento virou opcional. Um padrao
    silencioso aqui (50, 100) traria de volta exatamente o erro que a graduacao
    existe para eliminar: um numero plausivel que ninguem conferiu.
    """
    if bruto is None:
        return None
    texto = bruto.strip().replace(",", ".")
    if not texto:
        return None
    valor = float(texto)
    return valor if valor > 0 else None


BASE = Path(__file__).resolve().parent
SAIDAS = BASE / "saidas"
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024


@app.get("/")
def inicio():
    return render_template("index.html")


@app.get("/saidas/<path:nome>")
def evidencias(nome: str):
    return send_from_directory(SAIDAS, nome)


@app.get("/api/calibracao")
def calibracao_atual():
    """Estado da calibração salva, para a interface saber o que oferecer."""
    try:
        dados = carregar_calibracao(CAMINHO_PADRAO_CALIBRACAO)
    except CalibracaoInvalida as erro:
        return jsonify({"existe": False, "motivo": str(erro)})

    idade = idade_em_dias(dados)
    return jsonify({
        "existe": True,
        "pixels_por_cm": dados["pixels_por_cm"],
        "geometria": dados.get("geometria", {}),
        "origem": dados.get("origem", {}),
        "idade_dias": None if idade is None else round(idade, 1),
    })


@app.post("/api/calibrar")
def calibrar():
    """Gera e salva a calibração a partir de uma foto com a referência."""
    arquivo = request.files.get("imagem")
    if arquivo is None or not arquivo.filename:
        return jsonify({"erro": "Envie a foto com a trena no quadro."}), 400

    SAIDAS.mkdir(exist_ok=True)
    temporaria = SAIDAS / f"calibracao-origem-{secure_filename(arquivo.filename)}"
    try:
        arquivo.save(temporaria)
        dados = calibrar_de_foto(
            temporaria,
            _cm_opcional(request.form.get("referencia_cm")),
            float(request.form.get("altura_camera_cm", "140")),
            float(request.form.get("distancia_alvo_cm", "200")),
        )
    except (CalibracaoInvalida, ReferenciaNaoEncontrada, ValueError) as erro:
        return jsonify({"erro": str(erro)}), 422
    finally:
        temporaria.unlink(missing_ok=True)

    salvar_calibracao(dados, CAMINHO_PADRAO_CALIBRACAO)
    return jsonify(dados)


@app.post("/api/processar")
def processar():
    arquivo = request.files.get("imagem")
    if arquivo is None or not arquivo.filename:
        return jsonify({"erro": "Selecione ou capture uma imagem antes de processar."}), 400

    # "arquivo" mede sem régua no quadro; "haste" detecta a régua na foto.
    via = request.form.get("via", "haste")

    try:
        if via == "arquivo":
            calibracao = carregar_calibracao(CAMINHO_PADRAO_CALIBRACAO)
            resultado = processar_foto(
                arquivo.read(), secure_filename(arquivo.filename), None, SAIDAS,
                calibracao=calibracao,
            )
        else:
            resultado = processar_foto(
                arquivo.read(),
                secure_filename(arquivo.filename),
                _cm_opcional(request.form.get("altura_haste_cm")),
                SAIDAS,
            )
        evidencias_geradas = resultado.get("evidencias", {})
        resultado["urls"] = {chave: f"/saidas/{valor}" for chave, valor in evidencias_geradas.items()}
        return jsonify(resultado)
    except (FotoInvalida, CalibracaoInvalida, ValueError) as erro:
        return jsonify({"erro": str(erro)}), 422


if __name__ == "__main__":
    SAIDAS.mkdir(exist_ok=True)
    app.run(host="127.0.0.1", port=8766, debug=False)
