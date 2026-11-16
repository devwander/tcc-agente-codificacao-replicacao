"""Análise do estudo retrospectivo (29/07 a 31/10/2026) do caso [produto] - versão 2.

Uso: python analisar_v2.py <dados_dir> <instrumento.md> <fig_dir> <saida.json>

Lê as tabelas de extrair_v2.py e extrair_linhas_v2.py (base sincronizada em
02/11/2026 e histórico Git de origin/dev) e o instrumento de percepção já
congelado, e grava todos os números do Capítulo 5 em um JSON, além das figuras.
Nenhum número do texto é digitado à mão.

Convenções:
- Fuso America/Recife. R1 = sessões iniciadas até 31/08; R2 = de 01/09 a 31/10.
- Sessão válida = ao menos uma resposta do modelo. Projeto = [produto] e suas worktrees.
- Merge request = merge na linha principal (main até 07/10; dev a partir de 08/10),
  excluídas as integrações dev -> main.
- Retrabalho em 14 dias só é calculado quando a janela está completa na data de
  observação do Git (OBS); o restante é recalculado em 14/11/2026.
- Microsserviços (services/) ficam fora de todas as métricas.
"""
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

D, INSTR, FIG, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
TZ = "America/Recife"
START = pd.Timestamp("2026-07-29", tz=TZ)
R2_START = pd.Timestamp("2026-09-01", tz=TZ)
PAR_START = pd.Timestamp("2026-10-23", tz=TZ)
END = pd.Timestamp("2026-11-01", tz=TZ)            # exclusivo: recorte até 31/10
OBS = pd.Timestamp(os.environ.get("TCC_OBS", "2026-11-02 15:00"), tz=TZ)  # leitura do Git (origin/dev = remoto);
#   2a leitura, com a janela fechada: TCC_OBS="2026-11-15 12:00" sobre dados/extraido-20261115
REWORK_DAYS = 14
# Reorganizações sem mudança de comportamento excluídas do retrabalho (decisão de 15/11/2026, tomada depois
# de ver os dados; a versão sem exclusão é relatada como sensibilidade com TCC_INCLUIR_REORG=1).
REORG_EXCLUIDOS = {} if os.environ.get("TCC_INCLUIR_REORG") else {
    "c93a8c7dd9b3cb44f6da7e4720af831c30d9b2c0": "consolidação das 84 migrações em baseline (03/11/2026)"}
RNG = np.random.default_rng(20261031)
SOURCE_EXT = (".ts", ".tsx", ".js", ".jsx", ".sql", ".css", ".scss", ".json", ".prisma")
NOT_SOURCE = ("package-lock.json", "pnpm-lock.yaml", "yarn.lock")
R = {}


def put(key, value):
    if isinstance(value, np.integer):
        value = int(value)
    elif isinstance(value, np.floating):
        value = None if np.isnan(value) else float(value)
    R[key] = value


def q123(x):
    x = pd.Series(x, dtype=float).dropna()
    if x.empty:
        return [None, None, None]
    return [float(x.quantile(0.25)), float(x.median()), float(x.quantile(0.75))]


def cliffs_delta(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) == 0 or len(b) == 0:
        return None
    gt = sum((x > b).sum() for x in a)
    lt = sum((x < b).sum() for x in a)
    return float((gt - lt) / (len(a) * len(b)))


def mw(a, b):
    a, b = pd.Series(a, dtype=float).dropna(), pd.Series(b, dtype=float).dropna()
    out = {"n1": len(a), "n2": len(b), "med1": float(a.median()) if len(a) else None,
           "med2": float(b.median()) if len(b) else None, "p": None, "delta": None}
    if len(a) >= 3 and len(b) >= 3:
        res = stats.mannwhitneyu(a, b, alternative="two-sided")
        out.update({"U": float(res.statistic), "p": float(res.pvalue), "delta": cliffs_delta(a, b)})
    return out


def spearman_ci(x, y, reps=4000):
    df = pd.DataFrame({"x": list(x), "y": list(y)}).dropna()
    if len(df) < 5 or df.x.nunique() < 2 or df.y.nunique() < 2:
        return {"n": len(df), "rho": None}
    rho, p = stats.spearmanr(df.x, df.y)
    boots, idx = [], np.arange(len(df))
    for _ in range(reps):
        b = df.iloc[RNG.choice(idx, len(idx))]
        if b.x.nunique() > 1 and b.y.nunique() > 1:
            boots.append(stats.spearmanr(b.x, b.y)[0])
    lo, hi = np.nanpercentile(boots, [2.5, 97.5])
    return {"n": len(df), "rho": float(rho), "p": float(p), "ci": [float(lo), float(hi)]}


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [float(c - h), float(c + h)]


def ts(x):
    return pd.Timestamp(x).tz_convert(TZ)


# ================================================================ módulos
MODULES = {1: "Harness e infraestrutura", 2: "Interface", 3: "Acesso e permissões", 4: "Unidades",
           5: "Pacientes", 6: "Terapeutas e equipe", 7: "Agenda", 8: "Integrações", 9: "Personas",
           10: "Convênios e operadoras", 11: "Notificações", 12: "Estratégico", 13: "Auditoria"}
DIR2MOD = {"patients": 5, "therapeutic-plans": 5, "patient-app": 5, "patient-self-service": 5,
           "therapists": 6, "care-team": 6, "my-therapists": 6, "schedule": 7, "my-schedule": 7,
           "dashboard": 12, "reports": 12, "insights": 12, "audit": 13, "units": 4, "auth": 3,
           "rbac": 3, "admins": 3, "settings": 3, "integrations": 8, "convenios": 10,
           "operadoras": 10, "personas": 9, "notifications": 11}
SCOPE2MOD = {"pacientes": 5, "familia": 5, "terapeutas": 6, "agenda": 7, "estrategico": 12,
             "relatorios": 12, "insights": 12, "auditoria": 13, "unidades": 4, "auth": 3, "rbac": 3,
             "admins": 3, "integracoes": 8, "convenios": 10, "operadoras": 10, "personas": 9,
             "notificacoes": 11, "ui": 2, "layout": 2, "navegacao": 2, "harness": 1, "db": 1,
             "deps": 1, "ci": 1, "api": 1, "infra": 1}
E2E2MOD = [("patient", 5), ("pts", 5), ("famil", 5), ("therapist", 6), ("biometria", 6),
           ("care-team", 6), ("session", 7), ("schedule", 7), ("frequency", 13), ("audit", 13),
           ("dashboard", 12), ("insight", 12), ("report", 12), ("unit", 4), ("auth", 3),
           ("me.e2e", 3), ("rbac", 3), ("admin", 3), ("integration", 8), ("connect", 8),
           ("operadora", 10), ("convenio", 10), ("persona", 9), ("notification", 11)]
# Caminho absoluto do repositório do caso na máquina em que os transcritos foram gravados
# (o mesmo registrado pela ferramenta de coleta na tabela projects).
CASO = os.environ.get("TCC_CASO_PATH", "").rstrip("/")
if not CASO:
    sys.exit("defina TCC_CASO_PATH com o caminho do repositório do caso usado na coleta")
WT = re.compile("^" + re.escape(CASO) + r"(/\.claude/worktrees/[^/]+)?/")


def rel(path):
    return WT.sub("", path) if path.startswith(CASO) else None


def module_of(path):
    """Módulo de um caminho relativo ao repositório; None = fora do sistema principal."""
    if path is None or path.startswith("services/") or path.startswith("/"):
        return None
    m = re.match(r"(?:backend/src/modules|frontend/src/features)/([^/]+)/", path)
    if m:
        return DIR2MOD.get(m.group(1), 1)
    if path.startswith("backend/test/"):
        base = path.rsplit("/", 1)[-1]
        for k, mod in E2E2MOD:
            if k in base:
                return mod
        return 1
    if path.startswith(("frontend/src/shared", "frontend/src/app", "frontend/src/styles",
                        "frontend/src/components", "frontend/public", "frontend/index.html")):
        return 2
    return 1  # harness, banco, configuração, CI, documentação e raiz


