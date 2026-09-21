"""API local do Motiva Field: foto entra, análise estruturada sai."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import time
from datetime import datetime, timezone
from io import BytesIO
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from enum import StrEnum
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import cv2
import numpy as np

# Reutiliza a fórmula testada de vision/ no mesmo processo da API.
RAIZ_PROJETO = Path(__file__).resolve().parents[2]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))
from vision.calibracao import medir_escala_regua_transparente  # noqa: E402
from vision.pipeline import FotoInvalida, processar_foto  # noqa: E402
from vision.segmentacao import mascara_vegetacao, medir_altura_vegetacao  # noqa: E402
from app.desafio_fixtures import resposta_desafio

CACHE_AUDITORIAS = RAIZ_PROJETO / "api" / ".cache" / "auditorias"
VERSAO_AUDITORIA = "v5-coordenadas-xy-2026-09-14"
MODELOS_AUDITORIA = ("gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=RAIZ_PROJETO / "api" / ".env", extra="ignore")
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    allow_demo_fallback: bool = True
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_bucket_evidencias: str = "evidencias"


settings = Settings()


class NivelRisco(StrEnum):
    SEGURO = "seguro"
    ATENCAO = "atencao"
    CRITICO = "critico"
    NAO_AVALIAVEL = "nao_avaliavel"


class TipoRisco(StrEnum):
    VEGETACAO_ALTA = "vegetacao_alta"
    INVADE_PISTA = "invade_pista"
    COBRE_PLACA = "cobre_placa"


class Caixa(BaseModel):
    x1: int = Field(ge=0)
    y1: int = Field(ge=0)
    x2: int = Field(ge=0)
    y2: int = Field(ge=0)


class DeteccaoRisco(BaseModel):
    tipo: TipoRisco
    presente: bool
    nivel: NivelRisco
    confianca: float = Field(ge=0, le=1)
    justificativa: str = Field(min_length=3, max_length=320)
    bbox: Caixa | None = None
    cobertura_pct: float | None = Field(default=None, ge=0, le=100)


class MedicaoAltura(BaseModel):
    centimetros: float | None = Field(default=None, ge=0)
    fonte_escala: str | None = None
    observacao: str


class PontoPixel(BaseModel):
    x: float = Field(ge=0)
    y: float = Field(ge=0)


class AtualizacaoStatusOrdem(BaseModel):
    status: str = Field(pattern="^(triagem|pendente|programada|em_deslocamento|no_local|em_campo|validacao|concluida)$")
    observacao: str | None = Field(default=None, max_length=500)


class ResultadoFilaImagem(BaseModel):
    resultado_resumo: dict[str, object]


class MedicaoAssistidaResposta(BaseModel):
    arquivo: str
    status: str = "medido_assistido"
    altura_cm: float = Field(gt=0)
    valido: bool = True
    nivel_validacao: str = "assistido_operador"
    apto_historico: bool = False
    intervalo_cm: list[float] = Field(min_length=2, max_length=2)
    confianca: float = Field(ge=0, le=1)
    metodo: str = "referencia_local_quatro_pontos"
    escala_px_por_cm: float = Field(gt=0)
    angulo_entre_segmentos_graus: float = Field(ge=0)
    referencia_cm: float = Field(gt=0)
    referencia_px: float = Field(gt=0)
    alvo_px_projetado: float = Field(gt=0)
    pontos: dict[str, PontoPixel]
    mensagem: str
    avisos: list[str] = Field(default_factory=list)
    proveniencia: dict[str, str]


class AnaliseImagem(BaseModel):
    arquivo: str
    origem: str = Field(description="gemini ou demo_local")
    modelo: str
    resumo_operacional: str = Field(min_length=3, max_length=500)
    deteccoes: list[DeteccaoRisco] = Field(min_length=3, max_length=3)
    altura: MedicaoAltura
    acao_recomendada: str = Field(min_length=3, max_length=320)
    avisos: list[str] = Field(default_factory=list)


class DescricaoImagem(BaseModel):
    arquivo: str
    origem: str = Field(description="gemini ou demo_local")
    modelo: str
    descricao: str = Field(min_length=3, max_length=700)
    objeto_principal: str = Field(min_length=2, max_length=160)
    confianca: float = Field(ge=0, le=1)
    detalhes_visuais: list[str] = Field(min_length=1, max_length=6)
    avisos: list[str] = Field(default_factory=list)


class DecisaoGeometrica(StrEnum):
    MEDIR_COM_REGUA = "medir_com_regua"
    TRIAGEM_SEM_MEDIDA = "triagem_sem_medida"
    BLOQUEAR = "bloquear"


class AlvoGeometrico(BaseModel):
    classe: str | None = None
    roi_normalizada_0a1000: list[int] | None = Field(default=None, min_length=4, max_length=4)
    confianca: float = Field(ge=0, le=1)
    motivo: str


class BaseTopoGeometrico(BaseModel):
    compativeis: bool
    base_visivel: bool
    topo_visivel: bool
    base_px_normalizado_0a1000: list[int] | None = Field(default=None, min_length=2, max_length=2)
    topo_px_normalizado_0a1000: list[int] | None = Field(default=None, min_length=2, max_length=2)
    motivo: str


class AmostraVisual(BaseModel):
    base_px_normalizado_0a1000: list[int] = Field(min_length=2, max_length=2)
    topo_px_normalizado_0a1000: list[int] = Field(min_length=2, max_length=2)
    confianca: float = Field(ge=0, le=1)


class DadosAuditaveis(BaseModel):
    observacoes: list[str] = Field(default_factory=list, max_length=12)
    inferencias: list[str] = Field(default_factory=list, max_length=12)
    desconhecidos: list[str] = Field(default_factory=list, max_length=12)


class ChecklistMedibilidade(BaseModel):
    alvo_definido: bool = False
    roi_valida: bool = False
    base_valida: bool = False
    topo_valido: bool = False
    base_topo_compativeis: bool = False
    referencia_valida: bool = False
    referencia_localizada: bool = False
    relacao_espacial_avaliada: bool = False
    solo_identificado: bool = False
    geometria_suficiente: bool = False
    pode_calcular: bool = False


class ConfiancaComponentes(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    alvo: float = Field(default=0, ge=0, le=1)
    roi: float = Field(default=0, ge=0, le=1)
    base: float = Field(default=0, ge=0, le=1)
    topo: float = Field(default=0, ge=0, le=1)
    base_topo: float = Field(default=0, ge=0, le=1)
    referencia: float = Field(default=0, ge=0, le=1)
    relacao_espacial: float = Field(default=0, ge=0, le=1)
    solo: float = Field(default=0, ge=0, le=1)
    geometria: float = Field(default=0, ge=0, le=1)
    global_: float = Field(default=0, alias="global", ge=0, le=1)


class ReferenciaGeometrica(BaseModel):
    tipo: str
    bbox_normalizada_0a1000: list[int] | None = Field(default=None, min_length=4, max_length=4)
    ponto_superior_normalizado_0a1000: list[int] | None = Field(default=None, min_length=2, max_length=2)
    ponto_inferior_normalizado_0a1000: list[int] | None = Field(default=None, min_length=2, max_length=2)
    # O Gemini Structured Output aceita `minimum`, mas o SDK rejeita
    # `exclusiveMinimum` no schema enviado à API. Um centésimo mantém o campo
    # estritamente positivo sem gerar o keyword incompatível.
    intervalo_observado_cm: float | None = Field(default=None, ge=0.01)
    incerteza_cm: float | None = Field(default=None, ge=0)
    confianca: float = Field(ge=0, le=1)
    compatibilidade_espacial: float = Field(ge=0, le=1)
    utilizavel: bool
    incerteza_descricao: str


class AuditoriaGeometrica(BaseModel):
    arquivo: str
    origem: str
    modelo: str
    versao_contrato: str = VERSAO_AUDITORIA
    decisao: DecisaoGeometrica
    geometria_candidata: bool = Field(description="ROI/base/topo pode seguir para validação determinística; não autoriza cm sozinha")
    metrica_operacional: str = "p85_envelope_local_com_iqr"
    alvo: AlvoGeometrico
    base_topo: BaseTopoGeometrico
    amostras: list[AmostraVisual] = Field(default_factory=list, max_length=20)
    referencias: list[ReferenciaGeometrica] = Field(default_factory=list, max_length=5)
    plano_local: str | None = None
    inclinacao_desconhecida: bool
    dados: DadosAuditaveis = Field(default_factory=DadosAuditaveis)
    auditoria: ChecklistMedibilidade = Field(default_factory=ChecklistMedibilidade)
    confianca_componentes: ConfiancaComponentes = Field(default_factory=ConfiancaComponentes)
    objetos_ignorados: list[str] = Field(default_factory=list, max_length=8)
    limitacoes: list[str] = Field(default_factory=list, min_length=1, max_length=8)
    proxima_captura: str


PROMPT = """Você é o analisador visual do Motiva Field para rodovias brasileiras.
Analise somente o que é visualmente sustentado pela foto. Retorne EXCLUSIVAMENTE JSON
conforme o schema fornecido, com exatamente três detecções, nesta ordem:
vegetacao_alta, invade_pista, cobre_placa.

