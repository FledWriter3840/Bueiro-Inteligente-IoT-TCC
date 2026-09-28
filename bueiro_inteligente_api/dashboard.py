import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import date, datetime

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Bueiro Inteligente - Painel", page_icon="📉​", layout="wide")


# ---------------------------------------------------------------
# Funções auxiliares de acesso à API
# ---------------------------------------------------------------
def formatar_datas_pt_br(df: pd.DataFrame) -> pd.DataFrame:
    """Formata timestamps da API para o padrão brasileiro na apresentação."""
    df = df.copy()
    for coluna in ("data_hora", "data_analise"):
        if coluna in df.columns:
            df[coluna] = pd.to_datetime(df[coluna], errors="coerce").dt.strftime(
                "%d/%m/%Y %H:%M:%S"
            )
    return df


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


def calcular_indice_constancia_limpeza(limpezas: list[dict], janela_dias: int = 180):
    """Mede a regularidade dos intervalos entre registros de limpeza na janela."""
    datas = pd.to_datetime(
        pd.Series([limpeza.get("data_hora") for limpeza in limpezas]),
        errors="coerce",
        utc=True,
    ).dropna().drop_duplicates().sort_values()
    limite = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=janela_dias)
    datas = datas[datas >= limite]
    if len(datas) < 3:
        return None, len(datas)

    intervalos = datas.diff().dropna().dt.total_seconds() / 86400
    media = intervalos.mean()
    if media <= 0:
        return None, len(datas)

    coeficiente_variacao = intervalos.std(ddof=1) / media
    indice = 100 / (1 + coeficiente_variacao)
    return float(indice), len(datas)


CORES_RISCO = {
    "Baixo": "#2e8b57",
    "Médio": "#d6a500",
    "Alto": "#ed7d31",
    "Crítico": "#c0392b",
}
COR_GRAFICO_TEMPERATURA = "#f97316"


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

