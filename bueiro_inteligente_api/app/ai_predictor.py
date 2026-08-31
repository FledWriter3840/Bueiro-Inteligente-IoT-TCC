"""
Motor de Inteligência Artificial Preditiva Multivariada
para Previsão de Entupimentos, Risco de Alagamento e
Necessidade de Limpeza Preventiva (RF15 / UC09).

Agrega 6 dimensões de dados em um score ponderado:
  1. Sensor do Bueiro (telemetria IoT)      — peso 0.30
  2. Dados Climáticos (OpenWeatherMap)       — peso 0.25
  3. Histórico de Alagamentos (CGE SP)       — peso 0.15
  4. Dados Temporais / Sazonais              — peso 0.10
  5. Dados Geográficos / Topográficos        — peso 0.10
  6. Dados de Uso do Solo / Entorno          — peso 0.10

O resultado final inclui:
  - Probabilidade de entupimento (0-1)
  - Nível de risco (Baixo / Médio / Alto / Crítico)
  - Recomendação de ação e urgência de limpeza
  - Detalhamento do score por dimensão
"""

from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from . import models, schemas
from .config import (
    BUEIRO_LATITUDE,
    BUEIRO_LONGITUDE,
    PESO_SENSOR,
    PESO_CLIMA,
    PESO_TEMPORAL,
    PESO_HISTORICO_ALAGAMENTO,
    PESO_GEOGRAFICO,
    PESO_USO_SOLO,
)
from .weather_service import obter_dados_climaticos, DadosClimaticos
from .dados_temporais import extrair_dados_temporais, DadosTemporais
from .dados_externos import (
    historico_alagamentos,
    dados_geograficos,
    uso_do_solo,
    ScoreAlagamentoHistorico,
    PerfilTopografico,
    PerfilUsoSolo,
)