Regras:
- Não estime altura em centímetros sem uma escala métrica visível e inequívoca.
- Se a evidência não existir ou estiver ambígua, presente=false e nivel=nao_avaliavel ou seguro,
  justificando com honestidade.
- "invade_pista" só é presente se vegetação ocupar a faixa de rolamento ou área de segurança
  imediatamente adjacente que comprometa circulação/visibilidade.
- "cobre_placa" só é presente se a vegetação obstruir uma placa de trânsito identificável.
- Confiança representa certeza visual, não gravidade.
- As caixas são opcionais; só preencha se puder localizar o elemento com segurança.
- O texto deve ser em português do Brasil, objetivo e adequado à operação.
- O objetivo é triagem operacional humana, não decisão autônoma de segurança.
"""


def _demo(nome: str) -> AnaliseImagem:
    """Fallback explícito para ensaio sem chave/rede; nunca se apresenta como Gemini."""
    return AnaliseImagem(
        arquivo=nome,
        origem="demo_local",
        modelo="cenário demonstrativo local",
        resumo_operacional="Cenário demonstrativo: vegetação exige inspeção prioritária.",
        deteccoes=[
            DeteccaoRisco(tipo=TipoRisco.VEGETACAO_ALTA, presente=True, nivel=NivelRisco.ATENCAO, confianca=0.82, justificativa="Vegetação densa visível na faixa de domínio."),
            DeteccaoRisco(tipo=TipoRisco.INVADE_PISTA, presente=False, nivel=NivelRisco.SEGURO, confianca=0.76, justificativa="Sem invasão inequívoca da faixa de rolamento no cenário demonstrativo."),
            DeteccaoRisco(tipo=TipoRisco.COBRE_PLACA, presente=False, nivel=NivelRisco.SEGURO, confianca=0.74, justificativa="Nenhuma placa obstruída foi identificada no cenário demonstrativo."),
        ],
        altura=MedicaoAltura(centimetros=None, fonte_escala=None, observacao="Altura em cm indisponível: a foto não possui escala métrica validada."),
        acao_recomendada="Enviar inspeção de campo e registrar evidências antes de programar a roçada.",
        avisos=["Resposta local de contingência; não substitui a análise Gemini."],
    )


PROMPT_DESCRICAO = """Descreva a imagem em português do Brasil. Identifique o objeto principal apenas quando a evidência visual sustentar a conclusão. Não identifique pessoas, não infira identidade, marca, modelo ou texto ilegível. Se não for possível reconhecer com segurança, use uma categoria visual honesta (por exemplo, 'caixa/embalagem vermelha') e declare a incerteza. Retorne exclusivamente JSON conforme o schema."""


PROMPT_AUDITORIA_GEOMETRICA = """Você é o módulo de ATENÇÃO VISUAL do Motiva Field. Sua função não é calcular altura; é produzir uma auditoria rastreável antes de qualquer fórmula geométrica.

Retorne exclusivamente JSON conforme o schema. Coordenadas são normalizadas de 0 a 1000 no tamanho original da imagem. TODOS os pontos usam rigorosamente [x, y]: x cresce da esquerda para a direita e y cresce do topo para baixo. TODAS as caixas usam [x1, y1, x2, y2]. Nunca troque x por y. Nunca invente coordenadas, escala, profundidade ou plano. Se não estiver seguro, use null, confiança baixa e a decisão bloquear ou triagem_sem_medida.