def modules_of_files(paths):
    w = defaultdict(float)
    mods = [module_of(p) for p in paths]
    mods = [x for x in mods if x is not None]
    for x in mods:
        w[x] += 1 / len(mods)
    return dict(w)


def scope_module(text):
    """Módulo pelo escopo de 'tipo(escopo):' ou pelo prefixo de branch 'tipo/escopo-...'."""
    m = re.match(r"^\w+\(([^)]+)\)!?:", text) or re.match(r"^\w+/([a-z]+)", text)
    if not m:
        return None
    for tok in re.split(r"[,\s/-]+", m.group(1)):
        if tok in SCOPE2MOD:
            return SCOPE2MOD[tok]
    return None


def is_source(path):
    base = path.rsplit("/", 1)[-1]
    return (path.endswith(SOURCE_EXT) and base not in NOT_SOURCE and not path.startswith(".claude/")
            and not path.startswith("services/"))


# ================================================================ dados
s = pd.read_pickle(D / "sessions.pkl")
u = pd.read_pickle(D / "usages.pkl")
links = pd.read_pickle(D / "links.pkl")
changed = pd.read_pickle(D / "changed.pkl")
msgs = pd.read_pickle(D / "messages.pkl")
projects = pd.read_pickle(D / "projects.pkl")
g = json.load(open(D / "git.json"))
C = {c["hash"]: c for c in g["commits"]}
linhas = json.load(open(D / "linhas_por_arquivo.json"))

s["start"] = s.started_at.dt.tz_convert(TZ)
s["end"] = s.ended_at.dt.tz_convert(TZ)
s = s[(s.start >= START - pd.Timedelta(days=2)) & (s.start < END)].copy()
s["valid"] = s.assistant_message_count > 0
s["regime"] = np.where(s.start < R2_START, "R1", "R2")
s["worktree"] = s.project_id != int(projects[projects.path == CASO].id.iloc[0])
s["active_min"] = s.active_turn_seconds / 60
s["wall_h"] = s.duration_seconds / 3600
s["err_rate"] = s.tool_error_count / s.tool_call_count.replace(0, np.nan)
MODEL_LABEL = {"claude-opus-5": "Opus 5", "claude-opus-5-5": "Opus 5.5", "claude-sonnet-5": "Sonnet 5",
               "claude-sonnet-5-5": "Sonnet 5.5"}
s["model"] = s.models_used.apply(lambda m: "+".join(sorted(x for x in m if x != "<synthetic>")) or "nenhum")
s["model_label"] = s.model.map(MODEL_LABEL).fillna("outros/misto")
pref = (u.assign(rank=u.source.map({"ccusage": 0, "claude_transcript": 1}))
         .sort_values("rank").groupby("session_id").first())
s = s.join(pref[["source", "cost_usd", "total_tokens", "cache_read_tokens", "output_tokens"]], on="id")
has_cc = set(u[u.source == "ccusage"].session_id)
s["shell_edit"] = (s.files_modified == 0) & (s.tool_call_count > 20)
s["resumed"] = s.valid & ~s.id.isin(has_cc)
s["interrupted"] = s.status == "interrupted"
s["orig_missing"] = ~s.transcript_path.fillna("").apply(os.path.exists)
s["archived"] = s.archive_path.fillna("").apply(lambda p: bool(p) and os.path.exists(p))
SNAP = Path.home() / "Dev/ai-development-analytics/archive/snapshot-transcritos-20261102"
snap_ids = {p.stem for p in SNAP.rglob("*.jsonl")} if SNAP.exists() else set()
s["snapshot"] = s.claude_session_id.isin(snap_ids)

# ---------------------------------------------------------------- prompts
hp = msgs[(msgs.message_type == "human_prompt") & msgs.session_id.isin(s.id)].sort_values(
    ["session_id", "sequence"]).copy()
txt = hp.content.fillna("").str.strip()
SYS = r"^(<command-|<local-command|\[Request interrupted|<bash-|Caveat:|/[a-z][\w:-]*\s*$)"  # /exit etc.
PROC = (r"^(apenas\s+|somente\s+)?(realize|realizar|fa[çc]a|pode)?\s*(apenas\s+|somente\s+)?(o\s+|os\s+)?(teste[s]?\s+e\s+em\s+caso"
        r"\s+de\s+sucesso|commit|push|merge|merges realizados|merge realizado|mr mergiada|prossiga|continue"
        r"|continua|siga|ok\b|sim\b|pode seguir|segue)")
hp["k"] = "conteudo"
hp.loc[txt.str.match(SYS), "k"] = "sistema"
hp.loc[(hp.k == "conteudo") & txt.str.lower().str.match(PROC), "k"] = "rotina"
first_content = hp[hp.k == "conteudo"].groupby("session_id").sequence.min()
hp["abertura"] = hp.sequence.eq(hp.session_id.map(first_content))
hp["intervencao"] = (hp.k == "conteudo") & ~hp.abertura
s["prompts_conteudo"] = s.id.map(hp[hp.k == "conteudo"].groupby("session_id").size()).fillna(0)
s["prompts_rotina"] = s.id.map(hp[hp.k == "rotina"].groupby("session_id").size()).fillna(0)
s["intervencoes"] = s.id.map(hp[hp.intervencao].groupby("session_id").size()).fillna(0)
s["prompts_dev"] = s.prompts_conteudo + s.prompts_rotina
put("prompts_categorias", hp[hp.session_id.isin(s[s.valid].id)].k.value_counts().to_dict())

# ---------------------------------------------------------------- classes de sessão
PROTO = r"Vamos focar na resolu[çc][ãa]o individual|implementar exclusivamente a Issue"
INTEG = (r"Merge Requests|MRs delas|os MRs|Regras para Cria[çc][ãa]o do MR|unifica(ndo|r)? as (novas )?altera"
         r"|organiza[çc][ãa]o de branches")
allp = hp[hp.k != "sistema"].groupby("session_id").content.apply(lambda cs: "\n".join(cs.fillna("")))
s["all_prompts"] = s.id.map(allp).fillna("")
s["proto"] = s.first_prompt.fillna("").str.contains(PROTO)
s["issue"] = s.first_prompt.fillna("").str.extract(r"[Ii]ssue\s*#\s*(\d+)")[0].astype(float)
s["integ"] = s.first_prompt.fillna("").str.contains(INTEG)
src_mod = changed[changed.change_type.isin(["created", "modified"])].copy()
src_mod["rel"] = src_mod.file_path.apply(rel)
src_mod = src_mod[src_mod.rel.notna()]
src_mod["mod"] = src_mod.rel.apply(module_of)
src_mod = src_mod[src_mod["mod"].notna()]
s["arq_mod"] = s.id.map(src_mod.groupby("session_id").size()).fillna(0)
s["arq_codigo"] = s.id.map(src_mod[src_mod.rel.apply(is_source)].groupby("session_id").size()).fillna(0)
s["implementa"] = (s.arq_codigo > 0) | s.shell_edit


def issues_worked(row):
    """Issues de implementação da sessão: as citadas nos prompts e as branches criadas nela."""
    cited = set(map(int, re.findall(r"#(\d{1,3})\b", row.all_prompts)))
    cited |= set(map(int, re.findall(r"[Ii]ssues?\s+(\d{1,3})\b", row.all_prompts)))
    return cited


s["issues_cit"] = s.apply(issues_worked, axis=1)
s["n_issues"] = s.issues_cit.apply(len)


def classe(row):
    if row.integ:
        return "integracao"
    if row.proto and not np.isnan(row.issue):
        return "unica"
    if row.implementa and row.n_issues >= 2:
        return "agrupada"
    if row.implementa and row.n_issues == 1:
        return "unica"
    return "outra"