class PrevisorEntupimentoIA:
    """
    Motor de Inteligência Artificial e Machine Learning Preditivo
    para Previsão de Entupimentos e Risco de Alagamento (RF15 / UC09).

    Versão multivariada — agrega 6 fontes de dados em um score ponderado
    para recomendar frequência de limpeza.
    """

    # ═════════════════════════════════════════════════════════════
    # MÉTODO PRINCIPAL
    # ═════════════════════════════════════════════════════════════

    @staticmethod
    def analisar_e_prever(
        db: Session,
        id_sensor: int = 1,
        persistir: bool = True,
        lat: float = BUEIRO_LATITUDE,
        lon: float = BUEIRO_LONGITUDE,
    ) -> schemas.AnaliseIAResult:
        """
        Executa a análise preditiva multivariada sobre as leituras recentes
        do sensor e todas as fontes de dados disponíveis.
        """
        agora = datetime.utcnow()

        # ─── 1. Coleta de dados do sensor (banco de dados) ─────────
        leituras = db.query(models.LeituraSensor)\
                     .filter(models.LeituraSensor.id_sensor == id_sensor)\
                     .order_by(models.LeituraSensor.data_hora.desc())\
                     .limit(10)\
                     .all()

        if not leituras:
            return schemas.AnaliseIAResult(
                probabilidade_entupimento=0.0,
                nivel_risco="Baixo",
                tendencia="Sem dados suficientes",
                taxa_variacao_cm_min=0.0,
                distancia_atual_cm=400.0,
                tempo_estimado_transbordo_min=None,
                recomendacao="Aguardando primeira leitura de sensor.",
                alerta_gerado=False,
                data_analise=agora,
                urgencia_limpeza="Rotina",
                recomendacao_limpeza="Sem dados do sensor para análise. Manter rotina de limpeza padrão.",
                fontes_dados_disponiveis=[],
            )

        leitura_mais_recente = leituras[0]
        distancia_atual = float(leitura_mais_recente.valor_leitura)

        # ─── Calcula taxa de variação (derivada temporal) ──────────
        taxa_subida_cm_min, tendencia = _calcular_tendencia(leituras, agora)

        # ─── Busca nível de resíduo da última compactação ──────────
        ultima_compactacao = db.query(models.Compactacao)\
                               .order_by(models.Compactacao.data_hora.desc())\
                               .first()
        nivel_residuo_pct = float(ultima_compactacao.nivel_residuo) if ultima_compactacao else 0.0

        # ─── 2. Coleta de dados climáticos (OpenWeatherMap) ────────
        dados_clima = obter_dados_climaticos(lat, lon)

        # ─── 3. Coleta de dados temporais ──────────────────────────
        dados_tempo = extrair_dados_temporais(agora)

        # ─── 4. Coleta de dados de alagamentos ────────────────────
        score_alagamento = historico_alagamentos.obter_score_risco_local(lat, lon)

        # ─── 5. Coleta de dados geográficos ────────────────────────
        perfil_topo = dados_geograficos.obter_perfil_topografico(lat, lon)

        # ─── 6. Coleta de dados de uso do solo ─────────────────────
        perfil_solo = uso_do_solo.obter_perfil()

        # ═══════════════════════════════════════════════════════════
        # CÁLCULO DOS SCORES POR DIMENSÃO (cada um de 0.0 a 1.0)
        # ═══════════════════════════════════════════════════════════

        score_sensor = _calcular_score_sensor(
            distancia_atual, taxa_subida_cm_min, nivel_residuo_pct
        )
        score_clima = _calcular_score_clima(dados_clima)
        score_temporal = _calcular_score_temporal(dados_tempo)
        score_alag = _calcular_score_alagamento(score_alagamento)
        score_geo = _calcular_score_geografico(perfil_topo)
        score_solo = _calcular_score_uso_solo(perfil_solo)

        scores_detalhados = {
            "sensor": round(score_sensor, 3),
            "clima": round(score_clima, 3),
            "temporal": round(score_temporal, 3),
            "historico_alagamento": round(score_alag, 3),
            "geografico": round(score_geo, 3),
            "uso_solo": round(score_solo, 3),
        }

        # ═══════════════════════════════════════════════════════════
        # SCORE PONDERADO FINAL
        # ═══════════════════════════════════════════════════════════

        probabilidade = (
            PESO_SENSOR * score_sensor
            + PESO_CLIMA * score_clima
            + PESO_TEMPORAL * score_temporal
            + PESO_HISTORICO_ALAGAMENTO * score_alag
            + PESO_GEOGRAFICO * score_geo
            + PESO_USO_SOLO * score_solo
        )
        probabilidade = max(0.01, min(0.99, probabilidade))

        # ═══════════════════════════════════════════════════════════
        # CLASSIFICAÇÃO DE RISCO
        # ═══════════════════════════════════════════════════════════

        nivel_risco, recomendacao = _classificar_risco(probabilidade, distancia_atual)

        # ═══════════════════════════════════════════════════════════
        # RECOMENDAÇÃO DE LIMPEZA
        # ═══════════════════════════════════════════════════════════

        urgencia_limpeza, recomendacao_limpeza, proxima_limpeza_min = _recomendar_limpeza(
            probabilidade=probabilidade,
            score_sensor=score_sensor,
            score_clima=score_clima,
            dados_clima=dados_clima,
            dados_tempo=dados_tempo,
            taxa_subida_cm_min=taxa_subida_cm_min,
            distancia_atual=distancia_atual,
            nivel_residuo_pct=nivel_residuo_pct,
        )

        # ═══════════════════════════════════════════════════════════
        # TEMPO ESTIMADO ATÉ TRANSBORDO
        # ═══════════════════════════════════════════════════════════

        tempo_transbordo = None
        if taxa_subida_cm_min > 0.5 and distancia_atual > 15.0:
            tempo_transbordo = round((distancia_atual - 15.0) / taxa_subida_cm_min, 1)

        # ═══════════════════════════════════════════════════════════
        # FONTES DE DADOS UTILIZADAS
        # ═══════════════════════════════════════════════════════════

        fontes = ["Sensor IoT (Telemetria)"]
        if dados_clima.disponivel:
            fontes.append("OpenWeatherMap (Clima)")
        fontes.append("Dados Temporais (datetime)")
        if score_alagamento.disponivel:
            fontes.append("Histórico Alagamentos (CGE SP)")
        if perfil_topo.disponivel:
            fontes.append("Dados Geográficos (GeoSampa)")
        if perfil_solo.disponivel:
            fontes.append("Uso do Solo (Entorno)")

        # ═══════════════════════════════════════════════════════════
        # DADOS CLIMÁTICOS PARA RESPOSTA
        # ═══════════════════════════════════════════════════════════

        dados_clima_dict = None
        if dados_clima.disponivel:
            dados_clima_dict = {
                "chuva_mm_h": dados_clima.chuva_mm_h,
                "umidade_pct": dados_clima.umidade_pct,
                "vento_ms": dados_clima.vento_ms,
                "previsao_chuva_3h_mm": dados_clima.previsao_chuva_proximas_3h_mm,
                "descricao": dados_clima.descricao_clima,
            }

        # ═══════════════════════════════════════════════════════════
        # PERSISTÊNCIA NO BANCO DE DADOS
        # ═══════════════════════════════════════════════════════════

        alerta_gerado = False

        if persistir:
            nova_previsao = models.PrevisaoEntupimento(
                probabilidade=round(probabilidade, 2),
                nivel_risco=nivel_risco,
                id_leitura=leitura_mais_recente.id_leitura,
            )
            db.add(nova_previsao)

            # Dispara alerta se risco for Alto ou Crítico
            # (evita alertas duplicados nos últimos 2 min)
            if nivel_risco in ["Alto", "Crítico"]:
                dois_minutos_atras = agora - timedelta(minutes=2)
                alerta_recente = db.query(models.Alerta)\
                                   .filter(models.Alerta.data_hora >= dois_minutos_atras)\
                                   .first()
                if not alerta_recente:
                    desc_alerta = (
                        f"IA Multivariada: {nivel_risco.upper()} risco "
                        f"(Prob: {int(probabilidade * 100)}%). "
                        f"Limpeza: {urgencia_limpeza}. {recomendacao}"
                    )
                    novo_alerta = models.Alerta(
                        descricao=desc_alerta,
                        nivel_criticidade=nivel_risco,
                        id_leitura=leitura_mais_recente.id_leitura,
                    )
                    db.add(novo_alerta)
                    alerta_gerado = True

            db.commit()

        # ═══════════════════════════════════════════════════════════
        # RESULTADO FINAL
        # ═══════════════════════════════════════════════════════════

        return schemas.AnaliseIAResult(
            probabilidade_entupimento=round(probabilidade, 2),
            nivel_risco=nivel_risco,
            tendencia=tendencia,
            taxa_variacao_cm_min=round(taxa_subida_cm_min, 2),
            distancia_atual_cm=round(distancia_atual, 2),
            tempo_estimado_transbordo_min=tempo_transbordo,
            recomendacao=recomendacao,
            alerta_gerado=alerta_gerado,
            data_analise=agora,
            # Novos campos
            urgencia_limpeza=urgencia_limpeza,
            recomendacao_limpeza=recomendacao_limpeza,
            proxima_limpeza_sugerida_min=proxima_limpeza_min,
            scores_detalhados=scores_detalhados,
            dados_climaticos_utilizados=dados_clima_dict,
            fontes_dados_disponiveis=fontes,
        )


