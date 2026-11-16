"""Rastreia, para cada commit integrado, a origem das linhas que ele altera ou remove.

Uso: python extrair_linhas.py <repo> <saida_dir>

Para cada commit X (não merge, alcançável a partir de origin/main), lê as faixas
de linhas removidas ou alteradas em `git diff -U0 -M X^ X` nos arquivos-fonte e
executa `git blame` em X^ sobre essas faixas, à semelhança do algoritmo SZZ
(ŚLIWERSKI; ZIMMERMANN; ZELLER, 2005). O resultado associa cada commit às linhas
de commits anteriores que ele modificou. Somente leitura.
"""
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO, OUT = sys.argv[1], Path(sys.argv[2])
SOURCE_EXT = (".ts", ".tsx", ".js", ".jsx", ".sql", ".css", ".scss", ".json", ".prisma")
NOT_SOURCE = ("package-lock.json", "pnpm-lock.yaml", "yarn.lock")


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True, errors="replace",
                          check=True).stdout


def is_source(path):
    base = path.rsplit("/", 1)[-1]
    return (path.endswith(SOURCE_EXT) and base not in NOT_SOURCE and not path.startswith(".claude/")
            and not path.startswith("services/"))


commits = git("rev-list", "--no-merges", "origin/dev").split()
result = {}
for x in commits:
    parents = git("rev-list", "--parents", "-n", "1", x).split()[1:]
    if not parents:
        continue
    diff = git("diff", "-U0", "-M", "--no-color", f"{x}^", x)
    ranges, old = {}, None
    for line in diff.splitlines():
        if line.startswith("--- "):
            old = None if line == "--- /dev/null" else line[6:]
        elif line.startswith("@@") and old and is_source(old):
            m = re.match(r"@@ -(\d+)(?:,(\d+))? \+", line)
            start, count = int(m.group(1)), int(m.group(2) or 1)
            if count:
                ranges.setdefault(old, []).append((start, count))
    origins = {}
    for path, rs in ranges.items():
        args = ["blame", "-l", "-s"]
        for start, count in rs:
            args += ["-L", f"{start},+{count}"]
        try:
            out = git(*args, f"{x}^", "--", path)
        except subprocess.CalledProcessError:
            continue
        cnt = Counter(bl.split(" ", 1)[0].lstrip("^") for bl in out.splitlines())
        if cnt:
            origins[path] = dict(cnt)
    result[x] = origins  # versão 2: {arquivo no pai: {commit de origem: linhas}}
json.dump(result, open(OUT / "linhas_por_arquivo.json", "w"))
print("commits", len(commits), "com linhas alteradas", sum(1 for v in result.values() if v))
