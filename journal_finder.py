"""
Buscador de Periódicos Científicos para a área da Saúde
Scientific Journal Finder for Health Research

100% offline, baseado em três bases oficiais:
  - JCR 2026        → Fator de Impacto (JIF 2026/2025) e quartil (Web of Science)
  - Scimago 2025    → SJR e quartil Scimago/Scopus por categoria
  - Qualis/CAPES    → estrato brasileiro (A1–C) por área, quadriênio 2021–2024

Elaborado por Prof. Dr. Edgard Michel Crosato e Maria Isabel de Castro de Souza.
"""

import streamlit as st
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(HERE, "journals_data.json")

LOGOS = {
    "fousp": os.path.join(HERE, "images.jpg"),
    "nto": os.path.join(HERE, "Logo NTO azul.png"),
    "faperj": os.path.join(HERE, "logo_faperj_cor.jpg"),
    "telessaude": os.path.join(HERE, "telessaude.jpg"),
}

CREDITS = "Elaborado por Prof. Dr. Edgard Michel Crosato e Maria Isabel de Castro de Souza"

ESTRATO_ORDER = {"A1": 1, "A2": 2, "A3": 3, "A4": 4, "B1": 5, "B2": 6, "B3": 7, "B4": 8, "C": 9}

QUALIS_HEALTH_AREAS = [
    "MEDICINA I", "MEDICINA II", "MEDICINA III",
    "ODONTOLOGIA", "ENFERMAGEM", "SAÚDE COLETIVA",
    "FARMÁCIA", "NUTRIÇÃO",
    "EDUCAÇÃO FÍSICA, FISIOTERAPIA, FONOAUDIOLOGIA E TERAPIA OCUPACIONAL",
    "MEDICINA VETERINÁRIA", "BIOTECNOLOGIA",
    "CIÊNCIAS BIOLÓGICAS I", "CIÊNCIAS BIOLÓGICAS II", "CIÊNCIAS BIOLÓGICAS III",
    "CIÊNCIA DE ALIMENTOS", "PSICOLOGIA", "ENSINO", "INTERDISCIPLINAR",
]

# ─────────────────────────────────────────────
# IDIOMA
# ─────────────────────────────────────────────
T = {
    "PT": {
        "title": "🔬 Buscador de Periódicos Científicos",
        "subtitle": "Auxílio ao pesquisador da área da saúde na escolha do melhor periódico",
        "tab_search": "🔍 Buscar por Tema",
        "tab_check": "✅ Verificar Periódico",
        "tab_about": "ℹ️ Sobre",
        "search_label": "Tema, área ou nome do periódico",
        "search_ph": "Ex: dentistry, periodontics, oncology, public health, teleodontologia",
        "search_tip": "💡 Digite um termo livre **ou** escolha uma categoria temática abaixo (ou ambos). "
                      "Termos em inglês trazem mais resultados.",
        "cat_label": "📂 Categoria temática (Scimago)",
        "cat_any": "— todas as categorias —",
        "btn_search": "Buscar Periódicos",
        "filters": "Filtros e ordenação",
        "f_min_jif": "JIF mínimo (JCR)",
        "f_quartile": "Quartil mínimo (JCR ou Scimago)",
        "f_qualis_area": "Área de avaliação Qualis (quadriênio 2021–2024)",
        "f_min_estrato": "Estrato Qualis mínimo",
        "f_only_jcr": "Apenas com Fator de Impacto (JCR)",
        "sort_by": "Ordenar por",
        "sort_jif": "Fator de Impacto (JIF)",
        "sort_sjr": "SJR (Scimago)",
        "sort_qualis": "Estrato Qualis",
        "results": "periódicos encontrados",
        "no_results": "Nenhum periódico encontrado. Tente outro termo (ex: a categoria em inglês).",
        "check_label": "Nome ou ISSN do periódico",
        "check_ph": "Ex: Caries Research  ou  0008-6568",
        "btn_check": "Analisar Periódico",
        "not_found": "Periódico não encontrado nas três bases. Verifique o nome ou ISSN.",
        "best_health": "melhor estrato em saúde",
        "all_areas": "🩺 Melhor estrato em saúde",
        "any": "— qualquer —",
    },
    "EN": {
        "title": "🔬 Scientific Journal Finder",
        "subtitle": "Helping health researchers choose the best journal",
        "tab_search": "🔍 Search by Topic",
        "tab_check": "✅ Check a Journal",
        "tab_about": "ℹ️ About",
        "search_label": "Topic, field or journal name",
        "search_ph": "E.g.: dentistry, periodontics, oncology, public health",
        "search_tip": "💡 Type a free term **or** pick a subject category below (or both).",
        "cat_label": "📂 Subject category (Scimago)",
        "cat_any": "— all categories —",
        "btn_search": "Find Journals",
        "filters": "Filters and sorting",
        "f_min_jif": "Minimum JIF (JCR)",
        "f_quartile": "Minimum quartile (JCR or Scimago)",
        "f_qualis_area": "Qualis evaluation area (2021–2024)",
        "f_min_estrato": "Minimum Qualis stratum",
        "f_only_jcr": "Only with Impact Factor (JCR)",
        "sort_by": "Sort by",
        "sort_jif": "Impact Factor (JIF)",
        "sort_sjr": "SJR (Scimago)",
        "sort_qualis": "Qualis stratum",
        "results": "journals found",
        "no_results": "No journals found. Try another term (e.g. the English category).",
        "check_label": "Journal name or ISSN",
        "check_ph": "E.g.: Caries Research  or  0008-6568",
        "btn_check": "Analyse Journal",
        "not_found": "Journal not found in the three bases. Check the name or ISSN.",
        "best_health": "best health stratum",
        "all_areas": "🩺 Best health stratum",
        "any": "— any —",
    },
}


