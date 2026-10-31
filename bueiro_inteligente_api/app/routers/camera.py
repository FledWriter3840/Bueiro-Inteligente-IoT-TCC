import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..ml.residuos import (
    ImagemInvalidaError,
    ResultadoAnaliseResiduo,
    analisar_residuo,
)

router = APIRouter(prefix="/camera", tags=["Camera"])
logger = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 2 * 1024 * 1024
IMAGE_STORAGE_DIR = Path(
    os.getenv(
        "IMAGE_STORAGE_DIR",
        str(Path(__file__).resolve().parents[1] / "storage" / "images"),
    )
)


def _serializar_imagem(
    imagem: models.RegistroImagem,
) -> dict[str, int | str | float | bool | None]:
    analise = ResultadoAnaliseResiduo(
        imagem.tipo_residuo,
        imagem.confianca_ia,
        imagem.status_analise,
    )
    return {
        "id_imagem": imagem.id_imagem,
        "caminho_imagem": imagem.caminho_imagem,
        "data_hora": imagem.data_hora.isoformat() if imagem.data_hora else None,
        "id_camera": imagem.id_camera,
        "id_leitura": imagem.id_leitura,
        "tipo_residuo": imagem.tipo_residuo,
        "confianca_ia": imagem.confianca_ia,
        "status_analise": imagem.status_analise,
        "possivel_interferencia_sensor": analise.possivel_interferencia_sensor,
        "url_imagem": f"/camera/imagens/{imagem.id_imagem}",
    }


@router.get("/imagens")
def listar_imagens(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[dict[str, int | str | float | bool | None]]:
    """Lista as imagens mais recentes, incluindo a rota para visualizá-las."""
    imagens = (
        db.query(models.RegistroImagem)
        .order_by(models.RegistroImagem.data_hora.desc())
        .limit(limit)
        .all()
    )
    return [_serializar_imagem(imagem) for imagem in imagens]


@router.post("/imagens", status_code=201)
async def registrar_imagem(
    request: Request,
    camera_id: int = Query(default=1, gt=0),
    id_leitura: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
) -> dict[str, int | str | float | bool | None]:
    """Recebe uma foto JPEG, guarda o arquivo e registra seus metadados."""
    content_type = request.headers.get("content-type", "").split(";", maxsplit=1)[0]
    if content_type.strip().lower() != "image/jpeg":
        raise HTTPException(status_code=415, detail="Envie a imagem no formato JPEG.")

    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Imagem excede o limite de 2 MB.")

    image = bytearray()
    async for chunk in request.stream():
        image.extend(chunk)
        if len(image) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="Imagem excede o limite de 2 MB.")

    if len(image) < 4 or image[:3] != b"\xff\xd8\xff" or image[-2:] != b"\xff\xd9":
        raise HTTPException(status_code=400, detail="O conteúdo recebido não é um JPEG válido.")

    try:
        analise: ResultadoAnaliseResiduo = analisar_residuo(bytes(image))
    except ImagemInvalidaError as exc:
        raise HTTPException(
            status_code=400,
            detail="Não foi possível processar a imagem JPEG recebida.",
        ) from exc

    if id_leitura is not None and db.get(models.LeituraSensor, id_leitura) is None:
        raise HTTPException(status_code=404, detail="Leitura do sensor não encontrada.")

    camera = db.get(models.Camera, camera_id)
    if camera is None:
        camera = models.Camera(
            id_camera=camera_id,
            status_camera="Ativa",
            resolucao="VGA",
        )
        db.add(camera)

    filename = f"{uuid.uuid4().hex}.jpg"
    image_path = IMAGE_STORAGE_DIR / filename
    image_record = models.RegistroImagem(
        caminho_imagem=f"images/{filename}",
        id_leitura=id_leitura,
        id_camera=camera_id,
        tipo_residuo=analise.tipo_residuo,
        confianca_ia=analise.confianca,
        status_analise=analise.status,
    )

    try:
        IMAGE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        image_path.write_bytes(image)
        db.add(image_record)
        db.commit()
        db.refresh(image_record)
    except Exception:
        db.rollback()
        try:
            image_path.unlink(missing_ok=True)
        except OSError:
            logger.exception("Falha ao remover arquivo de imagem após erro no banco.")
        logger.exception("Falha ao persistir imagem da câmera %s.", camera_id)
        raise HTTPException(
            status_code=500,
            detail="Não foi possível salvar a imagem.",
        )

    return _serializar_imagem(image_record)


@router.get("/imagens/{id_imagem}")
def obter_imagem(
    id_imagem: int,
    db: Session = Depends(get_db),
) -> FileResponse:
    """Retorna a imagem armazenada para visualização no navegador."""
    image_record = db.get(models.RegistroImagem, id_imagem)
    if image_record is None:
        raise HTTPException(status_code=404, detail="Imagem não encontrada.")

    image_path = IMAGE_STORAGE_DIR / Path(image_record.caminho_imagem).name
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo da imagem não encontrado.")

    return FileResponse(image_path, media_type="image/jpeg")
