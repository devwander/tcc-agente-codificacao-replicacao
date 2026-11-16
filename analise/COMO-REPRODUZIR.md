# Como reproduzir a análise

Requer Python 3.11+, as dependências de `requirements.txt`, a base da ferramenta de coleta
restaurada em PostgreSQL e uma cópia do repositório do caso. Esses dados não são públicos
(ver o README principal).

```bash
pip install -r requirements.txt
export TCC_CASO_PATH=<caminho absoluto do repositório do caso na máquina da coleta>

# 1. tabelas de sessão (base da ferramenta, restaurada e sincronizada em 02/11/2026)
python extrair_v2.py postgresql://<usuário>:<senha>@<host>:<porta>/ai_analytics <repo do caso> dados/extraido
# 2. histórico Git (estrutura do recorte = commit e2f6b5ee; 2ª leitura em 15/11/2026)
python extrair_git_v3.py <repo do caso> dados/extraido
# 3. origem das linhas alteradas por commit (retrabalho por linha, à semelhança do SZZ)
python extrair_linhas_v2.py <repo do caso> dados/extraido
# 4. números e figuras (o instrumento é o de ../instrumentos/)
TCC_OBS="2026-11-15 12:00" python analisar_v2.py dados/extraido \
  ../instrumentos/INSTRUMENTO-PERCEPCAO-MODULOS-RESPONDIDO-20261102.md fig resultados_v3.json
# 5. sensibilidade: inclui a consolidação das migrações (c93a8c7d) no retrabalho
TCC_OBS="2026-11-15 12:00" TCC_INCLUIR_REORG=1 python analisar_v2.py dados/extraido \
  ../instrumentos/INSTRUMENTO-PERCEPCAO-MODULOS-RESPONDIDO-20261102.md fig resultados_v3_sens_reorg.json
```

Ficam fixados no `analisar_v2.py`: fuso America/Recife, regimes (R2 a partir de 01/09/2026),
corte em 31/10/2026, janela de retrabalho de 14 dias, mapa de pastas para módulos, regras de
classificação de prompts e de sessões, extensões de código-fonte e semente do bootstrap
(20261031, 4.000 reamostragens). `make_figs.py` gera a Figura 4.1 (linha do tempo). Os blocos `cmp_regimes` (Tabela 6.2) e `exposicao` (Seção 5.5) ficam no fim do `analisar_v2.py`, para não alterar a sequência aleatória dos intervalos calculados antes.
