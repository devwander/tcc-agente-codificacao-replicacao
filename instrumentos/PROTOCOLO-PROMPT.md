# Prompt-protocolo de abertura das sessões de tarefa (regime R2)

Usado desde 1º de setembro de 2026 para abrir cada sessão de tarefa única com o Claude Code
(Apêndice B da monografia). Variante mais frequente, presente em 81 das 228 sessões de tarefa
única; as outras dez variantes têm as mesmas cinco etapas, e 118 sessões omitem o parágrafo inicial.
O número da issue aparece como `#N` (ou `<NUMERO_DA_ISSUE>`, como no original).

```text
Vamos focar na resolução individual das issues criadas, garantindo que cada uma possa ser acompanhada de forma isolada para fins de métricas.

Sua tarefa agora é implementar exclusivamente a Issue #N.

Por favor, siga estas etapas:
1. Obtenção do Contexto: Use o MCP do GitLab para carregar a descrição, critérios de aceite e links do Figma referentes à Issue #<NUMERO_DA_ISSUE>.
2. Inspecionar Figma: Se a issue envolver interface, use o MCP do Figma para inspecionar os componentes e detalhes visuais referenciados na issue.
3. Plano de Execução Curto: Apresente brevemente quais arquivos serão criados ou modificados para solucionar a Issue #<NUMERO_DA_ISSUE>.
4. Implementação: Crie uma branch/solução isolada específica para esta issue e faça o desenvolvimento completo da demanda.
5. Encerramento: Confirme a implementação fazendo referência expressa ao número da issue para que possamos testar e registrar a conclusão da Issue #<NUMERO_DA_ISSUE> no GitLab.

Não inicie nenhuma outra issue além da Issue #<NUMERO_DA_ISSUE> no momento.
```

O texto exato, extraído dos transcritos, está em `PROTOCOLO-PROMPT.txt`; `sha256sum PROTOCOLO-PROMPT.txt` reproduz o resumo citado na monografia:
`f367cc1457b7adc6be46ddabbfdf595f79602f6623d335d299d72cb574980d39`.
O transcrito da primeira sessão com o protocolo (1º/09/2026, 14h39) está arquivado com SHA-256
`8f0bba747349d10b804c881ea8cdbfca0bd461a64bceae63bca27a1bb3817736` (não publicado).
