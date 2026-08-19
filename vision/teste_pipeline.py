"""Testes do pipeline de foto: contrato JSON, recusa sem escala e as duas vias.

A prova que interessa aqui é a última: a mesma cena, medida pela régua no
quadro e pela calibração salva, tem de dar o mesmo número. É isso que autoriza
tirar a régua da foto em produção.
"""
from __future__ import annotations

import tempfile
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import cv2

try:  # como pacote
    from .calibracao import (
        CalibracaoAntiga,
        CalibracaoInvalida,
        calibrar_de_foto,
        carregar_calibracao,
        detectar_referencia,
        medir_escala,
        pixels_por_cm,
        salvar_calibracao,
    )
    from .calibracao import _detectar_por_cor, _detectar_por_geometria
    from .pipeline import VIA_ARQUIVO, VIA_HASTE, FotoInvalida, processar_foto
    from .graduacao import escala_por_graduacao
    from .teste_sintetico import (
        COR_TRENA_AMARELA,
        LINHA_DO_CHAO,
        gerar_cena,
        gerar_trena_graduada,
    )
except ImportError:  # direto de dentro de vision/
    from calibracao import (
        CalibracaoAntiga,
        CalibracaoInvalida,
        calibrar_de_foto,
        carregar_calibracao,
        detectar_referencia,
        medir_escala,
        pixels_por_cm,
        salvar_calibracao,
    )
    from calibracao import _detectar_por_cor, _detectar_por_geometria
    from pipeline import VIA_ARQUIVO, VIA_HASTE, FotoInvalida, processar_foto
    from graduacao import escala_por_graduacao
    from teste_sintetico import (
        COR_TRENA_AMARELA,
        LINHA_DO_CHAO,
        gerar_cena,
        gerar_trena_graduada,
    )

# A cena sintética tem haste de 400 px valendo 100 cm e vegetação de 240 px,
# então a altura verdadeira é 60 cm por construção.
HASTE_PX = 400
VEGETACAO_PX = 240
HASTE_CM = 100.0
ALTURA_ESPERADA_CM = VEGETACAO_PX / (HASTE_PX / HASTE_CM)


def bytes_jpeg(imagem) -> bytes:
    ok, codificada = cv2.imencode(".jpg", imagem)
    assert ok, "não foi possível codificar a cena"
    return codificada.tobytes()


def testar_contrato_e_recusa(saida: Path) -> None:
    """Comportamento original: régua no quadro, contrato e recusa sem régua."""
    cena = gerar_cena(altura_haste_px=HASTE_PX, altura_vegetacao_px=VEGETACAO_PX)
    resultado = processar_foto(bytes_jpeg(cena), "teste.jpg", HASTE_CM, saida)

    deteccao = resultado["deteccoes"][0]
    assert deteccao["unidade"] == "cm"
    assert abs(deteccao["metrica"] - ALTURA_ESPERADA_CM) <= 3.0
    assert resultado["calibracao"]["pixels_por_cm"] > 0
    assert resultado["calibracao"]["referencia"] == VIA_HASTE
    assert (saida / resultado["evidencias"]["imagem_anotada"]).is_file()
    assert (saida / resultado["evidencias"]["mascara"]).is_file()
    assert (saida / resultado["evidencias"]["json"]).is_file()
    print(f"ok — contrato: {deteccao['metrica']} cm; evidências gravadas")

    try:
        processar_foto(bytes_jpeg(gerar_cena(0, 200, com_haste=False)), "sem-haste.jpg", HASTE_CM, saida)
    except FotoInvalida:
        print("ok — foto sem haste recusada quando a via é a régua no quadro")
    else:
        raise AssertionError("foto sem haste não foi recusada")


def testar_sem_fonte_de_escala(saida: Path) -> None:
    """Sem calibração e sem referência, o pipeline recusa em vez de estimar."""
    cena = gerar_cena(HASTE_PX, VEGETACAO_PX)
    try:
        processar_foto(bytes_jpeg(cena), "sem-escala.jpg", diretorio_saida=saida)
    except FotoInvalida as erro:
        assert "escala" in str(erro).lower()
        print("ok — sem fonte de escala o pipeline recusa")
    else:
        raise AssertionError("o pipeline mediu sem fonte de escala")


