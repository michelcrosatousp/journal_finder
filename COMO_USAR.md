# 🔬 Buscador de Periódicos Científicos

Ferramenta Streamlit para pesquisadores da saúde encontrarem periódicos com fator de impacto, critérios editoriais e detecção de periódicos predatórios.

## Instalação

### 1. Pré-requisito: Python 3.10+
Verifique com:
```
python --version
```

### 2. Instalar dependências
```
pip install -r requirements.txt
```

### 3. Executar o app
```
streamlit run journal_finder.py
```
O app abrirá automaticamente no navegador em `http://localhost:8501`.

---

## Funcionalidades

### 🔍 Aba "Buscar por Tema"
- Digite palavras-chave do seu tema de pesquisa (ex: *diabetes mellitus*, *hypertension*)
- Filtre por área da saúde (Cardiologia, Oncologia, etc.)
- Aplique filtros: quartil mínimo, apenas PubMed, apenas DOAJ, excluir alto risco
- Resultados ordenados por SJR (maior impacto primeiro)

### ✅ Aba "Verificar Periódico"
- Informe o nome exato ou ISSN (ex: `0140-6736`) de um periódico
- Receba o perfil completo: SJR, quartil, área, editora
- Verifique indexação PubMed/MEDLINE e presença no DOAJ
- Avaliação automática de risco predatório com justificativas

---

## Fontes de dados

| Fonte | O que fornece |
|---|---|
| **Scimago (SJR)** | Fator de impacto, quartil Q1–Q4, área temática |
| **NCBI NLM Catalog** | Indexação no PubMed/MEDLINE |
| **DOAJ** | Verificação de acesso aberto legítimo |

---

## Critérios de risco predatório

- 🟢 **Baixo** — nenhum indicador de risco
- 🟡 **Médio** — 1 indicador (ex: não indexado no PubMed)
- 🔴 **Alto** — editora conhecida como predatória ou ≥ 2 indicadores

### Indicadores de risco
- Não indexado no PubMed/MEDLINE
- Não listado no DOAJ
- Editora constante em listas de predatórios conhecidos
- Padrão de nome suspeito
- ISSN ausente ou inválido

---

## Dicas de uso
- Use termos em **inglês** para melhores resultados no Scimago
- Para periódicos brasileiros, tente o ISSN direto
- Prefira periódicos **Q1 ou Q2** indexados no PubMed para publicações de alto impacto
- O app usa cache de 1 hora — resultados repetidos são mais rápidos