# ═══════════════════════════════════════════════════════════════════
# FUNÇÕES DE CÁLCULO DE SCORE POR DIMENSÃO
# ═══════════════════════════════════════════════════════════════════

def _calcular_tendencia(
    leituras: list,
    agora: datetime,
) -> tuple[float, str]:
    """Calcula a taxa de subida (cm/min) e a tendência textual."""
    taxa_subida_cm_min = 0.0
    tendencia = "Estável"

    if len(leituras) < 2:
        return taxa_subida_cm_min, tendencia

    # Ordena da mais antiga para a mais recente
    leituras_cron = list(reversed(leituras))

    t0 = leituras_cron[0].data_hora or agora
    tempos_min = []
    distancias = []

    for l in leituras_cron:
        t_delta = ((l.data_hora or agora) - t0).total_seconds() / 60.0
        tempos_min.append(t_delta)
        distancias.append(float(l.valor_leitura))

    delta_t = tempos_min[-1] - tempos_min[0]
    if delta_t > 0.01:
        delta_d = distancias[-1] - distancias[0]
        slope_distancia = delta_d / delta_t
        taxa_subida_cm_min = -slope_distancia
    else:
        d_ant = float(leituras[1].valor_leitura)
        distancia_atual = float(leituras[0].valor_leitura)
        taxa_subida_cm_min = (d_ant - distancia_atual) * 12.0

    if taxa_subida_cm_min > 20.0:
        tendencia = "Enchendo muito rápido (Alerta de Chuva/Enxurrada)"
    elif taxa_subida_cm_min > 5.0:
        tendencia = "Enchendo moderadamente"
    elif taxa_subida_cm_min < -5.0:
        tendencia = "Esvaziando / Drenagem eficiente"
    else:
        tendencia = "Estável"

    return taxa_subida_cm_min, tendencia


