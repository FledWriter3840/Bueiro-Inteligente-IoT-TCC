from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from . import models, schemas

class PrevisorEntupimentoIA:
    """
    Motor de Inteligência Artificial e Machine Learning Preditivo
    para Previsão de Entupimentos e Risco de Alagamento (RF15 / UC09).
    """

    @staticmethod
    def analisar_e_prever(db: Session, id_sensor: int = 1, persistir: bool = True) -> schemas.AnaliseIAResult:
        # Busca as últimas 10 leituras do sensor ordenadas cronologicamente
        leituras = db.query(models.LeituraSensor)\
                     .filter(models.LeituraSensor.id_sensor == id_sensor)\
                     .order_by(models.LeituraSensor.data_hora.desc())\
                     .limit(10)\
                     .all()

        agora = datetime.utcnow()

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
                data_analise=agora
            )

        leitura_mais_recente = leituras[0]
        distancia_atual = float(leitura_mais_recente.valor_leitura)

        taxa_subida_cm_min = 0.0
        tendencia = "Estável"

        # Se tivermos mais de 1 leitura, calcula a taxa de variação (regressão / derivada)
        if len(leituras) >= 2:
            # Ordena da mais antiga para a mais recente
            leituras_cronologicas = list(reversed(leituras))
            
            t0 = leituras_cronologicas[0].data_hora or agora
            tempos_min = []
            distancias = []

            for l in leituras_cronologicas:
                t_delta = ((l.data_hora or agora) - t0).total_seconds() / 60.0
                tempos_min.append(t_delta)
                distancias.append(float(l.valor_leitura))

            # Regressão linear simples: slope da distância em relação ao tempo
            delta_t = tempos_min[-1] - tempos_min[0]
            if delta_t > 0.01:
                # delta_d negativo significa que a distância está diminuindo (água subindo)
                delta_d = distancias[-1] - distancias[0]
                slope_distancia = delta_d / delta_t
                # Taxa de subida da água/resíduo (positiva quando o nível sobe)
                taxa_subida_cm_min = -slope_distancia
            else:
                # Diferença instantânea entre as duas últimas amostras
                d_ant = float(leituras[1].valor_leitura)
                taxa_subida_cm_min = (d_ant - distancia_atual) * 12.0 # Projeção para 1 min

            if taxa_subida_cm_min > 20.0:
                tendencia = "Enchendo muito rápido (Alerta de Chuva/Enxurrada)"
            elif taxa_subida_cm_min > 5.0:
                tendencia = "Enchendo moderadamente"
            elif taxa_subida_cm_min < -5.0:
                tendencia = "Esvaziando / Drenagem eficiente"
            else:
                tendencia = "Estável"

        # -------------------------------------------------------------
        # Algoritmo de Score Probabilístico de Risco
        # -------------------------------------------------------------
        # 1. Base pela distância atual
        if distancia_atual <= 15.0:
            score_base = 0.85
        elif distancia_atual <= 30.0:
            score_base = 0.65
        elif distancia_atual <= 80.0:
            score_base = 0.40
        elif distancia_atual <= 150.0:
            score_base = 0.20
        else:
            score_base = 0.05

        # 2. Modificador pela velocidade de subida
        modificador_velocidade = 0.0
        if taxa_subida_cm_min >= 30.0:
            modificador_velocidade = +0.30
        elif taxa_subida_cm_min >= 15.0:
            modificador_velocidade = +0.20
        elif taxa_subida_cm_min >= 5.0:
            modificador_velocidade = +0.10
        elif taxa_subida_cm_min <= -5.0:
            modificador_velocidade = -0.20

        probabilidade = max(0.01, min(0.99, score_base + modificador_velocidade))

        # Classificação do Nível de Risco
        if probabilidade >= 0.80 or distancia_atual <= 15.0:
            nivel_risco = "Crítico"
            recomendacao = "ACIONAR EQUIPE DE EMERGÊNCIA IMEDIATAMENTE. Risco iminente de transbordo e alagamento na via pública."
        elif probabilidade >= 0.60:
            nivel_risco = "Alto"
            recomendacao = "Aumento rápido de resíduos/água. Abrir comportas e emitir alerta preventivo à Defesa Civil."
        elif probabilidade >= 0.35:
            nivel_risco = "Médio"
            recomendacao = "Volume moderado detectado. Manter monitoramento contínuo da taxa de elevação."
        else:
            nivel_risco = "Baixo"
            recomendacao = "Bueiro operando em condições normais de drenagem pluvial."

        # Estimativa de tempo restante até transbordo (limite crítico = 15 cm)
        tempo_transbordo = None
        if taxa_subida_cm_min > 0.5 and distancia_atual > 15.0:
            tempo_transbordo = round((distancia_atual - 15.0) / taxa_subida_cm_min, 1)

        alerta_gerado = False

        # -------------------------------------------------------------
        # Persistência no Banco de Dados (PrevisaoEntupimento & Alerta)
        # -------------------------------------------------------------
        if persistir:
            nova_previsao = models.PrevisaoEntupimento(
                probabilidade=round(probabilidade, 2),
                nivel_risco=nivel_risco,
                id_leitura=leitura_mais_recente.id_leitura
            )
            db.add(nova_previsao)

            # Dispara alerta se risco for Alto ou Crítico (evita alertas duplicados nos últimos 2 min)
            if nivel_risco in ["Alto", "Crítico"]:
                dois_minutos_atras = agora - timedelta(minutes=2)
                alerta_recente = db.query(models.Alerta)\
                                   .filter(models.Alerta.data_hora >= dois_minutos_atras)\
                                   .first()
                if not alerta_recente:
                    novo_alerta = models.Alerta(
                        descricao=f"IA: {nivel_risco.upper()} risco de alagamento (Probabilidade: {int(probabilidade*100)}%). {recomendacao}",
                        nivel_criticidade=nivel_risco,
                        id_leitura=leitura_mais_recente.id_leitura
                    )
                    db.add(novo_alerta)
                    alerta_gerado = True

            db.commit()

        return schemas.AnaliseIAResult(
            probabilidade_entupimento=round(probabilidade, 2),
            nivel_risco=nivel_risco,
            tendencia=tendencia,
            taxa_variacao_cm_min=round(taxa_subida_cm_min, 2),
            distancia_atual_cm=round(distancia_atual, 2),
            tempo_estimado_transbordo_min=tempo_transbordo,
            recomendacao=recomendacao,
            alerta_gerado=alerta_gerado,
            data_analise=agora
        )
