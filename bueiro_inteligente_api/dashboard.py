import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Bueiro Inteligente - Painel", page_icon="📉​", layout="wide")


# ---------------------------------------------------------------
# Funções auxiliares de acesso à API
# ---------------------------------------------------------------
def get_json(endpoint: str, params: dict | None = None):
    try:
        resp = requests.get(f"{API_URL}{endpoint}", params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Falha ao consultar {endpoint}: {e}")
        return None


def post_json(endpoint: str, payload: dict | None = None, params: dict | None = None):
    try:
        resp = requests.post(f"{API_URL}{endpoint}", json=payload, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Falha ao chamar {endpoint}: {e}")
        return None


# ---------------------------------------------------------------
# Cabeçalho e controles
# ---------------------------------------------------------------
st.title("Bueiro Inteligente — Painel de Monitoramento")
st.caption("Sistema IoT de limpeza automática de bueiros — TCC UNIP")

col_refresh, col_auto, _ = st.columns([1, 1, 4])
with col_refresh:
    if st.button("Atualizar agora"):
        st.rerun()
with col_auto:
    auto = st.checkbox("Auto-atualizar (10s)")
    if auto:
        st.markdown('<meta http-equiv="refresh" content="10">', unsafe_allow_html=True)

tab_geral, tab_leituras, tab_eventos, tab_ia, tab_simulacao, tab_manual = st.tabs(
    ["Visão Geral", "Leituras", "Alertas & Eventos", "IA & Previsão", "Simulação", "Inserir Dados"]
)


# ---------------------------------------------------------------
# ABA 1: Visão Geral
# ---------------------------------------------------------------
with tab_geral:
    leituras = get_json("/sensores/leituras") or []
    alertas = get_json("/alertas/") or []
    previsao = get_json("/ia/previsao", params={"id_sensor": 1})

    col1, col2, col3, col4 = st.columns(4)

    if leituras:
        ultima = leituras[0]
        col1.metric("Última leitura", f"{ultima['valor_leitura']:.1f} {ultima['unidade_medida']}")
    else:
        col1.metric("Última leitura", "sem dados")

    if previsao:
        col2.metric("Risco (motor regressão)", previsao["nivel_risco"])
        col3.metric("Probabilidade", f"{previsao['probabilidade_entupimento'] * 100:.0f}%")
    else:
        col2.metric("Risco", "—")
        col3.metric("Probabilidade", "—")

    col4.metric("Alertas registrados", len(alertas))

    if previsao and previsao["nivel_risco"] in ("Alto", "Crítico"):
        st.error(f"⚠️ {previsao['recomendacao']}")
    elif previsao:
        st.success(previsao["recomendacao"])

    st.divider()

    if leituras:
        df = pd.DataFrame(leituras)
        df["data_hora"] = pd.to_datetime(df["data_hora"])
        df = df.sort_values("data_hora")
        fig = px.line(
            df, x="data_hora", y="valor_leitura",
            title="Distância medida pelo sensor ao longo do tempo",
            labels={"valor_leitura": "Distância (cm)", "data_hora": "Data/Hora"}
        )
        fig.add_hline(y=15, line_dash="dash", line_color="red",
                       annotation_text="Limite crítico (15cm)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma leitura registrada ainda.")


# ---------------------------------------------------------------
# ABA 2: Leituras (tabela detalhada)
# ---------------------------------------------------------------
with tab_leituras:
    st.subheader("Histórico completo de leituras")
    leituras = get_json("/sensores/leituras") or []
    if leituras:
        df = pd.DataFrame(leituras)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma leitura registrada ainda.")


# ---------------------------------------------------------------
# ABA 3: Alertas, Limpeza, Compactação, Histórico
# ---------------------------------------------------------------
with tab_eventos:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🚨 Alertas")
        alertas = get_json("/alertas/") or []
        if alertas:
            st.dataframe(pd.DataFrame(alertas), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum alerta registrado.")

        st.subheader("🧹 Limpeza")
        limpezas = get_json("/limpeza/") or []
        if limpezas:
            st.dataframe(pd.DataFrame(limpezas), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma limpeza registrada.")

    with col_b:
        st.subheader("🗜️ Compactação")
        compactacoes = get_json("/compactacao/") or []
        if compactacoes:
            st.dataframe(pd.DataFrame(compactacoes), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma compactação registrada.")

        st.subheader("📜 Histórico do sistema")
        historico = get_json("/historico/") or []
        if historico:
            st.dataframe(pd.DataFrame(historico), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum evento registrado.")


# ---------------------------------------------------------------
# ABA 4: Comparativo dos dois motores de IA
# ---------------------------------------------------------------
with tab_ia:
    st.subheader("Comparativo entre os motores de IA")
    st.caption("Motor 1: regressão/tendência temporal + sistema probabilístico. Motor 2: Machine Learning (scikit-learn, treinado com dataset sintético).")

    if st.button("🧠 Rodar comparativo agora"):
        comparativo = get_json("/ia/comparativo", params={"id_sensor": 1})
        if comparativo:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📐 Motor de Regressão")
                r = comparativo["motor_regressao"]
                st.metric("Risco", r["nivel_risco"])
                st.metric("Probabilidade", f"{r['probabilidade_entupimento'] * 100:.0f}%")
                st.write(f"**Tendência:** {r['tendencia']}")
                st.write(f"**Taxa de variação:** {r['taxa_variacao_cm_min']:.2f} cm/min")
                st.write(f"**Recomendação:** {r['recomendacao']}")

            with col2:
                st.markdown("### 🤖 Motor Machine Learning")
                m = comparativo["motor_machine_learning"]
                st.metric("Risco", m["nivel_risco"])
                st.metric("Confiança", f"{m['probabilidade_classe'] * 100:.0f}%")
                st.write(f"**Modelo:** {m['modelo_utilizado']}")
                st.write("**Probabilidades por classe:**")
                st.bar_chart(pd.Series(m["classes_probabilidades"]))

            st.divider()
            if comparativo["convergencia"]:
                st.success(f"✅ {comparativo['observacao']}")
            else:
                st.warning(f"⚠️ {comparativo['observacao']}")
    else:
        st.info("Clique no botão acima para rodar os dois motores sobre a leitura mais recente.")

    st.divider()
    st.subheader("Treinar/retreinar o modelo de Machine Learning")
    n_amostras = st.slider("Número de amostras sintéticas", 500, 10000, 3000, step=500)
    if st.button("🔁 Treinar modelo"):
        with st.spinner("Treinando modelo..."):
            resultado = post_json("/ia/treinar-modelo-ml", params={"n_amostras": n_amostras})
        if resultado:
            st.success(f"Modelo treinado! Acurácia: {resultado['acuracia'] * 100:.1f}%")
            st.text(resultado["relatorio_classificacao"])


# ---------------------------------------------------------------
# ABA 5: Simulação de cenário de chuva
# ---------------------------------------------------------------
with tab_simulacao:
    st.subheader("Simular cenário de chuva intensa")
    st.caption("Projeção matemática de elevação de água.")

    col1, col2, col3 = st.columns(3)
    distancia_inicial = col1.number_input("Distância inicial (cm)", value=350.0, step=10.0)
    velocidade = col2.number_input("Velocidade de subida (cm/min)", value=25.0, step=5.0)
    minutos = col3.number_input("Minutos a simular", value=10, step=1, min_value=1, max_value=60)

    if st.button("▶️ Rodar simulação"):
        payload = {
            "distancia_inicial_cm": distancia_inicial,
            "velocidade_subida_cm_min": velocidade,
            "minutos_simulacao": int(minutos)
        }
        resultado = post_json("/ia/simular-cenario", payload=payload)
        if resultado:
            df = pd.DataFrame(resultado["projecoes"])
            fig = px.line(
                df, x="minuto", y="distancia_prevista_cm",
                title="Projeção de nível ao longo do tempo",
                labels={"minuto": "Minutos", "distancia_prevista_cm": "Distância prevista (cm)"}
            )
            fig.add_hline(y=15, line_dash="dash", line_color="red", annotation_text="Limite crítico")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------
# ABA 6: Inserção manual de dados (para testes rápidos)
# ---------------------------------------------------------------
with tab_manual:
    st.subheader("Inserir dados manualmente")
    st.caption("Simular cenários sem o hardware físico, ou testar o sistema em tempo real.")

    sub_leitura, sub_alerta, sub_limpeza, sub_compactacao, sub_historico = st.tabs(
        ["Leitura de Sensor", "Alerta", "Limpeza", "Compactação", "Histórico"]
    )

    with sub_leitura:
        st.markdown("#### Nova leitura de sensor")
        col1, col2 = st.columns(2)
        valor = col1.number_input("Valor da leitura (distância)", value=20.0, step=1.0, key="valor_leitura")
        unidade = col2.selectbox("Unidade", ["cm", "mm", "m"], key="unidade_leitura")
        id_sensor = st.number_input("ID do sensor", value=1, step=1, min_value=1, key="id_sensor_leitura")

        if st.button("➕ Registrar leitura", key="btn_leitura"):
            resultado = post_json("/sensores/leitura", payload={
                "valor_leitura": valor, "unidade_medida": unidade, "id_sensor": int(id_sensor)
            })
            if resultado:
                st.success(f"Leitura registrada! ID: {resultado['id_leitura']}")
                st.info("A IA já rodou automaticamente sobre essa leitura — confira a aba 'IA & Previsão'.")
                st.rerun()

        st.divider()
        st.markdown("##### Atalhos de cenário rápido")
        col_a, col_b, col_c = st.columns(3)
        if col_a.button("🟢 Simular normal (200cm)"):
            post_json("/sensores/leitura", payload={"valor_leitura": 200.0, "unidade_medida": "cm", "id_sensor": 1})
            st.rerun()
        if col_b.button("🟡 Simular moderado (60cm)"):
            post_json("/sensores/leitura", payload={"valor_leitura": 60.0, "unidade_medida": "cm", "id_sensor": 1})
            st.rerun()
        if col_c.button("🔴 Simular crítico (8cm)"):
            post_json("/sensores/leitura", payload={"valor_leitura": 8.0, "unidade_medida": "cm", "id_sensor": 1})
            st.rerun()

    with sub_alerta:
        st.markdown("#### Novo alerta manual")
        leituras_disponiveis = get_json("/sensores/leituras") or []
        if leituras_disponiveis:
            opcoes = {f"#{l['id_leitura']} — {l['valor_leitura']}{l['unidade_medida']} ({l['data_hora']})": l['id_leitura']
                      for l in leituras_disponiveis[:20]}
            escolha = st.selectbox("Leitura associada", list(opcoes.keys()))
            descricao = st.text_input("Descrição do alerta", value="Alerta manual de teste")
            nivel = st.selectbox("Nível de criticidade", ["baixo", "medio", "alto", "critico"])

            if st.button("➕ Registrar alerta"):
                resultado = post_json("/alertas/", payload={
                    "descricao": descricao, "nivel_criticidade": nivel, "id_leitura": opcoes[escolha]
                })
                if resultado:
                    st.success("Alerta registrado!")
                    st.rerun()
        else:
            st.warning("Registre pelo menos uma leitura antes de criar um alerta (relação obrigatória no banco).")

    with sub_limpeza:
        st.markdown("#### Novo registro de limpeza")
        status = st.selectbox("Status da limpeza", ["iniciada", "em_andamento", "concluida", "falha"])
        if st.button("➕ Registrar limpeza"):
            resultado = post_json("/limpeza/", payload={"status_limpeza": status})
            if resultado:
                st.success("Limpeza registrada!")
                st.rerun()

    with sub_compactacao:
        st.markdown("#### Novo registro de compactação")
        nivel_residuo = st.number_input("Nível de resíduo compactado (%)", value=50.0, step=5.0, min_value=0.0, max_value=100.0)
        if st.button("➕ Registrar compactação"):
            resultado = post_json("/compactacao/", payload={"nivel_residuo": nivel_residuo})
            if resultado:
                st.success("Compactação registrada!")
                st.rerun()

    with sub_historico:
        st.markdown("#### Novo evento de histórico")
        descricao_evento = st.text_input("Descrição do evento", value="Evento de teste manual")
        if st.button("➕ Registrar evento"):
            resultado = post_json("/historico/", payload={"descricao_evento": descricao_evento})
            if resultado:
                st.success("Evento registrado!")
                st.rerun()