def testar_calibracao_salva_bate_com_a_regua(saida: Path) -> None:
    """O teste que autoriza tirar a régua da foto.

    Mede a mesma vegetação por duas vias: régua no quadro e calibração salva,
    esta última numa cena que NÃO tem régua nenhuma. Os dois números têm de
    coincidir.
    """
    com_regua = gerar_cena(HASTE_PX, VEGETACAO_PX)
    sem_regua = gerar_cena(0, VEGETACAO_PX, com_haste=False)

    foto_calibracao = saida / "calibracao-origem.png"
    cv2.imwrite(str(foto_calibracao), com_regua)

    dados = calibrar_de_foto(
        foto_calibracao,
        comprimento_referencia_cm=HASTE_CM,
        altura_camera_cm=140.0,
        distancia_alvo_cm=200.0,
    )
    assert dados["pixels_por_cm"] > 0
    assert dados["geometria"]["altura_camera_cm"] == 140.0
    assert dados["origem"]["referencia_cm"] == HASTE_CM

    arquivo = salvar_calibracao(dados, saida / "calibracao.json")
    recarregada = carregar_calibracao(arquivo)
    assert recarregada["pixels_por_cm"] == dados["pixels_por_cm"]

    pela_regua = processar_foto(bytes_jpeg(com_regua), "com-regua.jpg", HASTE_CM)
    pelo_arquivo = processar_foto(
        bytes_jpeg(sem_regua), "sem-regua.jpg", calibracao=recarregada
    )

    altura_regua = pela_regua["deteccoes"][0]["metrica"]
    altura_arquivo = pelo_arquivo["deteccoes"][0]["metrica"]
    divergencia = abs(altura_arquivo - altura_regua) / altura_regua * 100

    assert pela_regua["calibracao"]["referencia"] == VIA_HASTE
    assert pelo_arquivo["calibracao"]["referencia"] == VIA_ARQUIVO
    assert "geometria" not in pela_regua["calibracao"]
    assert pelo_arquivo["calibracao"]["geometria"]["distancia_alvo_cm"] == 200.0
    assert divergencia < 10.0, f"divergência de {divergencia:.1f}% entre as vias"

    print(
        f"ok — régua no quadro {altura_regua} cm x calibração salva "
        f"{altura_arquivo} cm (divergência {divergencia:.2f}%)"
    )
    print("     a segunda foto não tinha régua nenhuma")


def testar_aviso_de_calibracao_antiga(saida: Path) -> None:
    """Calibração velha continua funcionando, mas precisa avisar."""
    arquivo = saida / "antiga.json"
    velha = {
        "pixels_por_cm": 4.0,
        "geometria": {"altura_camera_cm": 140.0, "distancia_alvo_cm": 200.0},
        "origem": {
            "foto": "antiga.jpg",
            "referencia_cm": 100.0,
            "criado_em": (datetime.now().astimezone() - timedelta(days=30)).isoformat(
                timespec="seconds"
            ),
        },
    }
    salvar_calibracao(velha, arquivo)

    with warnings.catch_warnings(record=True) as capturados:
        warnings.simplefilter("always")
        carregada = carregar_calibracao(arquivo)

    antigos = [a for a in capturados if issubclass(a.category, CalibracaoAntiga)]
    assert antigos, "calibração de 30 dias não gerou aviso"
    assert carregada["pixels_por_cm"] == 4.0
    print("ok — calibração de 30 dias avisa e continua utilizável")


def testar_calibracao_invalida(saida: Path) -> None:
    """Arquivo ausente ou incompleto falha claro, sem cair em valor padrão."""
    try:
        carregar_calibracao(saida / "nao-existe.json")
    except CalibracaoInvalida:
        print("ok — calibração ausente recusada")
    else:
        raise AssertionError("calibração ausente não foi recusada")

    incompleta = saida / "incompleta.json"
    incompleta.write_text('{"pixels_por_cm": 3.5}', encoding="utf-8")
    try:
        carregar_calibracao(incompleta)
    except CalibracaoInvalida:
        print("ok — calibração sem geometria recusada")
    else:
        raise AssertionError("calibração sem geometria não foi recusada")


def testar_vias_de_deteccao() -> None:
    """Cor é o método principal; forma é o fallback. Cada um no seu caso.

    A cena sintética usa haste cinza, que não tem amarelo nenhum — então ela
    prova o fallback. A cena de trena amarela prova a via de cor, sem depender
    de foto real.
    """
    cinza = gerar_cena(HASTE_PX, VEGETACAO_PX)
    encontrado = detectar_referencia(cinza)
    assert encontrado is not None, "haste cinza não foi encontrada por nenhuma via"
    metodo, (_, _, largura, altura) = encontrado
    assert metodo == "geometria", f"haste cinza deveria cair no fallback, veio '{metodo}'"
    print(f"ok — haste cinza: via '{metodo}', {largura}x{altura} px")

    amarela = gerar_cena(HASTE_PX, VEGETACAO_PX, cor_haste=COR_TRENA_AMARELA)
    encontrado = detectar_referencia(amarela)
    assert encontrado is not None, "trena amarela não foi encontrada"
    metodo, (_, _, largura, altura) = encontrado
    assert metodo == "cor", f"trena amarela deveria usar a cor, veio '{metodo}'"
    assert altura / largura >= 3.0
    print(f"ok — trena amarela: via '{metodo}', {largura}x{altura} px, razão {altura / largura:.1f}")

    # As duas vias precisam medir a mesma coisa: a haste tem a mesma altura.
    escala_cinza = pixels_por_cm(cinza, HASTE_CM)
    escala_amarela = pixels_por_cm(amarela, HASTE_CM)
    divergencia = abs(escala_amarela - escala_cinza) / escala_cinza * 100
    assert divergencia < 5.0, f"vias divergem {divergencia:.1f}% na mesma geometria"
    print(
        f"ok — escala igual pelas duas vias: {escala_cinza:.3f} x "
        f"{escala_amarela:.3f} px/cm ({divergencia:.2f}%)"
    )


