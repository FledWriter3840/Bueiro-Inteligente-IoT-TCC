import logging
import os
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services.monitoramento import (
    calcular_nivel_percentual,
    calcular_status_bueiro,
)

router = APIRouter(tags=["Aplicativo móvel"])
logger = logging.getLogger(__name__)
UPLOADS_DIR = Path(
    os.getenv("UPLOADS_DIR")
    or str(Path(__file__).resolve().parents[1] / "uploads")
)
MAX_FOTO_BYTES = 5 * 1024 * 1024
GRAVIDADES = ("leve", "moderada", "grave")
STATUS_OCORRENCIA = ("aberta", "em_analise", "resolvida")
STATUS_BUEIRO = ("livre", "atencao", "critico")


def _jpeg_valido(conteudo: bytes) -> bool:
    return conteudo.startswith(b"\xff\xd8\xff") and conteudo.endswith(b"\xff\xd9")


def _png_valido(conteudo: bytes) -> bool:
    return conteudo.startswith(b"\x89PNG\r\n\x1a\n")


def _webp_valido(conteudo: bytes) -> bool:
    return conteudo.startswith(b"RIFF") and conteudo[8:12] == b"WEBP"


TIPOS_IMAGEM = {
    "image/jpeg": (".jpg", _jpeg_valido),
    "image/png": (".png", _png_valido),
    "image/webp": (".webp", _webp_valido),
}


@router.post(
    "/ocorrencias",
    status_code=201,
    response_model=schemas.OcorrenciaOut,
    summary="Registra uma denúncia de alagamento",
    description=(
        "Cria uma ocorrência com coordenadas WGS84. A gravidade aceita "
        "leve, moderada ou grave; por padrão, é moderada."
    ),
)
def criar_ocorrencia(
    dados: schemas.OcorrenciaCreate,
    db: Session = Depends(get_db),
) -> models.Ocorrencia:
    ocorrencia = models.Ocorrencia(
        descricao=dados.descricao,
        latitude=dados.latitude,
        longitude=dados.longitude,
        gravidade=dados.gravidade,
        status="aberta",
    )
    try:
        db.add(ocorrencia)
        db.commit()
        db.refresh(ocorrencia)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Falha ao criar ocorrência de alagamento.")
        raise HTTPException(
            status_code=500,
            detail="Não foi possível registrar a ocorrência.",
        ) from exc
    return ocorrencia


@router.post(
    "/ocorrencias/{ocorrencia_id}/foto",
    status_code=201,
    response_model=schemas.OcorrenciaOut,
    summary="Anexa uma foto à denúncia",
    description=(
        "Recebe JPEG, PNG ou WebP de até 5 MB e armazena em `uploads/`, "
        "disponibilizando a imagem em `/uploads`."
    ),
)
async def anexar_foto_ocorrencia(
    ocorrencia_id: int,
    foto: UploadFile = File(..., description="Imagem JPEG, PNG ou WebP (máximo 5 MB)."),
    db: Session = Depends(get_db),
) -> models.Ocorrencia:
    ocorrencia = db.get(models.Ocorrencia, ocorrencia_id)
    if ocorrencia is None:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada.")

    tipo = (foto.content_type or "").lower()
    formato = TIPOS_IMAGEM.get(tipo)
    if formato is None:
        raise HTTPException(
            status_code=415,
            detail="Envie uma imagem JPEG, PNG ou WebP.",
        )

    conteudo = await foto.read(MAX_FOTO_BYTES + 1)
    await foto.close()
    if len(conteudo) > MAX_FOTO_BYTES:
        raise HTTPException(status_code=413, detail="A imagem excede o limite de 5 MB.")
    if not conteudo or not formato[1](conteudo):
        raise HTTPException(
            status_code=400,
            detail="O conteúdo não corresponde ao formato informado.",
        )

    nome_arquivo = f"{uuid.uuid4().hex}{formato[0]}"
    caminho = UPLOADS_DIR / nome_arquivo
    try:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        caminho.write_bytes(conteudo)
    except OSError as exc:
        logger.exception("Falha ao gravar foto da ocorrência %s.", ocorrencia_id)
        raise HTTPException(
            status_code=500,
            detail="Não foi possível salvar a foto.",
        ) from exc

    ocorrencia.foto_url = f"/uploads/{nome_arquivo}"
    try:
        db.commit()
        db.refresh(ocorrencia)
    except SQLAlchemyError as exc:
        db.rollback()
        try:
            caminho.unlink(missing_ok=True)
        except OSError:
            logger.exception("Falha ao remover foto após erro ao salvar ocorrência.")
        logger.exception("Falha ao associar foto à ocorrência %s.", ocorrencia_id)
        raise HTTPException(
            status_code=500,
            detail="Não foi possível associar a foto à ocorrência.",
        ) from exc
    return ocorrencia