s["classe"] = s.apply(classe, axis=1)
s["impl_sem_issue"] = (s.classe == "outra") & s.implementa
v = s[s.valid].copy()

# ================================================================ Git: MRs
fp = g["main_first_parent"]
dev_all = set(g["main_all"])


def ancestors(h, stop=frozenset()):
    seen, stack = set(), [h]
    while stack:
        x = stack.pop()
        if x in seen or x in stop or x not in C:
            continue
        seen.add(x)
        stack.extend(C[x]["parents"])
    return seen


def refs_of(body):
    return (set(map(int, re.findall(r"(?:Closes|Fixes|Resolves)\s+#(\d+)", body, re.I)))
            | set(map(int, re.findall(r"^Refs:\s*#(\d+)", body, re.M))))


mrs, integ_time = [], {}
for h in fp:
    c = C[h]
    if len(c["parents"]) != 2:
        integ_time.setdefault(h, ts(c["committed_at"]))
        continue
    if re.search(r"Merge branch '(dev|main)' into", c["body"]):
        continue
    p1, p2 = c["parents"]
    branch_commits = [x for x in ancestors(p2, frozenset(ancestors(p1))) if len(C[x]["parents"]) == 1]
    br = re.search(r"Merge branch '([^']+)'", c["body"])
    branch = br.group(1) if br else ""
    issues = set(map(int, re.findall(r"(?:Closes|Fixes|Resolves)\s+#(\d+)", c["body"], re.I)))
    suf = re.search(r"-(\d+)$", branch)
    if suf:
        issues.add(int(suf.group(1)))
    for x in branch_commits:
        issues |= refs_of(C[x]["body"])
    files = sorted({f[0] for x in branch_commits for f in C[x]["files"]})
    mt = ts(c["committed_at"])
    for x in branch_commits:
        integ_time.setdefault(x, mt)
    w = modules_of_files([f for f in files if not f.startswith("services/")])
    if not w:
        sm = scope_module(branch)
        w = {sm: 1.0} if sm else {}
    mrs.append({"mhash": h, "branch": branch, "tipo": branch.split("/")[0] if "/" in branch else "outro",
                "issues": sorted(issues), "merged_at": mt, "branch_commits": branch_commits,
                "n_commits": len(branch_commits), "files": files, "mods": w,
                "src_ins": sum(f[1] for x in branch_commits for f in C[x]["files"] if is_source(f[0]))})
mr = pd.DataFrame(mrs)
mr = mr[(mr.merged_at < END) & (mr.n_commits > 0)].reset_index(drop=True)
mr["regime"] = np.where(mr.merged_at < R2_START, "R1", "R2")
mr["mod_princ"] = mr.mods.apply(lambda w: max(w, key=w.get) if w else None)
put("mr_total", len(mr))
put("mr_R1", int((mr.regime == "R1").sum()))
put("mr_R2", int((mr.regime == "R2").sum()))
put("mr_tipos", mr.tipo.value_counts().to_dict())
put("mr_ultima", str(mr.merged_at.max()))
put("mr_linhas_q", {r: q123(mr[mr.regime == r].src_ins) for r in ("R1", "R2")})

# commits do recorte (alcançáveis por dev), por módulo
nonmerge = [C[h] for h in dev_all if len(C[h]["parents"]) == 1 and ts(C[h]["authored_at"]) < END]
for c in nonmerge:
    c["_t"] = ts(c["committed_at"])
    c["_it"] = integ_time.get(c["hash"], c["_t"])
    c["_fix"] = bool(re.match(r"^(fix|revert)(\(|!|:)", c["body"])) or c["body"].startswith("Revert")
    c["_co"] = "Co-Authored-By: Claude" in c["body"]
    c["_mods"] = modules_of_files([f[0] for f in c["files"]]) or (
        {scope_module(c["body"]): 1.0} if scope_module(c["body"]) else {})
    c["_svc"] = all(f[0].startswith("services/") for f in c["files"]) and bool(c["files"])
nonmerge = [c for c in nonmerge if not c["_svc"]]
put("repo_commits_nao_merge", len(nonmerge))
put("repo_commits_merge", sum(1 for h in dev_all if len(C[h]["parents"]) == 2 and ts(C[h]["authored_at"]) < END))
put("repo_coautoria", sum(c["_co"] for c in nonmerge))
coauth = defaultdict(int)
for c in nonmerge:
    for m in re.findall(r"Co-Authored-By:\s*(Claude [^<]+?)\s*<", c["body"]):
        coauth[m] += 1
put("repo_coautoria_modelos", dict(coauth))
put("repo_escopo_modulo", sum(1 for c in nonmerge if scope_module(c["body"]) is not None))
put("repo_refs_issue", sum(1 for c in nonmerge if refs_of(c["body"])))
put("repo_harness", sum(1 for c in nonmerge if any(f[0].startswith(".claude/") for f in c["files"])))
put("repo_ci", len(g["ci_commits"]))
ci_first = min((ts(C[h]["authored_at"]) for h in g["ci_commits"] if h in C), default=None)
put("repo_ci_primeiro", str(ci_first) if ci_first is not None else None)
put("snapshots", g["snapshots"])
src_ins = lambda c: sum(f[1] for f in c["files"] if is_source(f[0]))  # noqa: E731
put("repo_linhas_fonte", sum(src_ins(c) for c in nonmerge))
put("repo_linhas_coautoria_frac", sum(src_ins(c) for c in nonmerge if c["_co"]) / sum(src_ins(c) for c in nonmerge))
for reg, lo, hi in (("R1", START - pd.Timedelta(days=2), R2_START), ("R2", R2_START, END)):
    sel = [c for c in nonmerge if lo <= ts(c["authored_at"]) < hi]
    put(f"{reg}_commits", len(sel))
    put(f"{reg}_linhas_coautoria_frac", sum(src_ins(c) for c in sel if c["_co"]) / max(1, sum(src_ins(c) for c in sel)))

# ================================================================ sessão -> módulos
br_mod = {}
for b in {x for bs in s.git_branches for x in (bs or [])}:
    m_ = re.search(r"-(\d+)$", b)
    sm = scope_module(b)
    if m_ and sm:
        br_mod[int(m_.group(1))] = sm
issue_mod = dict(br_mod)
for _, row in mr.iterrows():
    for n in row.issues:
        if row.mod_princ:
            issue_mod.setdefault(n, row.mod_princ)
lk = links[links.likely_related]
sess_commit = lk.groupby("session_id").commit_hash.apply(list).to_dict()
for c in nonmerge:
    for sid in re.findall(r"Claude-Session:\s*\S*?([0-9a-f-]{36})", c["body"]):
        for i in s[s.claude_session_id == sid].id:
            sess_commit.setdefault(i, []).append(c["hash"])
files_by_s = src_mod.groupby("session_id").rel.apply(list).to_dict()


def attribute(row):
    w = modules_of_files(files_by_s.get(row.id, []))
    if w:
        return w, "arquivos"
    if not np.isnan(row.issue) and int(row.issue) in issue_mod:
        return {issue_mod[int(row.issue)]: 1.0}, "issue"
    cs = [C[h] for h in sess_commit.get(row.id, []) if h in C]
    w = modules_of_files([f[0] for c in cs for f in c["files"]])
    if w:
        return w, "commits"
    mods = [issue_mod[n] for n in row.issues_cit if n in issue_mod]
    if mods:
        return {m_: mods.count(m_) / len(mods) for m_ in set(mods)}, "issues citadas"
    return {}, "sem atribuição"


att = v.apply(attribute, axis=1)
v["mods"] = [a[0] for a in att]
v["atrib"] = [a[1] for a in att]
put("atrib_origem", v.atrib.value_counts().to_dict())
put("atrib_origem_horas", (v.groupby("atrib").active_min.sum() / 60).to_dict())

