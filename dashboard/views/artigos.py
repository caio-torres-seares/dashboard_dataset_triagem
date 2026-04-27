import streamlit as st
import pandas as pd
import sys, os

_root = os.environ.get("MEDCASE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from core.charts import COLORS, metric_card_html
from core.sintomas import SINTOMAS_DICT
import re


def _texto_valido(valor):
    return pd.notna(valor) and isinstance(valor, str) and valor.strip()

def _encontra_sintomas(texto: str) -> list:
    """Retorna lista de sintomas encontrados no texto."""
    texto_norm = texto.lower()
    encontrados = []
    for sintoma, termos in SINTOMAS_DICT.items():
        for termo in termos:
            pattern = r'\b' + re.escape(termo) + r'\b'
            if re.search(pattern, texto_norm):
                encontrados.append(sintoma)
                break
    return encontrados


def _highlight_texto(texto: str, sintomas_encontrados: list) -> str:
    """Adiciona destaque visual nos termos encontrados no texto."""
    texto_out = texto
    for sintoma in sintomas_encontrados:
        termos = SINTOMAS_DICT.get(sintoma, [])
        for termo in termos:
            pattern = re.compile(r'(' + re.escape(termo) + r')', re.IGNORECASE)
            texto_out = pattern.sub(
                r'<mark style="background:#1C3A5E;color:#58A6FF;border-radius:3px;padding:0 3px">\1</mark>',
                texto_out
            )
    return texto_out


def render(df: pd.DataFrame):
    st.markdown("# 📄 Explorador de Artigos")
    st.markdown("Navegue e inspecione artigos individuais com extração de sintomas.")
    st.markdown("---")

    # ── Filtros ───────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        filtro_relato = st.selectbox(
            "Relato de caso",
            ["Todos", "Com relato", "Sem relato"],
            key="art_filtro_relato"
        )
    with col2:
        anos_disponiveis = sorted(
            df["data_publicacao"].dropna().astype(str)
            .str.extract(r"(\d{4})")[0].dropna().unique().tolist()
        )
        ano_selecionado = st.selectbox(
            "Ano de publicação",
            ["Todos"] + anos_disponiveis,
            key="art_ano"
        )
    with col3:
        busca_titulo = st.text_input(
            "Buscar no título",
            placeholder="Ex: hipertensão",
            key="art_busca"
        )

    # Aplica filtros
    df_filt = df.copy()
    if filtro_relato == "Com relato":
        df_filt = df_filt[df_filt["tem_relato"]]
    elif filtro_relato == "Sem relato":
        df_filt = df_filt[~df_filt["tem_relato"]]

    if ano_selecionado != "Todos":
        df_filt = df_filt[df_filt["data_publicacao"].astype(str).str.contains(ano_selecionado)]

    if busca_titulo:
        df_filt = df_filt[
            df_filt["titulo"].str.contains(busca_titulo, case=False, na=False)
        ]

    st.markdown(f"**{len(df_filt):,}** artigos encontrados")
    st.markdown("---")

    if df_filt.empty:
        st.info("Nenhum artigo corresponde aos filtros selecionados.")
        return

    # ── Lista de artigos ──────────────────────────────────────────
    col_list, col_detail = st.columns([1, 2])

    with col_list:
        st.markdown("### Artigos")
        
        # Lógica de Paginação
        page_size = 15
        total_pages = max(1, (len(df_filt) - 1) // page_size + 1)
        
        # Resetar página se os filtros mudarem
        filter_state = f"{filtro_relato}_{ano_selecionado}_{busca_titulo}"
        if "art_last_filter" not in st.session_state or st.session_state["art_last_filter"] != filter_state:
            st.session_state["art_curr_page"] = 1
            st.session_state["art_last_filter"] = filter_state
            
        if "art_curr_page" not in st.session_state:
            st.session_state["art_curr_page"] = 1
            
        st.session_state["art_curr_page"] = min(st.session_state["art_curr_page"], total_pages)
        page = st.session_state["art_curr_page"]
        
        inicio = (page - 1) * page_size
        df_page = df_filt.iloc[inicio:inicio + page_size]

        # Renderização da lista
        container_list = st.container()
        with container_list:
            for _, row in df_page.iterrows():
                tem_relato_icon = "📋" if row["tem_relato"] else "📄"
                titulo_curto = row["titulo"][:60] + "..." if len(str(row["titulo"])) > 60 else row["titulo"]

                selected = st.session_state.get("artigo_selecionado") == row["pid"]
                btn_style = "primary" if selected else "secondary"

                c_sel, c_link, c_pdf = st.columns([0.80, 0.10, 0.10])
                
                with c_sel:
                    if st.button(
                        f"{tem_relato_icon} {titulo_curto}",
                        key=f"art_btn_{row['pid']}",
                        width='stretch',
                        type=btn_style if selected else "secondary",
                    ):
                        st.session_state["artigo_selecionado"] = row["pid"]
                        st.rerun()
                
                with c_link:
                    scielo_url = row.get("url")
                    if scielo_url:
                        st.link_button("🌐", scielo_url, help="Abrir no SciELO", width='stretch')
                    else:
                        st.button("🚫", key=f"no_link_{row['pid']}", disabled=True, width='stretch')

                with c_pdf:
                    pdf_url = row.get("pdf_link")
                    if pdf_url:
                        st.link_button("📕", pdf_url, help="Abrir PDF diretamente", width='stretch')
                    else:
                        st.button("🚫", key=f"no_pdf_list_{row['pid']}", disabled=True, width='stretch', help="PDF não disponível")

        # Controles de paginação no rodapé da coluna
        if total_pages > 1:
            st.markdown("---")
            c_prev, c_page, c_next = st.columns([1, 2, 1])
            with c_prev:
                if st.button("⬅️", disabled=(page <= 1), width='stretch', key="art_prev"):
                    st.session_state["art_curr_page"] -= 1
                    st.rerun()
            with c_page:
                st.markdown(f"<div style='text-align: center; color: #8B949E; font-size: 0.85rem; padding-top: 5px;'>{page} / {total_pages}</div>", unsafe_allow_html=True)
            with c_next:
                if st.button("➡️", disabled=(page >= total_pages), width='stretch', key="art_next"):
                    st.session_state["art_curr_page"] += 1
                    st.rerun()

    # ── Detalhes do artigo ────────────────────────────────────────
    with col_detail:
        pid_sel = st.session_state.get("artigo_selecionado")

        if not pid_sel:
            st.markdown("""
            <div style="
                display:flex; align-items:center; justify-content:center;
                height:300px; border:1px dashed #21262D; border-radius:12px;
                color:#484F58; flex-direction:column; gap:12px;
            ">
                <div style="font-size:2rem">👈</div>
                <div>Selecione um artigo para ver os detalhes</div>
            </div>
            """, unsafe_allow_html=True)
            return

        artigo = df[df["pid"] == pid_sel]
        if artigo.empty:
            st.warning("Artigo não encontrado.")
            return

        artigo = artigo.iloc[0]

        st.markdown(f"### {artigo['titulo']}")
        st.markdown(f"""
        <div style="font-size:0.8rem; color:#8B949E; margin-bottom:12px">
        📅 {artigo.get('data_publicacao', '—')} &nbsp;·&nbsp; 
        🔑 {artigo.get('pid', '—')} &nbsp;·&nbsp;
        {'📋 Com relato de caso' if artigo.get('tem_relato') else '📄 Sem relato de caso'}
        </div>
        """, unsafe_allow_html=True)

        # Botões de Ação
        col_btns1, col_btns2 = st.columns([1, 1])
        with col_btns1:
            if artigo.get("url"):
                st.link_button("🔗 Ver no SciELO", artigo["url"], width='stretch')
        with col_btns2:
            pdf_url = artigo.get("pdf_link")
            if pdf_url:
                st.link_button("📕 Baixar PDF", pdf_url, width='stretch', type="primary")
            else:
                st.button("🚫 PDF Indisponível", disabled=True, width='stretch')

        st.markdown("<br>", unsafe_allow_html=True)

        # Palavras-chave
        kws = artigo.get("palavras_chave", [])
        if kws:
            st.markdown("**Palavras-chave:**")
            kw_badges = " ".join([
                f'<span style="background:#21262D;color:#58A6FF;padding:2px 8px;border-radius:4px;font-size:0.78rem;margin:2px;display:inline-block">{kw}</span>'
                for kw in kws
            ])
            st.markdown(kw_badges, unsafe_allow_html=True)

        st.markdown("---")

        # Tabs do conteúdo
        tab_resumo, tab_relato, tab_completo = st.tabs(["Resumo", "Relato de Caso", "Texto Completo"])

        with tab_resumo:
            resumo = artigo.get("resumo", "")
            if _texto_valido(resumo):
                st.markdown(resumo)
            else:
                st.info("Resumo não disponível.")

        with tab_relato:
            relato = artigo.get("relato_caso", "")
            if _texto_valido(relato):
                # Extrai e exibe sintomas
                sintomas = _encontra_sintomas(relato)
                if sintomas:
                    st.markdown("**Sintomas identificados:**")
                    badges = " ".join([
                        f'<span style="background:#1A3A2A;color:#3FB950;padding:2px 8px;border-radius:4px;font-size:0.78rem;margin:2px;display:inline-block">✓ {s}</span>'
                        for s in sintomas
                    ])
                    st.markdown(badges, unsafe_allow_html=True)
                    st.markdown("---")

                # Texto com highlight
                relato_html = _highlight_texto(relato, sintomas)
                relato_html = relato_html.replace("\n", "<br>")
                st.markdown(f"""
                <div style="
                    background:#0D1117; border:1px solid #21262D; border-radius:8px;
                    padding:16px; font-size:0.88rem; line-height:1.75;
                    max-height:500px; overflow-y:auto;
                ">
                {relato_html}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Relato de caso não disponível para este artigo.")

        with tab_completo:
            texto = artigo.get("texto_completo", "")
            if _texto_valido(texto):
                st.markdown(f"""
                <div style="
                    background:#0D1117; border:1px solid #21262D; border-radius:8px;
                    padding:16px; font-size:0.85rem; line-height:1.75;
                    max-height:600px; overflow-y:auto;
                ">
                {texto.replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Texto completo não disponível.")
