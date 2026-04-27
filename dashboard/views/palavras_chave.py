import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter
import sys, os

_root = os.environ.get("MEDCASE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)
    

from core.charts import apply_template, bar_horizontal, COLORS, metric_card_html


def render(df: pd.DataFrame):
    st.markdown("# 🏷️ Análise de Palavras-chave")
    st.markdown("Frequência e distribuição das palavras-chave indexadas nos artigos.")
    st.markdown("---")

    df_kw = df[df["tem_palavras_chave"]].copy()

    if df_kw.empty:
        st.warning("Nenhum artigo com palavras-chave encontrado.")
        return

    # ── Filtros e Limpeza ─────────────────────────────────────────
    with st.expander("⚙️ Filtros e Limpeza"):
        c1, c2 = st.columns(2)
        normalize = c1.toggle("Unificar maiúsculas e minúsculas", value=True, help="Converte tudo para minúsculo e remove espaços extras.")
        remove_generic = c2.toggle("Remover termos genéricos", value=True)
        
        exclude_list = []
        if remove_generic:
            default_exclude = "relatos de casos, relatos de casos [tipo de publicação], relato de caso, relato de casos, case report, case reports, humanos, humans, masculino, male, feminino, female, middle aged, aged, person, people"
            exclude_input = st.text_area("Termos para excluir (separados por vírgula):", value=default_exclude)
            exclude_list = [t.strip().lower() for t in exclude_input.split(",") if t.strip()]

    # Processamento das palavras-chave baseado nos filtros
    def process_keywords(kw_list):
        if not isinstance(kw_list, list): return []
        processed = []
        for kw in kw_list:
            term = kw.strip()
            if not term: continue
            
            if normalize:
                term = term.lower()
            
            check_term = term.lower()
            if remove_generic and check_term in exclude_list:
                continue
            
            processed.append(term)
        return processed

    df_kw["palavras_chave_proc"] = df_kw["palavras_chave"].apply(process_keywords)
    df_kw["n_kw_proc"] = df_kw["palavras_chave_proc"].apply(len)

    # ── Métricas ─────────────────────────────────────────────────
    todas_kw = [kw for lista in df_kw["palavras_chave_proc"] for kw in lista]
    kw_counter = Counter(todas_kw)
    total_kw = len(todas_kw)
    distintas = len(kw_counter)
    media_por_artigo = df_kw["n_kw_proc"].mean()

    cols = st.columns(4)
    for col_, (label, value, color) in zip(cols, [
        ("Artigos c/ Palavras-chave", f"{len(df_kw):,}", COLORS["primary"]),
        ("Total de Palavras-chave", f"{total_kw:,}", COLORS["accent"]),
        ("Termos Distintos", f"{distintas:,}", COLORS["secondary"]),
        ("Média por Artigo", f"{media_por_artigo:.1f}", COLORS["warning"]),
    ]):
        with col_:
            st.markdown(metric_card_html(label, value, color=color), unsafe_allow_html=True)

    st.markdown("---")

    # ── Busca por termo ───────────────────────────────────────────
    st.markdown("### 🔎 Buscar Artigos por Palavra-chave")
    busca = st.text_input("Digite um termo para buscar", placeholder="Ex: diabetes")
    if busca:
        # Busca nas palavras-chave já processadas/filtradas
        resultado = df_kw[df_kw["palavras_chave_proc"].apply(
            lambda kws: any(busca.lower() in str(kw).lower() for kw in kws)
        )].copy()
        
        st.markdown(f"**{len(resultado)}** artigos encontrados para *\"{busca}\"*")
        if not resultado.empty:
            # ── Lógica de Paginação ──────────────────────────────────────
            page_size_search = 15
            total_pages_search = max(1, (len(resultado) - 1) // page_size_search + 1)
            
            # Resetar página se a busca mudou
            if "last_busca" not in st.session_state or st.session_state["last_busca"] != busca:
                st.session_state["kw_curr_page"] = 1
                st.session_state["last_busca"] = busca
            
            if "kw_curr_page" not in st.session_state:
                st.session_state["kw_curr_page"] = 1
                
            # Garantir que a página atual não está fora dos limites (ex: após mudar filtros)
            st.session_state["kw_curr_page"] = min(st.session_state["kw_curr_page"], total_pages_search)
            
            page_search = st.session_state["kw_curr_page"]
            inicio_search = (page_search - 1) * page_size_search
            df_page_search = resultado.iloc[inicio_search : inicio_search + page_size_search]

            # ── Cabeçalho da Tabela ──────────────────────────────────────
            # PID, Título, Data, Keywords, Ação
            col_widths = [0.15, 0.45, 0.05, 0.20, 0.05]
            cols_h = st.columns(col_widths)
            cols_h[0].markdown("**PID**")
            cols_h[1].markdown("**Título**")
            cols_h[2].markdown("**Data**")
            cols_h[3].markdown("**Keywords**")
            cols_h[4].markdown("**Ver Detalhes**")
            st.markdown("<hr style='margin: 0.5rem 0; border-color: #21262D'>", unsafe_allow_html=True)

            # ── Linhas da Tabela ─────────────────────────────────────────
            for _, row in df_page_search.iterrows():
                cols = st.columns(col_widths)
                cols[0].markdown(f"<div style='font-size: 0.85rem; font-family: monospace; color: #8B949E;'>{row['pid']}</div>", unsafe_allow_html=True)
                cols[1].markdown(f"<div style='font-size: 0.85rem; font-weight: 500;'>{row['titulo']}</div>", unsafe_allow_html=True)
                cols[2].markdown(f"<div style='font-size: 0.85rem;'>{row.get('data_publicacao', '—')}</div>", unsafe_allow_html=True)
                
                kws_list = row["palavras_chave_proc"]
                kws_str = ", ".join(kws_list)
                cols[3].markdown(f"<div style='font-size: 0.8rem; color: #8B949E;'>{kws_str}</div>", unsafe_allow_html=True)
                
                if cols[4].button("📁", key=f"view_kw_{row['pid']}", width='stretch', help="Ver detalhes do artigo"):
                    st.session_state["artigo_selecionado"] = row["pid"]
                    st.session_state["next_page"] = "📄 Explorar Artigos"
                    st.rerun()
            
            # ── Controles de Paginação (Rodapé) ──────────────────────────
            if total_pages_search > 1:
                st.markdown("<br>", unsafe_allow_html=True)
                c_prev, c_page, c_next = st.columns([1, 2, 1])
                with c_prev:
                    if st.button("⬅️ Anterior", disabled=(page_search <= 1), width='stretch', key="kw_prev"):
                        st.session_state["kw_curr_page"] -= 1
                        st.rerun()
                with c_page:
                    st.markdown(f"<div style='text-align: center; color: #8B949E; padding-top: 8px; font-size: 0.9rem;'>Página <b>{page_search}</b> de {total_pages_search}</div>", unsafe_allow_html=True)
                with c_next:
                    if st.button("Próximo ➡️", disabled=(page_search >= total_pages_search), width='stretch', key="kw_next"):
                        st.session_state["kw_curr_page"] += 1
                        st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("### Top Palavras-chave")
        top_n = st.slider("Top N termos", 10, min(50, distintas) if distintas > 10 else 10, 25, key="kw_topn")
        df_top_kw = pd.DataFrame(
            kw_counter.most_common(top_n),
            columns=["termo", "frequencia"]
        )
        fig = bar_horizontal(df_top_kw, x="frequencia", y="termo",
                             title=f"Top {top_n} Palavras-chave mais Frequentes",
                             top_n=top_n)
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.markdown("### Distribuição — Palavras-chave por Artigo")
        fig2 = px.histogram(
            df_kw,
            x="n_kw_proc",
            nbins=20,
            title="Quantas Palavras-chave por Artigo",
            labels={"n_kw_proc": "Nº de Palavras-chave", "count": "Artigos"},
            color_discrete_sequence=[COLORS["secondary"]],
        )
        fig2.update_traces(marker_line_width=0)
        st.plotly_chart(apply_template(fig2), width='stretch')

        # Palavras únicas (aparecem em 1 artigo apenas)
        unicas = sum(1 for v in kw_counter.values() if v == 1)
        st.markdown(metric_card_html(
            "Palavras-chave únicas (1 artigo)",
            f"{unicas:,}",
            f"{unicas/distintas*100:.1f}% do total",
            color=COLORS["danger"]
        ), unsafe_allow_html=True)

    st.markdown("---")

    # ── Treemap ───────────────────────────────────────────────────
    st.markdown("### Treemap de Palavras-chave")
    limit_tree = min(100, distintas) if distintas > 20 else max(20, distintas)
    top_tree = st.slider("Top N para treemap", 20 if distintas > 20 else distintas, limit_tree, 40 if distintas > 40 else distintas, key="kw_tree")
    df_tree = pd.DataFrame(
        kw_counter.most_common(top_tree),
        columns=["termo", "frequencia"]
    )
    fig_tree = px.treemap(
        df_tree,
        path=["termo"],
        values="frequencia",
        title=f"Top {top_tree} Palavras-chave",
        color="frequencia",
        color_continuous_scale=[[0, COLORS["surface"]], [0.3, COLORS["secondary"]], [1, COLORS["primary"]]],
    )
    fig_tree.update_traces(textinfo="label+value")
    fig_tree.update_layout(height=450)
    st.plotly_chart(apply_template(fig_tree), width='stretch')