# ================================================================ 5.1 cobertura
put("transcritos", len(s))
put("sessoes_validas", len(v))
for reg in ("R1", "R2"):
    sr, vr = s[s.regime == reg], v[v.regime == reg]
    put(f"{reg}_transcritos", len(sr))
    put(f"{reg}_validas", len(vr))
    put(f"{reg}_sem_resposta", int((~sr.valid).sum()))
    for f_ in ("shell_edit", "resumed", "interrupted", "orig_missing", "archived", "worktree", "snapshot"):
        put(f"{reg}_flag_{f_}", int(vr[f_].sum()))
    put(f"{reg}_nao_auditavel", int((vr.orig_missing & ~vr.archived & ~vr.snapshot).sum()))
    put(f"{reg}_com_commit", int(vr.id.isin(sess_commit.keys()).sum()))
put("nao_auditavel", int((v.orig_missing & ~v.archived & ~v.snapshot).sum()))
put("sem_resposta", int((~s.valid).sum()))
for f_ in ("shell_edit", "resumed", "interrupted", "orig_missing", "archived", "worktree", "snapshot"):
    put(f"flag_{f_}", int(v[f_].sum()))
put("com_commit", int(v.id.isin(sess_commit.keys()).sum()))
vers = sorted({x for vs in v.claude_code_versions for x in vs}, key=lambda t: [int(p) for p in re.findall(r"\d+", t)])
put("versoes_cc", [len(vers), vers[0], vers[-1]])
put("periodo", [str(v.start.min()), str(v.start.max())])
pv = u.pivot_table(index="session_id", columns="source", values=["total_tokens", "cost_usd"], aggfunc="sum")
pv.columns = [f"{a}_{b}" for a, b in pv.columns]
both = pv.dropna(subset=["total_tokens_ccusage", "total_tokens_claude_transcript"])
both = both[both.index.isin(v.id)]
put("cross_ambas", len(both))
put("cross_tokens_iguais", int((both.total_tokens_ccusage == both.total_tokens_claude_transcript).sum()))
cc_ = both[both.cost_usd_claude_transcript.fillna(0) > 0]
put("cross_custo_razao_mediana", float((cc_.cost_usd_ccusage / cc_.cost_usd_claude_transcript).median()))
put("sessoes_ccusage", int(v.id.isin(has_cc).sum()))
# sessões paralelas: intervalos de relógio que se sobrepõem a outra sessão com processamento
iv = v[["id", "start", "end"]].dropna().sort_values("start").values
over = set()
for i in range(len(iv)):
    for j in range(i + 1, len(iv)):
        if iv[j][1] >= iv[i][2]:
            break
        over |= {iv[i][0], iv[j][0]}
v["sobreposta"] = v.id.isin(over)
put("sobrepostas", {r: int(v[(v.regime == r)].sobreposta.sum()) for r in ("R1", "R2")})
put("sobrepostas_desde_23_10", int(v[(v.start >= PAR_START)].sobreposta.sum()))
put("sessoes_desde_23_10", int((v.start >= PAR_START).sum()))

