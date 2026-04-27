import re
import hashlib
import pandas as pd
from collections import Counter
from typing import Dict, List
import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# DICIONÁRIO DE SINTOMAS
# Chave  = nome canônico do sintoma
# Valor  = lista de termos/variações a buscar no texto
# ─────────────────────────────────────────────────────────────────────────────

SINTOMAS_DICT: Dict[str, List[str]] = {
    # Cardiovascular
    "Dor torácica":  ["dor torácica", "dor no peito", "precordialgia", "angina", "dor precordial"],
    "Palpitações":   ["palpitação", "palpitações", "taquicardia"],
    "Arritmia":      ["arritmia"],
    "Dispneia":      ["dispneia", "falta de ar", "dificuldade respiratória", "dyspneia", "dificuldade para respirar"],
    "Edema":         ["edema", "inchaço", "edema de membros", "edema periférico"],
    "Síncope":       ["síncope", "desmaio", "perda de consciência", "lipotimia"],
    "Hipertensão":   ["hipertensão", "pressão alta", "hta"],

    # Neurológico
    "Cefaleia":         ["cefaleia", "dor de cabeça", "enxaqueca", "migrânea"],
    "Tontura":          ["tontura", "vertigem", "desequilíbrio"],
    "Convulsão":        ["convulsão", "epilepsia", "crise epiléptica", "crise convulsiva"],
    "Paralisia":        ["paralisia", "paresia", "hemiplegia", "hemiparesia", "fraqueza muscular"],
    "Alteração mental": ["confusão mental", "desorientação", "encefalopatia", "alteração do nível de consciência"],
    "AVC":              ["avc", "acidente vascular cerebral", "acidente isquêmico", "ait", "avc isquemico", "acidente vascular encefálico"],

    # Gastrointestinal
    "Náusea/Vômito": ["náusea", "vômito", "enjoo", "vômitos"],
    "Dor abdominal": ["dor abdominal", "dor na barriga", "dor epigástrica", "dor em cólica", "cólica abdominal"],
    "Diarreia":      ["diarreia", "diarréia", "evacuações líquidas"],
    "Constipação":   ["constipação", "obstipação", "prisão de ventre"],
    "Icterícia":     ["icterícia", "pele amarela", "colestase"],
    "Hematêmese":    ["hematêmese", "vômito com sangue", "sangramento digestivo alto"],
    "Melena":        ["melena", "fezes escuras", "sangramento digestivo"],

    # Respiratório
    "Tosse":     ["tosse", "tosse seca", "tosse produtiva"],
    "Hemoptise": ["hemoptise", "tosse com sangue"],
    "Chiado":    ["chiado", "sibilância", "sibilo", "broncoespasmo"],

    # Sistêmico / Geral
    "Fadiga":         ["fadiga", "cansaço", "astenia", "fraqueza", "mal-estar"],
    "Perda de peso":  ["perda de peso", "emagrecimento", "caquexia"],
    "Sudorese":       ["sudorese", "suor excessivo", "diaforese"],
    "Anemia":         ["anemia", "palidez", "hemoglobina baixa"],
    "Febre":     ["febre", "hipertermia", "febril", "estado febril"],

    # Endócrino / Metabólico
    "Diabetes":    ["diabetes", "diabetes mellitus", "hiperglicemia", "glicemia elevada"],
    "Hipoglicemia":["hipoglicemia", "glicemia baixa"],
    "Poliúria":    ["poliúria", "urina em excesso"],
    "Polidipsia":  ["polidipsia", "sede excessiva"],

    # Renal / Urológico
    "Hematúria": ["hematúria", "sangue na urina"],
    "Disúria":   ["disúria", "ardência ao urinar", "dor ao urinar"],
    "Oligúria":  ["oligúria", "redução do débito urinário"],

    # Musculoesquelético
    "Artralgia": ["artralgia", "dor nas articulações", "artrite", "dor articular"],
    "Mialgia":   ["mialgia", "dor muscular", "dores musculares"],
    "Lombalgia": ["lombalgia", "dor nas costas", "dor lombar"],

    # Dermatológico
    "Rash cutâneo": ["rash", "erupção cutânea", "exantema", "manchas na pele"],
    "Prurido":      ["prurido", "coceira", "pruritus"],
}


