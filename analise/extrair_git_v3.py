"""Reextrai apenas o histórico Git do caso (versão 3: janela de retrabalho fechada em 14/11/2026).

Uso: python extrair_git_v3.py <repo> <saida_dir> [ref_recorte]

ref_recorte (padrão e2f6b5ee, topo de origin/dev na 1a leitura, 02/11/2026) define a estrutura do
recorte: cadeia de primeiro pai (merge requests), commits alcançáveis e snapshots. Em 11/11/2026
a dev recebeu fast-forward para a main, e a cadeia de primeiro pai do topo atual passou a seguir
as integrações dev -> main, escondendo os merge requests de outubro. Os commits posteriores
(até o topo atual) continuam no git.json e entram só na medição do retrabalho.
Mesmo código da parte Git de extrair_v2.py; as tabelas de sessão de extrair_v2.py não mudam
(a base sincronizada em 02/11/2026 cobre todo o recorte). Somente leitura.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO, OUT = sys.argv[1], Path(sys.argv[2])
REF = sys.argv[3] if len(sys.argv) > 3 else "e2f6b5ee97b140858ad96f30a2893d50ef4f28d4"
OUT.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ Git
def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], check=True, capture_output=True,
                          text=True).stdout

SEP = "\x1e"
raw = git("log", "--all", "--date=iso-strict", "--numstat",
          f"--format={SEP}%H%x1f%P%x1f%an%x1f%ad%x1f%cd%x1f%B%x1f")
commits = []
for block in raw.split(SEP)[1:]:
    parts = block.split("\x1f")
    h, parents, author, ad, cd, body = parts[:6]
    numstat = parts[6] if len(parts) > 6 else ""
    files = []
    for line in numstat.strip().splitlines():
        cols = line.split("\t")
        if len(cols) == 3:
            ins = int(cols[0]) if cols[0].isdigit() else 0
            dels = int(cols[1]) if cols[1].isdigit() else 0
            files.append((cols[2], ins, dels))
    commits.append({"hash": h, "parents": parents.split(), "author": author,
                    "authored_at": ad, "committed_at": cd, "body": body.strip(),
                    "files": files})
# Desde 08/10 os merge requests são integrados em dev, e dev é integrada em main;
# origin/dev contém todo o histórico de main até o corte.
first_parent_main = git("rev-list", "--first-parent", REF).split()
main_all = set(git("rev-list", REF).split())
ci = git("log", "--all", "--format=%H", "--", ".gitlab-ci.yml").split()
# Indicadores estáticos reconstruídos em datas de corte (estado de origin/main)
def snapshot(day):
    ref = git("rev-list", "-1", f"--before={day} 23:59:59 -0300", REF).strip()
    tree = git("ls-tree", "-r", "--name-only", ref).split("\n")

    def lines(*specs):
        out = git("grep", "-c", "", ref, "--", *specs)
        return sum(int(x.rsplit(":", 1)[1]) for x in out.splitlines() if x)

    def n(pred):
        return sum(1 for f in tree if f and pred(f))

    return {"ref": ref, "data": day,
            "backend_arquivos": n(lambda f: f.startswith("backend/") and f.endswith(".ts")),
            "backend_linhas": lines("backend/*.ts"),
            "frontend_arquivos": n(lambda f: f.startswith("frontend/") and f.endswith((".ts", ".tsx"))),
            "frontend_linhas": lines("frontend/*.ts", "frontend/*.tsx"),
            "testes_backend_unit": n(lambda f: f.startswith("backend/") and f.endswith(".spec.ts")
                                     and not f.endswith("e2e-spec.ts")),
            "testes_backend_e2e": n(lambda f: f.startswith("backend/") and f.endswith("e2e-spec.ts")),
            "testes_frontend": n(lambda f: f.startswith("frontend/")
                                 and re.search(r"\.(test|spec)\.(ts|tsx)$", f) is not None),
            "harness_regras": n(lambda f: f.startswith(".claude/rules/")),
            "harness_adr": n(lambda f: "/decisions/adr-" in f),
            "harness_hooks": n(lambda f: f.startswith(".claude/hooks/"))}


snapshots = [snapshot(d) for d in ("2026-08-31", "2026-09-30", "2026-10-31")]
json.dump({"commits": commits, "snapshots": snapshots, "main_first_parent": first_parent_main,
           "main_all": sorted(main_all), "ci_commits": ci, "ref_recorte": REF},
          open(OUT / "git.json", "w"))
print("commits", len(commits), "main fp", len(first_parent_main), "ci", len(ci))