# ---------------------------------------------------------------
# Barra lateral: Localização + Telemetria Externa
# ---------------------------------------------------------------
with st.sidebar:
    # ── Seletor de Localização ──────────────────────────────────
    st.header("📍 Localização do Bueiro")
    st.caption("Coordenadas usadas pela IA, clima e topografia")

    PRESETS_LOCALIZACAO = {
        "São Paulo - Centro (padrão)": (-23.5505, -46.6333),
        "São Paulo - Marginal Tietê":  (-23.5230, -46.6820),
        "São Paulo - Marginal Pinheiros": (-23.5870, -46.6920),
        "São Paulo - Ipiranga":        (-23.5900, -46.6100),
        "Rio de Janeiro - Centro":     (-22.9068, -43.1729),
        "Curitiba - Centro":           (-25.4284, -49.2733),
        "Personalizado":               (None, None),
    }

    opcao_inventario = "Inventário rodoviário (bueiros.csv)"
    opcao_sac = "Localização do SAC (bueiro/boca de lobo)"
    preset_escolhido = st.selectbox(
        "Local predefinido",
        [*PRESETS_LOCALIZACAO.keys(), opcao_inventario, opcao_sac],
        key="preset_local",
    )

    bueiros_rota = []
    bueiro_selecionado = None
    local_sac_selecionado = None
    ponto_selecionado = "Montante"
    if preset_escolhido == opcao_inventario:
        rodovias_disponiveis = get_json("/bueiros/rodovias") or []
        if rodovias_disponiveis:
            rodovia = st.selectbox("Rodovia do inventário", rodovias_disponiveis, key="bueiro_rodovia")
            bueiros_rota = get_json("/bueiros/", params={"rodovia": rodovia}) or []
        if bueiros_rota:
            bueiro_selecionado = st.selectbox(
                "Bueiro por quilômetro",
                bueiros_rota,
                format_func=lambda b: f"km {b['km']:.3f} | {b['regional']} | #{b['id']}",
                key=f"bueiro_registro_{rodovia}",
            )
            ponto_selecionado = st.selectbox(
                "Coordenada do bueiro",
                ["Montante", "Jusante"],
                key=f"bueiro_ponto_{bueiro_selecionado['id']}",
            )
            sufixo_ponto = ponto_selecionado.lower()
            preset_lat = bueiro_selecionado[f"latitude_{sufixo_ponto}"]
            preset_lon = bueiro_selecionado[f"longitude_{sufixo_ponto}"]
        else:
            preset_lat, preset_lon = -23.5505, -46.6333
            st.warning("Não há bueiros com coordenadas válidas para essa rodovia.")
    elif preset_escolhido == opcao_sac:
        locais_sac = get_json("/bueiros/locais-sac") or []
        if locais_sac:
            local_sac_selecionado = st.selectbox(
                "Local do chamado SAC",
                locais_sac,
                format_func=lambda local: (
                    f"{local['logradouro']}, {local['numero']} · "
                    f"{local['total_solicitacoes']} chamado(s)"
                ),
                key="local_sac_selecionado",
            )
            preset_lat = local_sac_selecionado["latitude"]
            preset_lon = local_sac_selecionado["longitude"]
        else:
            preset_lat, preset_lon = -23.5505, -46.6333
            st.warning("Não há locais georreferenciados no arquivo de chamados SAC.")
    else:
        preset_lat, preset_lon = PRESETS_LOCALIZACAO[preset_escolhido]

    chave_localizacao = (
        f"inventario_{bueiro_selecionado['id']}_{ponto_selecionado}"
        if bueiro_selecionado
        else f"{local_sac_selecionado['id']}" if local_sac_selecionado
        else preset_escolhido.replace(" ", "_")
    )
    if preset_escolhido == "Personalizado":
        user_lat = st.number_input("Latitude", value=-23.5505, format="%.7f", key="lat_input")
        user_lon = st.number_input("Longitude", value=-46.6333, format="%.7f", key="lon_input")
    else:
        user_lat = st.number_input(
            "Latitude", value=float(preset_lat), format="%.7f", key=f"lat_{chave_localizacao}"
        )
        user_lon = st.number_input(
            "Longitude", value=float(preset_lon), format="%.7f", key=f"lon_{chave_localizacao}"
        )

    if bueiro_selecionado:
        st.caption(f"{bueiro_selecionado['rodovia']} · km {bueiro_selecionado['km']:.3f} · {ponto_selecionado}")
    elif local_sac_selecionado:
        st.caption("Local do SAC selecionado; use o cadastro abaixo para adicioná-lo ao inventário.")

    with st.expander("Adicionar novo bueiro", expanded=False):
        mensagem_cadastro = st.session_state.pop("bueiro_cadastrado_msg", None)
        if mensagem_cadastro:
            st.success(mensagem_cadastro)

        with st.form("form_novo_bueiro", clear_on_submit=False):
            regional_nova = st.text_input(
                "Regional",
                value="Cadastro via SAC" if local_sac_selecionado else "Cadastro manual",
                max_chars=80,
            )
            elemento_novo = st.selectbox(
                "Elemento",
                ["Bueiro", "Boca de lobo", "Poço de visita", "Outro"],
                index=1 if local_sac_selecionado else 0,
            )
            rodovia_nova = st.text_input(
                "Rodovia ou logradouro",
                value=(
                    f"{local_sac_selecionado['logradouro']}, {local_sac_selecionado['numero']}"
                    if local_sac_selecionado
                    else bueiro_selecionado["rodovia"] if bueiro_selecionado else ""
                ),
                max_chars=80,
            )
            km_novo = st.number_input("Quilômetro / referência", min_value=0.0, value=0.0, step=0.1)
            levantamento_novo = st.date_input("Data do levantamento", value=date.today())
            tipo_novo = st.text_input(
                "Tipo / material",
                value="Boca de lobo (local do SAC)" if local_sac_selecionado else "Boca de lobo",
                max_chars=160,
            )
            extensao_nova = st.number_input("Extensão (m)", min_value=0.0, value=0.0, step=0.5)
            dimensao_nova = st.number_input("Dimensão (m)", min_value=0.0, value=0.0, step=0.1)
            st.caption("Informe as coordenadas geográficas dos pontos de montante e jusante.")
            latitude_montante_nova = st.number_input(
                "Latitude de montante", min_value=-90.0, max_value=90.0,
                value=float(user_lat), format="%.7f",
            )
            longitude_montante_nova = st.number_input(
                "Longitude de montante", min_value=-180.0, max_value=180.0,
                value=float(user_lon), format="%.7f",
            )
            latitude_jusante_nova = st.number_input(
                "Latitude de jusante", min_value=-90.0, max_value=90.0,
                value=float(user_lat), format="%.7f",
            )
            longitude_jusante_nova = st.number_input(
                "Longitude de jusante", min_value=-180.0, max_value=180.0,
                value=float(user_lon), format="%.7f",
            )
            salvar_bueiro = st.form_submit_button("Salvar novo bueiro")

        if salvar_bueiro:
            if not regional_nova.strip() or not rodovia_nova.strip() or not tipo_novo.strip():
                st.error("Preencha Regional, Rodovia ou logradouro e Tipo / material.")
            else:
                resultado_cadastro = post_json("/bueiros/", payload={
                    "regional": regional_nova.strip(),
                    "elemento": elemento_novo,
                    "rodovia": rodovia_nova.strip(),
                    "levantamento": levantamento_novo.isoformat(),
                    "km": km_novo,
                    "extensao_m": extensao_nova or None,
                    "dimensao_m": dimensao_nova or None,
                    "tipo": tipo_novo.strip(),
                    "latitude_montante": latitude_montante_nova,
                    "longitude_montante": longitude_montante_nova,
                    "latitude_jusante": latitude_jusante_nova,
                    "longitude_jusante": longitude_jusante_nova,
                })
                if resultado_cadastro:
                    st.session_state["bueiro_cadastrado_msg"] = (
                        f"Bueiro cadastrado com identificador {resultado_cadastro['id']}. "
                        "Ele já estará disponível no inventário."
                    )
                    st.rerun()

    # Parâmetros globais de localização para todas as chamadas
    loc_params = {"lat": user_lat, "lon": user_lon}

    st.divider()

    # ── Telemetria Externa ──────────────────────────────────────
    st.header("🌍 Telemetria Externa")
    st.caption("Dados ambientais em tempo real (OpenWeatherMap & Copernicus DEM)")

    clima_side = get_json("/ia/clima-atual", params=loc_params)
    if clima_side and clima_side.get("disponivel"):
        st.subheader("🌤️ Clima Atual")
        st.write(f"**Condição:** {clima_side.get('descricao_clima')}")
        st.write(f"**Temperatura:** {clima_side.get('temperatura_c')} °C")
        st.write(f"**Umidade:** {clima_side.get('umidade_pct')}%")
        st.write(f"**Chuva acumulada:** {clima_side.get('chuva_mm_h')} mm/h")
        st.write(f"**Previsão 3h:** {clima_side.get('previsao_chuva_proximas_3h_mm')} mm")
    else:
        st.caption("🌤️ Clima: Fallback ativo")

    st.divider()
    topo_side = get_json("/ia/topografia-atual", params=loc_params)
    if topo_side and topo_side.get("disponivel"):
        st.subheader("⛰️ Topografia (COP30)")
        st.write(f"**Cota Altimétrica:** {topo_side.get('altitude_metros')} m")
        fundo_label = "Sim ⚠️ (Depressão)" if topo_side.get("eh_fundo_de_vale") else "Não"
        st.write(f"**Fundo de Vale:** {fundo_label}")
        st.write(f"**Declividade:** {topo_side.get('declividade_pct')}%")
        st.write(f"**Risco Topográfico:** {topo_side.get('classificacao_risco')}")
    else:
        st.caption("⛰️ Topografia: Cota padrão")

