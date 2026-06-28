# Buscador de Periódicos Científicos — Saúde

App em Streamlit que reúne, **offline e em um só lugar**, três sistemas de avaliação de
periódicos, para ajudar o pesquisador da saúde a escolher onde publicar:

- **JCR 2026** — Fator de Impacto (JIF 2026/2025) e quartil (Web of Science)
- **Scimago 2025** — SJR e quartil por categoria (Scopus)
- **Qualis/CAPES** — estrato brasileiro A1–C por área (quadriênio 2021–2024)

*Elaborado por Prof. Dr. Edgard Michel Crosato e Maria Isabel de Castro de Souza.*

---

## Rodar localmente

```bash
pip install -r requirements.txt
streamlit run journal_finder.py
```

Acesse `http://localhost:8501`. A senha fica em `.streamlit/secrets.toml`.

---

## Publicar no Streamlit Community Cloud (link fixo)

### 1. Suba o projeto para um repositório **privado** no GitHub
Devido à licença do JCR, mantenha o repositório **privado**. Arquivos necessários:

```
journal_finder.py
journals_data.json        ← base unificada (obrigatória)
images.jpg                ← logo FO-USP
Logo NTO azul.png         ← logo Núcleo de Teleodontologia
logo_faperj_cor.jpg       ← logo FAPERJ
telessaude.jpg            ← logo Núcleo de Telessaúde UERJ
requirements.txt
.gitignore
```

> O `.gitignore` já exclui a senha, os arquivos-fonte (xlsx/csv/pdf) e os JSONs
> intermediários — eles **não** sobem para a nuvem.

### 2. Deploy
1. Acesse **https://share.streamlit.io** e entre com sua conta GitHub.
2. Clique em **Create app** → escolha o repositório, o branch e o arquivo
   `journal_finder.py`.
3. Em **Advanced settings → Secrets**, cole a senha (mesmo conteúdo do
   `secrets.toml`):
   ```toml
   app_password = "suaSenhaAqui"
   ```
4. Clique em **Deploy**. Em ~2 min o app sobe num link fixo
   `https://SEU-APP.streamlit.app`.

### 3. Restringir quem vê (opcional, recomendado)
Nas configurações do app no Streamlit Cloud, em **Sharing**, você pode limitar a
visualização a **e-mails específicos** — além da senha do próprio app.

---

## Atualizar as bases no futuro

1. Coloque na pasta os novos arquivos-fonte (PDF do JCR, CSV do Scimago, XLSX do Qualis).
2. Rode `python build_data.py` para regenerar o `journals_data.json`.
3. Faça commit do novo `journals_data.json` e o Streamlit Cloud reimplanta sozinho.
