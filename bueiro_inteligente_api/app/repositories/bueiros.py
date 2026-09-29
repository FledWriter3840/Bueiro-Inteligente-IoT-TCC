import json
from pathlib import Path


class BueiroStorageError(Exception):
    pass


class BueiroJsonRepository:
    def __init__(self, path: Path):
        self.path = path

    def listar_adicionados(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            registros = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise BueiroStorageError(
                "Não foi possível ler os bueiros cadastrados."
            ) from exc
        return registros if isinstance(registros, list) else []

    def adicionar(self, registro: dict) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            registros = self.listar_adicionados()
            registros.append(registro)
            self.path.write_text(
                json.dumps(registros, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise BueiroStorageError(
                "Não foi possível salvar o novo bueiro."
            ) from exc