tab_geral, tab_leituras, tab_eventos, tab_ia, tab_simulacao, tab_manual, tab_mapa = st.tabs(
    ["Visão Geral", "Leituras", "Alertas & Eventos", "IA & Previsão", "Simulação", "Inserir Dados", "Mapa de Bueiros"]
)


# ---------------------------------------------------------------
# ABA 1: Visão Geral
# ---------------------------------------------------------------
with tab_geral:
    leituras = get_json("/sensores/leituras") or []
    alertas = get_json("/alertas/") or []
    previsao = get_json("/ia/previsao", params={"id_sensor": 1, **loc_params})

    col1, col2, col3, col4, col5 = st.columns(5)

    if leituras:
        ultima = leituras[0]
        col1.metric("Última leitura", f"{ultima['valor_leitura']:.1f} {ultima['unidade_medida']}")
    else:
        col1.metric("Última leitura", "sem dados")

    if previsao:
        col2.metric("Risco de Alagamento", previsao["nivel_risco"])
        col3.metric("Probabilidade", f"{previsao['probabilidade_entupimento'] * 100:.0f}%")
        urgencia = previsao.get("urgencia_limpeza", "Rotina")
        col4.metric("Urgência Limpeza", urgencia)
    else:
        col2.metric("Risco", "—")
        col3.metric("Probabilidade", "—")
        col4.metric("Urgência Limpeza", "—")

    col5.metric("Alertas registrados", len(alertas))

    if previsao:
        if previsao["nivel_risco"] in ("Alto", "Crítico"):
            st.error(f"⚠️ **Risco Iminente:** {previsao['recomendacao']}")
        else:
            st.success(f"ℹ️ **Status:** {previsao['recomendacao']}")

        rec_limp = previsao.get("recomendacao_limpeza")
        if rec_limp:
            st.info(f"🧹 **Diretriz de Limpeza:** {rec_limp}")

        risco_atual = previsao.get("nivel_risco", "Baixo")
        urgencia_atual = previsao.get("urgencia_limpeza", "Rotina")
        risco_urgente = risco_atual == "Crítico" or urgencia_atual in ("Urgente", "Emergência")
        risco_elevado = risco_atual == "Alto" or urgencia_atual == "Preventiva"
        cor_previsao = (
            "#c0392b" if risco_urgente else
            "#ed7d31" if risco_elevado else
            CORES_RISCO.get(risco_atual, "#2e8b57")
        )
        fig_risco = px.bar(
            pd.DataFrame({
                "Indicador": ["Probabilidade de entupimento"],
                "Probabilidade": [previsao.get("probabilidade_entupimento", 0)],
            }),
            x="Indicador",
            y="Probabilidade",
            title="IA / Previsão — risco e necessidade de limpeza",
        )
        fig_risco.update_traces(
            marker_color=cor_previsao,
            hovertemplate=(
                f"Risco: {risco_atual}<br>Limpeza: {urgencia_atual}"
                "<br>Probabilidade: %{y:.0%}<extra></extra>"
            ),
        )
        fig_risco.update_yaxes(range=[0, 1], tickformat=".0%", title="Probabilidade")
        fig_risco.update_layout(showlegend=False, xaxis_title=None)
        st.plotly_chart(fig_risco, use_container_width=True)

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
        fig.update_traces(line_color=COR_GRAFICO_TEMPERATURA, line_width=2.5)
        fig.update_xaxes(tickformat="%d/%m/%Y %H:%M")
        fig.add_hline(y=15, line_dash="dash", line_color="red",
                       annotation_text="Limite crítico (15cm)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma leitura registrada ainda.")

    limpezas_indice = get_json("/limpeza/") or []
    indice_constancia, registros_indice = calcular_indice_constancia_limpeza(limpezas_indice)
    if indice_constancia is None:
        valor_indice = "Dados insuficientes"
        detalhe_indice = f"São necessários 3 registros nos últimos 180 dias; encontrados: {registros_indice}."
    else:
        valor_indice = f"{indice_constancia:.0f}/100"
        detalhe_indice = f"Calculado com {registros_indice} registros nos últimos 180 dias."
    st.metric("Índice de constância de limpeza", valor_indice)
    st.caption(
        f"{detalhe_indice} Indicador global dos registros do sistema, não individual por bueiro. "
        "Quanto mais regulares os intervalos, maior o índice."
    )
    st.caption(
        "Método: IC = 100 / (1 + CV), em que CV = desvio-padrão amostral / média dos intervalos. "
        "Referência para o CV: [NIST Dataplot — Coefficient of Variation]"
        "(https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/coefvari.htm). "
        "O índice é uma métrica operacional derivada para este projeto, não uma norma de manutenção."
    )


