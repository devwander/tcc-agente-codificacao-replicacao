# Instrumento de percepção retrospectiva por módulo — versão 1.1 (02/11/2026)

Este é o instrumento da Seção 4.6.3 e do Apêndice A da monografia. Você o preenche **uma única vez**, e é ele que fornece os dados de percepção do TCC.

> **Versão 1.1:** os módulos foram renumerados por ordem de entrada no sistema e ganharam a coluna "onde aparece". A alteração foi feita antes de qualquer resposta.
>
> **Modo de aplicação:** respostas coletadas em diálogo com o assistente (Claude Code). O assistente apresentou as perguntas sem sugerir valores e sem mostrar métricas. A conversa fica como trilha de auditoria.

## Antes de começar (regras)

1. **Preencha numa sessão só**, de preferência em menos de 40 minutos. Anote abaixo o horário de início e de fim.
2. **Não consulte nada:** nem git, painel da ferramenta, GitLab, transcritos ou o Cap. 5. Responda só de memória, porque é exatamente a sua percepção que está sendo medida.
3. **Não existe resposta certa.** Se não lembrar de algo, escreva "não lembro". Não chute com base em números que tenha visto.
4. **Ao terminar, não altere mais nada.** Avise que terminou. O arquivo será congelado com SHA-256 e data, e só depois disso as métricas por módulo serão calculadas.
5. Considere o período de **29/07 a 31/10/2026** e apenas o [produto] principal (backend + frontend). Os microsserviços ficam de fora.

- Início: 02/11 às 14:15
- Fim: 02/11 às 15:10

---

## Parte 1 — Os módulos

Os nomes correspondem às pastas e aos escopos de commit, para ajudar você a identificar cada módulo.

| Id | Módulo | Onde aparece na aplicação | Inclui (código) |
|---|---|---|---|
| M1 | Harness e infraestrutura (transversal) | Fora da tela: `.claude/` (regras, hooks, agentes, knowledge), banco, CI | `.claude/`, escopos `harness`, `db`, `ci`, `deps` |
| M2 | Interface e design system (transversal) | Layout, menu lateral, `/style-guide`, componentes compartilhados | escopo `ui`, `shared/`, `app/layouts` |
| M3 | Acesso e permissões | `/login`, recuperar/redefinir senha, `/administradores`, `/settings`, `/meu-perfil`, filtro de menu por papel | `auth`, `rbac`, `admins`, `settings` |
| M4 | Unidades (multiunidade) | `/unidades` e seletor de unidade ativa no topo | `units` |
| M5 | Pacientes | `/pacientes` (lista, detalhe, prontuário), aba de PTS no detalhe, área da família `/patient-app` | `patients`, `therapeutic-plans`, `patient-app`, `patient-self-service` |
| M6 | Terapeutas e equipe de cuidado | `/team` (Equipe Terapêutica), primeiro acesso com biometria, equipe no detalhe do paciente | `therapists`, `care-team`, `my-therapists` |
| M7 | Agenda | `/agenda` (Agenda & Conciliação), prontuário da sessão, "Minha Agenda" da família | `schedule`, `my-schedule` |
| M8 | Integrações | Aba "Integração Digital" no detalhe do paciente ([produto] Connect / hub digital) | `integrations` |
| M9 | Personas | `/personas` (Biblioteca de Personas, ainda "em construção" na tela; só backend) | `personas` |
| M10 | Convênios e operadoras | `/operadoras` e convênio no detalhe do paciente | `convenios`, `operadoras` |
| M11 | Notificações | Avisos dentro da Agenda e da "Minha Agenda" da família; preferências | `notifications` |
| M12 | Estratégico | `/dashboard`, `/strategic-insights` ([produto] Insights), `/reports` | `dashboard`, `reports`, `insights` |
| M13 | Auditoria | `/pre-auditoria`, `/validacao-amostras`, `/correcoes` | `audit` |

A numeração segue a **ordem de entrada no sistema**, isto é, a data do primeiro commit de cada módulo em `origin/main`. Módulos que entraram no mesmo dia aparecem em ordem arbitrária. Um módulo pode ter crescido depois da entrada: em Pacientes, por exemplo, a área da família e o PTS vieram mais tarde. As datas não aparecem aqui de propósito, para não servir de âncora para as respostas.