# ================================================================ 5.2 sessões por regime e classe
for reg in ("total", "R1", "R2"):
    vr = v if reg == "total" else v[v.regime == reg]
    a = vr.active_min.dropna()
    top = a.sort_values(ascending=False)
    k = max(1, len(top) // 5)
    put(f"{reg}_n", len(vr))
    put(f"{reg}_ativo_h", float(a.sum() / 60))
    put(f"{reg}_relogio_h", float(vr.wall_h.sum()))
    put(f"{reg}_ativo_q", q123(a))
    put(f"{reg}_ativo_max_h", float(a.max() / 60))
    put(f"{reg}_quintil", float(top.iloc[:k].sum() / a.sum()))
    put(f"{reg}_prompts_dev", int(vr.prompts_dev.sum()))
    put(f"{reg}_prompts_q", q123(vr.prompts_dev))
    put(f"{reg}_prompts_media", float(vr.prompts_dev.mean()))
    put(f"{reg}_interv", int(vr.intervencoes.sum()))
    put(f"{reg}_interv_q", q123(vr.intervencoes))
    put(f"{reg}_interv_zero", int((vr.intervencoes == 0).sum()))
    put(f"{reg}_ferr", int(vr.tool_call_count.sum()))
    put(f"{reg}_ferr_err", int(vr.tool_error_count.sum()))
    put(f"{reg}_modelos", vr.model_label.value_counts().to_dict())
    put(f"{reg}_custo", float(vr.cost_usd.sum()))
    put(f"{reg}_custo_q", q123(vr.cost_usd))
    put(f"{reg}_tokens", float(vr.total_tokens.sum()))
    put(f"{reg}_tokens_cache", float(vr.cache_read_tokens.sum() / vr.total_tokens.sum()))
    put(f"{reg}_tokens_saida", float(vr.output_tokens.sum() / vr.total_tokens.sum()))
    put(f"{reg}_classes", vr.classe.value_counts().to_dict())
    put(f"{reg}_impl_sem_issue", int(vr.impl_sem_issue.sum()))
    put(f"{reg}_dias", int(vr.start.dt.date.nunique()))
    put(f"{reg}_mr_por_h", float(R[f"mr_{reg}" if reg != "total" else "mr_total"] / (a.sum() / 60)))
put("razao_relogio_ativo", R["total_relogio_h"] / R["total_ativo_h"])
cls = {}
for cl in ("unica", "agrupada", "integracao", "outra"):
    for reg in ("R1", "R2"):
        sub = v[(v.classe == cl) & (v.regime == reg)]
        cls[f"{cl}_{reg}"] = {"n": len(sub), "horas": float(sub.active_min.sum() / 60),
                              "ativo_q": q123(sub.active_min), "interv_q": q123(sub.intervencoes),
                              "interv": int(sub.intervencoes.sum()), "custo": float(sub.cost_usd.sum()),
                              "ferr_q": q123(sub.tool_call_count)}
put("classes", cls)

# ---------------------------------------------------------------- variantes do prompt-protocolo (Apêndice B)
def norm_prompt(text):
    text = re.sub(r"</?pasted_content[^>]*>", "", text)
    text = re.sub(r"#(\d+|<NUMERO_DA_ISSUE>)", "#N", text)
    return re.sub(r"\s+", " ", text).strip()


_u = v[v.classe == "unica"]
_var = _u.first_prompt.fillna("").apply(norm_prompt).value_counts()
put("protocolo_sessoes", len(_u))
put("protocolo_variantes", len(_var))
put("protocolo_variante_principal", int(_var.iloc[0]))
put("protocolo_modulo", int(_u.first_prompt.fillna("").str.contains("para o módulo de", regex=False).sum()))
put("protocolo_sem_paragrafo_inicial", int((~_u.first_prompt.fillna("").str.contains("Vamos focar", regex=False)).sum()))
_canon = next(p_ for p_ in _u.first_prompt if norm_prompt(p_) == _var.index[0])
_canon = re.sub(r"</?pasted_content[^>]*>", "", _canon).strip()
_canon = re.sub(r"Issue #\d+", "Issue #N", _canon)
put("protocolo_sha256", hashlib.sha256(_canon.encode("utf-8")).hexdigest())

# ================================================================ tarefas (R2, tarefa única)
issue_sessions = defaultdict(list)
for _, row in v.iterrows():
    if row.classe == "unica":
        n = int(row.issue) if not np.isnan(row.issue) else min(row.issues_cit)
        issue_sessions[n].append(row.id)
in_group = {n for _, row in v[v.classe == "agrupada"].iterrows() for n in row.issues_cit}
issue_to_mr = defaultdict(list)
for i, row in mr.iterrows():
    for n in row.issues:
        issue_to_mr[n].append(i)
trows = []
for n, sids in issue_sessions.items():
    ss = v[v.id.isin(sids)]
    if ss.regime.eq("R1").any() or n in in_group:
        continue
    start = ss.start.min()
    cands = [mr.loc[i] for i in issue_to_mr.get(n, []) if mr.loc[i].merged_at >= start]
    m_ = min(cands, key=lambda x: x.merged_at) if cands else None
    trows.append({"issue": n, "sessoes": len(ss), "start": start, "ativo": ss.active_min.sum(),
                  "interv": ss.intervencoes.sum(), "prompts": ss.prompts_dev.sum(),
                  "ferr": ss.tool_call_count.sum(), "err": ss.tool_error_count.sum(),
                  "custo": ss.cost_usd.sum(), "modelo": ss.model_label.iloc[0],
                  "worktree": bool(ss.worktree.any()), "paralela": bool(ss.sobreposta.any()),
                  "mod": issue_mod.get(n, max(ss.mods.iloc[0], key=ss.mods.iloc[0].get) if ss.mods.iloc[0] else None),
                  "mhash": None if m_ is None else m_.mhash, "merged_at": None if m_ is None else m_.merged_at,
                  "tipo": None if m_ is None else m_.tipo})
T = pd.DataFrame(trows)
T["integrada"] = T.mhash.notna()
T["ciclo_h"] = (pd.to_datetime(T.merged_at) - T.start).dt.total_seconds() / 3600
put("tarefas_n", len(T))
put("tarefas_multi_sessao", int((T.sessoes > 1).sum()))
put("tarefas_integradas", int(T.integrada.sum()))
put("tarefas_ativo_q", q123(T.ativo))
put("tarefas_interv_q", q123(T.interv))
put("tarefas_interv_dist", {"0": int((T.interv == 0).sum()), "1": int((T.interv == 1).sum()),
                            "2+": int((T.interv >= 2).sum())})
put("tarefas_ferr_q", q123(T.ferr))
put("tarefas_err_q", q123(100 * T.err / T.ferr.replace(0, np.nan)))
put("tarefas_custo_q", q123(T.custo))
put("tarefas_ciclo_q", q123(T.ciclo_h))
put("tarefas_ciclo_24h", int((T.ciclo_h <= 24).sum()))
put("tarefas_tipos", T[T.integrada].tipo.value_counts().to_dict())
put("tarefas_por_tipo", {tp: {"n": int((T.tipo == tp).sum()), "ativo": q123(T[T.tipo == tp].ativo),
                              "custo": q123(T[T.tipo == tp].custo)} for tp in ("feat", "fix", "docs", "test")})
put("tarefas_feat_fix_ativo", mw(T[T.tipo == "feat"].ativo, T[T.tipo == "fix"].ativo))
put("tarefas_por_modelo", {mm: {"n": int((T.modelo == mm).sum()), "ativo": q123(T[T.modelo == mm].ativo),
                                "custo": q123(T[T.modelo == mm].custo),
                                "periodo": [str(T[T.modelo == mm].start.min().date()) if (T.modelo == mm).any() else None,
                                            str(T[T.modelo == mm].start.max().date()) if (T.modelo == mm).any() else None]}
                           for mm in ("Opus 5", "Opus 5.5", "Sonnet 5", "Sonnet 5.5")})
T["dia"] = (T.start - T.start.min()).dt.total_seconds() / 86400
put("tarefas_tendencia_ativo", spearman_ci(T.dia, T.ativo))
put("tarefas_tendencia_custo", spearman_ci(T.dia, T.custo))
put("tarefas_paralelas", int(T.paralela.sum()))
put("tarefas_paralela_vs_nao", mw(T[T.paralela].ativo, T[~T.paralela & (T.start >= PAR_START)].ativo))

# ================================================================ retrabalho (linhas, SZZ simplificado)
origin_mod = {}
for c in nonmerge:
    origin_mod[c["hash"]] = c
ins_by = defaultdict(lambda: defaultdict(int))   # commit -> módulo -> linhas inseridas (fonte)
for c in nonmerge:
    for f, n_ins, _ in c["files"]:
        if is_source(f):
            mmod = module_of(f)
            if mmod is not None:
                ins_by[c["hash"]][mmod] += n_ins
churn_by = defaultdict(lambda: defaultdict(int))
churn_fix_by = defaultdict(lambda: defaultdict(int))
for x, per_file in linhas.items():
    cx = C.get(x)
    if x in REORG_EXCLUIDOS:
        continue
    if cx is None or ts(cx["authored_at"]) >= END + pd.Timedelta(days=REWORK_DAYS):
        continue
    tx = ts(cx["committed_at"])
    is_fix = bool(re.match(r"^(fix|revert)(\(|!|:)", cx["body"])) or cx["body"].startswith("Revert")
    for path, origins in per_file.items():
        mmod = module_of(path)
        if mmod is None:
            continue
        for o, n in origins.items():
            co = origin_mod.get(o)
            if co is None or o == x:
                continue
            it = co["_it"]
            if it < tx <= it + pd.Timedelta(days=REWORK_DAYS) and integ_time.get(x, tx) != it:
                churn_by[o][mmod] += n
                if is_fix:
                    churn_fix_by[o][mmod] += n
complete = lambda c: c["_it"] + pd.Timedelta(days=REWORK_DAYS) <= OBS  # noqa: E731
put("rw_reorg_excluidos", REORG_EXCLUIDOS)
put("rw_ultimo_integ_elegivel", str(OBS - pd.Timedelta(days=REWORK_DAYS)))
elig = [c for c in nonmerge if complete(c) and c["_it"] < END]
put("rw_commits_elegiveis", len(elig))
put("rw_commits_pendentes", sum(1 for c in nonmerge if not complete(c)))
tot_ins = sum(sum(ins_by[c["hash"]].values()) for c in elig)
tot_ch = sum(sum(churn_by[c["hash"]].values()) for c in elig)
tot_fx = sum(sum(churn_fix_by[c["hash"]].values()) for c in elig)
put("rw_linhas_inseridas", tot_ins)
put("rw_linhas_alteradas", tot_ch)
put("rw_linhas_alteradas_fix", tot_fx)
put("rw_frac", tot_ch / tot_ins)
put("rw_frac_fix", tot_fx / tot_ins)

# por MR (janela completa)
mr["completa"] = mr.merged_at + pd.Timedelta(days=REWORK_DAYS) <= OBS
mr["ins"] = mr.branch_commits.apply(lambda bc: sum(sum(ins_by[x].values()) for x in bc))
mr["churn"] = mr.branch_commits.apply(lambda bc: sum(sum(churn_by[x].values()) for x in bc))
mr["churn_fix"] = mr.branch_commits.apply(lambda bc: sum(sum(churn_fix_by[x].values()) for x in bc))
mc = mr[mr.completa & (mr.ins > 0)]
put("rw_mr_n", len(mc))
put("rw_mr_pendentes", int((~mr.completa).sum()))
for k_, col in (("linha", "churn"), ("linha_fix", "churn_fix")):
    kk = int((mc[col] > 0).sum())
    put(f"rw_mr_{k_}", [kk, len(mc), wilson(kk, len(mc))])
    put(f"rw_mr_{k_}_reg", {r: [int((mc[mc.regime == r][col] > 0).sum()), int((mc.regime == r).sum())]
                            for r in ("R1", "R2")})
put("rw_mr_frac_reg", {r: float(mc[mc.regime == r].churn.sum() / mc[mc.regime == r].ins.sum()) for r in ("R1", "R2")})
put("rw_mr_fixfrac_reg", {r: float(mc[mc.regime == r].churn_fix.sum() / mc[mc.regime == r].ins.sum()) for r in ("R1", "R2")})

# pós-hoc (sensibilidade da comparação R1 x R2 ao modelo): modelo predominante nas linhas inseridas do MR,
# pelo rodapé de coautoria de cada commit ("sem coautoria" quando o commit não traz o rodapé)
def modelo_mr(bc):
    acc = defaultdict(int)
    for x in bc:
        mm = re.findall(r"Co-Authored-By:\s*Claude ([^<]+?)\s*<", C[x]["body"])
        acc[mm[0] if mm else "sem coautoria"] += sum(ins_by[x].values())
    return max(acc, key=acc.get) if acc and max(acc.values()) > 0 else "sem coautoria"


mc = mc.assign(modelo=mc.branch_commits.apply(modelo_mr))
sens = {}
for (r_, m_), g_ in mc.groupby(["regime", "modelo"]):
    sens[f"{r_}|{m_}"] = {"mrs": int(len(g_)), "ins": int(g_.ins.sum()),
                          "frac": float(g_.churn.sum() / g_.ins.sum()),
                          "frac_fix": float(g_.churn_fix.sum() / g_.ins.sum()),
                          "mrs_com_rw": int((g_.churn > 0).sum()), "mrs_com_rw_fix": int((g_.churn_fix > 0).sum())}
put("posthoc_rw_modelo", sens)

# por tarefa (commits que citam a issue)
def task_commits(n, mh):
    m_ = mr[mr.mhash == mh].iloc[0]
    mine = [x for x in m_.branch_commits if n in refs_of(C[x]["body"])]
    if not mine and len(m_.issues) <= 1:
        mine = list(m_.branch_commits)
    return mine


T["completa"] = T.merged_at.apply(lambda t_: t_ is not None and pd.notna(t_) and t_ + pd.Timedelta(days=REWORK_DAYS) <= OBS)
tins, tch, tfx = [], [], []
for _, row in T.iterrows():
    if not row.integrada:
        tins.append(np.nan); tch.append(np.nan); tfx.append(np.nan)
        continue
    mine = task_commits(row.issue, row.mhash)
    tins.append(sum(sum(ins_by[x].values()) for x in mine))
    tch.append(sum(sum(churn_by[x].values()) for x in mine))
    tfx.append(sum(sum(churn_fix_by[x].values()) for x in mine))
T["t_ins"], T["t_churn"], T["t_fix"] = tins, tch, tfx
TC = T[T.completa & (T.t_ins > 0)].copy()
TC["rw"] = TC.t_churn > 0
put("rw_tarefas_n", len(TC))
put("rw_tarefas", [int(TC.rw.sum()), len(TC), wilson(int(TC.rw.sum()), len(TC))])
put("rw_tarefas_fix", [int((TC.t_fix > 0).sum()), len(TC), wilson(int((TC.t_fix > 0).sum()), len(TC))])
put("rw_tarefas_frac", float(TC.t_churn.sum() / TC.t_ins.sum()))
put("rw_tarefas_ativo", mw(TC[TC.rw].ativo, TC[~TC.rw].ativo))
put("rw_tarefas_interv", mw(TC[TC.rw].interv, TC[~TC.rw].interv))

# H4: sessões agrupadas x tarefa única (retrabalho por linha dos commits das issues da sessão)
def session_rw(row):
    iss = row.issues_cit if row.classe == "agrupada" else ({int(row.issue)} if not np.isnan(row.issue) else row.issues_cit)
    hs = [c for c in nonmerge if refs_of(c["body"]) & iss and c["_t"] >= row.start - pd.Timedelta(hours=1)
          and c["_t"] <= row.start + pd.Timedelta(days=3)]
    hs += [C[h] for h in sess_commit.get(row.id, []) if h in origin_mod]
    hs = {c["hash"]: c for c in hs}.values()
    hs = [c for c in hs if complete(c)]
    ins = sum(sum(ins_by[c["hash"]].values()) for c in hs)
    ch = sum(sum(churn_by[c["hash"]].values()) for c in hs)
    fx = sum(sum(churn_fix_by[c["hash"]].values()) for c in hs)
    return pd.Series({"h_ins": ins, "h_churn": ch, "h_fix": fx})


impl = v[v.classe.isin(["unica", "agrupada"])].copy()
impl = impl.join(impl.apply(session_rw, axis=1))
impl = impl[impl.h_ins > 0]
impl["h_frac"] = impl.h_churn / impl.h_ins
put("h4_n", impl.classe.value_counts().to_dict())
put("h4_frac", mw(impl[impl.classe == "agrupada"].h_frac, impl[impl.classe == "unica"].h_frac))
put("h4_frac_R1", mw(impl[(impl.classe == "agrupada") & (impl.regime == "R1")].h_frac,
                     impl[(impl.classe == "unica") & (impl.regime == "R1")].h_frac))
put("h4_global", {cl: float(impl[impl.classe == cl].h_churn.sum() / impl[impl.classe == cl].h_ins.sum())
                  for cl in ("agrupada", "unica")})
put("h4_regimes", pd.crosstab(impl.classe, impl.regime).to_dict())
put("h4_ins_q", {cl: q123(impl[impl.classe == cl].h_ins) for cl in ("agrupada", "unica")})

# H5: modelos
op5, op55 = T[T.modelo == "Opus 5"], T[T.modelo == "Opus 5.5"]
put("h5_custo", mw(op5.custo, op55.custo))
put("h5_ativo", mw(op5.ativo, op55.ativo))
a5, a55 = TC[TC.modelo == "Opus 5"], TC[TC.modelo == "Opus 5.5"]
tab = [[int(a5.rw.sum()), int((~a5.rw).sum())], [int(a55.rw.sum()), int((~a55.rw).sum())]]
put("h5_rw_tab", tab)
put("h5_rw_p", float(stats.fisher_exact(tab)[1]) if min(map(sum, tab)) > 0 else None)
put("h5_rw_frac", mw(a5.t_churn / a5.t_ins, a55.t_churn / a55.t_ins))
sn = TC[TC.modelo == "Sonnet 5"]
put("h5_rw_sonnet", [int(sn.rw.sum()), len(sn)])

# ================================================================ nível do módulo
mod = pd.DataFrame(index=sorted(MODULES))
mod["nome"] = pd.Series(MODULES)
for col, src in (("sessoes", None), ("ativo_h", "active_min"), ("prompts", "prompts_dev"),
                 ("interv", "intervencoes"), ("ferr", "tool_call_count"), ("custo", "cost_usd")):
    acc = defaultdict(float)
    for _, row in v.iterrows():
        for m_, w in row.mods.items():
            acc[m_] += w * (1 if src is None else (0 if pd.isna(row[src]) else row[src]))
    mod[col] = pd.Series(acc)
mod["ativo_h"] = mod.ativo_h / 60
mod = mod.fillna(0)
for reg in ("R1", "R2"):
    acc = defaultdict(float)
    for _, row in v[v.regime == reg].iterrows():
        for m_, w in row.mods.items():
            acc[m_] += w * (0 if pd.isna(row.active_min) else row.active_min) / 60
    mod[f"ativo_h_{reg}"] = pd.Series(acc)
cm_ = defaultdict(float)
lm_ = defaultdict(float)
lco = defaultdict(float)
for c in nonmerge:
    for m_, w in c["_mods"].items():
        cm_[m_] += w
    for m_, n in ins_by[c["hash"]].items():
        lm_[m_] += n
        if c["_co"]:
            lco[m_] += n
mod["commits"] = pd.Series(cm_)
mod["linhas"] = pd.Series(lm_)
mod["coautoria"] = pd.Series(lco) / mod.linhas
acc = defaultdict(float)
for _, row in mr.iterrows():
    for m_, w in row.mods.items():
        acc[m_] += w
mod["mr"] = pd.Series(acc)
ins_e, ch_e, fx_e = defaultdict(int), defaultdict(int), defaultdict(int)
for c in elig:
    for m_, n in ins_by[c["hash"]].items():
        ins_e[m_] += n
    for m_, n in churn_by[c["hash"]].items():
        ch_e[m_] += n
    for m_, n in churn_fix_by[c["hash"]].items():
        fx_e[m_] += n
mod["rw_ins"] = pd.Series(ins_e)
mod["rw_churn"] = pd.Series(ch_e)
mod["rw_fix"] = pd.Series(fx_e)
mod = mod.fillna(0)
mod["rw_frac"] = mod.rw_churn / mod.rw_ins.replace(0, np.nan)
mod["rw_fix_frac"] = mod.rw_fix / mod.rw_ins.replace(0, np.nan)
mod["interv_por_sessao"] = mod.interv / mod.sessoes.replace(0, np.nan)
mod["interv_por_h"] = mod.interv / mod.ativo_h.replace(0, np.nan)
first_c = defaultdict(lambda: None)
for c in sorted(nonmerge, key=lambda c: c["_t"]):
    for m_ in c["_mods"]:
        if first_c[m_] is None:
            first_c[m_] = str(c["_t"].date())
mod["primeiro_commit"] = pd.Series(dict(first_c))
put("modulos", json.loads(mod.to_json(orient="index", force_ascii=False)))

# comparação sistemática entre regimes (v10): o que mudou junto com o protocolo
def _reg(t):
    return "R1" if t < R2_START else "R2"
put("cmp_regimes", {
    "mr_tipos": {r: mr[mr.regime == r].tipo.value_counts().to_dict() for r in ("R1", "R2")},
    "commits_harness": {r: sum(1 for c in nonmerge if _reg(c["_t"]) == r and any(f[0].startswith(".claude/") for f in c["files"]))
                        for r in ("R1", "R2")},
    "commits": {r: sum(1 for c in nonmerge if _reg(c["_t"]) == r) for r in ("R1", "R2")},
    "modulos_iniciados": {r: int((pd.to_datetime(mod.primeiro_commit, utc=True).dt.tz_convert(TZ) < R2_START).sum()) if r == "R1"
                          else int((pd.to_datetime(mod.primeiro_commit, utc=True).dt.tz_convert(TZ) >= R2_START).sum()) for r in ("R1", "R2")},
})
put("modulos_totais", {"ativo_h": float(mod.ativo_h.sum()), "sessoes": float(mod.sessoes.sum()),
                       "linhas": float(mod.linhas.sum()), "mr": float(mod.mr.sum())})

# ================================================================ instrumento (percepção)
it_all = INSTR.read_text(encoding="utf-8")
it2 = it_all[it_all.index("## Parte 2"):it_all.index("## Parte 3")]
it3 = it_all[it_all.index("## Parte 3"):it_all.index("## Parte 4")]
it = it2
rank_rows = re.findall(r"^\| M(\d+) [^|]*\|\s*(\d+)[^|]*\|\s*(\d+)[^|]*\|\s*(\d+)[^|]*\|\s*(\d+)[^|]*\|\s*(\d+)[^|]*\|", it, re.M)
P = pd.DataFrame([[int(x) for x in r_] for r_ in rank_rows], columns=["m", "C1", "C2", "C3", "C4", "C5"]).set_index("m")
dfs = re.findall(r"^\| M(\d+) [^|]*\|\s*(\d)\s*\|\s*(\d)\s*\|\s*(\d)\s*\|", it3, re.M)
DFS = pd.DataFrame([[int(x) for x in r_] for r_ in dfs], columns=["m", "D", "F", "S"]).set_index("m")
assert len(P) == 13 and len(DFS) == 13, (len(P), len(DFS))
P = P.join(DFS)
put("instrumento", json.loads(P.to_json(orient="index")))
put("instrumento_DFS_q", {k: q123(P[k]) for k in ("D", "F", "S")})
put("instrumento_DFS_dist", {k: P[k].value_counts().sort_index().to_dict() for k in ("D", "F", "S")})
K = [m_ for m_ in MODULES if m_ != 9]   # personas: não implementado na tela, excluído das correlações
J = P.loc[K].join(mod.loc[K])
# Convenção: postos medidos com 1 = maior valor (como na ordenação percebida).
rk = lambda col: J[col].rank(ascending=False, method="average")  # noqa: E731
comp = {}
pairs = [("C1", "prompts", "H1 (principal): esforço próprio x prompts do desenvolvedor"),
         ("C1", "interv", "H1 (alternativa): esforço próprio x intervenções"),
         ("C1", "ativo_h", "Esforço próprio x tempo ativo do agente"),
         ("C2", "ativo_h", "Trabalho do agente x tempo ativo do agente"),
         ("C2", "custo", "Trabalho do agente x custo equivalente"),
         ("C2", "linhas", "Trabalho do agente x linhas inseridas"),
         ("C3", "interv_por_sessao", "H3 (provisória): dificuldade x intervenções por sessão"),
         ("C3", "ativo_h", "Dificuldade x tempo ativo do agente"),
         ("C4", "rw_frac", "Retrabalho percebido x fração de linhas alteradas em 14 dias"),
         ("C4", "rw_fix_frac", "Retrabalho percebido x fração alterada por correções"),
         ("C4", "rw_churn", "Retrabalho percebido x linhas alteradas em 14 dias"),
         ("C1", "C2", "Esforço próprio x trabalho do agente (ambos percebidos)")]
for a_, b_, label in pairs:
    x = J[a_]
    y = J[b_] if b_.startswith("C") else rk(b_)
    comp[f"{a_}~{b_}"] = {"rotulo": label, **spearman_ci(x, y)}
# H2: qualidade (1 = melhor) x retrabalho medido (1 = menor retrabalho)
for col in ("rw_frac", "rw_fix_frac"):
    comp[f"C5~{col}"] = {"rotulo": f"H2: qualidade percebida x {col} (1 = menos retrabalho)",
                         **spearman_ci(J.C5, J[col].rank(ascending=True, method="average"))}
comp["C5~C4"] = {"rotulo": "Qualidade x retrabalho, ambos percebidos (1 = menos retrabalho)",
                 **spearman_ci(J.C5, J.C4.rank(ascending=False))}
put("concordancia", comp)

# ---------------------------------------------------------------- pós-hoc: H2 e o regime de construção
# Análise exploratória feita depois dos resultados (Seção 6.2, Proposição 3): a qualidade percebida
# acompanha a parcela do trabalho do módulo feita em R1? E a relação C5 x retrabalho corretivo
# persiste quando essa parcela (ou a data de entrada do módulo) é controlada (correlação parcial de postos)?
J["frac_R1"] = J.ativo_h_R1 / (J.ativo_h_R1 + J.ativo_h_R2)
J["entrada"] = pd.to_datetime(J.primeiro_commit).astype("int64")


def parcial_postos(df, a, b, z):
    from scipy.stats import rankdata
    d_ = df[[a, b, z]].dropna()
    ra, rb, rz = (rankdata(d_[c]) for c in (a, b, z))
    res = lambda y: y - np.polyval(np.polyfit(rz, y, 1), rz)  # noqa: E731
    return {"rho_parcial": float(np.corrcoef(res(ra), res(rb))[0, 1]), "n": int(len(d_))}


J["rw_fix_menor"] = J.rw_fix_frac.rank(ascending=True, method="average")
put("posthoc_regime", {
    "C5~frac_R1": spearman_ci(J.C5, rk("frac_R1")),
    "C5~C1": spearman_ci(J.C5, J.C1),
    "C5~interv": spearman_ci(J.C5, rk("interv")),
    "C5~entrada": spearman_ci(J.C5, J.entrada.rank(ascending=True)),
    "rw_fix~frac_R1": spearman_ci(rk("rw_fix_frac"), rk("frac_R1")),
    "C5~rw_fix_menor|frac_R1": parcial_postos(J, "C5", "rw_fix_menor", "frac_R1"),
    "C5~rw_fix_menor|entrada": parcial_postos(J, "C5", "rw_fix_menor", "entrada"),
})
J["rank_prompts"] = rk("prompts")
J["rank_ativo"] = rk("ativo_h")
J["rank_rw"] = rk("rw_frac")
J["rank_interv_sessao"] = rk("interv_por_sessao")
J["dif_C1"] = J.C1 - J.rank_prompts
J["dif_C2"] = J.C2 - J.rank_ativo
J["dif_C4"] = J.C4 - J.rank_rw
put("postos", json.loads(J[["C1", "C2", "C3", "C4", "C5", "rank_prompts", "rank_ativo", "rank_rw",
                            "rank_interv_sessao", "dif_C1", "dif_C2", "dif_C4"]].to_json(orient="index")))

# P1, P4, P5: contrapartidas observadas
dias_uteis = pd.bdate_range("2026-07-29", "2026-10-31")
feriados = [pd.Timestamp("2026-09-07"), pd.Timestamp("2026-10-12")]
du = len([d for d in dias_uteis if d not in feriados])
put("p5_dias_uteis", du)
put("p5_feriados", [str(f.date()) for f in feriados])
put("p5_horas", [4 * du, 6 * du])
put("dias_com_sessao", int(v.start.dt.date.nunique()))
put("dias_uteis_com_sessao", int(sum(1 for d in v.start.dt.date.unique() if pd.Timestamp(d).weekday() < 5)))
put("p1_mr_por_h", {r: R[f"{r}_mr_por_h"] for r in ("R1", "R2")})
weeks_R1 = (pd.Timestamp("2026-08-31") - pd.Timestamp("2026-07-29")).days / 7
weeks_R2 = (pd.Timestamp("2026-10-31") - pd.Timestamp("2026-08-31")).days / 7
put("p1_mr_por_semana", {"R1": R["mr_R1"] / weeks_R1, "R2": R["mr_R2"] / weeks_R2})
lin_R = {r: sum(src_ins(c) for c in nonmerge if (ts(c["authored_at"]) < R2_START) == (r == "R1")) for r in ("R1", "R2")}
put("p1_linhas_por_semana", {"R1": lin_R["R1"] / weeks_R1, "R2": lin_R["R2"] / weeks_R2})
put("p1_dias_sessao", {r: int(v[v.regime == r].start.dt.date.nunique()) for r in ("R1", "R2")})

# ================================================================ semanas (figura)
week = lambda x: (x - pd.to_timedelta(x.dt.weekday, unit="D")).dt.normalize()  # noqa: E731
v["semana"] = week(v.start)
mrw = mr.assign(semana=week(mr.merged_at))
weeks = pd.date_range(v.semana.min(), v.semana.max(), freq="7D")
wk = pd.DataFrame(index=weeks)
wk["sessoes"] = v.groupby("semana").size()
wk["horas"] = v.groupby("semana").active_min.sum() / 60
wk["mr"] = mrw.groupby("semana").size()
wk["custo"] = v.groupby("semana").cost_usd.sum()
wk["interv"] = v.groupby("semana").intervencoes.sum()
wk = wk.fillna(0)
put("semanas", [{"inicio": str(i.date()), **{k: float(x) for k, x in r_.items()}} for i, r_ in wk.iterrows()])

# ================================================================ figuras
plt.rcParams.update({"font.family": "Liberation Sans", "font.size": 9, "axes.titlesize": 9,
                     "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
                     "legend.fontsize": 8, "axes.spines.top": False, "axes.spines.right": False})
CM = 1 / 2.54

# Figura 5.1: série semanal
fig, ax = plt.subplots(2, 1, figsize=(16 * CM, 9.5 * CM), sharex=True, gridspec_kw={"height_ratios": [1.15, 1]})
x = np.arange(len(wk))
labels = [d.strftime("%d/%m") for d in wk.index]
ax[0].bar(x - 0.2, wk.sessoes, 0.4, color="#9db4cf", label="Sessões válidas")
ax[0].bar(x + 0.2, wk.mr, 0.4, color="#3d5a80", label="Merge requests integrados")
ax[0].set_ylabel("Quantidade")
ax[0].legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2)
ax[1].bar(x, wk.horas, 0.6, color="#bbbbbb", label="Horas ativas do agente")
ax[1].set_ylabel("Horas ativas")
ax2 = ax[1].twinx()
ax2.plot(x, wk.custo, color="#c0392b", marker="o", ms=3, lw=1.2, label="Custo equivalente (US$)")
ax2.set_ylabel("US$")
ax2.spines["top"].set_visible(False)
h1, l1 = ax[1].get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax[1].legend(h1 + h2, l1 + l2, frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2)
r2i = int(np.searchsorted(wk.index, R2_START)) - 1
pi = int(np.searchsorted(wk.index, PAR_START))
ax[0].set_ylim(0, max(wk.sessoes.max(), wk.mr.max()) * 1.18)
for a_ in ax:
    a_.axvline(r2i - 0.5, color="#555", ls="--", lw=0.8)
    a_.axvline(pi - 0.5, color="#999", ls=":", lw=0.8)
