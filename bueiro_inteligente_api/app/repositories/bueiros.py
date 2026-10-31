import json
from pathlib import Path


class BueiroStorageError(Exception):
    pass


class BueiroJsonRepository:
    """Persiste em JSON os bueiros adicionados ao inventário."""

    def __init__(self, path: Path) -> None:
        """Define o caminho do arquivo de persistência."""
        self.path = path

    def listar_adicionados(self) -> list[dict]:
        """Carrega os registros de bueiros persistidos."""
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
        """Adiciona um registro ao arquivo JSON."""
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

    def remover(self, identificador: str) -> bool:
        """Remove um bueiro cadastrado localmente pelo identificador."""
        try:
            registros = self.listar_adicionados()
            atualizados = [
                registro for registro in registros
                if registro.get("id") != identificador
            ]
            if len(atualizados) == len(registros):
                return False
            self.path.write_text(
                json.dumps(atualizados, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise BueiroStorageError(
                "Não foi possível remover o bueiro cadastrado."
            ) from exc
        return True