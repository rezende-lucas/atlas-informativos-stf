"""Extrai diplomas e artigos do campo "Legislação" dos Informativos do STF.

parse(texto, ano) -> {diploma canônico: set(artigos)}; artigos como "37", "5", "1228", "74-A".
Leis estaduais, municipais e distritais ficam de fora (o índice é de legislação federal).
"""
import re

# Leis que são códigos ou têm nome consagrado: número/ano -> nome canônico
LEI_CODIGO = {
    ("Lei", "5.172/1966"): "CTN", ("Lei", "8.069/1990"): "ECA", ("Lei", "8.078/1990"): "CDC",
    ("Lei", "7.210/1984"): "LEP", ("Lei", "10.406/2002"): "CC/2002", ("Lei", "3.071/1916"): "CC/1916",
    ("Lei", "13.105/2015"): "CPC/2015", ("Lei", "5.869/1973"): "CPC/1973", ("Lei", "4.737/1965"): "Código Eleitoral",
    ("Decreto-Lei", "2.848/1940"): "CP", ("Decreto-Lei", "3.689/1941"): "CPP", ("Decreto-Lei", "5.452/1943"): "CLT",
    ("Decreto-Lei", "1.001/1969"): "CPM", ("Decreto-Lei", "1.002/1969"): "CPPM",
    ("Lei", "9.503/1997"): "CTB", ("Decreto-Lei", "3.688/1941"): "LCP", ("LC", "35/1979"): "LOMAN",
}

APELIDO = {
    "CF/1988": "Constituição Federal", "ADCT": "Ato das Disposições Constitucionais Transitórias",
    "CP": "Código Penal", "CPP": "Código de Processo Penal", "CPC/2015": "Código de Processo Civil de 2015",
    "CPC/1973": "Código de Processo Civil de 1973", "CC/2002": "Código Civil de 2002", "CC/1916": "Código Civil de 1916",
    "CTN": "Código Tributário Nacional", "CLT": "Consolidação das Leis do Trabalho", "CDC": "Código de Defesa do Consumidor",
    "ECA": "Estatuto da Criança e do Adolescente", "LEP": "Lei de Execução Penal", "CPM": "Código Penal Militar",
    "CPPM": "Código de Processo Penal Militar", "Código Eleitoral": "Lei 4.737/1965", "RISTF": "Regimento Interno do STF",
    "Lei 8.112/1990": "Regime jurídico dos servidores federais", "Lei 11.343/2006": "Lei de Drogas",
    "Lei 9.099/1995": "Juizados Especiais", "Lei 8.429/1992": "Improbidade Administrativa", "Lei 9.868/1999": "Lei da ADI e da ADC",
    "Lei 9.882/1999": "Lei da ADPF", "Lei 12.850/2013": "Organizações Criminosas", "Lei 8.666/1993": "Licitações (antiga)",
    "Lei 14.133/2021": "Nova Lei de Licitações", "Lei 9.504/1997": "Lei das Eleições", "Lei 7.347/1985": "Ação Civil Pública",
    "Lei 12.016/2009": "Mandado de Segurança", "Lei 6.815/1980": "Estatuto do Estrangeiro", "Lei 13.445/2017": "Lei de Migração",
    "Lei 8.212/1991": "Custeio da Seguridade Social", "Lei 8.213/1991": "Planos de Benefícios da Previdência",
    "Lei 11.340/2006": "Lei Maria da Penha", "Lei 8.072/1990": "Crimes Hediondos", "Lei 9.613/1998": "Lavagem de Dinheiro",
    "Lei 10.826/2003": "Estatuto do Desarmamento", "Lei 9.296/1996": "Interceptação Telefônica", "Lei 13.964/2019": "Pacote Anticrime",
    "Lei 12.527/2011": "Lei de Acesso à Informação", "Lei 13.709/2018": "LGPD", "Lei 8.906/1994": "Estatuto da OAB",
    "Lei 9.784/1999": "Processo Administrativo Federal", "Lei 8.137/1990": "Crimes contra a Ordem Tributária",
    "Lei 1.079/1950": "Crimes de Responsabilidade", "Lei 8.038/1990": "Processos no STJ e no STF",
    "LC 64/1990": "Lei das Inelegibilidades", "LC 135/2010": "Lei da Ficha Limpa", "LC 101/2000": "Lei de Responsabilidade Fiscal",
    "LC 87/1996": "Lei Kandir (ICMS)", "LC 116/2003": "ISS", "LC 123/2006": "Simples Nacional", "LOMAN": "Lei Orgânica da Magistratura (LC 35/1979)", "CTB": "Código de Trânsito Brasileiro", "LCP": "Lei das Contravenções Penais",
    "LC 75/1993": "Estatuto do MPU", "LC 80/1994": "Lei Orgânica da Defensoria Pública",
    "Decreto-Lei 201/1967": "Responsabilidade de Prefeitos",
}

NUM = r"(?:n(?:º|°|o|\.º|\.°|\.)?\s*)?(\d{1,2}(?:\.\d{3})+|\d{1,5})(-[A-Z0-9]+)?\s*[/,]\s*(?:de\s+)?(\d{4}|\d{2})\b"