top = ax[0].get_ylim()[1] * 0.97
ax[0].text(r2i - 0.42, top, "R2 →", fontsize=7.5, color="#555", va="top")
ax[0].text(r2i - 0.58, top, "← R1", fontsize=7.5, color="#555", va="top", ha="right")
ax[0].text(pi - 0.42, top, "worktrees", fontsize=7, color="#777", va="top")
ax[1].set_xticks(x, labels, rotation=45)
ax[1].set_xlabel("Semana (segunda-feira de início)")
fig.tight_layout()
fig.savefig(FIG / "fig51_serie_semanal.png", dpi=300)
plt.close(fig)

# Figura 5.2: esforço e entrega por módulo
order = mod.sort_values("ativo_h", ascending=True).index
fig, ax = plt.subplots(1, 3, figsize=(16 * CM, 8 * CM), sharey=True)
ylab = [f"M{i} {MODULES[i]}" for i in order]
yy = np.arange(len(order))
ax[0].barh(yy, mod.loc[order, "ativo_h"], color="#3d5a80")
ax[0].set_title("Tempo ativo do agente (h)")
ax[1].barh(yy, mod.loc[order, "prompts"], color="#9db4cf")
ax[1].set_title("Prompts do desenvolvedor")
ax[2].barh(yy, mod.loc[order, "linhas"] / 1000, color="#bbbbbb")
ax[2].set_title("Linhas inseridas (mil)")
ax[0].set_yticks(yy, ylab)
fig.tight_layout()
fig.savefig(FIG / "fig52_modulos.png", dpi=300)
plt.close(fig)

