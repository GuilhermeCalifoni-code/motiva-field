"""Servidor local para testar a visão com upload ou webcam no Chrome."""
from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

from pipeline import FotoInvalida, processar_foto

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


@app.post("/api/processar")
def processar():
    arquivo = request.files.get("imagem")
    if arquivo is None or not arquivo.filename:
        return jsonify({"erro": "Selecione ou capture uma imagem antes de processar."}), 400
    try:
        altura = float(request.form.get("altura_haste_cm", "100"))
        resultado = processar_foto(arquivo.read(), secure_filename(arquivo.filename), altura, SAIDAS)
        evidencias_geradas = resultado.get("evidencias", {})
        resultado["urls"] = {chave: f"/saidas/{valor}" for chave, valor in evidencias_geradas.items()}
        return jsonify(resultado)
    except (FotoInvalida, ValueError) as erro:
        return jsonify({"erro": str(erro)}), 422


if __name__ == "__main__":
    SAIDAS.mkdir(exist_ok=True)
    app.run(host="127.0.0.1", port=8766, debug=False)
