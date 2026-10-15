from sqlalchemy.orm import Session

from .. import schemas
from ..ai_predictor import PrevisorEntupimentoIA
from ..config import BUEIRO_LATITUDE, BUEIRO_LONGITUDE, LIMIAR_CRITICO_CM
from ..dados_externos import dados_geograficos, historico_alagamentos, uso_do_solo
from ..enums import NivelRisco
from ..ml.predictor import PrevisorEntupimentoML
from ..weather_service import obter_dados_climaticos_dict


def simular_cenario_chuva(
    cenario: schemas.CenarioSimulacaoRequest,
) -> dict[str, object]:
    """Gera projeções de risco para o cenário informado."""
    projecoes = []
    for minuto in range(cenario.minutos_simulacao + 1):
        distancia_min = max(
            0.0,
            cenario.distancia_inicial_cm
            - cenario.velocidade_subida_cm_min * minuto,
        )

        if distancia_min <= LIMIAR_CRITICO_CM:
            probabilidade = 0.95
            risco = NivelRisco.CRITICO
        elif distancia_min <= 50.0:
            probabilidade = 0.75
            risco = NivelRisco.ALTO
        elif distancia_min <= 150.0:
            probabilidade = 0.45
            risco = NivelRisco.MEDIO
        else:
            probabilidade = 0.15
            risco = NivelRisco.BAIXO

        projecoes.append({
            "minuto": minuto,
            "distancia_prevista_cm": round(distancia_min, 1),
            "probabilidade_alagamento": probabilidade,
            "nivel_risco": risco.value,
        })

    return {
        "cenario": {
            "distancia_inicial_cm": cenario.distancia_inicial_cm,
            "velocidade_subida_cm_min": cenario.velocidade_subida_cm_min,
            "tempo_total_simulado_min": cenario.minutos_simulacao,
        },
        "projecoes": projecoes,
    }


def comparar_motores_ia(
    db: Session,
    id_sensor: int,
    persistir: bool,
    lat: float,
    lon: float,
) -> schemas.ComparativoIAResult:
    """Compara os resultados dos motores multivariado e ML."""
    resultado_regressao = PrevisorEntupimentoIA.analisar_e_prever(
        db=db,
        id_sensor=id_sensor,
        persistir=persistir,
        lat=lat,
        lon=lon,
    )
    resultado_ml = PrevisorEntupimentoML.prever(
        db=db,
        id_sensor=id_sensor,
        persistir=False,
    )
    convergencia = resultado_regressao.nivel_risco == resultado_ml.nivel_risco

    if convergencia:
        observacao = (
            f"Os dois motores concordam: risco '{resultado_regressao.nivel_risco}'. "
            "Isso reforça a confiabilidade do diagnóstico."
        )
    else:
        observacao = (
            f"Divergência entre os motores: regressão indica "
            f"'{resultado_regressao.nivel_risco}', Machine Learning indica "
            f"'{resultado_ml.nivel_risco}'. Recomenda-se monitoramento contínuo "
            "até a próxima leitura confirmar a tendência."
        )

    return schemas.ComparativoIAResult(
        motor_regressao=resultado_regressao,
        motor_machine_learning=resultado_ml,
        convergencia=convergencia,
        observacao=observacao,
    )


def obter_topografia_atual(lat: float, lon: float) -> dict[str, object]:
    """Converte o perfil topográfico para o contrato da API."""
    from ..topography_service import topografia_service

    perfil = topografia_service.obter_perfil_completo(lat=lat, lon=lon)
    return {
        "latitude": lat,
        "longitude": lon,
        "altitude_metros": perfil.altitude_metros,
        "eh_fundo_de_vale": perfil.eh_fundo_de_vale,
        "classificacao_risco": perfil.classificacao_risco,
        "declividade_pct": perfil.declividade_pct,
        "dataset_origem": perfil.dataset_origem,
        "disponivel": perfil.disponivel,
        "detalhes_analise": perfil.detalhes_analise,
    }


def listar_fontes_dados() -> dict[str, object]:
    """Resume disponibilidade das seis fontes de dados da análise."""
    perfil_solo = uso_do_solo.obter_perfil(
        lat=BUEIRO_LATITUDE,
        lon=BUEIRO_LONGITUDE,
    )
    clima_disponivel = obter_dados_climaticos_dict().get("disponivel", False)
    uso_solo_ativo = perfil_solo.disponivel

    return {
        "fontes": [
            {
                "nome": "Sensor IoT (Telemetria)",
                "status": "Ativo",
                "descricao": "Dados do sensor ultrassônico e compactação via banco de dados MySQL.",
            },
            {
                "nome": "OpenWeatherMap (Clima)",
                "status": "Ativo" if clima_disponivel else "Indisponível (configurar OPENWEATHER_API_KEY)",
                "descricao": "Dados climáticos em tempo real: chuva, umidade, vento, previsão.",
            },
            {
                "nome": "Dados Temporais (datetime)",
                "status": "Ativo",
                "descricao": "Features derivadas do horário: estação do ano, horário de pico, feriados SP.",
            },
            {
                "nome": "Histórico de Alagamentos (CGE SP / ARTESP)",
                "status": "Ativo" if historico_alagamentos.disponivel else "Esqueleto (aguardando dataset)",
                "descricao": "Pontos recorrentes de alagamento, erosão e manchas de inundação.",
            },
            {
                "nome": "Topografia / Relevo (Copernicus DEM GLO-30)",
                "status": "Ativo" if dados_geograficos.disponivel else "Indisponível (configurar OPENTOPOGRAPHY_API_KEY)",
                "descricao": "Altitude precisa, fundo de vale e declividade via Copernicus DEM 30m.",
            },
            {
                "nome": "Uso do Solo (Entorno)",
                "status": "Ativo" if uso_solo_ativo else "Indisponível (Overpass e dataset local)",
                "descricao": "Tipo de via, proximidade com feiras/parques, impermeabilização.",
            },
        ],
        "total_ativas": sum([
            True,
            clima_disponivel,
            True,
            historico_alagamentos.disponivel,
            dados_geograficos.disponivel,
            uso_solo_ativo,
        ]),
        "total_fontes": 6,
    }
