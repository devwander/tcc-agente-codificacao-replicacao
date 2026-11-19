# Registro de integridade

Dados brutos não publicados (transcritos, banco e repositório do produto, sujeitos à LGPD), com os
resumos SHA-256 que permitem a uma auditoria autorizada confirmar que são os mesmos usados.

| Artefato | SHA-256 | Observação |
|---|---|---|
| Backup da base da ferramenta, 30/10/2026 | `18750c08cceb1b356bfebacf36f2ef6d3c7d3b62d2d09703b40fc9b5e17d7c2f` | restaurado em instância separada |
| Base sincronizada em 02/11/2026 | `8259c174bd96f892e0516137d9c78f269691cd7122936334216370d80e9c3ae6` | entrada de `extrair_v2.py` |
| Lista de resumos dos transcritos de 05/10–30/10 | `45409265053b9c26985684be9ffb48a50c74d3fc7c55cfc27325993fe392b0ae` | cópia feita antes de expirarem |
| Instrumento de percepção respondido | `58db32ad3f4b4bfc0b64e8d2cefc7bf133b8d224392cab9dd3f1f6fc60da9d2e` | publicado em `instrumentos/`; congelado em 02/11/2026 15h10 |
| Livro de códigos v1.2 | `52148d78c703d8a1cf60a28c0a6e25d004cc4322d994b85e74a8aaaeb2aed4cd` | publicado em `instrumentos/` |
| Codificação do autor (amostra de 60) | `95fe7363bdd8bc2d457e90ca91dcf97236c587b3e6a5bb124458b780fa2170eb` | não publicada (texto de prompts) |
| Adendo da codificação (2 substituições) | `bc379e4c5693efc85f345ed3a8718acffd160afd33b18bc277cf5d1ec9a27a97` | não publicado |
| Texto do prompt-protocolo | `f367cc1457b7adc6be46ddabbfdf595f79602f6623d335d299d72cb574980d39` | `instrumentos/PROTOCOLO-PROMPT.md` |
| Transcrito da 1ª sessão com o protocolo | `8f0bba747349d10b804c881ea8cdbfca0bd461a64bceae63bca27a1bb3817736` | não publicado |

Referências Git do caso: estrutura do recorte = topo de `origin/dev` em 02/11/2026,
commit `e2f6b5ee97b140858ad96f30a2893d50ef4f28d4`; reorganização excluída do retrabalho =
commit `c93a8c7d` (consolidação das migrações, 03/11/2026).

## Versão v1.2 (anonimizada)

Na v1.2, o nome do produto estudado foi substituído por `[produto]` no instrumento respondido e
nos comentários dos scripts, a pedido da orientação. Nenhuma outra palavra foi alterada, e os
scripts continuam funcionando, porque o caminho do caso vem da variável `TCC_CASO_PATH`.
O SHA-256 acima, do instrumento, refere-se ao arquivo original, congelado em 02/11/2026, guardado
com o autor. O SHA-256 da versão publicada na v1.2 é
`32969b6cf61c8a409f2e20e609396cd2db8dcc67e1f66211092831fd5bbbf5a4`.