def testar_fundo_poluido_com_trena() -> None:
    """O caso que motivou a mudança: fundo real quebra a detecção por forma.

    Reproduz o mecanismo relatado, não só a aparência: pinta um céu claro que
    **encosta** no topo da trena. Aí a trena deixa de ser um componente próprio
    e passa a fazer parte de um blob que atravessa a imagem inteira — o filtro
    de largura reprova, e a via geométrica desiste.

    A via de cor não se abala: amarelo continua sendo amarelo.
    """
    cena = gerar_cena(HASTE_PX, VEGETACAO_PX, cor_haste=COR_TRENA_AMARELA)
    topo_da_trena = LINHA_DO_CHAO - HASTE_PX
    # O céu cobre até 5 px abaixo do topo da trena, encostando nela.
    cena[0 : topo_da_trena + 5, :] = (205, 195, 185)

    assert _detectar_por_geometria(cena) is None, (
        "o fallback geométrico deveria falhar com fundo poluído — se passou, "
        "a cena de teste não reproduz o problema relatado"
    )

    caixa = _detectar_por_cor(cena)
    assert caixa is not None, "a detecção por cor falhou com fundo poluído"
    _, _, largura, altura = caixa
    assert altura / largura >= 3.0
    print(
        f"ok — fundo poluído: forma falha, cor acha {largura}x{altura} px "
        f"(razão {altura / largura:.1f})"
    )


def testar_graduacao_em_varias_escalas() -> None:
    """A leitura da graduação tem de acertar sem ninguém digitar nada.

    A faixa inclui 25, 29 e 35 px/cm de propósito: foram exatamente essas que
    travavam no segundo harmônico e devolviam o dobro da escala.
    """
    for ppc in (10, 15, 20, 25, 29, 30, 35, 40, 50):
        imagem, bbox = gerar_trena_graduada(ppc, 14.0)
        leitura = escala_por_graduacao(imagem, bbox)
        assert leitura is not None, f"graduação não foi lida a {ppc} px/cm"
        erro = abs(leitura["pixels_por_cm"] - ppc) / ppc * 100
        assert erro < 5.0, f"a {ppc} px/cm leu {leitura['pixels_por_cm']} ({erro:.1f}%)"
        assert abs(leitura["comprimento_visivel_cm"] - 14.0) < 0.7
        print(
            f"ok — {ppc} px/cm: leu {leitura['pixels_por_cm']:.2f} ({erro:.2f}%), "
            f"período {leitura['periodo_px']:.1f} px como {leitura['interpretacao']}, "
            f"fita {leitura['comprimento_visivel_cm']:.1f} cm"
        )


def testar_largura_desempata_a_escala() -> None:
    """A largura física da fita é o que decide entre 5 mm e 1 cm.

    Este é o caso que produziu 41,6 cm para uma grama de 5-6 cm: o período de
    2,655 px foi lido como 5 mm em vez de 1 mm, e a escala saiu 5,5x menor. A
    largura recuperada tem de bater com a fita desenhada.
    """
    for ppc in (20, 29, 40):
        imagem, bbox = gerar_trena_graduada(ppc, 14.0, largura_fita_cm=2.5)
        leitura = escala_por_graduacao(imagem, bbox)
        assert leitura is not None, f"recusou a {ppc} px/cm"
        assert leitura["interpretacao"] == "10mm", (
            f"a {ppc} px/cm interpretou como {leitura['interpretacao']}"
        )
        largura = leitura["largura_fita_cm"]
        assert abs(largura - 2.5) < 0.5, f"largura recuperada {largura} cm"
        print(
            f"ok — {ppc} px/cm: interpretação {leitura['interpretacao']}, "
            f"fita recuperada em {largura:.2f} cm"
        )


