# Métricas e Medições (GQM)

A equipe elaborou o plano de medição segundo o paradigma **GQM** (*Goal, Question, Metric*; Basili, Caldiera e Rombach, 1994): cada objetivo de medição é desdobrado em questões que dependem de métricas quantificáveis. Abaixo, para cada objetivo, o objeto, o propósito, o ponto de vista e o ambiente, seguidos da métrica associada.

## Objetivo 1 – Acompanhar o progresso do desenvolvimento

| Item | Descrição |
| ---- | --------- |
| Objeto | Requisitos do sistema |
| Propósito | Controlar o progresso do desenvolvimento dos requisitos ao longo das sprints, identificando desvios em relação ao planejado |
| Ponto de vista | Equipe de desenvolvimento |
| Ambiente | Sprints 1 a 6, no ambiente de desenvolvimento e versionamento do projeto (GitHub), com a implementação realizada pelos desenvolvedores |

| Métrica | Cálculo | Unidade | Medição | Valor esperado | Análise |
| ------- | ------- | ------- | ------- | -------------- | ------- |
| Taxa de conclusão dos requisitos | (Requisitos concluídos ÷ requisitos planejados) × 100 | % de requisitos | Ao final de cada sprint | No mínimo 70% ao fim de cada sprint; no mínimo 90% ao fim da Sprint 6 | Acompanha o andamento e identifica atrasos cedo. Abaixo de 70%, aciona o [replanejamento](projeto.md#criterios-de-replanejamento) |

## Objetivo 2 – Avaliar a qualidade de software

| Item | Descrição |
| ---- | --------- |
| Objeto | Funcionalidades implementadas do sistema |
| Propósito | Identificar defeitos nas funcionalidades implementadas a cada sprint, para avaliar a qualidade do software e orientar as correções antes da entrega |
| Ponto de vista | Analistas de Qualidade e desenvolvedores |
| Ambiente | Sprints 1 a 6, com testes executados no ambiente de desenvolvimento local e na branch `sprintN` |

| Métrica | Cálculo | Unidade | Medição | Valor esperado | Análise |
| ------- | ------- | ------- | ------- | -------------- | ------- |
| Densidade de defeitos | Defeitos encontrados ÷ requisitos testados | Defeitos/requisito | Ao final de cada sprint | No máximo 0,2 defeito por requisito testado | Mostra se a qualidade evolui ao longo das sprints; valores acima do esperado pedem reparos antes da próxima entrega |

## Objetivo 3 – Avaliar a cobertura dos testes

| Item | Descrição |
| ---- | --------- |
| Objeto | Requisitos do sistema |
| Propósito | Verificar se todos os requisitos implementados foram contemplados pelos testes, para que nenhuma funcionalidade seja entregue sem validação |
| Ponto de vista | Analistas de Qualidade e desenvolvedores |
| Ambiente | Sprints 1 a 6, com testes executados no ambiente de desenvolvimento e na branch `sprintN` |

| Métrica | Cálculo | Unidade | Medição | Valor esperado | Análise |
| ------- | ------- | ------- | ------- | -------------- | ------- |
| Cobertura de requisitos | (Requisitos testados ÷ requisitos implementados) × 100 | % de requisitos | Ao final de cada sprint | 100% dos requisitos implementados testados em cada sprint | Abaixo de 100% há requisitos sem validação, que devem ser testados antes da entrega da sprint |