PATTERNS = [
    ("ADCT", r"\bADCT\b|Ato das Disposi[çc][õo]es Constitucionais Transit[óo]rias"),
    ("CF", r"\bCF(?:\s*/\s*(?:19)?88)?\b|\bCR(?:FB)?(?:/88|/1988)?\b|Constitui[çc][ãa]o (?:Federal|da Rep[úu]blica)|Carta (?:Magna|Federal|da Rep[úu]blica)"),
    ("CPPM", r"\bCPPM\b|C[óo]digo de Processo Penal Militar"),
    ("CPM", r"\bCPM\b|C[óo]digo Penal Militar"),
    ("CPP", r"\bCPP(?:\s*/\s*(?:19)?41)?\b|C[óo]digo de Processo Penal"),
    ("CPC", r"\bCPC(?:\s*/\s*(\d{2,4}))?\b|C[óo]digo de Processo Civil(?: de (\d{4}))?"),
    ("CP", r"\bCP(?:\s*/\s*(?:19)?40)?\b|C[óo]digo Penal"),
    ("CC", r"\bCC(?:\s*/\s*(\d{2,4}))?\b|C[óo]digo Civil(?: de (\d{4}))?"),
    ("CTN", r"\bCTN(?:\s*/\s*(?:19)?66)?\b|C[óo]digo Tribut[áa]rio Nacional"),
    ("CLT", r"\bCLT(?:\s*/\s*(?:19)?43)?\b|Consolida[çc][ãa]o das Leis do Trabalho"),
    ("CDC", r"\bCDC\b|C[óo]digo de Defesa do Consumidor"),
    ("ECA", r"\bECA\b|Estatuto da Crian[çc]a e do Adolescente"),
    ("LEP", r"\bLEP\b|Lei de Execu[çc][ãa]o Penal"),
    ("Código Eleitoral", r"C[óo]digo Eleitoral"),
    ("CTB", r"CTB|C[óo]digo de Tr[âa]nsito Brasileiro"),
    ("LCP", r"LCP|Lei (?:das|de) Contraven[çc][õo]es Penais"),
    ("LOMAN", r"LOMAN|Loman|Lei Org[âa]nica da Magistratura"),
    ("RISTF", r"\bRISTF\b|Regimento Interno do (?:STF|Supremo Tribunal Federal)"),
    ("EC", r"\b(?:EC|Emenda Constitucional)\s*" + NUM),
    ("LC", r"\b(?:LC|Lei Complementar)(?:\s+federal)?\s*" + NUM),
    ("Decreto-Lei", r"\b(?:Decreto-Lei|Decreto Lei|DL)\s*" + NUM),
    ("MP", r"\b(?:MP|Medida Provis[óo]ria)\s*" + NUM),
    ("Decreto", r"\bDecreto(?!-)(?:\s+federal)?\s*" + NUM),
    ("Lei", r"\bLei(?!\s+Complementar|\s+Org|\s+de\s+Execu)(?:\s+federal)?\s*" + NUM),
]
DIP_RE = re.compile("|".join(f"(?P<g{i}>{p})" for i, (_, p) in enumerate(PATTERNS)))
LOCAL_RE = re.compile(r"^\W{0,3}(?:do|da|de)\s+(?:Estado|estado|Munic[íi]pio|munic[íi]pio|Distrito Federal|DF\b)|^\W{0,3}(?:estadual|municipal|distrital)|^\s*/\s*[A-Z]{2}\b")
STATE_CONST_RE = re.compile(r"Constitui[çc][ãa]o (?:do Estado|Estadual|estadual)")
TOK_RE = re.compile(r"arts?\b\.?|artigos?\b|§+|par[áa]grafo|\bitem\b|\bn[º°o]\b\.?|(\d{1,2}(?:\.\d{3})+|\d{1,4})\s*(?:º|°)?(-[A-Z]{1,2})?(?![\d/])", re.I)


def full_year(y):
    y = int(y)
    if y < 100:
        y += 1900 if y > 30 else 2000
    return y


def canon(kind, m, gi, ano):
    g = m.groups()
    if kind in ("CPC", "CC"):
        yrs = [x for x in m.group(f"g{gi}") and re.findall(r"\d{2,4}", m.group(f"g{gi}"))]
        y = full_year(yrs[-1]) if yrs else None
        if kind == "CPC":
            y = y or (2015 if ano >= 2016 else 1973)
            return "CPC/2015" if y >= 2015 else "CPC/1973"
        y = y or (2002 if ano >= 2003 else 1916)
        return "CC/2002" if y >= 2002 else "CC/1916"
    if kind == "CF":
        return "CF/1988"
    if kind in ("EC", "LC", "Decreto-Lei", "MP", "Decreto", "Lei"):
        sub = re.search(NUM, m.group(f"g{gi}"))
        num, suf, y = sub.group(1), sub.group(2) or "", full_year(sub.group(3))
        n = int(num.replace(".", ""))
        num = f"{n:,}".replace(",", ".") if n >= 1000 else str(n)
        key = f"{num}{suf}/{y}"
        if (kind, key) in LEI_CODIGO:
            return LEI_CODIGO[(kind, key)]
        return f"{kind} {key}"
    return kind


