from pathlib import Path

import cv2
from fastapi.testclient import TestClient

import app.main as main
from app.main import (
    AuditoriaGeometrica,
    _aplicar_guardas_consistencia_auditoria,
    _avaliar_consenso_numerico,
    _calcular_medicao_assistida,
    _criar_estimativa_assistida,
    _medir_por_pontos_auditados,
    _normalizar_coordenadas_auditoria,
)
from vision.calibracao import medir_escala_regua_transparente


def auditoria_valida() -> dict:
    checklist = {k: True for k in (
        "alvo_definido", "roi_valida", "base_valida", "topo_valido",
        "base_topo_compativeis", "referencia_valida", "referencia_localizada",
        "relacao_espacial_avaliada", "solo_identificado", "geometria_suficiente",
        "pode_calcular",
    )}
    conf = {k: .9 for k in (
        "alvo", "roi", "base", "topo", "base_topo", "referencia",
        "relacao_espacial", "solo", "geometria", "global",
    )}
    amostras = [
        {"base_px_normalizado_0a1000": [100 + i * 90, 800], "topo_px_normalizado_0a1000": [100 + i * 90, 600 + (i % 3) * 5], "confianca": .9}
        for i in range(9)
    ]
    return {
        "arquivo": "teste.png", "origem": "gemini", "modelo": "teste",
        "decisao": "medir_com_regua", "geometria_candidata": True,
        "alvo": {"classe": "faixa de grama", "roi_normalizada_0a1000": [50, 500, 950, 850], "confianca": .9, "motivo": "faixa local"},
        "base_topo": {"compativeis": True, "base_visivel": True, "topo_visivel": True, "base_px_normalizado_0a1000": [500, 800], "topo_px_normalizado_0a1000": [500, 600], "motivo": "mesma faixa"},
        "amostras": amostras,
        "referencias": [{"tipo": "regua", "bbox_normalizada_0a1000": [900, 300, 950, 800], "ponto_superior_normalizado_0a1000": [925, 400], "ponto_inferior_normalizado_0a1000": [925, 800], "intervalo_observado_cm": 20, "incerteza_cm": .2, "confianca": .95, "compatibilidade_espacial": .95, "utilizavel": True, "incerteza_descricao": "marcas nítidas"}],
        "plano_local": "solo plano", "inclinacao_desconhecida": False,
        "dados": {"observacoes": ["régua visível"], "inferencias": [], "desconhecidos": []},
        "auditoria": checklist, "confianca_componentes": conf,
        "objetos_ignorados": ["folha isolada"], "limitacoes": ["leve paralaxe"], "proxima_captura": "manter padrão",
    }


def test_amostragem_p85_produz_medida():
    dados = _aplicar_guardas_consistencia_auditoria(auditoria_valida())
    audit = AuditoriaGeometrica.model_validate(dados)
    resultado = _medir_por_pontos_auditados(audit, 1000, 1000)
    assert resultado is not None
    assert resultado["altura_cm"] > 0
    assert resultado["intervalo_cm"][0] < resultado["altura_cm"] < resultado["intervalo_cm"][1]


def test_menos_de_oito_amostras_bloqueia_faixa_continua():
    dados = auditoria_valida()
    dados["amostras"] = dados["amostras"][:4]
    resultado = _aplicar_guardas_consistencia_auditoria(dados)
    assert resultado["decisao"] == "triagem_sem_medida"
    assert resultado["geometria_candidata"] is False


def test_oclusao_da_base_bloqueia():
    dados = auditoria_valida()
    dados["limitacoes"] = ["base da vegetação oculta pela palhada"]
    resultado = _aplicar_guardas_consistencia_auditoria(dados)
    assert resultado["decisao"] == "triagem_sem_medida"
    assert resultado["base_topo"]["base_visivel"] is False


def test_oclusao_da_base_da_regua_nao_equivale_a_base_da_planta():
    dados = auditoria_valida()
    dados["limitacoes"] = ["leve oclusão da base da régua por uma haste"]
    resultado = _aplicar_guardas_consistencia_auditoria(dados)
    assert resultado["decisao"] == "medir_com_regua"
    assert resultado["geometria_candidata"] is True


def test_normaliza_troca_global_yx_quando_regua_vertical_veio_horizontal():
    dados = auditoria_valida()
    dados["dados"]["observacoes"] = ["régua posicionada verticalmente"]
    dados["referencias"][0]["bbox_normalizada_0a1000"] = [0, 550, 700, 650]
    dados["referencias"][0]["ponto_superior_normalizado_0a1000"] = [100, 570]
    dados["referencias"][0]["ponto_inferior_normalizado_0a1000"] = [350, 570]
    dados["base_topo"]["base_px_normalizado_0a1000"] = [800, 500]
    dados["base_topo"]["topo_px_normalizado_0a1000"] = [200, 500]
    resultado = _normalizar_coordenadas_auditoria(dados)
    assert resultado["referencias"][0]["bbox_normalizada_0a1000"] == [550, 0, 650, 700]
    assert resultado["referencias"][0]["ponto_superior_normalizado_0a1000"] == [570, 100]
    assert resultado["base_topo"]["base_px_normalizado_0a1000"] == [500, 800]


