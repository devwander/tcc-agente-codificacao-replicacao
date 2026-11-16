"""Extrai do banco restaurado e do Git do caso as tabelas usadas na análise (versão 2: recorte até 31/10).

Uso: python extrair.py <dsn> <repo> <saida_dir>
Somente leitura: consultas SELECT no banco e comandos de leitura no Git.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import psycopg

DSN, REPO, OUT = sys.argv[1], sys.argv[2], Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)

with psycopg.connect(DSN) as conn:
    def q(sql, params=None):
        return pd.read_sql(sql, conn, params=params)

    # [produto] principal e as cópias de trabalho (worktrees) criadas dentro dele
    CASO = os.environ.get("TCC_CASO_PATH", "").rstrip("/")
    if not CASO:
        sys.exit("defina TCC_CASO_PATH com o caminho do repositório do caso usado na coleta")
    projects = q("select id, name, path from projects where path = %(p)s or path like %(w)s",
                 {"p": CASO, "w": CASO + "/.claude/worktrees/%"})
    PROJECT_IDS = [int(i) for i in projects.id]
    projects.to_pickle(OUT / "projects.pkl")

    sessions = q("""
        select s.id, s.project_id, s.claude_session_id, s.started_at, s.ended_at, s.duration_seconds,
               s.active_turn_seconds, s.api_duration_seconds, s.status, s.first_prompt,
               s.models_used, s.claude_code_versions, s.git_branches, s.message_count,
               s.human_prompt_count, s.confirmed_human_prompt_count, s.assistant_message_count,
               s.tool_call_count, s.tool_error_count, s.thinking_block_count,
               s.files_touched, s.files_modified, s.files_read, s.files_outside_project,
               sf.unparseable_lines, sf.archive_path, sf.transcript_path
          from sessions s left join session_source_files sf on sf.session_id = s.id
         where s.project_id = any(%s)
    """, (PROJECT_IDS,))
    usages = q("""
        select u.session_id, u.source, u.input_tokens, u.output_tokens, u.cache_creation_tokens,
               u.cache_read_tokens, u.total_tokens, u.cost_usd
          from usages u join sessions s on s.id = u.session_id
         where s.project_id = any(%s) and u.model is null
    """, (PROJECT_IDS,))
    usages_model = q("""
        select u.session_id, u.source, u.model, u.total_tokens, u.cost_usd
          from usages u join sessions s on s.id = u.session_id
         where s.project_id = any(%s) and u.model is not null
    """, (PROJECT_IDS,))
    links = q("""
        select l.session_id, c.commit_hash, l.likely_related, l.overlap_count, l.within_session_window
          from session_commit_links l
          join git_commits c on c.id = l.git_commit_id
          join sessions s on s.id = l.session_id
         where s.project_id = any(%s)
    """, (PROJECT_IDS,))
    changed = q("""
        select cf.session_id, cf.file_path, cf.change_type, cf.tool_name, cf.insertions,
               cf.deletions, cf.is_within_project
          from changed_files cf join sessions s on s.id = cf.session_id
         where s.project_id = any(%s)
    """, (PROJECT_IDS,))
    tools = q("""
        select t.session_id, t.tool_name, count(*) n, sum(case when t.is_error then 1 else 0 end) err
          from tool_calls t join sessions s on s.id = t.session_id
         where s.project_id = any(%s) group by 1, 2
    """, (PROJECT_IDS,))
    surveys = q("select * from session_surveys")
    messages = q("""
        select m.session_id, m.sequence, m.role, m.message_type, m.timestamp,
               case when m.message_type = 'human_prompt' then left(m.content, 4000) end as content
          from messages m join sessions s on s.id = m.session_id
         where s.project_id = any(%s) and not m.is_sidechain
    """, (PROJECT_IDS,))

for name, df in [("sessions", sessions), ("usages", usages), ("usages_model", usages_model),
                 ("links", links), ("changed", changed), ("tools", tools), ("surveys", surveys),
                 ("messages", messages)]:
    df.to_pickle(OUT / f"{name}.pkl")
    print(name, len(df))

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
first_parent_main = git("rev-list", "--first-parent", "origin/dev").split()
main_all = set(git("rev-list", "origin/dev").split())
ci = git("log", "--all", "--format=%H", "--", ".gitlab-ci.yml").split()
# Indicadores estáticos reconstruídos em datas de corte (estado de origin/main)
def snapshot(day):
    ref = git("rev-list", "-1", f"--before={day} 23:59:59 -0300", "origin/dev").strip()
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
           "main_all": sorted(main_all), "ci_commits": ci},
          open(OUT / "git.json", "w"))
print("commits", len(commits), "main fp", len(first_parent_main), "ci", len(ci))
