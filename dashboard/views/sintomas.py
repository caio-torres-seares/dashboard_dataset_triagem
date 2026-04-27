import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

_root = os.environ.get("MEDCASE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from core.sintomas import (
    extrair_sintomas_df,
    extrair_sintomas_por_artigo,
    get_coocorrencias,
    SINTOMAS_DICT,
)
from core.charts import (
    apply_template, bar_horizontal, COLORS, metric_card_html
)


def render(df: pd.DataFrame):
    st.markdown("# 🔍 Análise de Sintomas")
    
    # ── Configuração de Origem ─────────────────────────────────────
    c1, c2 = st.columns([2, 2])
    with c1:
        origem = st.radio(
            "Fonte para busca de sintomas:",
            ["Relato de Caso", "Palavras-chave"],
            horizontal=True,
            help="Relato de Caso: busca no texto livre (mais abrangente). Palavras-chave: busca nos termos indexados (mais preciso)."
        )
    
    campo_busca = "relato_caso" if origem == "Relato de Caso" else "palavras_chave"
    fonte_nome = "relatos de caso" if campo_busca == "relato_caso" else "palavras-chave"

    st.markdown(
        f"Extração automática de sintomas a partir das **{fonte_nome}** usando "
        "busca por dicionário clínico estruturado."
    )

    df_filt = df[df["tem_relato"]] if campo_busca == "relato_caso" else df[df["tem_palavras_chave"]]
    total_analisados = len(df_filt)

    if total_analisados == 0:
        st.warning(f"Nenhum artigo com {fonte_nome} encontrado.")
        return

    st.info(f"🔎 Analisando **{total_analisados:,}** {fonte_nome} · "
            f"**{len(SINTOMAS_DICT)}** categorias de sintomas no dicionário")

    # ── Extração ──────────────────────────────────────────────────
    with st.spinner(f"Extraindo sintomas das {fonte_nome}..."):
        df_sintomas = extrair_sintomas_df(df, campo=campo_busca)
        df_por_artigo = extrair_sintomas_por_artigo(df, campo=campo_busca)

    if df_sintomas.empty:
        st.warning(f"Nenhum sintoma encontrado nas {fonte_nome}. Verifique a cobertura do dicionário ou a integridade dos dados.")
        return

    # ── Métricas ─────────────────────────────────────────────────
    st.markdown("---")
    total_mencoes = int(df_sintomas["mencoes"].sum())
    sintomas_distintos = len(df_sintomas)
    artigos_com_sintoma = int((df_por_artigo["n_sintomas"] > 0).sum())
    media_sintomas = df_por_artigo["n_sintomas"].mean()

    cols = st.columns(4)
    metricas_cards = [
        ("Menções Totais", f"{total_mencoes:,}", COLORS["primary"]),
        ("Sintomas Distintos", str(sintomas_distintos), COLORS["secondary"]),
        ("Artigos c/ ≥1 Sintoma", f"{artigos_com_sintoma:,}", COLORS["success"]),
        ("Média por Artigo", f"{media_sintomas:.1f}", COLORS["warning"]),
    ]
    for col_, (label, value, color) in zip(cols, metricas_cards):
        with col_:
            st.markdown(metric_card_html(label, value, color=color), unsafe_allow_html=True)

    # ── Filtros Globais da Página ────────────────────────────────
    with st.expander("⚙️ Configurações da Análise", expanded=True):
        c1, c2, c3 = st.columns([2, 2, 2])
        with c1:
            metrica = st.radio(
                "Métrica principal",
                ["mencoes", "artigos_afetados", "percentual"],
                format_func=lambda x: {
                    "mencoes": "Total de menções",
                    "artigos_afetados": "Artigos afetados",
                    "percentual": "% dos artigos",
                }[x],
                horizontal=True,
                key="metrica_global"
            )
        with c2:
            top_n = st.slider("Top N sintomas (Gráficos/Heatmap)", 5, min(50, len(df_sintomas)), 15, key="top_n_global")
        with c3:
            top_n_cooc = st.slider("Top N pares (Co-ocorrência)", 10, 50, 20, key="top_n_cooc_global")
        
        label_metrica = {
            "mencoes": "Menções",
            "artigos_afetados": "Artigos",
            "percentual": "% Artigos",
        }[metrica]

    st.markdown("---")

    # ── Tabs de análise ───────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Frequência", "🌡️ Treemap", "🔗 Co-ocorrência", "🗂️ Por Artigo"
    ])

    # ── Tab 1: Frequência ─────────────────────────────────────────
    with tab1:
        df_top = df_sintomas.nlargest(top_n, metrica)
        fig = bar_horizontal(
            df_top, x=metrica, y="sintoma",
            title=f"Top {top_n} Sintomas — {label_metrica}",
            top_n=top_n,
        )
        st.plotly_chart(fig, width='stretch')

        # Tabela completa
        st.markdown("#### Tabela Completa de Sintomas")
        df_display = df_sintomas.copy()
        df_display.columns = ["Sintoma", "Menções", "Artigos Afetados", "% Artigos"]
        st.dataframe(
            df_display,
            width='stretch',
            hide_index=True,
        )

    # ── Tab 2: Treemap ────────────────────────────────────────────
    with tab2:
        st.markdown(f"#### Treemap de Sintomas por {label_metrica}")
        st.markdown(f"Tamanho proporcional ao valor de **{label_metrica}**.")

        fig_tree = px.treemap(
            df_sintomas.nlargest(top_n * 2, metrica), # Mostra um pouco mais que o Top N para contexto
            path=["sintoma"],
            values=metrica,
            color=metrica,
            title=f"Distribuição de Sintomas ({label_metrica})",
            color_continuous_scale=[
                [0, COLORS["surface"]],
                [0.3, COLORS["secondary"]],
                [1, COLORS["primary"]],
            ],
            hover_data=["mencoes", "artigos_afetados", "percentual"],
        )
        fig_tree.update_traces(
            textinfo="label+value",
            textfont_size=12,
        )
        fig_tree.update_layout(height=500)
        st.plotly_chart(apply_template(fig_tree), width='stretch')

    # ── Tab 3: Co-ocorrência ──────────────────────────────────────
    with tab3:
        st.markdown("#### Sintomas que Aparecem Juntos nos Mesmos Artigos")

        df_cooc = get_coocorrencias(df_por_artigo, top_n=top_n_cooc)

        if df_cooc.empty:
            st.info("Dados insuficientes para calcular co-ocorrências.")
        else:
            # Bar chart dos pares
            df_cooc["par"] = df_cooc["sintoma_a"] + " + " + df_cooc["sintoma_b"]
            fig_cooc = px.bar(
                df_cooc.head(top_n_cooc),
                x="coocorrencias",
                y="par",
                orientation="h",
                title=f"Top {top_n_cooc} Pares de Sintomas Co-ocorrentes",
                color="coocorrencias",
                color_continuous_scale=[[0, COLORS["secondary"]], [1, COLORS["primary"]]],
            )
            fig_cooc.update_layout(
                yaxis={"categoryorder": "total ascending"},
                showlegend=False,
            )
            fig_cooc.update_traces(marker_line_width=0)
            st.plotly_chart(apply_template(fig_cooc), width='stretch')

            # Heatmap de co-ocorrência
            st.markdown(f"#### Mapa de Calor — Co-ocorrências (Baseado no Top {top_n} {label_metrica})")
            
            # Usa os sintomas do Top N global para o heatmap
            sintomas_heatmap = df_sintomas.nlargest(top_n, metrica)["sintoma"].tolist()

            df_artigos_filt = df_por_artigo.copy()
            # Monta matriz
            matrix_data = {}
            for s in sintomas_heatmap:
                matrix_data[s] = {}
                for s2 in sintomas_heatmap:
                    if s == s2:
                        matrix_data[s][s2] = 0
                        continue
                    count = df_artigos_filt.apply(
                        lambda row: int(s in row["sintomas"] and s2 in row["sintomas"]),
                        axis=1
                    ).sum()
                    matrix_data[s][s2] = int(count)

            matrix_df = pd.DataFrame(matrix_data)
            fig_heat = go.Figure(data=go.Heatmap(
                z=matrix_df.values,
                x=matrix_df.columns.tolist(),
                y=matrix_df.index.tolist(),
                colorscale=[
                    [0, COLORS["surface"]],
                    [0.4, COLORS["secondary"]],
                    [1, COLORS["primary"]],
                ],
                showscale=True,
            ))
            fig_heat.update_layout(
                title=f"Heatmap de Co-ocorrência (Top {top_n} Sintomas)",
                height=max(400, 150 + (top_n * 20)), # Altura dinâmica baseada no N
                xaxis=dict(tickangle=-45),
            )
            st.plotly_chart(apply_template(fig_heat), width='stretch')

    # ── Tab 4: Por Artigo ─────────────────────────────────────────
    with tab4:
        st.markdown("#### Artigos e Sintomas Identificados")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_sintoma = st.multiselect(
                "Filtrar por sintoma",
                options=sorted(df_sintomas["sintoma"].tolist()),
                key="filtro_sintoma_artigo",
            )
        with col_f2:
            min_sintomas = st.slider(
                "Mínimo de sintomas por artigo",
                0, int(df_por_artigo["n_sintomas"].max()), 0,
                key="min_sintomas"
            )

        df_filtrado = df_por_artigo[df_por_artigo["n_sintomas"] >= min_sintomas]
        if filtro_sintoma:
            df_filtrado = df_filtrado[
                df_filtrado["sintomas"].apply(
                    lambda s: any(x in s for x in filtro_sintoma)
                )
            ]

        st.markdown(f"**{len(df_filtrado)}** artigos encontrados")

        # Formata para exibição
        df_exib = df_filtrado[["pid", "titulo", "n_sintomas", "sintomas"]].copy()
        df_exib["sintomas"] = df_exib["sintomas"].apply(lambda x: ", ".join(x) if x else "—")
        df_exib.columns = ["PID", "Título", "Nº Sintomas", "Sintomas Identificados"]

        st.dataframe(df_exib, width='stretch', hide_index=True)

        # Distribuição de sintomas por artigo
        st.markdown("#### Distribuição — Quantos Sintomas por Artigo?")
        fig_dist = px.histogram(
            df_por_artigo,
            x="n_sintomas",
            nbins=max(1, int(df_por_artigo["n_sintomas"].max())),
            title="Histograma — Nº de Sintomas por Artigo",
            labels={"n_sintomas": "Nº de Sintomas", "count": "Artigos"},
            color_discrete_sequence=[COLORS["primary"]],
        )
        fig_dist.update_traces(marker_line_width=0)
        st.plotly_chart(apply_template(fig_dist), width='stretch')
