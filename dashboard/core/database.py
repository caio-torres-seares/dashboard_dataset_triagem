import streamlit as st
import pandas as pd
from typing import Optional

@st.cache_data(ttl=300)
def load_artigos_csv(path: str = "data/csv/v2_dataset_relatos_caso_csv.csv") -> pd.DataFrame:
    """
    Carrega artigos a partir de um CSV.
    """
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")

        if "palavras_chave" in df.columns:
            df["palavras_chave"] = df["palavras_chave"].apply(
                lambda x: [p.strip() for p in x.split(",")] if isinstance(x, str) and x.strip() else []
            )

        # Flags
        df["tem_relato"] = df["relato_caso"].apply(
            lambda x: pd.notna(x) and bool(str(x).strip())
        )
        df["tem_resumo"] = df["resumo"].apply(
            lambda x: pd.notna(x) and bool(str(x).strip())
        )
        df["tem_palavras_chave"] = df["palavras_chave"].apply(
            lambda x: bool(x and len(x) > 0)
        )
        df["n_palavras_chave"] = df["palavras_chave"].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        )
        df["tamanho_relato"] = df["relato_caso"].apply(
            lambda x: len(str(x).split()) if x else 0
        )

        # Filtrar linhas onde o texto completo é nulo ou vazio (nesse caso, provavelmente ocorreu um erro da página estar fora do ar)
        df = df[pd.notna(df["texto_completo"]) & df["texto_completo"].str.strip().ne("")]

        return df

    except Exception as e:
        st.error(f"Erro ao carregar CSV: {e}")
        return pd.DataFrame()


def invalidate_cache():
    """Invalida o cache de dados (útil para recarregar manualmente)."""
    load_artigos_csv.clear()