# ─────────────────────────────────────────────
# DADOS
# ─────────────────────────────────────────────

def _ni(s):
    return re.sub(r"[^0-9Xx]", "", str(s or "")).upper()


def _nn(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def parse_categories(s):
    """'Dentistry (miscellaneous) (Q1); Oncology (Q1)' → ['Dentistry (miscellaneous)', 'Oncology']."""
    out = []
    for part in (s or "").split(";"):
        part = re.sub(r"\s*\(Q[1-4]\)\s*$", "", part.strip()).strip()
        if part:
            out.append(part)
    return out


@st.cache_resource(show_spinner="Carregando bases JCR + Scimago + Qualis...")
def load_journals():
    with open(DATA_FILE, encoding="utf-8") as f:
        journals = json.load(f)
    by_issn, by_name, areas, categories = {}, {}, set(), set()
    for j in journals:
        for issn in j["issns"]:
            by_issn.setdefault(_ni(issn), j)
        by_name.setdefault(_nn(j["name"]), j)
        for c in j["qualis"]:
            if c["area"]:
                areas.add(c["area"])
        j["cat_list"] = parse_categories(j.get("categories", ""))
        categories.update(j["cat_list"])
    return {"list": journals, "by_issn": by_issn, "by_name": by_name,
            "areas": sorted(areas), "categories": sorted(categories)}


def lookup(query):
    """Procura um periódico por ISSN ou nome."""
    data = load_journals()
    issn = _ni(query)
    if len(issn) == 8 and issn in data["by_issn"]:
        return data["by_issn"][issn]
    return data["by_name"].get(_nn(query))


def best_estrato(qualis, area=None):
    if not qualis:
        return "", ""
    if area:
        pool = [c for c in qualis if c["area"] == area]
    else:
        pool = [c for c in qualis if c["area"] in QUALIS_HEALTH_AREAS] or qualis
    if not pool:
        return "", ""
    b = min(pool, key=lambda c: ESTRATO_ORDER.get(c["estrato"], 99))
    return b["estrato"], b["area"]


def q_rank(quartile):
    return {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}.get(quartile, 5)


# ─────────────────────────────────────────────
# BADGES
# ─────────────────────────────────────────────

def badge_quartile(q, source):
    if not q:
        return ""
    colors = {"Q1": "#1565C0", "Q2": "#2e7d32", "Q3": "#f57c00", "Q4": "#c62828"}
    bg = colors.get(q, "#555")
    return (f'<span style="background:{bg};color:#fff;padding:2px 9px;border-radius:11px;'
            f'font-weight:700;font-size:0.8em">{q} {source}</span>')


def badge_qualis(estrato):
    if not estrato:
        return ""
    colors = {"A1": "#0d47a1", "A2": "#1565c0", "A3": "#1976d2", "A4": "#42a5f5",
              "B1": "#2e7d32", "B2": "#558b2f", "B3": "#9e9d24", "B4": "#f9a825", "C": "#c62828"}
    bg = colors.get(estrato, "#555")
    return (f'<span style="background:{bg};color:#fff;padding:2px 9px;border-radius:11px;'
            f'font-weight:700;font-size:0.8em">Qualis {estrato}</span>')


def fmt_jif(v):
    return f"{v}" if v is not None else "—"


def fmt_sjr(v):
    return f"{v:.3f}" if v is not None else "—"


# ─────────────────────────────────────────────
# CABEÇALHO COM LOGOS
# ─────────────────────────────────────────────

def render_header(t):
    st.markdown(f'<h1 style="margin-bottom:0;font-size:1.9rem">{t["title"]}</h1>',
                unsafe_allow_html=True)
    st.markdown(f'<p style="color:#666;margin-top:2px;font-size:1.02rem">{t["subtitle"]}</p>',
                unsafe_allow_html=True)


def render_footer(t):
    """Rodapé com logos pequenos + créditos."""
    st.divider()
    # Logos quadrados menores; horizontais (telessaúde, faperj) mais largos p/ equilibrar a altura
    widths = {"fousp": 70, "nto": 70, "telessaude": 130, "faperj": 130}
    spacer1, lc1, lc2, lc3, lc4, spacer2 = st.columns([1.5, 1, 1, 1.6, 1.6, 1.5])
    for col, key in zip([lc1, lc2, lc3, lc4], ["fousp", "nto", "telessaude", "faperj"]):
        if os.path.exists(LOGOS[key]):
            col.image(LOGOS[key], width=widths[key])
    st.markdown(f'<p class="credits">{CREDITS}</p>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CARD DE PERIÓDICO
# ─────────────────────────────────────────────

def render_card(j, qualis_area):
    estrato, est_area = best_estrato(j["qualis"], qualis_area)
    with st.container():
        st.markdown('<div class="jcard">', unsafe_allow_html=True)
        c1, c2 = st.columns([5, 3])
        with c1:
            st.markdown(f'**{j["name"]}**')
            cat = j["categories"] or j["areas"] or "—"
            pub = j["publisher"] or "—"
            st.markdown(f'<span class="det">🗂️ {cat}</span>', unsafe_allow_html=True)
            st.markdown(f'<span class="det">🏢 {pub} &nbsp;|&nbsp; ISSN: {", ".join(j["issns"]) or "—"}</span>',
                        unsafe_allow_html=True)
        with c2:
            # Indicadores numéricos
            parts = []
            if j["jif_2026"] is not None:
                jif25 = f' <span style="color:#999;font-size:0.7rem">(2025: {j["jif_2025"]})</span>' if j["jif_2025"] is not None else ""
                parts.append(f'<span style="color:#4527a0;font-weight:700;font-size:1.05rem">JIF {j["jif_2026"]}</span>{jif25}')
            if j["sjr"] is not None:
                parts.append(f'<span style="color:#00695c;font-weight:700">SJR {j["sjr"]:.3f}</span>')
            if j["h_index"]:
                parts.append(f'<span style="color:#888;font-size:0.8rem">h={j["h_index"]}</span>')
            st.markdown(" &nbsp; ".join(parts) or "—", unsafe_allow_html=True)
            # Badges
            badges = []
            if j["jcr_quartile"]:
                badges.append(badge_quartile(j["jcr_quartile"], "JCR"))
            if j["sjr_quartile"]:
                badges.append(badge_quartile(j["sjr_quartile"], "Scimago"))
            if estrato:
                area_hint = ""
                if not qualis_area and est_area:
                    area_hint = f' <span style="color:#888;font-size:0.65rem">({est_area.split(",")[0][:20]})</span>'
                badges.append(badge_qualis(estrato) + area_hint)
            st.markdown(" ".join(badges) or "<span style='color:#aaa'>—</span>",
                        unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SENHA DE ACESSO
# ─────────────────────────────────────────────

def check_password() -> bool:
    """Tela de senha simples. Retorna True quando autenticado."""
    try:
        correct = st.secrets["app_password"]
    except Exception:
        # Sem arquivo de senha configurado → libera o acesso
        return True

    if st.session_state.get("auth_ok"):
        return True

    def _verify():
        if st.session_state.get("pw_input", "") == correct:
            st.session_state["auth_ok"] = True
            st.session_state["pw_bad"] = False
            st.session_state.pop("pw_input", None)
        else:
            st.session_state["auth_ok"] = False
            st.session_state["pw_bad"] = True

    st.markdown("<div style='max-width:420px;margin:8vh auto 0 auto'>", unsafe_allow_html=True)
    st.markdown("### 🔒 Acesso restrito")
    st.caption("Buscador de Periódicos Científicos — informe a senha para continuar.")
    st.text_input("Senha", type="password", key="pw_input", on_change=_verify)
    if st.session_state.get("pw_bad"):
        st.error("Senha incorreta. Tente novamente.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(f'<p class="credits" style="margin-top:24px">{CREDITS}</p>', unsafe_allow_html=True)
    return False


# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────

def main():
    st.set_page_config(page_title="Buscador de Periódicos | Journal Finder",
                       page_icon="🔬", layout="wide", initial_sidebar_state="collapsed")

    st.markdown("""
    <style>
        .jcard { background:#fafafa; border:1px solid #e0e0e0; border-radius:10px;
                 padding:14px 16px; margin-bottom:10px; }
        .det { color:#555; font-size:0.86rem; display:block; margin-top:3px; }
        footer { visibility:hidden; }
        .credits { color:#555; font-size:0.9rem; text-align:center; margin-top:8px; }
    </style>
    """, unsafe_allow_html=True)

    if not check_password():
        return

    c1, c2 = st.columns([6, 1])
    with c2:
        lang = st.selectbox("idioma", ["PT", "EN"], label_visibility="collapsed", key="lang")
    t = T[lang]

    render_header(t)
    st.divider()

    data = load_journals()
    tab_search, tab_check, tab_about = st.tabs([t["tab_search"], t["tab_check"], t["tab_about"]])

    # ── ABA BUSCAR ──────────────────────────────
    with tab_search:
        sc1, sc2 = st.columns([3, 2])
        with sc1:
            query = st.text_input(t["search_label"], placeholder=t["search_ph"], key="q")
        with sc2:
            cat_sel = st.selectbox(t["cat_label"], [t["cat_any"]] + data["categories"], key="cat")
        st.caption(t["search_tip"])
        cat_filter = None if cat_sel == t["cat_any"] else cat_sel

        qualis_opts = [t["all_areas"]] + data["areas"]
        with st.expander(t["filters"], expanded=False):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                min_jif = st.number_input(t["f_min_jif"], min_value=0.0, value=0.0, step=0.5, key="mjif")
                only_jcr = st.checkbox(t["f_only_jcr"], key="ojcr")
            with fc2:
                min_q = st.selectbox(t["f_quartile"], [t["any"], "Q1", "Q2", "Q3", "Q4"], key="mq")
                sort_by = st.selectbox(t["sort_by"],
                                       [t["sort_jif"], t["sort_sjr"], t["sort_qualis"]], key="sb")
            with fc3:
                qualis_area_sel = st.selectbox(t["f_qualis_area"], qualis_opts, key="qa")
                min_estrato = st.selectbox(t["f_min_estrato"],
                                           [t["any"], "A1", "A2", "A3", "A4", "B1", "B2"], key="me")
        qualis_area = None if qualis_area_sel == t["all_areas"] else qualis_area_sel

        if st.button(t["btn_search"], type="primary", key="bs") and (query.strip() or cat_filter):
            hits = data["list"]
            if query.strip():
                qn = _nn(query.strip())
                hits = [j for j in hits if qn in j["search"]]
            if cat_filter:
                hits = [j for j in hits if cat_filter in j.get("cat_list", [])]

            # Filtros
            if only_jcr:
                hits = [j for j in hits if j["jif_2026"] is not None]
            if min_jif > 0:
                hits = [j for j in hits if (j["jif_2026"] or 0) >= min_jif]
            if min_q != t["any"]:
                maxr = q_rank(min_q)
                hits = [j for j in hits
                        if min(q_rank(j["jcr_quartile"]), q_rank(j["sjr_quartile"])) <= maxr]
            if min_estrato != t["any"]:
                maxe = ESTRATO_ORDER[min_estrato]
                def ok_estrato(j):
                    e, _ = best_estrato(j["qualis"], qualis_area)
                    return e and ESTRATO_ORDER.get(e, 99) <= maxe
                hits = [j for j in hits if ok_estrato(j)]

            # Ordenação
            if sort_by == t["sort_sjr"]:
                hits.sort(key=lambda j: (j["sjr"] or 0, j["jif_2026"] or 0), reverse=True)
            elif sort_by == t["sort_qualis"]:
                def qkey(j):
                    e, _ = best_estrato(j["qualis"], qualis_area)
                    return (-ESTRATO_ORDER.get(e, 99), j["jif_2026"] or 0)
                hits.sort(key=qkey, reverse=True)
            else:
                hits.sort(key=lambda j: (j["jif_2026"] or 0, j["sjr"] or 0), reverse=True)

            st.markdown(f"**{len(hits)} {t['results']}**")
            if not hits:
                st.info(t["no_results"])
            else:
                for j in hits[:60]:
                    render_card(j, qualis_area)
                if len(hits) > 60:
                    st.caption(f"… mostrando os 60 primeiros de {len(hits)}.")

    # ── ABA VERIFICAR ───────────────────────────
    with tab_check:
        ci = st.text_input(t["check_label"], placeholder=t["check_ph"], key="ci")
        if st.button(t["btn_check"], type="primary", key="bc") and ci.strip():
            j = lookup(ci.strip())
            if not j:
                st.warning(t["not_found"])
            else:
                st.subheader(j["name"])
                st.caption(f'ISSN: {", ".join(j["issns"]) or "—"}  ·  {j["publisher"] or ""}')

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("JIF 2026 (JCR)", fmt_jif(j["jif_2026"]),
                          delta=j["jcr_quartile"] or None, delta_color="off")
                m2.metric("JIF 2025 (JCR)", fmt_jif(j["jif_2025"]))
                m3.metric("SJR (Scimago)", fmt_sjr(j["sjr"]),
                          delta=j["sjr_quartile"] or None, delta_color="off")
                est_s, area_s = best_estrato(j["qualis"], None)
                m4.metric("Qualis (saúde)", est_s or "—",
                          delta=area_s.split(",")[0][:18] if area_s else None, delta_color="off")

                st.markdown("---")
                ic, qc = st.columns([3, 2])
                with ic:
                    st.markdown(f"**🗂️ Categorias (Scimago):** {j['categories'] or '—'}")
                    st.markdown(f"**📚 Grande área:** {j['areas'] or '—'}")
                    st.markdown(f"**🏢 Editora:** {j['publisher'] or '—'}")
                    st.markdown(f"**📈 h-index (Scimago):** {j['h_index'] or '—'}")
                    bases = []
                    if j["in_jcr"]: bases.append("JCR")
                    if j["in_scimago"]: bases.append("Scimago")
                    if j["in_qualis"]: bases.append("Qualis")
                    st.markdown(f"**🗄️ Presente em:** {', '.join(bases) or '—'}")
                with qc:
                    st.markdown("**Classificações**")
                    bb = []
                    if j["jcr_quartile"]: bb.append(badge_quartile(j["jcr_quartile"], "JCR"))
                    if j["sjr_quartile"]: bb.append(badge_quartile(j["sjr_quartile"], "Scimago"))
                    if est_s: bb.append(badge_qualis(est_s))
                    st.markdown(" ".join(bb) or "—", unsafe_allow_html=True)

                if j["qualis"]:
                    st.markdown("---")
                    head = ("🇧🇷 Qualis / CAPES — quadriênio 2021–2024" if lang == "PT"
                            else "🇧🇷 Qualis / CAPES — 2021–2024")
                    if est_s:
                        st.markdown(f"**{head}** — {t['best_health']}: **{est_s}** ({area_s})")
                    else:
                        st.markdown(f"**{head}**")
                    ordered = sorted(j["qualis"],
                                     key=lambda c: (0 if c["area"] in QUALIS_HEALTH_AREAS else 1,
                                                    ESTRATO_ORDER.get(c["estrato"], 99)))
                    rows = "".join(
                        f"<tr><td style='padding:2px 10px'>{badge_qualis(c['estrato'])}</td>"
                        f"<td style='padding:2px 10px;color:#444'>{c['area']}</td></tr>"
                        for c in ordered)
                    with st.expander(f"Ver todas as {len(ordered)} áreas de avaliação"
                                     if lang == "PT" else f"View all {len(ordered)} areas"):
                        st.markdown(f"<table>{rows}</table>", unsafe_allow_html=True)

    # ── ABA SOBRE ───────────────────────────────
    with tab_about:
        total_fmt = f"{len(data['list']):,}".replace(",", ".")
        about_pt = f"""
### Como o app ajuda você a escolher o melhor periódico

Esta ferramenta reúne, **em um só lugar e sem depender de internet**, os três principais
sistemas de avaliação de periódicos usados no Brasil — para que o pesquisador da saúde
escolha onde publicar com **informação confiável e atualizada**.

| Base | O que fornece |
|---|---|
| **JCR 2026** | Fator de Impacto (JIF 2026 e 2025) e quartil oficial (Q1–Q4) — *Web of Science / Clarivate* |
| **Scimago 2025** | SJR e quartil por categoria (Q1–Q4) — *Scopus / Elsevier* |
| **Qualis/CAPES** | Estrato brasileiro (A1–C) por área de avaliação — *quadriênio 2021–2024* |

**Total: {total_fmt} periódicos** indexados.

### Como interpretar
- **JIF (Fator de Impacto)** e **SJR** são indicadores quantitativos de impacto; quanto maior, melhor.
- **Quartil (Q1–Q4)**: Q1 reúne os 25% melhores periódicos da categoria.
- **Qualis (A1–C)**: classificação da CAPES por área de avaliação; A1 é o estrato mais alto.
- JCR e Scimago podem indicar **quartis diferentes** para o mesmo periódico — são metodologias distintas (Web of Science × Scopus). Considere os dois.

### Recomendações
1. Priorize periódicos **Q1/Q2** e **Qualis A1–A2** na sua área.
2. Confira a **categoria temática** para garantir aderência ao seu tema.
3. Use os filtros para combinar impacto (JIF/SJR) e relevância nacional (Qualis).
        """
        about_en = f"""
### How this app helps you choose the best journal

This tool brings together, **offline and in one place**, the three main journal evaluation
systems used in Brazil, so health researchers can decide where to publish with reliable data.

| Base | Provides |
|---|---|
| **JCR 2026** | Impact Factor (JIF 2026/2025) and official quartile — *Web of Science* |
| **Scimago 2025** | SJR and quartile per category — *Scopus* |
| **Qualis/CAPES** | Brazilian stratum (A1–C) per area — *2021–2024* |

**Total: {len(data['list'])} indexed journals.**
        """
        st.markdown(about_pt if lang == "PT" else about_en)

    # Rodapé com logos pequenos + créditos em todas as abas
    render_footer(t)


if __name__ == "__main__":
    main()