def _calcular_score_sensor(
    distancia_atual: float,
    taxa_subida_cm_min: float,
    nivel_residuo_pct: float,
) -> float:
    """
    Score da dimensão SENSOR (0.0 a 1.0).

    Combina:
    - Distância atual do sensor ultrassônico (quanto menor, mais cheio)
    - Taxa de subida da água/resíduo
    - Nível de resíduo da compactação
    """
    # Base pela distância (mesma lógica do motor original)
    if distancia_atual <= 15.0:
        score_dist = 0.95
    elif distancia_atual <= 30.0:
        score_dist = 0.75
    elif distancia_atual <= 80.0:
        score_dist = 0.50
    elif distancia_atual <= 150.0:
        score_dist = 0.25
    else:
        score_dist = 0.05

    # Modificador pela velocidade de subida
    if taxa_subida_cm_min >= 30.0:
        mod_vel = 0.30
    elif taxa_subida_cm_min >= 15.0:
        mod_vel = 0.20
    elif taxa_subida_cm_min >= 5.0:
        mod_vel = 0.10
    elif taxa_subida_cm_min <= -5.0:
        mod_vel = -0.15
    else:
        mod_vel = 0.0

    # Modificador pelo nível de resíduo acumulado
    mod_residuo = min(0.15, nivel_residuo_pct / 100.0 * 0.20)

    score = score_dist + mod_vel + mod_residuo
    return max(0.0, min(1.0, score))


def _calcular_score_clima(dados: DadosClimaticos) -> float:
    """
    Score da dimensão CLIMÁTICA (0.0 a 1.0).

    Maior risco quando:
    - Está chovendo forte agora (chuva_mm_h alta)
    - Previsão de mais chuva nas próximas 3h
    - Umidade muito alta (>85%) indica saturação do solo
    - Vento forte pode arrastar mais detritos
    """
    if not dados.disponivel:
        # Sem dados climáticos: retorna score neutro (0.3)
        return 0.30

    # Chuva atual
    if dados.chuva_mm_h >= 25.0:
        score_chuva = 1.0   # Chuva muito forte
    elif dados.chuva_mm_h >= 10.0:
        score_chuva = 0.80  # Chuva forte
    elif dados.chuva_mm_h >= 5.0:
        score_chuva = 0.55  # Chuva moderada
    elif dados.chuva_mm_h >= 1.0:
        score_chuva = 0.30  # Chuva leve
    else:
        score_chuva = 0.05  # Sem chuva

    # Previsão de chuva próximas 3h
    if dados.previsao_chuva_proximas_3h_mm >= 30.0:
        score_previsao = 0.90
    elif dados.previsao_chuva_proximas_3h_mm >= 15.0:
        score_previsao = 0.65
    elif dados.previsao_chuva_proximas_3h_mm >= 5.0:
        score_previsao = 0.35
    else:
        score_previsao = 0.05

    # Umidade do ar
    if dados.umidade_pct >= 90:
        score_umidade = 0.80
    elif dados.umidade_pct >= 75:
        score_umidade = 0.50
    elif dados.umidade_pct >= 60:
        score_umidade = 0.25
    else:
        score_umidade = 0.05

    # Vento (contribuição menor)
    score_vento = min(0.50, dados.vento_ms / 20.0)

    # Média ponderada dos sub-scores climáticos
    score = (
        0.40 * score_chuva
        + 0.30 * score_previsao
        + 0.20 * score_umidade
        + 0.10 * score_vento
    )
    return max(0.0, min(1.0, score))


