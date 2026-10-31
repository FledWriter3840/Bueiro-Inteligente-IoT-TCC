import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Protocol, runtime_checkable

import cv2
import joblib
import numpy as np
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CLASSES_RESIDUOS = {
    "plastico": "Plástico",
    "papel_papelao": "Papel/papelão",
    "metal": "Metal",
    "vidro": "Vidro",
    "organico": "Orgânico",
    "sem_residuo": "Sem resíduo",
}
EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png"}
TAMANHO_IMAGEM = (128, 128)
LIMIAR_CONFIANCA = float(os.getenv("RESIDUOS_CONFIDENCE_THRESHOLD", "0.60"))
if not 0.0 <= LIMIAR_CONFIANCA <= 1.0:
    raise ValueError("RESIDUOS_CONFIDENCE_THRESHOLD deve estar entre 0 e 1.")

CAMINHO_MODELO = Path(
    os.getenv(
        "RESIDUOS_MODEL_PATH",
        str(Path(__file__).with_name("residuos_modelo.joblib")),
    )
)


@runtime_checkable
class ModeloResiduos(Protocol):
    @property
    def classes_(self) -> np.ndarray: ...

    def predict_proba(self, X: np.ndarray) -> np.ndarray: ...


class ImagemInvalidaError(ValueError):
    """Indica que os bytes recebidos não podem ser decodificados como imagem."""


@dataclass(frozen=True)
class ResultadoAnaliseResiduo:
    tipo_residuo: str | None
    confianca: float | None
    status: str | None

    @property
    def possivel_interferencia_sensor(self) -> bool | None:
        if self.status != "Analisada" or self.tipo_residuo is None:
            return None
        return self.tipo_residuo != CLASSES_RESIDUOS["sem_residuo"]


def extrair_caracteristicas(imagem: bytes) -> np.ndarray:
    """Extrai forma (HOG) e histograma de cor de uma imagem para classificação."""
    buffer = np.frombuffer(imagem, dtype=np.uint8)
    imagem_bgr = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if imagem_bgr is None:
        raise ImagemInvalidaError("Não foi possível decodificar a imagem.")

    imagem_bgr = cv2.resize(imagem_bgr, TAMANHO_IMAGEM)
    imagem_cinza = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY)
    descritor_hog = cv2.HOGDescriptor(
        TAMANHO_IMAGEM,
        (16, 16),
        (8, 8),
        (8, 8),
        9,
    )
    caracteristicas_forma = descritor_hog.compute(imagem_cinza).flatten()

    imagem_hsv = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2HSV)
    caracteristicas_cor = []
    for canal, faixa in enumerate(((0, 180), (0, 256), (0, 256))):
        histograma = cv2.calcHist(
            [imagem_hsv],
            [canal],
            None,
            [16],
            list(faixa),
        )
        cv2.normalize(histograma, histograma)
        caracteristicas_cor.extend(histograma.flatten())

    return np.concatenate((caracteristicas_forma, caracteristicas_cor)).astype(
        np.float32
    )


@lru_cache(maxsize=4)
def _carregar_modelo_cacheado(
    caminho: str,
    data_modificacao_ns: int,
) -> ModeloResiduos:
    del data_modificacao_ns
    artefato = joblib.load(caminho)
    if (
        not isinstance(artefato, dict)
        or artefato.get("versao") != 1
        or not isinstance(artefato.get("modelo"), ModeloResiduos)
        or set(artefato.get("classes", [])) != set(CLASSES_RESIDUOS)
    ):
        raise ValueError(f"Modelo de resíduos inválido: {caminho}")
    return artefato["modelo"]


def carregar_modelo(caminho: Path = CAMINHO_MODELO) -> ModeloResiduos | None:
    if not caminho.is_file():
        return None
    return _carregar_modelo_cacheado(
        str(caminho.resolve()),
        caminho.stat().st_mtime_ns,
    )


def analisar_residuo(
    imagem: bytes,
    caminho_modelo: Path = CAMINHO_MODELO,
) -> ResultadoAnaliseResiduo:
    modelo = carregar_modelo(caminho_modelo)
    if modelo is None:
        logger.warning(
            "Classificação de resíduos indisponível: modelo local não encontrado em %s.",
            caminho_modelo,
        )
        return ResultadoAnaliseResiduo(None, None, "Sem modelo")

    caracteristicas = extrair_caracteristicas(imagem).reshape(1, -1)
    probabilidades = modelo.predict_proba(caracteristicas)[0]
    indice = int(np.argmax(probabilidades))
    confianca = float(probabilidades[indice])
    classe = str(modelo.classes_[indice])

    if classe not in CLASSES_RESIDUOS:
        raise ValueError(f"O modelo retornou uma classe desconhecida: {classe}")
    if confianca < LIMIAR_CONFIANCA:
        return ResultadoAnaliseResiduo(
            "Indefinido",
            round(confianca, 4),
            "Baixa confiança",
        )
    return ResultadoAnaliseResiduo(
        CLASSES_RESIDUOS[classe],
        round(confianca, 4),
        "Analisada",
    )