def testar_graduacao_inclinada() -> None:
    """Foto de campo não sai a prumo; o endireitamento tem de dar conta."""
    for angulo in (5.0, 10.0, -7.0):
        imagem, bbox = gerar_trena_graduada(30, 14.0, angulo_graus=angulo)
        leitura = escala_por_graduacao(imagem, bbox)
        assert leitura is not None, f"graduação não foi lida a {angulo}°"
        erro = abs(leitura["pixels_por_cm"] - 30) / 30 * 100
        assert erro < 5.0, f"a {angulo}° leu {leitura['pixels_por_cm']} ({erro:.1f}%)"
        print(f"ok — inclinada {angulo:+.0f}°: {leitura['pixels_por_cm']:.2f} px/cm ({erro:.2f}%)")


def testar_divergencia_entre_vias() -> None:
    """O erro que motivou tudo: comprimento digitado errado tem de gritar.

    Reproduz o caso real — a fita mostra ~14 cm e alguém informa 50 cm. A
    escala da graduação e a do número digitado divergem, e o resultado precisa
    dizer isso em vez de escalar tudo em silêncio.
    """
    imagem, bbox = gerar_trena_graduada(30, 14.0)

    medicao = medir_escala(imagem, comprimento_referencia_cm=50.0)
    assert medicao["via"] == "graduacao", "a graduação deveria ter precedência"
    assert medicao["divergencia_pct"] is not None
    assert medicao["divergencia_pct"] > 15.0
    assert any("divergem" in aviso for aviso in medicao["avisos"]), medicao["avisos"]
    print(
        f"ok — comprimento errado detectado: graduação {medicao['pixels_por_cm']:.1f} "
        f"px/cm x informado {medicao['pixels_por_cm_informado']:.1f} px/cm "
        f"(divergência {medicao['divergencia_pct']:.0f}%)"
    )

    # Com o comprimento certo, nenhuma divergência.
    correta = medir_escala(imagem, comprimento_referencia_cm=14.0)
    assert correta["divergencia_pct"] < 15.0
    assert not any("divergem" in aviso for aviso in correta["avisos"])
    print(f"ok — comprimento certo: divergência {correta['divergencia_pct']:.1f}%")

    # Sem informar nada, a graduação sozinha resolve.
    sozinha = medir_escala(imagem)
    assert sozinha["via"] == "graduacao"
    assert abs(sozinha["pixels_por_cm"] - 30) / 30 * 100 < 5.0
    print(f"ok — sem número digitado: {sozinha['pixels_por_cm']:.2f} px/cm")


def testar_avisos_de_plausibilidade(saida: Path) -> None:
    """Avisos acompanham o resultado sem impedi-lo."""
    imagem, _ = gerar_trena_graduada(30, 14.0)
    ok, codificada = cv2.imencode(".png", imagem)
    assert ok

    # Cena honesta: trena lida, sem vegetação absurda.
    limpa = gerar_cena(HASTE_PX, VEGETACAO_PX, cor_haste=COR_TRENA_AMARELA)
    resultado = processar_foto(bytes_jpeg(limpa), "limpa.jpg", HASTE_CM, saida)
    assert "avisos" in resultado, "o contrato precisa trazer o bloco de avisos"
    print(f"ok — bloco 'avisos' presente ({len(resultado['avisos'])} aviso(s))")

    # Régua curta no quadro (100 px) e vegetação alta (400 px): informando
    # 60 cm de régua, a vegetação sai em 240 cm — implausível para faixa de
    # domínio E quatro vezes maior que a própria referência. Os dois avisos
    # precisam aparecer.
    desproporcional = gerar_cena(100, 400, cor_haste=COR_TRENA_AMARELA)
    exagerada = processar_foto(bytes_jpeg(desproporcional), "exagerada.jpg", 60.0, saida)
    altura = exagerada["deteccoes"][0]["metrica"]
    assert altura > 200, f"esperava altura implausível, veio {altura}"
    texto = " ".join(exagerada["avisos"])
    assert "plausivel" in texto, exagerada["avisos"]
    assert "maior que a referencia" in texto, exagerada["avisos"]
    print(f"ok — altura de {altura:.0f} cm gerou {len(exagerada['avisos'])} aviso(s)")


def executar() -> int:
    testar_graduacao_em_varias_escalas()
    testar_largura_desempata_a_escala()
    testar_graduacao_inclinada()
    testar_divergencia_entre_vias()
    testar_vias_de_deteccao()
    testar_fundo_poluido_com_trena()
    with tempfile.TemporaryDirectory() as pasta_temporaria:
        saida = Path(pasta_temporaria)
        testar_contrato_e_recusa(saida)
        testar_sem_fonte_de_escala(saida)
        testar_avisos_de_plausibilidade(saida)
        testar_calibracao_salva_bate_com_a_regua(saida)
        testar_aviso_de_calibracao_antiga(saida)
        testar_calibracao_invalida(saida)
    return 0


if __name__ == "__main__":
    raise SystemExit(executar())
