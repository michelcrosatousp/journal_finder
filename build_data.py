"""
Constrói a base unificada de periódicos (journals_data.json) a partir das 3 fontes:
  - JCR 2026  (jcr_data.json)        → JIF 2026/2025 + quartil JCR
  - Scimago 2025 (scimagojr 2025.csv) → SJR + quartil Scimago + categorias
  - Qualis/CAPES 2021–2024 (qualis_data.json) → estrato por área

Mescla por ISSN usando union-find (liga ISSN impresso + eletrônico do mesmo periódico).
"""

import csv, json, re, os

HERE = os.path.dirname(os.path.abspath(__file__))


def ni(s):
    return re.sub(r"[^0-9Xx]", "", str(s or "")).upper()


def nn(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def sjr_float(s):
    s = (s or "").strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


# ── Union-Find sobre ISSNs ────────────────────
parent = {}

def find(x):
    parent.setdefault(x, x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x

def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb


# ── Carrega fontes ────────────────────────────
jcr = json.load(open(os.path.join(HERE, "jcr_data.json"), encoding="utf-8"))
qualis = json.load(open(os.path.join(HERE, "qualis_data.json"), encoding="utf-8"))
qualis_by_issn = qualis["by_issn"]

# Scimago: parse CSV em registros (um por linha = um periódico, vários ISSNs)
scimago_rows = []
with open(os.path.join(HERE, "scimagojr 2025.csv"), encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f, delimiter=";"):
        issns = [ni(p) for p in (row.get("Issn") or "").split(",")]
        issns = [i for i in issns if len(i) == 8]
        scimago_rows.append({
            "issns": issns,
            "title": (row.get("Title") or "").strip(),
            "sjr": sjr_float(row.get("SJR")),
            "sjr_quartile": (row.get("SJR Best Quartile") or "").strip(),
            "h_index": int(row["H index"]) if (row.get("H index") or "").strip().isdigit() else None,
            "categories": (row.get("Categories") or "").strip(),
            "areas": (row.get("Areas") or "").strip(),
            "publisher": (row.get("Publisher") or "").strip(),
        })

# JCR: lista de registros com eissn
jcr_records = [r for r in jcr if r.get("eissn")]
jcr_no_issn = [r for r in jcr if not r.get("eissn")]

# ── Cria nós e une ISSNs do mesmo periódico ───
# Cada fonte vira um "source record" com lista de ISSNs
sources = []  # (tipo, dados, issns)

for r in scimago_rows:
    if r["issns"]:
        sources.append(("scimago", r, r["issns"]))

for r in jcr_records:
    issn = ni(r["eissn"])
    sources.append(("jcr", r, [issn]))

for issn, classifs in qualis_by_issn.items():
    sources.append(("qualis", {"issn": issn, "classifs": classifs,
                               "title": qualis["titles"].get(issn, "")}, [issn]))

# Une ISSNs que aparecem juntos numa mesma fonte
for _, _, issns in sources:
    for i in issns[1:]:
        union(issns[0], i)

# ── Agrupa fontes por componente ──────────────
groups = {}  # root_issn -> {scimago, jcr, qualis:list}
for typ, data, issns in sources:
    root = find(issns[0])
    g = groups.setdefault(root, {"scimago": None, "jcr": None, "qualis": [], "issns": set()})
    g["issns"].update(issns)
    if typ == "scimago" and g["scimago"] is None:
        g["scimago"] = data
    elif typ == "jcr" and g["jcr"] is None:
        g["jcr"] = data
    elif typ == "qualis":
        g["qualis"].append(data)

# ── Monta registros unificados ────────────────
ESTRATO_ORDER = {"A1": 1, "A2": 2, "A3": 3, "A4": 4, "B1": 5, "B2": 6, "B3": 7, "B4": 8, "C": 9}

journals = []
for root, g in groups.items():
    sci, jc = g["scimago"], g["jcr"]
    # nome: Scimago > JCR > Qualis
    name = ""
    if sci and sci["title"]:
        name = sci["title"]
    elif jc and jc["name"]:
        name = jc["name"]
    elif g["qualis"]:
        name = g["qualis"][0]["title"]
    if not name:
        continue

    # Qualis: une classificações de todas as fontes qualis do grupo
    qclassifs = []
    seen_q = set()
    for q in g["qualis"]:
        for c in q["classifs"]:
            key = (c["area"], c["estrato"])
            if key not in seen_q:
                seen_q.add(key)
                qclassifs.append(c)

    issns_fmt = sorted({f"{i[:4]}-{i[4:]}" for i in g["issns"] if len(i) == 8})

    journals.append({
        "name": name,
        "issns": issns_fmt,
        "jif_2026": jc["jif_2026"] if jc else None,
        "jif_2025": jc["jif_2025"] if jc else None,
        "jcr_quartile": jc["quartile"] if jc else "",
        "sjr": sci["sjr"] if sci else None,
        "sjr_quartile": sci["sjr_quartile"] if sci else "",
        "categories": sci["categories"] if sci else "",
        "areas": sci["areas"] if sci else "",
        "h_index": sci["h_index"] if sci else None,
        "publisher": (sci["publisher"] if sci else "") or (jc.get("publisher", "") if jc else ""),
        "qualis": qclassifs,
        "in_jcr": jc is not None,
        "in_scimago": sci is not None,
        "in_qualis": len(qclassifs) > 0,
    })

# JCR sem ISSN (não entram no union-find) — adiciona por nome
for r in jcr_no_issn:
    journals.append({
        "name": r["name"], "issns": [],
        "jif_2026": r["jif_2026"], "jif_2025": r["jif_2025"], "jcr_quartile": r["quartile"],
        "sjr": None, "sjr_quartile": "", "categories": "", "areas": "", "h_index": None,
        "publisher": "", "qualis": [], "in_jcr": True, "in_scimago": False, "in_qualis": False,
    })

# texto de busca (nome + categorias + áreas + áreas qualis)
for j in journals:
    qareas = " ".join(c["area"] for c in j["qualis"])
    j["search"] = nn(j["name"] + " " + j["categories"] + " " + j["areas"] + " " + qareas)

json.dump(journals, open(os.path.join(HERE, "journals_data.json"), "w", encoding="utf-8"),
          ensure_ascii=False)

# Estatísticas
n = len(journals)
print("Periódicos unificados:", n)
print("  com JIF (JCR):", sum(1 for j in journals if j["jif_2026"] is not None))
print("  com SJR (Scimago):", sum(1 for j in journals if j["sjr"] is not None))
print("  com Qualis:", sum(1 for j in journals if j["in_qualis"]))
print("  nas 3 bases:", sum(1 for j in journals if j["in_jcr"] and j["in_scimago"] and j["in_qualis"]))
print("File size:", round(os.path.getsize(os.path.join(HERE, "journals_data.json")) / 1024 / 1024, 2), "MB")