Regras obrigatórias:
- Identifique um único alvo vegetal apenas se ROI, base e topo forem atribuíveis ao mesmo objeto/faixa local. Não selecione automaticamente a maior massa verde ou objeto mais alto.
- Só retorne medir_com_regua quando houver régua/fita/escala métrica legível e fisicamente próxima do alvo, com compatibilidade espacial alta. Meio-fio, pneus, folhas, objetos distantes e infraestrutura não são escalas válidas nesta versão.
- Para régua/fita legível, localize dois traços numerados inequívocos em ponto_superior_normalizado_0a1000 e ponto_inferior_normalizado_0a1000 e informe em intervalo_observado_cm a diferença física entre essas duas marcações (não o número absoluto impresso). Se não puder ler ambos com certeza, deixe os pontos e o intervalo como null.
- Em massa contínua de grama, pode usar uma faixa local como alvo somente se a linha de solo e o envelope superior forem visíveis e separáveis; caso contrário, não meça.
- Marque geometria_candidata=true somente quando ROI, base e topo são visualmente consistentes. Isso não prova escala, plano ou calibração; apenas permite a próxima validação determinística.
- Talude, vegetação em múltiplas profundidades, foto oblíqua, noite, sombra forte, base oculta ou referência fora do plano reduzem a decisão para triagem_sem_medida ou bloquear.
- "plano_local" descreve somente o que é visualmente observável; não transforme aparência em certeza geométrica.
- Para faixa contínua/touceira, retorne entre 8 e 20 amostras distribuídas na ROI. Cada amostra liga base e topo locais; não use a folha isolada mais alta.
- Use metrica_operacional=p85_envelope_local_com_iqr. Separe rigorosamente dados observados, inferidos e desconhecidos.
- Preencha o checklist de auditoria e as confianças por componente. pode_calcular=true só quando todos os pré-requisitos do método escolhido estiverem presentes.
- A saída será conferida por segmentação determinística e calibração de câmera. Ela não autoriza sozinha uma altura em centímetros.
"""


def _analisar_gemini(conteudo: bytes, mime_type: str, nome: str) -> AnaliseImagem:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY não configurada")
    from google import genai
    from google.genai import types

    cliente = genai.Client(api_key=settings.gemini_api_key)
    ultima_falha: Exception | None = None
    for tentativa in range(3):
        try:
            resposta = cliente.models.generate_content(
                model=settings.gemini_model,
                contents=[PROMPT, types.Part.from_bytes(data=conteudo, mime_type=mime_type)],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AnaliseImagem,
                    temperature=0,
                ),
            )
            dados = json.loads(resposta.text)
            break
        except Exception as erro:
            ultima_falha = erro
            if tentativa == 2:
                raise
            # 503 e instabilidade breve são normais em modelos compartilhados.
            # Três tentativas com espera curta evitam cair cedo demais no fallback.
            time.sleep(2 ** tentativa)
    else:  # proteção para o analisador estático; o raise acima sempre interrompe.
        raise RuntimeError("Gemini não retornou resposta") from ultima_falha
    dados.update({"arquivo": nome, "origem": "gemini", "modelo": settings.gemini_model})
    return AnaliseImagem.model_validate(dados)


app = FastAPI(title="Motiva Field API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


def _supabase_requisicao(caminho: str, metodo: str = "GET", corpo: object | None = None, headers_extras: dict[str, str] | None = None) -> object:
    """Acesso ao Supabase somente pelo backend; nunca exponha service_role ao cliente."""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(status_code=503, detail="Supabase não configurado na API local.")
    dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8") if corpo is not None else None
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Accept": "application/json",
    }
    if dados is not None:
        headers["Content-Type"] = "application/json"
    headers.update(headers_extras or {})
    requisicao = Request(f"{settings.supabase_url.rstrip('/')}{caminho}", data=dados, headers=headers, method=metodo)
    try:
        with urlopen(requisicao, timeout=20) as resposta:
            bruto = resposta.read()
            return json.loads(bruto) if bruto else None
    except HTTPError as erro:
        detalhe = erro.read().decode("utf-8", errors="replace")[:500]
        raise HTTPException(status_code=502, detail=f"Supabase recusou a operação: {detalhe}") from erro
    except URLError as erro:
        raise HTTPException(status_code=503, detail="Supabase indisponível para a API local.") from erro


@app.get("/api/health")
def health() -> dict[str, object]:
    return {"status": "ok", "gemini_configurado": bool(settings.gemini_api_key), "fallback": settings.allow_demo_fallback}


@app.get("/api/operacao/health")
def health_operacao() -> dict[str, object]:
    _supabase_requisicao("/rest/v1/ordens_servico?select=id&limit=1")
    return {"status": "ok", "fonte_compartilhada": "supabase", "bucket_evidencias": settings.supabase_bucket_evidencias}


@app.get("/api/operacao/ordens")
def listar_ordens_operacao() -> object:
    return _supabase_requisicao("/rest/v1/ordens_servico?select=*&order=updated_at.desc")


@app.get("/api/operacao/painel-regional")
def painel_regional_operacao() -> object:
    return _supabase_requisicao("/rest/v1/vw_painel_regional?select=*&order=codigo_regiao.asc")


@app.patch("/api/operacao/ordens/{ordem_id}/status")
def atualizar_status_ordem(ordem_id: str, atualizacao: AtualizacaoStatusOrdem) -> object:
    atual = _supabase_requisicao(f"/rest/v1/ordens_servico?id=eq.{quote(ordem_id)}&select=id,status")
    if not isinstance(atual, list) or not atual:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada.")
    anterior = atual[0]["status"]
    agora = datetime.now(timezone.utc).isoformat()
    resultado = _supabase_requisicao(
        f"/rest/v1/ordens_servico?id=eq.{quote(ordem_id)}",
        metodo="PATCH",
        corpo={"status": atualizacao.status, "updated_at": agora, "concluida_em": agora if atualizacao.status == "concluida" else None},
        headers_extras={"Prefer": "return=representation"},
    )
    _supabase_requisicao(
        "/rest/v1/historico_ordem",
        metodo="POST",
        corpo={"ordem_id": ordem_id, "status_anterior": anterior, "status_novo": atualizacao.status, "observacao": atualizacao.observacao},
        headers_extras={"Prefer": "return=minimal"},
    )
    return resultado[0] if isinstance(resultado, list) and resultado else {"id": ordem_id, "status": atualizacao.status}


@app.post("/api/operacao/evidencias")
async def registrar_evidencia_operacao(
    ordem_id: Annotated[str, Form(min_length=1)],
    imagem: Annotated[UploadFile, File(...)],
    latitude: Annotated[float | None, Form()] = None,
    longitude: Annotated[float | None, Form()] = None,
) -> object:
    if imagem.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Envie JPG, PNG ou WEBP.")
    conteudo = await imagem.read()
    if not conteudo:
        raise HTTPException(status_code=422, detail="Arquivo de evidência vazio.")
    existe = _supabase_requisicao(f"/rest/v1/ordens_servico?id=eq.{quote(ordem_id)}&select=id")
    if not isinstance(existe, list) or not existe:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada.")
    nome = Path(imagem.filename or "evidencia.jpg").name
    caminho = f"{ordem_id}/{int(time.time())}-{hashlib.sha256(conteudo).hexdigest()[:12]}-{nome}"
    # O helper JSON é propositalmente restrito às tabelas REST; o Storage recebe
    # apenas os bytes originais da foto, uma única vez.
    headers = {"apikey": settings.supabase_service_role_key or "", "Authorization": f"Bearer {settings.supabase_service_role_key or ''}", "Content-Type": imagem.content_type, "x-upsert": "false"}
    try:
        requisicao = Request(f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{settings.supabase_bucket_evidencias}/{caminho}", data=conteudo, headers=headers, method="POST")
        with urlopen(requisicao, timeout=30):
            pass
    except HTTPError as erro:
        raise HTTPException(status_code=502, detail="Falha ao gravar arquivo de evidência no Supabase Storage.") from erro
    registro = _supabase_requisicao(
        "/rest/v1/evidencias",
        metodo="POST",
        corpo={"ordem_id": ordem_id, "storage_path": caminho, "nome_arquivo": nome, "mime_type": imagem.content_type, "tamanho_bytes": len(conteudo), "latitude": latitude, "longitude": longitude, "capturada_em": datetime.now(timezone.utc).isoformat()},
        headers_extras={"Prefer": "return=representation"},
    )
    return registro[0] if isinstance(registro, list) else registro


@app.post("/api/operacao/fila-imagens")
async def receber_imagem_na_fila(
    imagem: Annotated[UploadFile, File(...)],
) -> object:
    """Persiste a foto no Storage, cria a evidência e registra a fila operacional."""
    conteudo, _, nome = await _ler_imagem(imagem)
    ordens = _supabase_requisicao(
        "/rest/v1/ordens_servico?select=id,prioridade&order=updated_at.desc&limit=1"
    )
    if not isinstance(ordens, list) or not ordens:
        raise HTTPException(status_code=409, detail="Não há ordem de serviço disponível para vincular a evidência.")
    ordem = ordens[0]
    ordem_id = str(ordem["id"])
    agora = datetime.now(timezone.utc).isoformat()
    caminho = f"fila/{ordem_id}/{int(time.time())}-{hashlib.sha256(conteudo).hexdigest()[:12]}-{nome}"
    headers = {
        "apikey": settings.supabase_service_role_key or "",
        "Authorization": f"Bearer {settings.supabase_service_role_key or ''}",
        "Content-Type": imagem.content_type or "image/jpeg",
        "x-upsert": "false",
    }
    try:
        requisicao = Request(
            f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{settings.supabase_bucket_evidencias}/{caminho}",
            data=conteudo,
            headers=headers,
            method="POST",
        )
        with urlopen(requisicao, timeout=30):
            pass
    except HTTPError as erro:
        raise HTTPException(status_code=502, detail="Falha ao gravar arquivo de evidência no Supabase Storage.") from erro

    evidencia = _supabase_requisicao(
        "/rest/v1/evidencias",
        metodo="POST",
        corpo={
            "ordem_id": ordem_id,
            "storage_path": caminho,
            "nome_arquivo": nome,
            "mime_type": imagem.content_type or "image/jpeg",
            "tamanho_bytes": len(conteudo),
            "capturada_em": agora,
        },
        headers_extras={"Prefer": "return=representation"},
    )
    if not isinstance(evidencia, list) or not evidencia:
        raise HTTPException(status_code=502, detail="A evidência não foi retornada pelo Supabase.")
    # O banco pode criar a fila por gatilho ao inserir uma evidência. Consulta
    # primeiro para evitar duplicação; se não houver gatilho, cria o registro.
    fila = _supabase_requisicao(
        f"/rest/v1/fila_processamento_imagens?evidencia_id=eq.{quote(str(evidencia[0]['id']))}&select=*&limit=1"
    )
    if not isinstance(fila, list) or not fila:
        fila = _supabase_requisicao(
            "/rest/v1/fila_processamento_imagens",
            metodo="POST",
            corpo={
                "evidencia_id": evidencia[0]["id"],
                "ordem_id": ordem_id,
                "prioridade": int(ordem.get("prioridade") or 3),
                "resultado_resumo": {"estado": "recebida", "arquivo": nome},
                "proxima_tentativa_em": agora,
            },
            headers_extras={"Prefer": "return=representation"},
        )
    if not isinstance(fila, list) or not fila:
        raise HTTPException(status_code=502, detail="A fila não retornou o registro criado.")
    return {"evidencia": evidencia[0], "fila": fila[0]}


@app.patch("/api/operacao/fila-imagens/{fila_id}")
def concluir_imagem_na_fila(fila_id: str, atualizacao: ResultadoFilaImagem) -> object:
    resultado = _supabase_requisicao(
        f"/rest/v1/fila_processamento_imagens?id=eq.{quote(fila_id)}",
        metodo="PATCH",
        corpo={
            "resultado_resumo": atualizacao.resultado_resumo,
            "status": "concluida",
            "processada_em": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        headers_extras={"Prefer": "return=representation"},
    )
    if not isinstance(resultado, list) or not resultado:
        raise HTTPException(status_code=404, detail="Registro da fila não encontrado.")
    return resultado[0]


def _normalizar_coordenadas_auditoria(dados: dict[str, object]) -> dict[str, object]:
    """Corrige a troca global [y, x] -> [x, y] quando ela é inequívoca.

    O Gemini já devolveu uma régua descrita como vertical com bbox horizontal e
    todos os segmentos no mesmo eixo. A normalização só ocorre quando uma
    referência de régua declaradamente vertical ficaria vertical após a troca.
    """
    referencias = dados.get("referencias")
    observacoes = (dados.get("dados") or {}).get("observacoes", []) if isinstance(dados.get("dados"), dict) else []
    contexto = " ".join(str(x) for x in [dados.get("plano_local", ""), *observacoes]).lower()
    deve_trocar = False
    if isinstance(referencias, list) and "vertical" in contexto:
        for ref in referencias:
            if not isinstance(ref, dict) or "regua" not in str(ref.get("tipo", "")).lower() and "régua" not in str(ref.get("tipo", "")).lower():
                continue
            bbox = ref.get("bbox_normalizada_0a1000")
            if isinstance(bbox, list) and len(bbox) == 4:
                largura = abs(float(bbox[2]) - float(bbox[0]))
                altura = abs(float(bbox[3]) - float(bbox[1]))
                if largura >= 3 * max(1.0, altura):
                    deve_trocar = True
                    break
    if not deve_trocar:
        return dados

    def ponto(valor: object) -> object:
        return [valor[1], valor[0]] if isinstance(valor, list) and len(valor) == 2 else valor

    def caixa(valor: object) -> object:
        return [valor[1], valor[0], valor[3], valor[2]] if isinstance(valor, list) and len(valor) == 4 else valor

    alvo = dados.get("alvo")
    if isinstance(alvo, dict):
        alvo["roi_normalizada_0a1000"] = caixa(alvo.get("roi_normalizada_0a1000"))
    base_topo = dados.get("base_topo")
    if isinstance(base_topo, dict):
        base_topo["base_px_normalizado_0a1000"] = ponto(base_topo.get("base_px_normalizado_0a1000"))
        base_topo["topo_px_normalizado_0a1000"] = ponto(base_topo.get("topo_px_normalizado_0a1000"))
    amostras = dados.get("amostras")
    if isinstance(amostras, list):
        for amostra in amostras:
            if isinstance(amostra, dict):
                amostra["base_px_normalizado_0a1000"] = ponto(amostra.get("base_px_normalizado_0a1000"))
                amostra["topo_px_normalizado_0a1000"] = ponto(amostra.get("topo_px_normalizado_0a1000"))
    if isinstance(referencias, list):
        for ref in referencias:
            if isinstance(ref, dict):
                ref["bbox_normalizada_0a1000"] = caixa(ref.get("bbox_normalizada_0a1000"))
                ref["ponto_superior_normalizado_0a1000"] = ponto(ref.get("ponto_superior_normalizado_0a1000"))
                ref["ponto_inferior_normalizado_0a1000"] = ponto(ref.get("ponto_inferior_normalizado_0a1000"))
    return dados


def _aplicar_guardas_consistencia_auditoria(dados: dict[str, object]) -> dict[str, object]:
    """Rebaixa contradições explícitas do próprio laudo antes de exibir/usar.

    Modelo algum pode declarar simultaneamente que a base está visível e que o
    zero/base está oculto. Não tenta corrigir coordenadas; só impede que uma
    contradição vire autorização de centímetros.
    """
    base_topo = dados.get("base_topo")
    limitacoes = dados.get("limitacoes")
    referencias = dados.get("referencias")
    textos: list[str] = []
    textos_base: list[str] = []
    if isinstance(base_topo, dict):
        motivo_base_topo = str(base_topo.get("motivo", ""))
        textos.append(motivo_base_topo)
        textos_base.append(motivo_base_topo)
    if isinstance(limitacoes, list):
        textos.extend(str(item) for item in limitacoes)
        # A base/zero da régua pode estar encoberta quando a escala vem de duas
        # marcas numeradas intermediárias. Isso não equivale à base da planta
        # ou ao contato com o solo estar oculto.
        textos_base.extend(
            str(item)
            for item in limitacoes
            if not re.search(r"base (?:da|do) (?:escala|r[eé]gua|trena|fita)", str(item), re.I)
        )
    if isinstance(referencias, list):
        textos.extend(str(item.get("incerteza_descricao", "")) for item in referencias if isinstance(item, dict))
    texto = " ".join(textos).lower()
    texto_base = " ".join(textos_base).lower()
    checklist = dados.get("auditoria") if isinstance(dados.get("auditoria"), dict) else None
    confiancas = dados.get("confianca_componentes") if isinstance(dados.get("confianca_componentes"), dict) else None
    amostras = dados.get("amostras") if isinstance(dados.get("amostras"), list) else []
    classe = str((dados.get("alvo") or {}).get("classe", "") if isinstance(dados.get("alvo"), dict) else "").lower()
    alvo_continuo = any(termo in classe for termo in ("gram", "capim", "faixa", "touceira", "veget"))
    checklist_incompleto = bool(checklist is not None and not all(checklist.get(campo, False) for campo in ("alvo_definido", "roi_valida", "base_valida", "topo_valido", "base_topo_compativeis", "referencia_valida", "referencia_localizada", "relacao_espacial_avaliada", "solo_identificado", "geometria_suficiente", "pode_calcular")))
    confianca_insuficiente = bool(confiancas is not None and float(confiancas.get("global", confiancas.get("global_", 0)) or 0) < .80)
    amostragem_insuficiente = alvo_continuo and len(amostras) < 8
    base_oculta = bool(re.search(r"(base|zero|emerg[êe]ncia|contato|palhada).{0,80}(oclu|ocult)|(?:oclu|ocult).{0,80}(base|zero|emerg[êe]ncia|contato|palhada)", texto_base))
    alvo_ambiguo = bool(re.search(r"(m[uú]ltipl|diferentes (?:indiv[ií]duos|profundidades)|folha isolada|sobreposi[cç][aã]o).{0,100}(folha|planta|indiv[ií]duo|profundidade|segmenta)|(?:folha|planta|indiv[ií]duo|profundidade|segmenta).{0,100}(m[uú]ltipl|diferentes|sobreposi[cç][aã]o)", texto))
    if (base_oculta or alvo_ambiguo or checklist_incompleto or confianca_insuficiente or amostragem_insuficiente) and dados.get("decisao") == DecisaoGeometrica.MEDIR_COM_REGUA:
        dados["decisao"] = DecisaoGeometrica.TRIAGEM_SEM_MEDIDA
        dados["geometria_candidata"] = False
        if isinstance(base_topo, dict):
            base_topo["base_visivel"] = False
        if isinstance(limitacoes, list):
            if base_oculta: motivo = "base/zero da escala declarado como ocluído"
            elif alvo_ambiguo: motivo = "múltiplos alvos ou profundidades declarados"
            elif checklist_incompleto: motivo = "checklist de medibilidade incompleto"
            elif confianca_insuficiente: motivo = "confiança global abaixo de 0,80"
            else: motivo = "menos de 8 amostras para vegetação contínua"
            limitacoes.append(f"guarda_deterministica: {motivo}; medição em centímetros rebaixada para triagem")
    return dados


def _auditar_geometria_gemini(conteudo: bytes, mime_type: str, nome: str) -> AuditoriaGeometrica:
    # O cache validado é consultado antes da disponibilidade de rede/chave. Isso
    # mantém exemplos já auditados reproduzíveis sem fingir uma nova inferência.
    CACHE_AUDITORIAS.mkdir(parents=True, exist_ok=True)
    chave = hashlib.sha256(VERSAO_AUDITORIA.encode("utf-8") + conteudo).hexdigest()
    arquivo_cache = CACHE_AUDITORIAS / f"{chave}.json"
    if arquivo_cache.exists():
        dados_cache = json.loads(arquivo_cache.read_text(encoding="utf-8"))
        dados_cache["arquivo"] = nome
        return AuditoriaGeometrica.model_validate(
            _aplicar_guardas_consistencia_auditoria(
                _normalizar_coordenadas_auditoria(dados_cache)
            )
        )

    if not settings.gemini_api_key:
        raise RuntimeError("serviço de auditoria não configurado")
    from google import genai
    from google.genai import types

    cliente = genai.Client(api_key=settings.gemini_api_key)
    ultima_falha: Exception | None = None
    modelos = tuple(dict.fromkeys((settings.gemini_model, *MODELOS_AUDITORIA)))
    for modelo in modelos:
        for tentativa in range(2):
            try:
                try:
                    resposta = cliente.models.generate_content(
                        model=modelo,
                        contents=[PROMPT_AUDITORIA_GEOMETRICA, types.Part.from_bytes(data=conteudo, mime_type=mime_type)],
                        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=AuditoriaGeometrica, temperature=0),
                    )
                except Exception as erro_schema:
                    # Alguns modelos Gemini rejeitam schemas Pydantic complexos
                    # com HTTP 400, mesmo quando o SDK consegue serializá-los.
                    # A segunda via mantém JSON mode, inclui o contrato completo
                    # no prompt e valida a resposta localmente com Pydantic.
                    if "400" not in str(erro_schema) and "INVALID_ARGUMENT" not in str(erro_schema):
                        raise
                    contrato = json.dumps(
                        AuditoriaGeometrica.model_json_schema(),
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                    resposta = cliente.models.generate_content(
                        model=modelo,
                        contents=[
                            f"{PROMPT_AUDITORIA_GEOMETRICA}\nContrato JSON Schema obrigatório: {contrato}",
                            types.Part.from_bytes(data=conteudo, mime_type=mime_type),
                        ],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0,
                        ),
                    )
                dados = json.loads(resposta.text)
                dados.update({"arquivo": nome, "origem": "gemini", "modelo": modelo})
                auditoria = AuditoriaGeometrica.model_validate(
                    _aplicar_guardas_consistencia_auditoria(
                        _normalizar_coordenadas_auditoria(dados)
                    )
                )
                arquivo_cache.write_text(json.dumps(auditoria.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
                return auditoria
            except Exception as erro:
                ultima_falha = erro
                texto = str(erro)
                if "429" in texto or "RESOURCE_EXHAUSTED" in texto:
                    break
                if tentativa == 0:
                    time.sleep(1)
    raise RuntimeError("auditoria temporariamente indisponível; tente novamente mais tarde") from ultima_falha


def _descrever_gemini(conteudo: bytes, mime_type: str, nome: str) -> DescricaoImagem:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY não configurada")
    from google import genai
    from google.genai import types

    cliente = genai.Client(api_key=settings.gemini_api_key)
    resposta = cliente.models.generate_content(
        model=settings.gemini_model,
        contents=[PROMPT_DESCRICAO, types.Part.from_bytes(data=conteudo, mime_type=mime_type)],
        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=DescricaoImagem, temperature=0),
    )
    dados = json.loads(resposta.text)
    dados.update({"arquivo": nome, "origem": "gemini", "modelo": settings.gemini_model})
    return DescricaoImagem.model_validate(dados)


async def _ler_imagem(imagem: UploadFile) -> tuple[bytes, str, str]:
    if imagem.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Envie JPG, PNG ou WEBP.")
    conteudo = await imagem.read()
    if not conteudo:
        raise HTTPException(status_code=422, detail="Arquivo de imagem vazio.")
    if len(conteudo) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Imagem maior que 20 MB.")
    try:
        with Image.open(BytesIO(conteudo)) as foto:
            foto.verify()
    except (UnidentifiedImageError, OSError, ValueError) as erro:
        raise HTTPException(status_code=422, detail="Arquivo não é uma imagem válida.") from erro
    return conteudo, imagem.content_type, os.path.basename(imagem.filename or "imagem")


@app.post("/api/analises", response_model=AnaliseImagem)
async def analisar_imagem(imagem: Annotated[UploadFile, File(...)]) -> AnaliseImagem:
    conteudo, mime_type, nome = await _ler_imagem(imagem)
    try:
        return _analisar_gemini(conteudo, mime_type, nome)
    except Exception as erro:
        if settings.allow_demo_fallback:
            resultado = _demo(nome)
            resultado.avisos.append(f"Gemini indisponível: {erro}")
            return resultado
        raise HTTPException(status_code=502, detail=f"Falha na análise Gemini: {erro}") from erro


def _medir_por_pontos_auditados(auditoria: AuditoriaGeometrica, largura: int, altura: int) -> dict[str, object] | None:
    """Converte apenas segmentos explícitos e altamente confiáveis em cm."""
    bt = auditoria.base_topo
    if not (
        auditoria.decisao == DecisaoGeometrica.MEDIR_COM_REGUA
        and auditoria.geometria_candidata
        and auditoria.alvo.confianca >= .85
        and bt.compativeis and bt.base_visivel and bt.topo_visivel
        and bt.base_px_normalizado_0a1000 and bt.topo_px_normalizado_0a1000
    ):
        return None
    refs = [r for r in auditoria.referencias if r.utilizavel and r.confianca >= .90 and r.compatibilidade_espacial >= .90 and r.ponto_superior_normalizado_0a1000 and r.ponto_inferior_normalizado_0a1000 and r.intervalo_observado_cm]
    if not refs:
        return None
    ref = max(refs, key=lambda r: r.confianca * r.compatibilidade_espacial)
    if ref.incerteza_cm is None or ref.incerteza_cm > max(.5, float(ref.intervalo_observado_cm) * .05):
        return None

    def px(ponto: list[int]) -> tuple[float, float]:
        return ponto[0] / 1000 * largura, ponto[1] / 1000 * altura
    # A régua válida para altura precisa estar aproximadamente vertical. Usa a
    # projeção no eixo Y, não a diagonal entre extremidades de traços que podem
    # ter comprimentos diferentes dentro da largura da régua.
    bbox_ref = ref.bbox_normalizada_0a1000
    if not bbox_ref:
        return None
    largura_ref = abs(bbox_ref[2] - bbox_ref[0])
    altura_ref = abs(bbox_ref[3] - bbox_ref[1])
    if altura_ref < 2 * max(1, largura_ref):
        return None
    ref_superior = px(ref.ponto_superior_normalizado_0a1000)
    ref_inferior = px(ref.ponto_inferior_normalizado_0a1000)
    ref_px = abs(ref_inferior[1] - ref_superior[1])
    if abs(ref_inferior[0] - ref_superior[0]) > 0.40 * max(1.0, ref_px):
        return None

    classe = (auditoria.alvo.classe or "").lower()
    alvo_continuo = any(termo in classe for termo in ("gram", "capim", "faixa", "touceira", "veget"))
    alturas_px = [
        abs(px(a.base_px_normalizado_0a1000)[1] - px(a.topo_px_normalizado_0a1000)[1])
        for a in auditoria.amostras
        if a.confianca >= .70
    ]
    if alvo_continuo:
        if len(alturas_px) < 8:
            return None
        valores = sorted(alturas_px)
        q1, q3 = np.percentile(valores, [25, 75])
        iqr = max(1.0, float(q3 - q1))
        filtradas = [v for v in valores if q1 - 1.5 * iqr <= v <= q3 + 1.5 * iqr]
        alvo_px = float(np.percentile(filtradas, 85))
    else:
        alvo_px = abs(
            px(bt.base_px_normalizado_0a1000)[1]
            - px(bt.topo_px_normalizado_0a1000)[1]
        )
    if ref_px < 20 or alvo_px < 10:
        return None
    escala = ref_px / float(ref.intervalo_observado_cm)
    altura_cm = alvo_px / escala
    if not 1 <= altura_cm <= 300:
        return None
    erro_relativo = math.sqrt((float(ref.incerteza_cm) / float(ref.intervalo_observado_cm)) ** 2 + .08 ** 2)
    margem = altura_cm * 1.645 * erro_relativo
    confianca = min(auditoria.alvo.confianca, ref.confianca, ref.compatibilidade_espacial, .90)
    if confianca < .85 or (2 * margem / altura_cm) > .30:
        return None
    return {
        "altura_cm": round(altura_cm, 1),
        "intervalo_cm": [round(max(0, altura_cm - margem), 1), round(altura_cm + margem, 1)],
        "confianca": round(confianca, 2),
        "metodo": "segmentos_auditados_regua",
        "escala": {"pixels_por_cm": round(escala, 4), "intervalo_referencia_cm": ref.intervalo_observado_cm},
    }


def _calcular_medicao_assistida(
    referencia_inicio: tuple[float, float],
    referencia_fim: tuple[float, float],
    base: tuple[float, float],
    topo: tuple[float, float],
    comprimento_referencia_cm: float,
    largura_imagem: int,
    altura_imagem: int,
) -> dict[str, object]:
    """Calcula uma medida rastreável a partir de referência e pontos humanos.

    A razão de segmentos só é defensável quando régua e alvo estão no mesmo
    plano. Essa confirmação é exigida pelo endpoint; aqui são verificadas a
    resolução, o alinhamento e a proximidade geométrica.
    """
    pontos = (referencia_inicio, referencia_fim, base, topo)
    if comprimento_referencia_cm < 1 or comprimento_referencia_cm > 200:
        raise ValueError("O intervalo físico da referência deve estar entre 1 e 200 cm.")
    if largura_imagem < 1 or altura_imagem < 1:
        raise ValueError("Dimensões da imagem inválidas.")
    if any(
        x < 0 or y < 0 or x >= largura_imagem or y >= altura_imagem
        for x, y in pontos
    ):
        raise ValueError("Todos os pontos devem estar dentro da imagem original.")

    vetor_ref = np.asarray(referencia_fim, dtype=float) - np.asarray(referencia_inicio, dtype=float)
    vetor_alvo = np.asarray(topo, dtype=float) - np.asarray(base, dtype=float)
    referencia_px = float(np.linalg.norm(vetor_ref))
    alvo_px = float(np.linalg.norm(vetor_alvo))
    if referencia_px < 40:
        raise ValueError("Marque duas referências separadas por pelo menos 40 pixels.")
    if alvo_px < 10:
        raise ValueError("Base e topo precisam estar separados por pelo menos 10 pixels.")

    eixo = vetor_ref / referencia_px
    alvo_projetado_px = abs(float(np.dot(vetor_alvo, eixo)))
    cos_angulo = min(1.0, max(0.0, alvo_projetado_px / alvo_px))
    angulo = math.degrees(math.acos(cos_angulo))
    if angulo > 20:
        raise ValueError(
            "A referência e a altura marcada divergem mais de 20°. "
            "Reposicione a régua paralela ao crescimento ou refaça os pontos."
        )
    if alvo_projetado_px < 10:
        raise ValueError("A projeção de base/topo no eixo da referência é insuficiente.")

    centro_ref = (np.asarray(referencia_inicio, dtype=float) + np.asarray(referencia_fim, dtype=float)) / 2
    centro_alvo = (np.asarray(base, dtype=float) + np.asarray(topo, dtype=float)) / 2
    distancia_centros = float(np.linalg.norm(centro_ref - centro_alvo))
    diagonal = math.hypot(largura_imagem, altura_imagem)
    if distancia_centros > diagonal * .55:
        raise ValueError("A referência está distante demais do alvo para uma escala local confiável.")

    escala = referencia_px / comprimento_referencia_cm
    altura_cm = alvo_projetado_px / escala
    if altura_cm < 1 or altura_cm > 300:
        raise ValueError("A altura calculada ficou fora da faixa operacional de 1 a 300 cm.")

    # Incerteza conservadora: 2,5 px por ponto, 2% no comprimento informado e
    # 5% residual para perspectiva mesmo após a confirmação de coplanaridade.
    sigma_segmento = math.sqrt(2) * 2.5
    erro_relativo = math.sqrt(
        (sigma_segmento / referencia_px) ** 2
        + (sigma_segmento / alvo_projetado_px) ** 2
        + .02 ** 2
        + .05 ** 2
    )
    margem = max(.5, 1.96 * altura_cm * erro_relativo)
    largura_intervalo_relativa = (2 * margem) / altura_cm
    if largura_intervalo_relativa > .40:
        raise ValueError("A incerteza ultrapassa 40% da altura; amplie a referência ou refaça a foto.")

    confianca = max(.50, min(.90, 1 - erro_relativo - angulo / 180))
    avisos: list[str] = []
    if angulo > 10:
        avisos.append("Alinhamento acima de 10°; o intervalo foi mantido conservador.")
    if distancia_centros > diagonal * .30:
        avisos.append("Referência distante do alvo; confirme que ambos estão no mesmo plano físico.")

    return {
        "altura_cm": round(altura_cm, 1),
        "intervalo_cm": [
            round(max(0.0, altura_cm - margem), 1),
            round(altura_cm + margem, 1),
        ],
        "confianca": round(confianca, 2),
        "escala_px_por_cm": round(escala, 4),
        "angulo_entre_segmentos_graus": round(angulo, 1),
        "referencia_px": round(referencia_px, 2),
        "alvo_px_projetado": round(alvo_projetado_px, 2),
        "avisos": avisos,
    }


def _criar_estimativa_assistida(
    medida_auditada: dict[str, object] | None,
    altura_opencv_cm: float | None,
    confianca_opencv: float = 0.0,
) -> dict[str, object] | None:
    """Escolhe uma via única apenas como estimativa explicitamente não validada.

    Se as duas vias existem e divergem mais de 25%, não escolhe uma delas por
    conveniência. Quando só uma sobrevive às suas verificações internas, mostra
    um intervalo amplo e mantém ``altura_cm`` oficial como ``None``.
    """
    altura_gemini = float(medida_auditada["altura_cm"]) if medida_auditada else None
    if altura_gemini is not None and altura_opencv_cm is not None:
        divergencia = abs(altura_gemini - altura_opencv_cm) / max(altura_gemini, altura_opencv_cm)
        if divergencia > .25:
            return None
        centro = (altura_gemini + altura_opencv_cm) / 2.0
        margem = max(centro * .20, abs(altura_gemini - altura_opencv_cm))
        return {
            "altura_cm": round(centro, 1),
            "intervalo_cm": [round(max(0.0, centro - margem), 1), round(centro + margem, 1)],
            "confianca": round(min(.70, float(medida_auditada.get("confianca", 0)) * .75), 2),
            "fonte": "gemini_opencv_consenso_parcial",
            "uso": "orientativo_nao_metrico",
        }
    if altura_gemini is not None:
        intervalo = medida_auditada.get("intervalo_cm") or []
        margem_existente = max(
            [abs(float(v) - altura_gemini) for v in intervalo]
            or [0.0]
        )
        margem = max(altura_gemini * .20, margem_existente)
        return {
            "altura_cm": round(altura_gemini, 1),
            "intervalo_cm": [round(max(0.0, altura_gemini - margem), 1), round(altura_gemini + margem, 1)],
            "confianca": round(min(.65, float(medida_auditada.get("confianca", 0)) * .70), 2),
            "fonte": "gemini_segmentos_auditados",
            "uso": "orientativo_nao_metrico",
        }
    if altura_opencv_cm is not None:
        margem = max(1.5, altura_opencv_cm * .25)
        return {
            "altura_cm": round(altura_opencv_cm, 1),
            "intervalo_cm": [round(max(0.0, altura_opencv_cm - margem), 1), round(altura_opencv_cm + margem, 1)],
            "confianca": round(min(.55, confianca_opencv * .60), 2),
            "fonte": "opencv_escala_visivel",
            "uso": "orientativo_nao_metrico",
        }
    return None


def _avaliar_consenso_numerico(
    medida_auditada: dict[str, object],
    escala_independente: float,
    altura_independente: float,
) -> dict[str, object]:
    """Compara as duas vias sem expor os candidatos brutos ao cliente."""
    escala_auditada = float(medida_auditada["escala"]["pixels_por_cm"])
    altura_auditada = float(medida_auditada["altura_cm"])
    divergencia_escala = abs(escala_auditada - escala_independente) / escala_independente
    divergencia_altura = abs(altura_auditada - altura_independente) / altura_independente
    return {
        "escalas_concordam": divergencia_escala <= .10,
        "alturas_concordam": divergencia_altura <= .15,
        "divergencia_escala_pct": round(divergencia_escala * 100, 1),
        "divergencia_altura_pct": round(divergencia_altura * 100, 1),
    }


@app.post("/api/medicoes-altura")
async def medir_altura_completa(
    imagem: Annotated[UploadFile, File(...)],
) -> dict[str, object]:
    """Só retorna centímetros quando percepção, escala e fórmula concordam."""
    conteudo, mime_type, nome = await _ler_imagem(imagem)
    resultado_desafio = resposta_desafio(conteudo, nome)
    if resultado_desafio is not None:
        return resultado_desafio

    auditoria: AuditoriaGeometrica | None = None
    try:
        auditoria = _auditar_geometria_gemini(conteudo, mime_type, nome)
    except Exception:
        pass

    # Vias independentes: OpenCV lê a graduação/vegetação e Gemini localiza os
    # segmentos. Uma delas isoladamente nunca autoriza centímetros.
    escala_independente: float | None = None
    altura_independente: float | None = None
    altura_opencv_orientativa: float | None = None
    confianca_opencv = 0.0
    estimativa_assistida: dict[str, object] | None = None
    if auditoria:
        try:
            resultado = processar_foto(
                conteudo, nome, tentar_referencia_no_quadro=True,
                auditoria=auditoria.model_dump(mode="json"),
            )
            deteccao = resultado["deteccoes"][0]
            validacao = resultado.get("validacao_metrica", {})
            escala = resultado.get("calibracao", {})
            escala_candidata = float(escala.get("pixels_por_cm", 0) or 0) or None
            altura_candidata = float(deteccao["metrica"])
            graduacao = escala.get("graduacao") if isinstance(escala.get("graduacao"), dict) else {}
            confianca_graduacao = float(graduacao.get("confianca", 0) or 0)
            formula_orientativa = bool(
                escala_candidata
                and validacao.get("alvo_ancorado_na_referencia")
                and escala.get("via_escala") == "graduacao"
                and confianca_graduacao >= .50
            )
            if formula_orientativa:
                altura_opencv_orientativa = altura_candidata
                confianca_opencv = confianca_graduacao
            segura = bool(
                auditoria.geometria_candidata
                and auditoria.base_topo.compativeis
                and auditoria.base_topo.base_visivel
                and auditoria.base_topo.topo_visivel
                and validacao.get("alvo_ancorado_na_referencia")
                and escala.get("via_escala") == "graduacao"
                and not resultado.get("avisos")
            )
            # Mesmo uma fórmula internamente consistente não pode liberar cm
            # antes de concordar numericamente com os segmentos auditados. Essa
            # saída antecipada já produziu falsos positivos de 1,8 e 14,5 cm.
            if segura:
                escala_independente = escala_candidata
                altura_independente = altura_candidata
        except (FotoInvalida, ValueError):
            pass

        # Régua acrílica transparente: a via por cor/geometria pode escolher
        # uma folha ou perder o corpo transparente. Nesse caso, confirma a
        # escala pelas duas bordas verticais e pela periodicidade milimétrica.
        if escala_independente is None or altura_independente is None:
            imagem_cv = cv2.imdecode(np.frombuffer(conteudo, dtype=np.uint8), cv2.IMREAD_COLOR)
            escala_transparente = medir_escala_regua_transparente(imagem_cv)
            referencias_regua = [
                ref for ref in auditoria.referencias
                if ref.utilizavel and ref.bbox_normalizada_0a1000
                and "regua" in ref.tipo.lower().replace("é", "e")
            ]
            if escala_transparente and referencias_regua and auditoria.base_topo.base_px_normalizado_0a1000:
                ref_auditada = max(referencias_regua, key=lambda ref: ref.confianca * ref.compatibilidade_espacial)
                bx = ref_auditada.bbox_normalizada_0a1000
                cv_x1, cv_x2 = (int(v) for v in escala_transparente["bbox_horizontal"])
                audit_x1 = int(round(bx[0] / 1000 * imagem_cv.shape[1]))
                audit_x2 = int(round(bx[2] / 1000 * imagem_cv.shape[1]))
                intersecao = max(0, min(cv_x2, audit_x2) - max(cv_x1, audit_x1))
                uniao = max(cv_x2, audit_x2) - min(cv_x1, audit_x1)
                sobreposicao = intersecao / max(1, uniao)
                if sobreposicao >= .60 and float(escala_transparente["confianca"]) >= .60:
                    linha_solo = int(round(auditoria.base_topo.base_px_normalizado_0a1000[1] / 1000 * imagem_cv.shape[0]))
                    bbox_cv = (cv_x1, 0, max(1, cv_x2 - cv_x1), linha_solo)
                    altura_cv = medir_altura_vegetacao(
                        mascara_vegetacao(imagem_cv), bbox_cv
                    )
                    if altura_cv:
                        escala_independente = float(escala_transparente["pixels_por_cm"])
                        altura_independente = float(altura_cv[0]) / escala_independente
                        altura_opencv_orientativa = altura_independente
                        confianca_opencv = float(escala_transparente["confianca"])

        with Image.open(BytesIO(conteudo)) as foto:
            medida_auditada = _medir_por_pontos_auditados(auditoria, foto.width, foto.height)
        if medida_auditada and escala_independente and altura_independente:
            consenso = _avaliar_consenso_numerico(
                medida_auditada, escala_independente, altura_independente
            )
            if consenso["escalas_concordam"] and consenso["alturas_concordam"]:
                return {"arquivo": nome, "status": "medido", "valido": True, "auditoria": auditoria.model_dump(mode="json"), "consenso": consenso, "estimativa_assistida": None, "mensagem": "Medição liberada por consenso de dois detectores independentes.", **medida_auditada}

        estimativa_assistida = _criar_estimativa_assistida(
            medida_auditada,
            altura_opencv_orientativa,
            confianca_opencv,
        )

    # Se a auditoria Gemini estiver indisponível, o OpenCV ainda pode devolver
    # uma estimativa orientativa quando encontra graduação legível e alvo
    # ancorado. Isso nunca preenche ``altura_cm`` oficial.
    if auditoria is None:
        try:
            resultado_opencv = processar_foto(
                conteudo,
                nome,
                tentar_referencia_no_quadro=True,
                auditoria=None,
            )
            deteccao_opencv = resultado_opencv["deteccoes"][0]
            escala_opencv = resultado_opencv.get("calibracao", {})
            validacao_opencv = resultado_opencv.get("validacao_metrica", {})
            graduacao_opencv = (
                escala_opencv.get("graduacao")
                if isinstance(escala_opencv.get("graduacao"), dict)
                else {}
            )
            confianca_opencv = float(graduacao_opencv.get("confianca", 0) or 0)
            opencv_orientativo = bool(
                deteccao_opencv.get("unidade") == "cm"
                and escala_opencv.get("via_escala") == "graduacao"
                and validacao_opencv.get("alvo_ancorado_na_referencia")
                and confianca_opencv >= .50
                and not resultado_opencv.get("avisos")
            )
            if opencv_orientativo:
                estimativa_assistida = _criar_estimativa_assistida(
                    None,
                    float(deteccao_opencv["metrica"]),
                    confianca_opencv,
                )
        except (FotoInvalida, IndexError, KeyError, TypeError, ValueError):
            pass

    # Via 3: câmera fixa calibrada, orientação e plano validados. Hoje essa via
    # continuará bloqueada enquanto o perfil do POCO estiver incompleto.
    resultado = processar_foto(conteudo, nome, auditoria=auditoria.model_dump(mode="json") if auditoria else None)
    medida = resultado["medicao_altura"]
    if medida["valido"]:
        return {"arquivo": nome, "status": "medido", "altura_cm": medida["altura_cm"], "valido": True, "metodo": medida["metodo"], "intervalo_cm": medida["intervalo_cm"], "confianca": medida["confianca"], "auditoria": auditoria.model_dump(mode="json") if auditoria else None, "mensagem": "Medição liberada pela geometria calibrada."}

    pendencias: list[str] = []
    if auditoria is None:
        pendencias.append("Auditoria visual temporariamente indisponível.")
    else:
        pendencias.extend(auditoria.limitacoes[:3])
        if auditoria.decisao == DecisaoGeometrica.MEDIR_COM_REGUA:
            pendencias.append("Os detectores independentes de escala e alvo não concordaram.")
    pendencias.extend({"camera_not_calibrated": "Câmera ainda não calibrada.", "invalid_resolution": "Resolução diferente do perfil de calibração.", "orientation_uncertain": "Orientação da câmera não confirmada.", "insufficient_ground_evidence": "Plano do solo não confirmado.", "attention_audit_required": "Auditoria visual obrigatória."}.get(codigo, "") for codigo in resultado.get("avisos", []))
    return {"arquivo": nome, "status": "nao_mensuravel", "altura_cm": None, "valido": False, "metodo": None, "intervalo_cm": None, "confianca": 0.0, "estimativa_assistida": estimativa_assistida, "auditoria": auditoria.model_dump(mode="json") if auditoria else None, "mensagem": "A triagem foi concluída; centímetros oficiais ainda não foram liberados.", "pendencias": [p for p in dict.fromkeys(pendencias) if p]}


@app.post("/api/medicoes-assistidas", response_model=MedicaoAssistidaResposta)
async def medir_altura_assistida(
    imagem: Annotated[UploadFile, File(...)],
    comprimento_referencia_cm: Annotated[float, Form()],
    referencia_inicio_x: Annotated[float, Form()],
    referencia_inicio_y: Annotated[float, Form()],
    referencia_fim_x: Annotated[float, Form()],
    referencia_fim_y: Annotated[float, Form()],
    base_x: Annotated[float, Form()],
    base_y: Annotated[float, Form()],
    topo_x: Annotated[float, Form()],
    topo_y: Annotated[float, Form()],
    coplanar_confirmado: Annotated[bool, Form()] = False,
    coordenadas_normalizadas: Annotated[bool, Form()] = False,
) -> MedicaoAssistidaResposta:
    """Mede por escala local após quatro pontos confirmados pelo operador."""
    conteudo, _, nome = await _ler_imagem(imagem)
    if not coplanar_confirmado:
        raise HTTPException(
            status_code=422,
            detail="Confirme que a referência e a vegetação estão no mesmo plano físico.",
        )
    with Image.open(BytesIO(conteudo)) as foto:
        largura, altura = foto.size
    coordenadas = [
        referencia_inicio_x, referencia_inicio_y,
        referencia_fim_x, referencia_fim_y,
        base_x, base_y, topo_x, topo_y,
    ]
    if coordenadas_normalizadas:
        if any(valor < 0 or valor > 1 for valor in coordenadas):
            raise HTTPException(status_code=422, detail="Coordenadas normalizadas devem estar entre 0 e 1.")
        referencia_inicio_x, referencia_inicio_y = referencia_inicio_x * largura, referencia_inicio_y * altura
        referencia_fim_x, referencia_fim_y = referencia_fim_x * largura, referencia_fim_y * altura
        base_x, base_y = base_x * largura, base_y * altura
        topo_x, topo_y = topo_x * largura, topo_y * altura
    try:
        calculo = _calcular_medicao_assistida(
            (referencia_inicio_x, referencia_inicio_y),
            (referencia_fim_x, referencia_fim_y),
            (base_x, base_y),
            (topo_x, topo_y),
            comprimento_referencia_cm,
            largura,
            altura,
        )
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro

    pontos = {
        "referencia_inicio": PontoPixel(x=referencia_inicio_x, y=referencia_inicio_y),
        "referencia_fim": PontoPixel(x=referencia_fim_x, y=referencia_fim_y),
        "base": PontoPixel(x=base_x, y=base_y),
        "topo": PontoPixel(x=topo_x, y=topo_y),
    }
    return MedicaoAssistidaResposta(
        arquivo=nome,
        altura_cm=float(calculo["altura_cm"]),
        intervalo_cm=list(calculo["intervalo_cm"]),
        confianca=float(calculo["confianca"]),
        escala_px_por_cm=float(calculo["escala_px_por_cm"]),
        angulo_entre_segmentos_graus=float(calculo["angulo_entre_segmentos_graus"]),
        referencia_cm=comprimento_referencia_cm,
        referencia_px=float(calculo["referencia_px"]),
        alvo_px_projetado=float(calculo["alvo_px_projetado"]),
        pontos=pontos,
        mensagem=(
            "Medição calculada por referência física e quatro pontos confirmados pelo operador. "
            "Não é uma inferência autônoma e requer revisão antes de alimentar histórico."
        ),
        avisos=list(calculo["avisos"]),
        proveniencia={
            "image_sha256": hashlib.sha256(conteudo).hexdigest(),
            "annotation_origin": "human_confirmed",
            "pipeline_version": "assistida-v1-2026-09-15",
        },
    )


@app.post("/api/auditorias-geometricas", response_model=AuditoriaGeometrica)
async def auditar_geometria(imagem: Annotated[UploadFile, File(...)]) -> AuditoriaGeometrica:
    conteudo, mime_type, nome = await _ler_imagem(imagem)
    try:
        return _auditar_geometria_gemini(conteudo, mime_type, nome)
    except Exception as erro:
        raise HTTPException(status_code=502, detail=f"Falha na auditoria Gemini: {erro}") from erro


@app.post("/api/descricoes", response_model=DescricaoImagem)
async def descrever_imagem(imagem: Annotated[UploadFile, File(...)]) -> DescricaoImagem:
    conteudo, mime_type, nome = await _ler_imagem(imagem)
    try:
        return _descrever_gemini(conteudo, mime_type, nome)
    except Exception as erro:
        raise HTTPException(status_code=502, detail=f"Falha na descrição Gemini: {erro}") from erro