def test_schema_gemini_nao_usa_exclusive_minimum():
    schema = AuditoriaGeometrica.model_json_schema()
    referencia = schema["$defs"]["ReferenciaGeometrica"]["properties"]
    intervalo = referencia["intervalo_observado_cm"]
    texto = str(intervalo)
    assert "exclusiveMinimum" not in texto
    assert "minimum" in texto


def test_medicao_assistida_calcula_razao_de_segmentos():
    resultado = _calcular_medicao_assistida(
        (100, 100), (100, 500),
        (300, 500), (300, 60),
        20.0, 1200, 1600,
    )
    assert resultado["altura_cm"] == 22.0
    assert resultado["escala_px_por_cm"] == 20.0
    assert resultado["angulo_entre_segmentos_graus"] == 0.0
    assert resultado["intervalo_cm"][0] < 22 < resultado["intervalo_cm"][1]


def test_medicao_assistida_rejeita_segmentos_desalinhados():
    try:
        _calcular_medicao_assistida(
            (100, 100), (100, 500),
            (300, 500), (700, 500),
            20.0, 1200, 1600,
        )
    except ValueError as erro:
        assert "20°" in str(erro)
    else:
        raise AssertionError("Segmentos perpendiculares deveriam ser rejeitados")


def test_endpoint_medicao_assistida_retorna_medida_rastreavel():
    raiz = Path(__file__).resolve().parents[2]
    imagem = raiz / "api" / "tests" / "fixtures" / "regua-via-unica.jpg"
    dados = {
        "comprimento_referencia_cm": "20",
        "referencia_inicio_x": "100",
        "referencia_inicio_y": "100",
        "referencia_fim_x": "100",
        "referencia_fim_y": "500",
        "base_x": "300",
        "base_y": "500",
        "topo_x": "300",
        "topo_y": "60",
        "coplanar_confirmado": "true",
    }
    with TestClient(main.app) as cliente:
        resposta = cliente.post(
            "/api/medicoes-assistidas",
            data=dados,
            files={"imagem": (imagem.name, imagem.read_bytes(), "image/jpeg")},
        )
    corpo = resposta.json()
    assert resposta.status_code == 200
    assert corpo["altura_cm"] == 22.0
    assert corpo["valido"] is True
    assert corpo["nivel_validacao"] == "assistido_operador"
    assert corpo["apto_historico"] is False
    assert corpo["proveniencia"]["annotation_origin"] == "human_confirmed"


def test_estimativa_assistida_usa_via_unica_sem_validar_cm():
    estimativa = _criar_estimativa_assistida(None, 14.3, .75)
    assert estimativa is not None
    assert estimativa["altura_cm"] == 14.3
    assert estimativa["uso"] == "orientativo_nao_metrico"
    assert estimativa["confianca"] <= .55


def test_estimativa_assistida_nao_escolhe_entre_vias_em_conflito():
    gemini = {"altura_cm": 21.0, "intervalo_cm": [18.0, 24.0], "confianca": .9}
    assert _criar_estimativa_assistida(gemini, 14.5, .8) is None


def test_consenso_rejeita_falsos_positivos_observados():
    base = {"altura_cm": 9.0, "escala": {"pixels_por_cm": 48.0}}
    resultado = _avaliar_consenso_numerico(base, 48.5, 1.8)
    assert resultado["escalas_concordam"] is True
    assert resultado["alturas_concordam"] is False

    base = {"altura_cm": 21.0, "escala": {"pixels_por_cm": 40.0}}
    resultado = _avaliar_consenso_numerico(base, 38.3, 14.5)
    assert resultado["escalas_concordam"] is True
    assert resultado["alturas_concordam"] is False


def test_consenso_aceita_foto_transparente_validada():
    base = {"altura_cm": 13.8, "escala": {"pixels_por_cm": 33.84}}
    resultado = _avaliar_consenso_numerico(base, 36.5062, 12.1)
    assert resultado["escalas_concordam"] is True
    assert resultado["alturas_concordam"] is True


def test_endpoint_usa_opencv_orientativo_quando_gemini_falha(monkeypatch):
    def falhar_auditoria(*_args, **_kwargs):
        raise RuntimeError("Gemini indisponível")

    monkeypatch.setattr(main, "_auditar_geometria_gemini", falhar_auditoria)
    raiz = Path(__file__).resolve().parents[2]
    imagem = raiz / "api" / "tests" / "fixtures" / "regua-via-unica.jpg"
    with TestClient(main.app) as cliente:
        resposta = cliente.post(
            "/api/medicoes-altura",
            files={"imagem": (imagem.name, imagem.read_bytes(), "image/png")},
        )
    dados = resposta.json()
    assert resposta.status_code == 200
    assert dados["altura_cm"] is None
    assert dados["valido"] is False
    assert dados["estimativa_assistida"] is not None
    assert dados["estimativa_assistida"]["fonte"] == "opencv_escala_visivel"


def test_detecta_periodicidade_da_regua_transparente_no_lote_real():
    raiz = Path(__file__).resolve().parents[2]
    imagem = cv2.imread(
        str(raiz / "vision" / "fotos" / "validacao-lote-2026-09-14" / "foto_1.png")
    )
    resultado = medir_escala_regua_transparente(imagem)
    assert resultado is not None
    assert 33.0 <= resultado["pixels_por_cm"] <= 39.0
    assert resultado["bbox_horizontal"][0] < resultado["bbox_horizontal"][1]
    assert resultado["confianca"] >= .60