---

## Parte 2 — Ordenação dos módulos

Em cada critério, **ordene os 13 módulos de 1 (mais) a 13 (menos)**. Evite empates. Se for inevitável, repita o número (ex.: dois módulos em 4º).

- **C1. Esforço seu:** o seu tempo e atenção para especificar, acompanhar o agente, revisar, testar e corrigir. Não é o trabalho do agente.
- **C2. Trabalho do agente:** o quanto o agente precisou trabalhar, em tempo de processamento e tamanho das sessões.
- **C3. Dificuldade:** complexidade técnica ou de regra de negócio.
- **C4. Retrabalho depois de entregue:** quanto precisou ser corrigido ou refeito depois do merge.
- **C5. Qualidade final:** o quanto você considera o módulo bem resolvido hoje. 1 = melhor qualidade.

| Módulo | C1 Esforço seu | C2 Trabalho do agente | C3 Dificuldade | C4 Retrabalho | C5 Qualidade (1 = melhor) |
|---|---|---|---|---|---|
| M1 Harness/infra (transversal) | 4 | 11 | 5 | 11 | 2 |
| M2 Interface (transversal) | 1 | 4 | 12 | 5 | 1 |
| M3 Acesso/permissões | 5 | 7 | 10 | 4 | 7 |
| M4 Unidades | 10 | 10 | 11 | 8 | 5 |
| M5 Pacientes | 2 | 5 | 8 | 1 | 3 |
| M6 Terapeutas/equipe | 3 | 6 | 7 | 2 | 4 |
| M7 Agenda | 9 | 8 | 6 | 3 | 6 |
| M8 Integrações | 8 | 3 | 2 | 7 | 12 |
| M9 Personas | 12 (ainda não desenvolvido) | 13 | 4 | 13 | 13 |
| M10 Convênios/operadoras | 11 | 9 | 9 | 10 | 8 |
| M11 Notificações | 13 | 12 | 13 | 12 | 11 |
| M12 Estratégico | 7 | 2 | 3 | 6 | 9 |
| M13 Auditoria | 6 | 1 | 1 | 9 | 10 |

---

## Parte 3 — Avaliação de cada módulo (escalas de 1 a 5)

- **D. Delegação:** 1 = eu escrevi quase tudo; 3 = metade; 5 = o agente escreveu quase tudo.
- **F. Confiança no código do agente:** 1 = revisei tudo linha a linha; 3 = revisei os pontos críticos; 5 = integraria sem revisar.
- **S. Satisfação com a experiência de desenvolver o módulo com o agente:** 1 = muito insatisfeito; 5 = muito satisfeito.
- **Episódio marcante:** uma frase sobre o que mais marcou, positivo ou negativo.

| Módulo | D | F | S | Episódio marcante |
|---|---|---|---|---|
| M1 Harness/infra | 5 | 3 | 5 | Em vários momentos do desenvolvimento foi essencial ao levantar decisões já tomadas e pontos de atenção. |
| M2 Interface | 5 | 3 | 5 | Precisou de mais atenção de inicio, porém após conseguir deixar fidedigno ao designer, foi bem aplicado. |
| M3 Acesso/permissões | 5 | 3 | 4 | Precisou de alguns testes práticos para entender se estava sendo implementado corretamente. |
| M4 Unidades | 5 | 4 | 5 | Foi implementado conforme instruído. |
| M5 Pacientes | 5 | 3 | 4 | Precisou de revisões e retrabalhos devido a divergências com o designer, porém funcionou bem depois de revisão. |
| M6 Terapeutas/equipe | 5 | 3 | 4 | Foi implementado bem, porém precisou de revisão para pontos que não tinha sido implementados de inicio com a visualização dos dados do terapeuta. |
| M7 Agenda | 5 | 3 | 4 | Funcional, mas precisou de revisões de uso e exibição para ficar coerente. |
| M8 Integrações | 5 | 3 | 5 | Realizou bem a integração com um sistema externo e fornecendo a captação de dados de forma genérica. |
| M9 Personas | 5 | 5 | 3 | Modulo propriamente não implementando, aguardando a base para elaborar o possível micro serviço de personas. |
| M10 Convênios/operadoras | 5 | 4 | 3 | Funcional, mas creio que ainda necessita de testes para checar o funcionamento e a integração com outras partes do sistema. |
| M11 Notificações | 5 | 5 | 3 | Foi implementado como parte de outro módulo (agenda) basicamente. Creio que há espaço para aprimorar recursos, mas creio que funciona no que se propõe atualmente. |
| M12 Estratégico | 5 | 4 | 4 | Realizou bem a exibição de dados e também o consumo de dados para geração de texto no [produto]-insights, porém acredito que há pontos de melhoria. |
| M13 Auditoria | 5 | 4 | 4 | Apesar de dificuldades iniciais realizou bem a integração do micro serviço de validação de documentos. Infelizmente ainda não foi testado em documentos reais. |