def _calcular_score_temporal(dados: DadosTemporais) -> float:
    """
    Score da dimensão TEMPORAL/SAZONAL (0.0 a 1.0).

    Maior risco quando:
    - Período chuvoso (outubro a março em SP)
    - Horário de pico (mais trânsito = mais lixo nas ruas)
    - Feriados/fins de semana (feiras, eventos)
    - Madrugada (acúmulo de resíduos do dia anterior)
    """
    score = 0.10  # Base mínima

    if dados.periodo_chuvoso:
        score += 0.30  # Estação chuvosa é o fator mais importante

    if dados.eh_horario_pico:
        score += 0.10

    if dados.eh_feriado:
        score += 0.15  # Feriados: feiras, eventos, mais lixo

    if dados.eh_fim_de_semana:
        score += 0.10

    # Madrugada: acúmulo noturno de resíduos
    if dados.periodo_do_dia == "Madrugada":
        score += 0.10

    # Estação do ano (verão é mais chuvoso no hemisfério sul)
    if dados.estacao_do_ano == "Verão":
        score += 0.10
    elif dados.estacao_do_ano == "Primavera":
        score += 0.05

    return max(0.0, min(1.0, score))


def _calcular_score_alagamento(dados: ScoreAlagamentoHistorico) -> float:
    """
    Score da dimensão HISTÓRICO DE ALAGAMENTOS (0.0 a 1.0).
    Usa diretamente o score calculado pelo provider.
    """
    return dados.score


def _calcular_score_geografico(perfil: PerfilTopografico) -> float:
    """
    Score da dimensão GEOGRÁFICA/TOPOGRÁFICA (0.0 a 1.0).

    Maior risco quando:
    - Localizado em fundo de vale (acumula água)
    - Classificado como área de risco alto
    - Declividade negativa (água desce para o ponto)
    """
    if not perfil.disponivel:
        return 0.30  # Default conservador

    score = 0.10  # Base

    # Fundo de vale é o fator mais impactante
    if perfil.eh_fundo_de_vale:
        score += 0.40

    # Classificação de risco
    classificacao = perfil.classificacao_risco.lower()
    if "muito alto" in classificacao:
        score += 0.35
    elif "alto" in classificacao:
        score += 0.25
    elif "médio" in classificacao or "medio" in classificacao:
        score += 0.15
    elif "baixo" in classificacao:
        score += 0.05

    # Declividade negativa = água desce para cá
    if perfil.declividade_pct < -3.0:
        score += 0.15
    elif perfil.declividade_pct < -1.0:
        score += 0.08

    return max(0.0, min(1.0, score))


def _calcular_score_uso_solo(perfil: PerfilUsoSolo) -> float:
    """
    Score da dimensão USO DO SOLO (0.0 a 1.0).

    Maior risco quando:
    - Via comercial (mais resíduos sólidos)
    - Próximo a feiras (restos orgânicos obstruem bueiros)
    - Alta impermeabilização (menos infiltração, mais escoamento)
    """
    if not perfil.disponivel:
        return 0.30  # Default conservador

    score = 0.10  # Base

    # Tipo de via
    tipo = perfil.tipo_via.lower()
    if "comercial" in tipo:
        score += 0.20
    elif "mista" in tipo:
        score += 0.12
    elif "industrial" in tipo:
        score += 0.08
    # Residencial contribui menos (+ 0.0)

    # Proximidade com feira (mais resíduos orgânicos)
    if perfil.proximidade_feira_m is not None:
        if perfil.proximidade_feira_m <= 100:
            score += 0.25
        elif perfil.proximidade_feira_m <= 300:
            score += 0.15
        elif perfil.proximidade_feira_m <= 500:
            score += 0.08

    # Proximidade com parque (folhas, galhos)
    if perfil.proximidade_parque_m is not None:
        if perfil.proximidade_parque_m <= 100:
            score += 0.15
        elif perfil.proximidade_parque_m <= 300:
            score += 0.08

    # Índice de impermeabilização
    score += perfil.indice_impermeabilizacao * 0.15

    # Zona comercial intensa
    if perfil.zona_comercial_intensa:
        score += 0.10

    return max(0.0, min(1.0, score))


# ═══════════════════════════════════════════════════════════════════
# CLASSIFICAÇÃO DE RISCO E RECOMENDAÇÃO DE LIMPEZA
# ═══════════════════════════════════════════════════════════════════

