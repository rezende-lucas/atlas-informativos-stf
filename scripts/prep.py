"""Converte Dados_InformativosSTF.xlsx nos arquivos de dados do Atlas dos Informativos STF."""
import json, os, re, sys
import pandas as pd
import legis

SRC = sys.argv[1] if len(sys.argv) > 1 else "Dados_InformativosSTF.xlsx"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "data")
os.makedirs(OUT, exist_ok=True)

df = pd.read_excel(SRC)

SMALL = {"de", "da", "do", "das", "dos", "e"}
MERGE = {"Roberto Barroso": "Luís Roberto Barroso", "Carlos Britto": "Ayres Britto"}


def pretty_min(v):
    if not isinstance(v, str) or not v.strip():
        return None
    v = v.strip()
    m = re.match(r"^MIN\.\s+(.*)$", v)
    if not m:
        return v.capitalize().replace("jurisprudência", "Jurisprudência")
    words = m.group(1).lower().split()
    name = " ".join(w if w in SMALL else w[:1].upper() + w[1:] for w in words)
    return MERGE.get(name, name)


def s(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def split_list(v):
    return [x.strip() for x in s(v).split(";") if x.strip()]


class Dict:
    def __init__(self):
        self.items, self.pos = [], {}

    def id(self, v):
        if v not in self.pos:
            self.pos[v] = len(self.items)
            self.items.append(v)
        return self.pos[v]


classes, relatores, ramos, ods, orgaos = Dict(), Dict(), Dict(), Dict(), Dict()
for o in ["Plenário", "Primeira Turma", "Segunda Turma"]:
    orgaos.id(o)

rows = []
for idx, r in df.iterrows():
    d = r["Data Julgamento"]
    tema = r["Tema RG"]
    rel = pretty_min(r["Relator"])
    red = pretty_min(r["Redator Acórdão"])
    cov = s(r["Covid-19"])
    rows.append([
        int(r["Informativo"]),                       # 0 informativo
        classes.id(s(r["Classe Processo"])),         # 1 classe
        int(r["Número Processo"]),                   # 2 número
        s(r["Incidente Julgamento"]),                # 3 incidente
        s(r["UF"]),                                  # 4 UF
        d.strftime("%Y-%m-%d") if not pd.isna(d) else "",  # 5 data
        relatores.id(rel),                           # 6 relator
        relatores.id(red) if red else -1,            # 7 redator
        orgaos.id(s(r["Órgão Julgador"])),           # 8 órgão
        1 if s(r["Tipo Julgamento"]) == "Virtual" else 0,  # 9 virtual
        1 if s(r["Situação Julgamento"]) == "Suspenso" else 0,  # 10 suspenso
        s(r["Título"]),                              # 11 título
        s(r["Tese Julgado"]),                        # 12 tese
        s(r["Resumo"]),                              # 13 resumo
        sorted({ramos.id(x) for x in split_list(r["Ramo Direito"])}),  # 14 ramos
        s(r["Matéria"]),                             # 15 matéria
        1 if s(r["Repercussão Geral"]) == "Sim" else 0,  # 16 RG
        int(tema) if not pd.isna(tema) else 0,       # 17 tema
        s(r["Legislação"]),                          # 18 legislação
        [ods.id(x) for x in split_list(r["ODS ONU 2030"])],  # 19 ODS
        1 if cov == "Sim" else 0,                    # 20 covid
        s(r["Observação"]),                          # 21 observação
        -1,                                          # 22 bloco da notícia (preenchido abaixo)
        len(s(r["Notícia"])),                        # 23 tamanho da notícia
    ])

# ---------- Unificação: mesmo informativo + notícia idêntica = um único julgado ----------
def norm(t):
    return re.sub(r"\s+", " ", t).strip()


groups, gpos = [], {}
for i in range(len(rows)):
    txt = norm(s(df.at[i, "Notícia"]))
    key = (rows[i][0], txt) if txt else ("solo", i)
    if key not in gpos:
        gpos[key] = len(groups)
        groups.append([])
    groups[gpos[key]].append(i)


def distinct(vals):
    """Valores distintos (comparados sem diferenças de espaço), na ordem em que aparecem."""
    out, seen = [], {}
    for v, who in vals:
        if not v:
            continue
        k = norm(v)
        if k not in seen:
            seen[k] = len(out)
            out.append([v, []])
        out[seen[k]][1].append(who)
    return out


def uniq(seq):
    out = []
    for x in seq:
        if x and x not in out:
            out.append(x)
    return out


julgados = []
for g in groups:
    # processos ordenados por classe (ordem de aparição) e número
    g = sorted(g, key=lambda i: (rows[g[0]][1] != rows[i][1], rows[i][1], rows[i][2]))
    procs = [[rows[i][1], rows[i][2], rows[i][4], rows[i][3], rows[i][6], rows[i][7], rows[i][5], rows[i][16], rows[i][17]] for i in g]
    # processos repetidos (mesmo processo e incidente) entram uma vez só
    seen, keep = set(), []
    for pi, pr in enumerate(procs):
        k = (pr[0], pr[1], pr[3])
        if k not in seen:
            seen.add(k)
            keep.append(pi)
    procs = [procs[pi] for pi in keep]
    idx = {i: n for n, i in enumerate(g)}
    remap = {old: new for new, old in enumerate(keep)}

    def who(i):
        return remap.get(idx[i], 0)

    titles = [t for t, _ in sorted(distinct([(rows[i][11], i) for i in g]), key=lambda x: -len(x[1]))]
    teses = distinct([(rows[i][12], who(i)) for i in g])
    resumos = distinct([(rows[i][13], who(i)) for i in g])
    all_p = list(range(len(procs)))
    teses = [[t, sorted(set(w))] if len(teses) > 1 else [t] for t, w in teses]
    resumos = [[t, sorted(set(w))] if len(resumos) > 1 else [t] for t, w in resumos]
    orgs = [rows[i][8] for i in g]
    dates = [rows[i][5] for i in g if rows[i][5]]
    julgados.append([
        rows[g[0]][0],                                          # 0 informativo
        max(dates) if dates else "",                            # 1 data (mais recente)
        max(set(orgs), key=orgs.count),                         # 2 órgão
        max(rows[i][9] for i in g),                             # 3 virtual
        max(rows[i][10] for i in g),                            # 4 suspenso
        titles[0] if titles else "",                            # 5 título
        titles[1:],                                             # 6 outros títulos
        teses,                                                  # 7 teses [[texto, (processos)]]
        resumos,                                                # 8 resumos [[texto, (processos)]]
        sorted({x for i in g for x in rows[i][14]}),            # 9 ramos
        "; ".join(uniq(x.strip() for i in g for x in rows[i][15].split(";"))),  # 10 matéria
        max(rows[i][16] for i in g),                            # 11 RG
        "\n".join(uniq(l.strip() for i in g for l in rows[i][18].split("\n"))),  # 12 legislação
        uniq(x for i in g for x in rows[i][19]),                # 13 ODS
        max(rows[i][20] for i in g),                            # 14 covid
        "\n".join(t for t, _ in distinct([(rows[i][21], i) for i in g])),  # 15 observação
        -1,                                                     # 16 bloco da notícia
        rows[g[0]][23],                                         # 17 tamanho da notícia
        procs,                                                  # 18 processos [classe, número, UF, incidente, relator, redator, data, RG, tema]
        g,                                                      # 19 linhas originais da planilha
    ])

# ---------- Índice de legislação: diploma + artigos citados ----------
diplomas = Dict()
for j in julgados:
    ano = int(j[1][:4]) if j[1] else 2000
    parsed = legis.parse(j[12], ano)
    j.append(sorted(([diplomas.id(d), sorted(a, key=lambda x: (int(re.match(r"\d+", x).group()), x))] for d, a in parsed.items()), key=lambda x: x[0]))  # 20 legislação estruturada

# Blocos de inteiro teor (~2,5 MB cada), agrupados por faixa de informativo
order = sorted(range(len(julgados)), key=lambda j: julgados[j][0])
chunks, cur, cur_size = [], None, 0
LIMIT = 2_500_000
for j in order:
    txt = s(df.at[julgados[j][19][0], "Notícia"])
    if not txt:
        continue
    if cur is None or cur_size > LIMIT:
        cur = {"texts": [], "map": {}, "pos": {}, "lo": julgados[j][0], "hi": julgados[j][0]}
        chunks.append(cur)
        cur_size = 0
    if txt not in cur["pos"]:
        cur["pos"][txt] = len(cur["texts"])
        cur["texts"].append(txt)
        cur_size += len(txt.encode("utf-8"))
    cur["map"][j] = cur["pos"][txt]
    cur["hi"] = julgados[j][0]
    julgados[j][16] = len(chunks) - 1

for fn in os.listdir(OUT):
    if fn.startswith("teor-"):
        os.remove(os.path.join(OUT, fn))
for k, c in enumerate(chunks):
    with open(os.path.join(OUT, f"teor-{k}.json"), "w", encoding="utf-8") as f:
        json.dump({"texts": c["texts"], "map": c["map"]}, f, ensure_ascii=False, separators=(",", ":"))

index = {
    "versao": 2,
    "linhas": len(rows),
    "classes": classes.items,
    "relatores": relatores.items,
    "ramos": ramos.items,
    "ods": ods.items,
    "orgaos": orgaos.items,
    "diplomas": [[d, legis.APELIDO.get(d, ""), legis.kind_of(d)] for d in diplomas.items],
    "chunks": [[c["lo"], c["hi"]] for c in chunks],
    "julgados": julgados,
}
with open(os.path.join(OUT, "indice.json"), "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, separators=(",", ":"))

multi = [j for j in julgados if len(j[18]) > 1]
print("linhas", len(rows), "julgados", len(julgados), "unificados", len(multi), "blocos", len(chunks))
print("teses multiplas", sum(1 for j in julgados if len(j[7]) > 1), "resumos multiplos", sum(1 for j in julgados if len(j[8]) > 1))
for fn in sorted(os.listdir(OUT)):
    print(fn, os.path.getsize(os.path.join(OUT, fn)))