# Figura 5.3: percepção x medição por módulo (postos)
fig, ax = plt.subplots(1, 3, figsize=(16 * CM, 6 * CM))
for a_, (pc, mc_, tl) in zip(ax, [("C1", "rank_prompts", "(a) Esforço próprio x prompts"),
                                  ("C2", "rank_ativo", "(b) Trabalho do agente x tempo ativo"),
                                  ("C4", "rank_rw", "(c) Retrabalho x linhas alteradas")]):
    a_.plot([1, 12], [1, 12], color="#ccc", lw=0.8, ls="--")
    a_.scatter(J[mc_], J[pc], color="#3d5a80", s=14)
    for m_, r_ in J.iterrows():
        a_.annotate(f"M{m_}", (r_[mc_], r_[pc]), fontsize=6.5, xytext=(2, 2), textcoords="offset points")
    a_.set_xlim(0.3, 12.7)
    a_.set_ylim(0.3, 12.7)
    a_.invert_xaxis()
    a_.invert_yaxis()
    a_.set_xlabel("Posto medido (1 = maior)")
    a_.set_title(tl, fontsize=8)
ax[0].set_ylabel("Posto percebido (1 = maior)")
fig.tight_layout()
fig.savefig(FIG / "fig53_percepcao_medicao.png", dpi=300)
plt.close(fig)

json.dump(R, open(OUT, "w"), ensure_ascii=False, indent=1, default=str)
mod.to_csv(OUT.with_name("modulos.csv"))
T.to_pickle(D / "tarefas_v2.pkl")
v.drop(columns=["first_prompt", "all_prompts"]).to_pickle(D / "sessoes_v2.pkl")
hp.to_pickle(D / "prompts_v2.pkl")
print("ok", len(R), "chaves")