def _classificar_risco(
    probabilidade: float,
    distancia_atual: float,
) -> tuple[str, str]:
    """Classifica o nível de risco e gera a recomendação textual."""
    if probabilidade >= 0.80 or distancia_atual <= 15.0:
        return (
            "Crítico",
            "ACIONAR EQUIPE DE EMERGÊNCIA IMEDIATAMENTE. "
            "Risco iminente de transbordo e alagamento na via pública.",
        )
    elif probabilidade >= 0.60:
        return (
            "Alto",
            "Aumento rápido de resíduos/água detectado por múltiplas fontes. "
            "Abrir comportas e emitir alerta preventivo à Defesa Civil.",
        )
    elif probabilidade >= 0.35:
        return (
            "Médio",
            "Volume moderado detectado. Condições climáticas e históricas "
            "indicam atenção redobrada. Manter monitoramento contínuo.",
        )
    else:
        return (
            "Baixo",
            "Bueiro operando em condições normais de drenagem pluvial.",
        )


def _recomendar_limpeza(
    probabilidade: float,
    score_sensor: float,
    score_clima: float,
    dados_clima: DadosClimaticos,
    dados_tempo: DadosTemporais,
    taxa_subida_cm_min: float,
    distancia_atual: float,
    nivel_residuo_pct: float,
) -> tuple[str, str, float | None]:
    """
    Gera recomendação de limpeza baseada no score ponderado e contexto.

    Retorna: (urgencia, recomendacao_texto, proxima_limpeza_minutos)
    """

    # ── EMERGÊNCIA: Risco iminente de transbordo ──────────────────
    if probabilidade >= 0.80 or distancia_atual <= 15.0:
        return (
            "Emergência",
            "LIMPEZA DE EMERGÊNCIA NECESSÁRIA! O bueiro está próximo do "
            "transbordo. Acionar equipe imediatamente para desobstrução e "
            "abertura de comportas. Risco de alagamento na via.",
            0.0,  # Agora!
        )

    # ── URGENTE: Risco alto com fatores agravantes ────────────────
    if probabilidade >= 0.60:
        motivos = []
        if score_sensor >= 0.60:
            motivos.append("nível de preenchimento alto")
        if score_clima >= 0.60:
            motivos.append("condições climáticas adversas")
        if taxa_subida_cm_min > 10.0:
            motivos.append(f"taxa de subida acelerada ({taxa_subida_cm_min:.1f} cm/min)")

        detalhes = ", ".join(motivos) if motivos else "múltiplos indicadores elevados"
        return (
            "Urgente",
            f"Antecipar limpeza com urgência: {detalhes}. "
            f"Recomendado despachar equipe dentro de 30 minutos.",
            30.0,
        )

    # ── PREVENTIVA: Risco moderado — antecipar limpeza ────────────
    if probabilidade >= 0.35:
        motivos = []
        tempo_sugerido = 120.0  # 2 horas

        if dados_clima.disponivel and dados_clima.previsao_chuva_proximas_3h_mm >= 10.0:
            motivos.append(
                f"previsão de {dados_clima.previsao_chuva_proximas_3h_mm:.0f}mm "
                f"de chuva nas próximas 3h"
            )
            tempo_sugerido = 60.0  # 1 hora se chuva forte vindo

        if dados_tempo.periodo_chuvoso:
            motivos.append("período chuvoso ativo (outubro-março)")

        if nivel_residuo_pct >= 50.0:
            motivos.append(f"nível de resíduo em {nivel_residuo_pct:.0f}%")
            tempo_sugerido = min(tempo_sugerido, 90.0)

        if score_sensor >= 0.40:
            motivos.append("nível de preenchimento moderado")

        detalhes = ". ".join(motivos) if motivos else "Indicadores moderados detectados"
        return (
            "Preventiva",
            f"Agendar limpeza preventiva: {detalhes}. "
            f"Sugestão: realizar limpeza em até {int(tempo_sugerido)} minutos.",
            tempo_sugerido,
        )

    # ── ROTINA: Sem risco significativo ───────────────────────────
    observacoes = []
    if dados_tempo.periodo_chuvoso:
        observacoes.append("Atenção: período chuvoso — manter frequência de inspeção elevada.")
    if dados_clima.disponivel and dados_clima.previsao_chuva_proximas_3h_mm >= 5.0:
        observacoes.append(
            f"Nota: previsão de {dados_clima.previsao_chuva_proximas_3h_mm:.0f}mm "
            f"de chuva nas próximas 3h."
        )

    obs_texto = " ".join(observacoes) if observacoes else ""
    return (
        "Rotina",
        f"Manter rotina normal de limpeza. Bueiro em boas condições. {obs_texto}".strip(),
        None,
    )