---

## Parte 4 — Percepção sobre o processo (respostas curtas)

**P1. Antes × depois do protocolo.** Comparando agosto (sessões longas, várias tarefas) com setembro e outubro (uma sessão por issue), você foi mais produtivo em qual período? Quanto, mais ou menos, em %?
> Creio que fui mais produtivo trabalhando issue por issue, diria que cerca de 20-30%.
**P2. Qualidade antes × depois do protocolo.** Em qual período o código saiu com mais qualidade, ou com menos retrabalho?
> Creio que após o protocolo houve mais qualidade.
**P3. Issues agrupadas.** Quando juntou várias issues num mesmo chat, o resultado foi melhor, igual ou pior que o de uma issue por sessão? Por que agrupava?
> Creio que dependa do agrupamento, houve momentos que agrupei devido ao tamanho da tarefa como um todo ser pequeno, porém creio que em momentos de tarefas maiores não faça muito sentido. Para os casos que realizei isso, não consigo distinguir se o resultado ficou pior ou melhor.
**P4. Sessões paralelas em worktrees** (a partir de 23/10). Elas aumentaram a sua produtividade? E o seu esforço de acompanhar?
> Minha impressão é que elas possivelmente reduziram minha produtividade devido a conflitos (pode ter sido impressão), mas prefiro trabalhar com uma sessão em um mesmo projeto, para evitar conflitos.
**P5. Esforço total.** Sem consultar nada, quantas horas **suas** você estima ter dedicado ao [produto] entre 29/07 e 31/10?
> Creio que trabalhei cerca de 4-6 horas diretamente no [produto] nos dias úteis (leve em conta que a empresa é de [local omitido] para os feriados)
**P6. Sem o agente.** Quanto tempo você acha que levaria para chegar ao mesmo ponto do [produto] sem o agente, trabalhando sozinho?
> Diria que algo em torno de 1-2 anos, não tenho conhecimento técnico para implementar módulos como a verificação de documentos e a geração de texto por ia diretamente, certamente sem o agente eu levaria mais tempo estudando para conseguir colocar em prática.
**P7. Onde foi o seu tempo.** Distribua 100% do seu tempo entre: especificar/escrever issues ___%, acompanhar o agente ___%, revisar/testar ___%, integrar/MRs ___%, outros ___%.
> especificar/escrever issues 30%, acompanhar o agente 15%, revisar/testar 30%, integrar/MRs 15%, outros 10%.
**P8. Comentário livre.**
> O agente sem dúvida foi essencial para o desenvolvimento do projeto, porém trouxe outros pontos de atenção, como: escrever melhor as issues, acompanhar as alterações de outros (agente), revisar e testar venho a levar mais tempo, afinal 'eu' não havia escrito o código e deveria dobrar a atenção para garantir que tudo estava funcionando como devia e encontrar erros e  bugs, mais código = mais MRs e mais trabalho para integração (não que eu ache ruim), revisões de documentos com regras de negócios assim como designer para buscar garantir que o que o agente receberia estaria correto e condizente com os nosso objetivos.
---

*Ao terminar, não edite mais o arquivo e avise para que ele seja congelado (SHA-256 + data) antes de qualquer análise por módulo.*