@router.get(
    "/ocorrencias",
    response_model=list[schemas.OcorrenciaOut],
    summary="Lista denúncias de alagamento",
    description="Permite filtrar a lista por status e gravidade.",
)
def listar_ocorrencias(
    status: Literal["aberta", "em_analise", "resolvida"] | None = Query(default=None),
    gravidade: Literal["leve", "moderada", "grave"] | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[models.Ocorrencia]:
    consulta = db.query(models.Ocorrencia)
    if status is not None:
        consulta = consulta.filter(models.Ocorrencia.status == status)
    if gravidade is not None:
        consulta = consulta.filter(models.Ocorrencia.gravidade == gravidade)
    return consulta.order_by(
        models.Ocorrencia.criado_em.desc(),
        models.Ocorrencia.id.desc(),
    ).all()


@router.patch(
    "/ocorrencias/{ocorrencia_id}",
    response_model=schemas.OcorrenciaOut,
    summary="Atualiza o status da denúncia",
    description="Operadores podem definir aberta, em_analise ou resolvida.",
)
def atualizar_status_ocorrencia(
    ocorrencia_id: int,
    dados: schemas.OcorrenciaStatusUpdate,
    db: Session = Depends(get_db),
) -> models.Ocorrencia:
    ocorrencia = db.get(models.Ocorrencia, ocorrencia_id)
    if ocorrencia is None:
        raise HTTPException(status_code=404, detail="Ocorrência não encontrada.")
    ocorrencia.status = dados.status
    try:
        db.commit()
        db.refresh(ocorrencia)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Falha ao atualizar a ocorrência %s.", ocorrencia_id)
        raise HTTPException(
            status_code=500,
            detail="Não foi possível atualizar a ocorrência.",
        ) from exc
    return ocorrencia


@router.get(
    "/resumo",
    response_model=schemas.ResumoOut,
    summary="Retorna os totais do sistema",
    description="Agrupa os bueiros por nível e as ocorrências por status e gravidade.",
)
def obter_resumo(db: Session = Depends(get_db)) -> dict[str, dict[str, int]]:
    bueiros = {status: 0 for status in STATUS_BUEIRO}
    sensores = db.query(models.Sensor).all()
    for sensor in sensores:
        leitura = (
            db.query(models.LeituraSensor)
            .filter(models.LeituraSensor.id_sensor == sensor.id_sensor)
            .order_by(
                models.LeituraSensor.data_hora.desc(),
                models.LeituraSensor.id_leitura.desc(),
            )
            .first()
        )
        nivel = (
            calcular_nivel_percentual(leitura.valor_leitura, leitura.unidade_medida)
            if leitura is not None
            else 0.0
        )
        bueiros[calcular_status_bueiro(nivel)] += 1

    por_status = {status: 0 for status in STATUS_OCORRENCIA}
    por_gravidade = {gravidade: 0 for gravidade in GRAVIDADES}
    status_rows = (
        db.query(models.Ocorrencia.status, func.count(models.Ocorrencia.id))
        .group_by(models.Ocorrencia.status)
        .all()
    )
    gravidade_rows = (
        db.query(models.Ocorrencia.gravidade, func.count(models.Ocorrencia.id))
        .group_by(models.Ocorrencia.gravidade)
        .all()
    )
    por_status.update({status: total for status, total in status_rows})
    por_gravidade.update({gravidade: total for gravidade, total in gravidade_rows})
    return {
        "bueiros_por_status": bueiros,
        "ocorrencias_por_status": por_status,
        "ocorrencias_por_gravidade": por_gravidade,
    }


@router.get(
    "/saude",
    summary="Verifica a disponibilidade da API",
    description="Healthcheck de disponibilidade HTTP para o aplicativo móvel.",
)
def verificar_saude() -> dict[str, str]:
    return {"status": "ok"}
