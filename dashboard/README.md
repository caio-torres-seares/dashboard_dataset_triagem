# 🩺 MedCase Explorer

Dashboard de análise exploratória de relatos de caso clínico extraídos do SciELO.

## Estrutura do Projeto

```
dashboard/
├── app.py                    ← Entrada principal (roteamento + sidebar)
├── requirements.txt
├── core/                     ← Módulos reutilizáveis
│   ├── database.py           ← Conexão MongoDB + cache de dados
│   ├── sintomas.py           ← Extração de sintomas (dicionário clínico)
│   └── charts.py             ← Helpers de gráficos Plotly (tema unificado)
│
└── views/                    ← Uma página por análise
    ├── visao_geral.py        ← Métricas gerais do dataset
    ├── sintomas.py           ← Análise de sintomas
    ├── palavras_chave.py     ← Análise de palavras-chave
    └── artigos.py            ← Explorador de artigos individuais
```

## Como Executar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Entrar na pasta
cd dashboard/

# 3. Rodar o dashboard
streamlit run app.py
```

## Análise de Sintomas

A extração de sintomas usa um **dicionário clínico** em `core/sintomas.py`.
Para adicionar novos termos, edite o dicionário `SINTOMAS_DICT`:

```python
SINTOMAS_DICT = {
    "Nome do Sintoma": ["termo1", "termo2", "variação"],
    ...
}
```

## Estrutura esperada dos documentos MongoDB

```json
{
  "pid": "S0066-782X2026000102201",
  "titulo": "...",
  "data_publicacao": "2026",
  "url": "...",
  "dados_extraidos": {
    "resumo": "...",
    "palavras_chave": ["termo1", "termo2"],
    "relato_caso": "...",
    "texto_completo": "..."
  },
  "reprocess_status": "ok"
}
```
