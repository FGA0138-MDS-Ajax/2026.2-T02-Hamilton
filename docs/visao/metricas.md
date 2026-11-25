# Métricas e Medições (GQM)

A equipe elaborou o plano de medição segundo o paradigma **GQM** (*Goal, Question, Metric*; Basili, Caldiera e Rombach, 1994): cada objetivo de medição (G) é desdobrado em questões (Q) que, para serem respondidas, dependem de métricas quantificáveis (M). Abaixo, para cada objetivo, o objeto, o propósito, o ponto de vista e o ambiente, seguidos das questões e da métrica que as responde.

## Visão geral

| Objetivo (G) | Questões (Q) | Métrica (M) |
| ------------ | ------------ | ----------- |
| G1 – Acompanhar o progresso do desenvolvimento | Q1.1, Q1.2, Q1.3 | M1 – Taxa de conclusão dos requisitos |
| G2 – Avaliar a qualidade de software | Q2.1, Q2.2, Q2.3 | M2 – Densidade de defeitos |
| G3 – Avaliar a cobertura dos testes | Q3.1, Q3.2 | M3 – Cobertura de requisitos |

## Objetivo 1 – Acompanhar o progresso do desenvolvimento

| Item | Descrição |
| ---- | --------- |
| Objeto | Requisitos do sistema |
| Propósito | Controlar o progresso do desenvolvimento dos requisitos ao longo das sprints, identificando desvios em relação ao planejado |
| Ponto de vista | Equipe de desenvolvimento |
| Ambiente | Sprints 1 a 6, no ambiente de desenvolvimento e versionamento do projeto (GitHub), com a implementação realizada pelos desenvolvedores |

| Questão | Descrição | Métrica que responde |
| :-----: | --------- | -------------------- |
| Q1.1 | Quantos dos requisitos planejados para a sprint foram concluídos? | M1, calculada ao fim de cada sprint |
| Q1.2 | O ritmo de conclusão é suficiente para entregar o escopo planejado até a Sprint 6? | M1 acumulada, comparada à meta de 90% ao fim da Sprint 6 |
| Q1.3 | O atraso de alguma sprint exige acionar o replanejamento? | M1 abaixo de 70% ao fim da sprint |

| ID | Métrica | Cálculo | Unidade | Medição | Valor esperado | Análise |
| :-: | ------- | ------- | ------- | ------- | -------------- | ------- |
| M1 | Taxa de conclusão dos requisitos | (Requisitos concluídos ÷ requisitos planejados) × 100 | % de requisitos | Ao final de cada sprint | No mínimo 70% ao fim de cada sprint; no mínimo 90% ao fim da Sprint 6 | Acompanha o andamento e identifica atrasos cedo. Abaixo de 70%, aciona o [replanejamento](projeto.md#criterios-de-replanejamento) |

## Objetivo 2 – Avaliar a qualidade de software

| Item | Descrição |
| ---- | --------- |
| Objeto | Funcionalidades implementadas do sistema |
| Propósito | Identificar defeitos nas funcionalidades implementadas a cada sprint, para avaliar a qualidade do software e orientar as correções antes da entrega |
| Ponto de vista | Analistas de Qualidade e desenvolvedores |
| Ambiente | Sprints 1 a 6, com testes executados no ambiente de desenvolvimento local e na branch `sprintN` |

| Questão | Descrição | Métrica que responde |
| :-----: | --------- | -------------------- |
| Q2.1 | Quantos defeitos são encontrados, em média, por requisito testado na sprint? | M2, calculada ao fim de cada sprint |
| Q2.2 | A qualidade das entregas melhora ou piora ao longo das sprints? | M2 comparada entre sprints consecutivas |
| Q2.3 | A quantidade de defeitos está dentro do limite aceitável para integrar a sprint à `main`? | M2 igual ou inferior a 0,2 defeito por requisito testado |

| ID | Métrica | Cálculo | Unidade | Medição | Valor esperado | Análise |
| :-: | ------- | ------- | ------- | ------- | -------------- | ------- |
| M2 | Densidade de defeitos | Defeitos encontrados ÷ requisitos testados | Defeitos/requisito | Ao final de cada sprint | No máximo 0,2 defeito por requisito testado | Mostra se a qualidade evolui ao longo das sprints; valores acima do esperado pedem reparos antes da próxima entrega e acionam o [replanejamento](projeto.md#criterios-de-replanejamento) |

## Objetivo 3 – Avaliar a cobertura dos testes

| Item | Descrição |
| ---- | --------- |
| Objeto | Requisitos do sistema |
| Propósito | Verificar se todos os requisitos implementados foram contemplados pelos testes, para que nenhuma funcionalidade seja entregue sem validação |
| Ponto de vista | Analistas de Qualidade e desenvolvedores |
| Ambiente | Sprints 1 a 6, com testes executados no ambiente de desenvolvimento e na branch `sprintN` |

| Questão | Descrição | Métrica que responde |
| :-----: | --------- | -------------------- |
| Q3.1 | Que proporção dos requisitos implementados na sprint foi testada? | M3, calculada ao fim de cada sprint |
| Q3.2 | Algum requisito implementado está sendo entregue à `main` sem validação? | M3 abaixo de 100% |

| ID | Métrica | Cálculo | Unidade | Medição | Valor esperado | Análise |
| :-: | ------- | ------- | ------- | ------- | -------------- | ------- |
| M3 | Cobertura de requisitos | (Requisitos testados ÷ requisitos implementados) × 100 | % de requisitos | Ao final de cada sprint | 100% dos requisitos implementados testados em cada sprint | Abaixo de 100% há requisitos sem validação, que devem ser testados antes da entrega da sprint; aciona o [replanejamento](projeto.md#criterios-de-replanejamento) |
