import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os

_root = os.environ.get("MEDCASE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from core.charts import (
    apply_template, bar_vertical, pie_chart,
    scatter, COLORS, metric_card_html
)


def render(df: pd.DataFrame):
    st.markdown("# 🏠 Visão Geral do Dataset")
    st.markdown("Estatísticas gerais sobre os artigos coletados do SciELO.")
    st.markdown("---")

    # ── Métricas principais ────────────────────────────────────────
    total = len(df)
    com_relato = int(df["tem_relato"].sum())
    sem_relato = total - com_relato
    com_resumo = int(df["tem_resumo"].sum())
    com_kw = int(df["tem_palavras_chave"].sum())
    taxa_relato = f"{com_relato/total*100:.1f}%" if total else "0%"

    cols = st.columns(5)
    metricas = [
        ("Total de Artigos", f"{total:,}", COLORS["primary"]),
        ("Com Relato de Caso", f"{com_relato:,}", COLORS["success"]),
        ("Sem Relato de Caso", f"{sem_relato:,}", COLORS["danger"]),
        ("Com Resumo", f"{com_resumo:,}", COLORS["accent"]),
        ("Taxa de Relatos", taxa_relato, COLORS["warning"]),
    ]
    for col, (label, value, color) in zip(cols, metricas):
        with col:
            st.markdown(metric_card_html(label, value, color=color), unsafe_allow_html=True)

    st.markdown("---")

    # ── Cobertura Temporal ──────────────────────────────────────────
    if "data_publicacao" in df.columns:
        df["ano"] = (
            df["data_publicacao"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
            .fillna("0")
            .astype(int)
        )
        df_anos_validos = df[df["ano"] > 0]

        if not df_anos_validos.empty:
            st.markdown("### 📅 Cobertura Temporal")

            artigo_antigo = df_anos_validos.loc[df_anos_validos["ano"].idxmin()]
            artigo_recente = df_anos_validos.loc[df_anos_validos["ano"].idxmax()]
            contagem_anos = df_anos_validos["ano"].value_counts()
            ano_pico = int(contagem_anos.idxmax())
            qtd_pico = int(contagem_anos.max())
            periodo = int(artigo_recente["ano"]) - int(artigo_antigo["ano"])

            def _titulo_curto(titulo, limite=40):
                titulo = str(titulo)
                return titulo[:limite] + "..." if len(titulo) > limite else titulo

            cols_tempo = st.columns(4)
            metricas_tempo = [
                ("Artigo Mais Antigo", str(artigo_antigo["ano"]), _titulo_curto(artigo_antigo["titulo"]), COLORS["secondary"]),
                ("Artigo Mais Recente", str(artigo_recente["ano"]), _titulo_curto(artigo_recente["titulo"]), COLORS["accent"]),
                ("Período Coberto", f"{periodo} anos", f"{artigo_antigo['ano']}–{artigo_recente['ano']}", COLORS["primary"]),
                ("Ano de Pico", str(ano_pico), f"{qtd_pico:,} artigos", COLORS["warning"]),
            ]
            for col_, (label, value, delta, color) in zip(cols_tempo, metricas_tempo):
                with col_:
                    st.markdown(metric_card_html(label, value, delta=delta, color=color), unsafe_allow_html=True)

            st.markdown("---")

    # ── Row 1: completude + publicações por ano ────────────────────
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Completude dos Campos")
        completude = pd.DataFrame({
            "campo": ["Relato de Caso", "Resumo", "Palavras-chave"],
            "preenchido": [com_relato, com_resumo, com_kw],
            "total": [total, total, total],
        })
        completude["ausente"] = completude["total"] - completude["preenchido"]

        fig = px.bar(
            completude,
            x="campo",
            y=["preenchido", "ausente"],
            title="Campos Preenchidos vs Ausentes",
            barmode="stack",
            color_discrete_map={
                "preenchido": COLORS["success"],
                "ausente": COLORS["danger"],
            },
            labels={"value": "Artigos", "variable": ""},
        )
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(apply_template(fig), width='stretch')

    with col2:
        st.markdown("### Artigos por Ano de Publicação")
        if "ano" in df.columns:
            df_ano_status = (
                df[df["ano"] > 0]
                .groupby(["ano", "tem_relato"])
                .size()
                .reset_index(name="quantidade")
            )
            df_ano_status["tipo"] = df_ano_status["tem_relato"].map(
                {True: "Com Relato", False: "Sem Relato"}
            )

            fig2 = px.bar(
                df_ano_status,
                x="ano",
                y="quantidade",
                color="tipo",
                title="Artigos por Ano (Com/Sem Relato de Caso)",
                color_discrete_map={
                    "Com Relato": COLORS["primary"],
                    "Sem Relato": COLORS["grid"],
                },
                barmode="stack",
                labels={"quantidade": "Artigos", "ano": "Ano"},
            )
            fig2.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02))
            st.plotly_chart(apply_template(fig2), width='stretch')

    st.markdown("---")

    # ── Row 2: Tamanho dos relatos + status de reprocessamento ────
    col3, col4 = st.columns([2, 1])

    with col3:
        st.markdown("### Distribuição do Tamanho dos Relatos (palavras)")
        df_relatos = df[df["tem_relato"] & (df["tamanho_relato"] > 0)]
        if not df_relatos.empty:
            fig3 = px.histogram(
                df_relatos,
                x="tamanho_relato",
                nbins=40,
                title="Histograma — Palavras por Relato de Caso",
                labels={"tamanho_relato": "Nº de Palavras", "count": "Artigos"},
                color_discrete_sequence=[COLORS["primary"]],
            )
            fig3.update_traces(marker_line_width=0, opacity=0.85)
            media = df_relatos["tamanho_relato"].mean()
            fig3.add_vline(
                x=media, line_dash="dash", line_color=COLORS["warning"],
                annotation_text=f"Média: {media:.0f}", annotation_position="top right"
            )
            st.plotly_chart(apply_template(fig3), width='stretch')

            # Stats descritivas
            stats = df_relatos["tamanho_relato"].describe()
            scols = st.columns(4)
            for col_, (label, key) in zip(scols, [
                ("Mínimo", "min"), ("Mediana", "50%"),
                ("Média", "mean"), ("Máximo", "max")
            ]):
                with col_:
                    st.metric(label, f"{stats[key]:.0f} palavras")

    with col4:
        st.markdown("### Status de Reprocessamento")
        if "reprocess_status" in df.columns:
            status_counts = (
                df["reprocess_status"]
                .fillna("sem_status")
                .value_counts()
                .reset_index()
            )
            status_counts.columns = ["status", "quantidade"]
            fig4 = pie_chart(status_counts, "status", "quantidade",
                             "Status dos Artigos")
            st.plotly_chart(fig4, width='stretch')

    st.markdown("---")

    # ── Confiança da IA ──────────────────────────────────────────
    st.markdown("### 🤖 Confiança da Análise de IA")

    if "ia_confianca" in df.columns and df["ia_confianca"].notna().any():
        df_ia = df[df["ia_confianca"].notna()]
        total_ia = len(df_ia)
        pct_ia = total_ia / total * 100 if total else 0
        confianca_media = df_ia["ia_confianca"].mean()

        cols_ia = st.columns(3)
        metricas_ia = [
            ("Artigos Analisados pela IA", f"{total_ia:,}", COLORS["primary"]),
            ("% do Dataset", f"{pct_ia:.1f}%", COLORS["accent"]),
            ("Confiança Média", f"{confianca_media:.1f}%", COLORS["success"]),
        ]
        for col_, (label, value, color) in zip(cols_ia, metricas_ia):
            with col_:
                st.markdown(metric_card_html(label, value, color=color), unsafe_allow_html=True)

        df_conf = (
            df_ia["ia_confianca"]
            .value_counts()
            .sort_index()
            .reset_index()
        )
        df_conf.columns = ["confianca", "quantidade"]
        df_conf["confianca"] = df_conf["confianca"].astype(int).astype(str) + "%"

        fig_ia = bar_vertical(
            df_conf, x="confianca", y="quantidade",
            title="Distribuição da Confiança da IA",
            color_val=COLORS["success"],
        )
        st.plotly_chart(fig_ia, width='stretch')
    else:
        st.info("ℹ️ Este dataset não possui análise de confiança da IA (disponível a partir da v3).")

    st.markdown("---")

    # ── Tabela de amostra ─────────────────────────────────────────
    with st.expander("📋 Amostra de Artigos (10 registros)"):
        colunas_exibir = ["pid", "titulo", "data_publicacao", "tem_relato",
                          "tamanho_relato", "n_palavras_chave"]
        colunas_exibir = [c for c in colunas_exibir if c in df.columns]
        st.dataframe(
            df[colunas_exibir].head(10),
            width='stretch',
            hide_index=True,
        )