# ---------------------------------------------------------------
# ABA 2: Leituras (tabela detalhada)
# ---------------------------------------------------------------
with tab_leituras:
    st.subheader("Histórico completo de leituras")
    leituras = get_json("/sensores/leituras") or []
    if leituras:
        df = pd.DataFrame(leituras)
        st.dataframe(formatar_datas_pt_br(df), use_container_width=True, hide_index=True)
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
            st.dataframe(formatar_datas_pt_br(pd.DataFrame(alertas)), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum alerta registrado.")

        st.subheader("🧹 Limpeza")
        limpezas = get_json("/limpeza/") or []
        if limpezas:
            st.dataframe(formatar_datas_pt_br(pd.DataFrame(limpezas)), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma limpeza registrada.")

    with col_b:
        st.subheader("🗜️ Compactação")
        compactacoes = get_json("/compactacao/") or []
        if compactacoes:
            st.dataframe(formatar_datas_pt_br(pd.DataFrame(compactacoes)), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma compactação registrada.")

        st.subheader("📜 Histórico do sistema")
        historico = get_json("/historico/") or []
        if historico:
            st.dataframe(formatar_datas_pt_br(pd.DataFrame(historico)), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum evento registrado.")


# ---------------------------------------------------------------
# ABA 4: Comparativo dos dois motores de IA
# ---------------------------------------------------------------
with tab_ia:
    st.subheader("Comparativo entre os motores de IA")
    st.caption("Motor 1: Multivariado (6 Fontes). Motor 2: Machine Learning.")

    if st.button("🧠 Rodar comparativo agora"):
        comparativo = get_json("/ia/comparativo", params={"id_sensor": 1, **loc_params})
        if comparativo:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 📐 Motor Multivariado (6 Fontes)")
                r = comparativo["motor_regressao"]
                st.metric("Risco", r["nivel_risco"])
                st.metric("Probabilidade", f"{r['probabilidade_entupimento'] * 100:.0f}%")
                st.write(f"**Urgência de Limpeza:** {r.get('urgencia_limpeza', 'Rotina')}")
                st.write(f"**Tendência:** {r['tendencia']}")
                st.write(f"**Taxa de variação:** {r['taxa_variacao_cm_min']:.2f} cm/min")
                st.write(f"**Recomendação:** {r['recomendacao']}")
                if r.get("recomendacao_limpeza"):
                    st.info(f"🧹 **Limpeza:** {r['recomendacao_limpeza']}")

                # Scores por dimensão
                scores = r.get("scores_detalhados", {})
                if scores:
                    st.markdown("#### Scores por Dimensão:")
                    df_scores = pd.DataFrame(list(scores.items()), columns=["Dimensão", "Score (0-1)"])
                    st.bar_chart(df_scores.set_index("Dimensão"))

            with col2:
                st.markdown("### 🤖 Motor Machine Learning")
                m = comparativo["motor_machine_learning"]
                st.metric("Risco", m["nivel_risco"])
                st.metric("Confiança", f"{m['probabilidade_classe'] * 100:.0f}%")
                st.write(f"**Modelo:** {m['modelo_utilizado']}")
                st.write("**Probabilidades por classe:**")
                df_probabilidades = pd.DataFrame(
                    list(m["classes_probabilidades"].items()),
                    columns=["Risco", "Probabilidade"],
                )
                fig_classes = px.bar(
                    df_probabilidades,
                    x="Risco",
                    y="Probabilidade",
                    color="Risco",
                    color_discrete_map=CORES_RISCO,
                    title=f"Probabilidade por nível de risco · limpeza {r.get('urgencia_limpeza', 'Rotina').lower()}",
                )
                fig_classes.update_yaxes(range=[0, 1], tickformat=".0%")
                fig_classes.update_layout(showlegend=False)
                st.plotly_chart(fig_classes, use_container_width=True)

                # Dados climáticos
                clima = r.get("dados_climaticos_utilizados")
                if clima:
                    st.markdown("#### 🌦️ Condições Climáticas Atuais:")
                    st.write(f"- **Condição:** {clima.get('descricao', 'N/A')}")
                    st.write(f"- **Chuva acumulada:** {clima.get('chuva_mm_h', 0.0)} mm/h")
                    st.write(f"- **Umidade:** {clima.get('umidade_pct', 0)}%")
                    st.write(f"- **Previsão (3h):** {clima.get('previsao_chuva_3h_mm', 0.0)} mm")

            st.divider()
            if comparativo["convergencia"]:
                st.success(f"✅ {comparativo['observacao']}")
            else:
                st.warning(f"⚠️ {comparativo['observacao']}")
    else:
        st.info("Clique no botão acima para rodar os dois motores sobre a leitura mais recente.")

    st.divider()
    st.subheader("🌐 Status das Fontes de Dados (Multivariado)")
    fontes_info = get_json("/ia/fontes-dados")
    if fontes_info:
        st.write(f"**Total de fontes ativas:** {fontes_info.get('total_ativas', 0)} de {fontes_info.get('total_fontes', 6)}")
        df_fontes = pd.DataFrame(fontes_info.get("fontes", []))
        st.dataframe(df_fontes, use_container_width=True, hide_index=True)

    col_clima, col_topo = st.columns(2)
    with col_clima:
        clima_info = get_json("/ia/clima-atual", params=loc_params)
        if clima_info and clima_info.get("disponivel"):
            st.markdown(f"**🌤️ Clima em Tempo Real:** {clima_info.get('descricao_clima')} ({clima_info.get('temperatura_c')}°C)")
            st.caption(f"Chuva: {clima_info.get('chuva_mm_h')} mm/h | Umidade: {clima_info.get('umidade_pct')}% | Vento: {clima_info.get('vento_ms')} m/s | Previsão 3h: {clima_info.get('previsao_chuva_proximas_3h_mm')} mm")
        else:
            st.caption("🌤️ Clima: Fallback sazonal ativo (configure OPENWEATHER_API_KEY).")

    with col_topo:
        topo_info = get_json("/ia/topografia-atual", params=loc_params)
        if topo_info and topo_info.get("disponivel"):
            fundo_txt = "Sim (Depressão/Convergência)" if topo_info.get("eh_fundo_de_vale") else "Não"
            st.markdown(f"**⛰️ Topografia (Copernicus DEM):** Cota {topo_info.get('altitude_metros')}m")
            st.caption(f"Fundo de Vale: {fundo_txt} | Declividade: {topo_info.get('declividade_pct')}% | Risco: {topo_info.get('classificacao_risco')}")
        else:
            st.caption("⛰️ Topografia: Cota padrão (configure OPENTOPOGRAPHY_API_KEY no .env para ativar).")

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
            fig.update_traces(line_color=COR_GRAFICO_TEMPERATURA, line_width=2.5)
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
            opcoes = {f"#{l['id_leitura']} — {l['valor_leitura']}{l['unidade_medida']} ({pd.to_datetime(l['data_hora']).strftime('%d/%m/%Y %H:%M:%S')})": l['id_leitura']
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

with tab_mapa:
    st.subheader("Inventário geográfico de bueiros")
    st.caption("Pontos de montante e jusante do bueiros.csv; coordenadas ausentes ou inválidas são omitidas.")
    rodovias_mapa = get_json("/bueiros/rodovias") or []
    if not rodovias_mapa:
        st.info("O inventário não está disponível.")
    else:
        rodovia_padrao = (
            bueiro_selecionado["rodovia"]
            if bueiro_selecionado and bueiro_selecionado["rodovia"] in rodovias_mapa
            else rodovias_mapa[0]
        )
        rodovia_mapa = st.selectbox(
            "Rodovia para visualizar",
            rodovias_mapa,
            index=rodovias_mapa.index(rodovia_padrao),
            key="rodovia_mapa",
        )
        registros_mapa = get_json("/bueiros/", params={"rodovia": rodovia_mapa}) or []
        pontos_mapa = []
        for bueiro in registros_mapa:
            selecionado = bool(
                bueiro_selecionado
                and bueiro["id"] == bueiro_selecionado["id"]
                and bueiro["rodovia"] == rodovia_mapa
            )
            for nome_ponto, sufixo in (("Montante", "montante"), ("Jusante", "jusante")):
                pontos_mapa.append({
                    "latitude": bueiro[f"latitude_{sufixo}"],
                    "longitude": bueiro[f"longitude_{sufixo}"],
                    "Bueiro": f"{bueiro['rodovia']} · km {bueiro['km']:.3f}",
                    "Ponto": nome_ponto,
                    "Legenda": f"{'Selecionado' if selecionado else 'Inventário'} · {nome_ponto}",
                    "Tipo": bueiro["tipo"],
                })

        if pontos_mapa:
            df_mapa = pd.DataFrame(pontos_mapa)
            mapa_foca_selecionado = bool(
                bueiro_selecionado and bueiro_selecionado["rodovia"] == rodovia_mapa
            )
            centro = {
                "lat": float(user_lat) if mapa_foca_selecionado else float(df_mapa["latitude"].median()),
                "lon": float(user_lon) if mapa_foca_selecionado else float(df_mapa["longitude"].median()),
            }
            fig_mapa = px.scatter_map(
                df_mapa,
                lat="latitude",
                lon="longitude",
                color="Legenda",
                hover_name="Bueiro",
                hover_data={"Ponto": True, "Tipo": True, "latitude": False, "longitude": False},
                color_discrete_map={
                    "Selecionado · Montante": "#c0392b",
                    "Selecionado · Jusante": "#ed7d31",
                    "Inventário · Montante": "#167d9a",
                    "Inventário · Jusante": "#35a6a0",
                },
                map_style="open-street-map",
                zoom=11 if mapa_foca_selecionado else 7,
                center=centro,
                height=620,
                title=f"Bueiros inventariados · {rodovia_mapa}",
            )
            fig_mapa.update_layout(margin={"r": 0, "t": 45, "l": 0, "b": 0})
            st.plotly_chart(fig_mapa, use_container_width=True)
            st.caption(f"{len(registros_mapa)} bueiros mapeados; cada registro pode ter até dois pontos geográficos.")
        else:
            st.info("Não há coordenadas válidas para a rodovia selecionada.")

    st.divider()
    titulo_local = (
        f"{bueiro_selecionado['rodovia']} · km {bueiro_selecionado['km']:.3f}"
        if bueiro_selecionado
        else preset_escolhido
    )
    st.subheader(f"Solicitações SAC de limpeza próximas · {titulo_local}")
    raio_sac = st.slider(
        "Raio de busca dos chamados SAC (m)",
        min_value=100,
        max_value=5000,
        value=500,
        step=100,
        key="raio_sac_limpeza",
    )
    dados_sac = get_json(
        "/bueiros/solicitacoes-limpeza",
        params={"lat": user_lat, "lon": user_lon, "raio_m": raio_sac},
    )
    if dados_sac:
        sac_col1, sac_col2, sac_col3 = st.columns(3)
        sac_col1.metric("Chamados encontrados", dados_sac["total_encontradas"])
        sac_col2.metric("Finalizados no SAC", dados_sac["total_finalizadas"])
        sac_col3.metric("Cancelados no SAC", dados_sac["total_canceladas"])

        indice_sac = dados_sac.get("indice_constancia_chamados")
        if indice_sac is None:
            st.info("Índice histórico indisponível: são necessários ao menos 3 chamados finalizados próximos.")
        else:
            periodo_sac = (
                f"Período dos pareceres: {dados_sac['periodo_inicio'][:10]} a {dados_sac['periodo_fim'][:10]}. "
                if dados_sac.get("periodo_inicio") and dados_sac.get("periodo_fim")
                else ""
            )
            st.metric("Regularidade histórica dos chamados SAC", f"{indice_sac:.0f}/100")
            st.caption(
                f"{periodo_sac}Intervalo médio entre pareceres finalizados: "
                f"{dados_sac['intervalo_medio_dias']:.1f} dias. "
                "É um indicador de recorrência de solicitações encerradas, não comprovação de limpeza executada."
            )

        pontos_sac = [{
            "latitude": float(user_lat),
            "longitude": float(user_lon),
            "Camada": "Local analisado",
            "Endereço": titulo_local,
            "Situação": "Referência",
            "Data do parecer": "",
            "Distância (m)": 0,
        }]
        for solicitacao in dados_sac.get("solicitacoes", []):
            endereco = f"{solicitacao['logradouro']}, {solicitacao['numero']}".strip(", ")
            pontos_sac.append({
                "latitude": solicitacao["latitude"],
                "longitude": solicitacao["longitude"],
                "Camada": f"SAC · {solicitacao['situacao'].title()}",
                "Endereço": endereco or f"Chamado SAC #{solicitacao['id']}",
                "Situação": solicitacao["situacao"],
                "Data do parecer": solicitacao["data_parecer"],
                "Distância (m)": solicitacao["distancia_m"],
            })

        if dados_sac["total_encontradas"]:
            df_sac = pd.DataFrame(pontos_sac)
            fig_sac = px.scatter_map(
                df_sac,
                lat="latitude",
                lon="longitude",
                color="Camada",
                hover_name="Endereço",
                hover_data={
                    "Situação": True,
                    "Data do parecer": True,
                    "Distância (m)": True,
                    "latitude": False,
                    "longitude": False,
                },
                color_discrete_map={
                    "Local analisado": "#c0392b",
                    "SAC · Finalizada": "#167d9a",
                    "SAC · Cancelada": "#d6a500",
                },
                map_style="open-street-map",
                zoom=max(11, min(15, 16 - round(raio_sac / 1000))),
                center={"lat": float(user_lat), "lon": float(user_lon)},
                height=560,
                title="Chamados SAC georreferenciados no entorno",
            )
            fig_sac.update_layout(margin={"r": 0, "t": 45, "l": 0, "b": 0})
            st.plotly_chart(fig_sac, use_container_width=True)
            st.dataframe(
                pd.DataFrame(dados_sac.get("solicitacoes", [])).drop(
                    columns=["latitude", "longitude", "servico"], errors="ignore"
                ).head(20),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info(f"Nenhum chamado SAC encontrado em um raio de {raio_sac} m desta localização.")
        st.caption(
            "Fonte: sac_limpeza_bueiro.csv (2020–2021). A situação FINALIZADA indica encerramento "
            "da solicitação no SAC; não confirma, isoladamente, a execução da limpeza no bueiro."
        )