def kind_of(name):
    if name in ("CF/1988", "ADCT") or name.startswith("EC "):
        return "Constituição"
    if name.startswith("LC "):
        return "Leis complementares"
    if name.startswith("Lei "):
        return "Leis ordinárias"
    if name.startswith("Decreto-Lei "):
        return "Decretos-leis"
    if name.startswith("MP "):
        return "Medidas provisórias"
    if name.startswith("Decreto "):
        return "Decretos"
    if name == "RISTF":
        return "Regimentos"
    return "Códigos e estatutos"


def articles(frag, lead_is_art=False):
    out, expect_skip, para = [], False, False
    started = lead_is_art
    for m in TOK_RE.finditer(frag):
        t = m.group(0)
        if m.group(1) is None:
            tl = t.lower()
            if tl.startswith("art"):
                started, para, expect_skip = True, False, False
            elif tl.startswith("§") or tl.startswith("par"):
                expect_skip, para = True, True
            else:  # item, nº
                expect_skip = True
            continue
        if not started:
            continue
        num, suf = m.group(1), m.group(2) or ""
        if expect_skip:
            expect_skip = False
            continue
        if para and not suf:
            continue
        n = int(num.replace(".", ""))
        if 0 < n < 3000:
            out.append(f"{n}{suf}")
    return out


def parse(text, ano):
    res = {}

    def add(d, arts):
        res.setdefault(d, set()).update(arts)

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        current = None
        for clause in re.split(r";", line):
            if STATE_CONST_RE.search(clause):
                current = None
                continue
            dips = []
            for m in DIP_RE.finditer(clause):
                gi = next(i for i in range(len(PATTERNS)) if m.group(f"g{i}"))
                kind = PATTERNS[gi][0]
                if LOCAL_RE.search(clause[m.end():m.end() + 30]):
                    dips.append((m.start(), m.end(), None))  # diploma local: interrompe, mas não entra
                    continue
                dips.append((m.start(), m.end(), canon(kind, m, gi, ano)))
            if not dips:
                if current:
                    lead = bool(re.match(r"\s*(?:e\s+)?\d", clause))
                    arts = articles(clause, lead_is_art=lead)
                    add(current, arts)
                continue
            # texto antes do primeiro diploma: forma "art. 87 do ADCT"
            pre = clause[:dips[0][0]]
            if dips[0][2] and re.search(r"arts?\b|artigos?\b", pre, re.I):
                add(dips[0][2], articles(pre))
            for k, (s0, e0, name) in enumerate(dips):
                seg = clause[e0:dips[k + 1][0]] if k + 1 < len(dips) else clause[e0:]
                nxt = dips[k + 1][2] if k + 1 < len(dips) else None
                if name:
                    add(name, [])
                # "..., art. 5º da Lei X" -> artigos do segmento pertencem ao próximo diploma
                if nxt and re.search(r"\b(?:do|da|dos|das|de)\s*(?:\(|\s)*$", seg) and re.search(r"arts?\b|artigos?\b", seg, re.I):
                    add(nxt, articles(seg))
                elif name:
                    add(name, articles(seg))
            current = dips[-1][2]
    return res


def art_label(a):
    m = re.match(r"(\d+)(.*)", a)
    n, suf = int(m.group(1)), m.group(2)
    base = f"{n}º" if n < 10 else (f"{n:,}".replace(",", ".") if n >= 1000 else str(n))
    return base + suf


if __name__ == "__main__":
    tests = [
        ("CF/1988: arts. 7º, VIII e XVII; 37, caput, X, XI e § 11; 39, § 4º; 102, I, \"n\"", 2020),
        ("Lei nº 9.430/1996: arts. 74, § 3º, X, e 74-A.", 2026),
        ("CF, art. 236, §3º; Arts 5º e 26 da Lei federal 8.935/94", 2000),
        ("art. 87, do ADCT, introduzido pela EC 37/2002;", 2005),
        ("Art. 544, §1º a 5º, do CPC.", 2005),
        ("Lei Complementar nº 64/1990: art. 1º, I, \"e\", item 9.", 2026),
        ("LC 39/2002 do estado da Paraíba.", 2010),
        ("CF/1988: art. 21, VI; e art. 22, XXI.", 2020),
        ("Lei 9.430/1996: art. 74, § 15 e 17.", 2020),
        ("RISTF, art. 83, § 1º, III, art. 131, § 2º;", 2010),
        ("CPC, art. 1.035", 2019),
        ("Constituição do Estado do Rio de Janeiro, art. 5º", 2010),
        ("MP 2.215-10/2001, art. 18", 2010),
    ]
    for t, a in tests:
        print(t, "->", {k: sorted(v, key=lambda x: int(re.match(r"\d+", x).group())) for k, v in parse(t, a).items()})