# ─────────────────────────────────────────────────────────────────────────────
# PRÉ-COMPILAÇÃO DOS PATTERNS
# Feita uma única vez no carregamento do módulo.
# Cada sintoma vira um único pattern OR:  \b(?:termo1|termo2|...)\b
# Isso é ~4x mais rápido do que um re.findall por termo dentro do loop.
# ─────────────────────────────────────────────────────────────────────────────

SINTOMAS_PATTERNS: Dict[str, re.Pattern] = {
    sintoma: re.compile(
        r'\b(?:' + '|'.join(re.escape(t) for t in termos) + r')\b',
        re.IGNORECASE,
    )
    for sintoma, termos in SINTOMAS_DICT.items()
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS DE HASH
# O hash de cache baseado em shape causa colisões (DataFrames com mesmo shape
# mas conteúdo diferente são tratados como iguais). Usar os PIDs é estável e
# barato para o tamanho de dataset esperado.
# ─────────────────────────────────────────────────────────────────────────────

def _hash_df(df: pd.DataFrame) -> str:
    """Hash estável baseado nos PIDs dos artigos."""
    if "pid" in df.columns:
        key = "|".join(df["pid"].astype(str).tolist())
    else:
        key = str(df.shape) + str(df.columns.tolist())
    return hashlib.md5(key.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÕES PÚBLICAS
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=600, hash_funcs={pd.DataFrame: _hash_df})
def extrair_sintomas_df(df: pd.DataFrame, campo: str = "relato_caso") -> pd.DataFrame:
    """
    Frequência de sintomas nos artigos baseada no campo escolhido.
    campo: "relato_caso" ou "palavras_chave"
    Retorna DataFrame com: sintoma | mencoes | artigos_afetados | percentual
    """
    if campo == "relato_caso":
        df_filt = df[df["tem_relato"]]
    else:
        df_filt = df[df["tem_palavras_chave"]]
        
    total = len(df_filt)

    sintoma_mencoes: Counter = Counter()
    sintoma_artigos: Counter = Counter()

    for valor in df_filt[campo]:
        # Se for lista (palavras_chave), une em string
        if isinstance(valor, list):
            texto_norm = " ".join(valor).lower()
        else:
            texto_norm = str(valor).lower()

        for sintoma, pattern in SINTOMAS_PATTERNS.items():
            matches = pattern.findall(texto_norm)
            if matches:
                sintoma_mencoes[sintoma] += len(matches)
                sintoma_artigos[sintoma] += 1

    if not sintoma_mencoes:
        return pd.DataFrame(columns=["sintoma", "mencoes", "artigos_afetados", "percentual"])

    return pd.DataFrame([
        {
            "sintoma": s,
            "mencoes": sintoma_mencoes[s],
            "artigos_afetados": sintoma_artigos[s],
            "percentual": round(sintoma_artigos[s] / total * 100, 1) if total else 0,
        }
        for s, _ in sintoma_mencoes.most_common()
    ])


@st.cache_data(ttl=600, hash_funcs={pd.DataFrame: _hash_df})
def extrair_sintomas_por_artigo(df: pd.DataFrame, campo: str = "relato_caso") -> pd.DataFrame:
    """
    Para cada artigo, lista de sintomas encontrados no campo especificado.
    """
    if campo == "relato_caso":
        df_filt = df[df["tem_relato"]]
    else:
        df_filt = df[df["tem_palavras_chave"]]

    rows = []
    for _, row in df_filt.iterrows():
        valor = row[campo]
        if isinstance(valor, list):
            texto_norm = " ".join(valor).lower()
        else:
            texto_norm = str(valor).lower()

        sintomas = [
            sintoma
            for sintoma, pattern in SINTOMAS_PATTERNS.items()
            if pattern.search(texto_norm)
        ]
        rows.append({
            "pid":      row["pid"],
            "titulo":   row["titulo"],
            "sintomas": sintomas,
            "n_sintomas": len(sintomas),
        })
    return pd.DataFrame(rows)


def get_coocorrencias(df_por_artigo: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Pares de sintomas que co-ocorrem nos mesmos artigos."""
    from itertools import combinations

    pares: Counter = Counter()
    for sintomas in df_por_artigo["sintomas"]:
        for a, b in combinations(sorted(sintomas), 2):
            pares[(a, b)] += 1

    return pd.DataFrame([
        {"sintoma_a": a, "sintoma_b": b, "coocorrencias": c}
        for (a, b), c in pares.most_common(top_n)
    ])