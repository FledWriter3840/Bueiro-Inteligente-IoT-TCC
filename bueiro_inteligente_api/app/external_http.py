from typing import Any

import requests


class ExternalHttpClient:
    """Oferece uma interface JSON comum para provedores externos."""

    @staticmethod
    def get_json(
        url: str,
        *,
        timeout: int,
        params: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Executa GET, valida o status HTTP e retorna o JSON."""
        resposta = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=timeout,
        )
        resposta.raise_for_status()
        return resposta.json()

    @staticmethod
    def post_json(
        url: str,
        *,
        timeout: int,
        data: str,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Executa POST, valida o status HTTP e retorna o JSON."""
        resposta = requests.post(
            url,
            data=data,
            headers=headers,
            timeout=timeout,
        )
        resposta.raise_for_status()
        return resposta.json()


external_http_client = ExternalHttpClient()
