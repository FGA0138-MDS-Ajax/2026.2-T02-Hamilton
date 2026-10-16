# Visão do Projeto

## Ciclo de vida

A equipe adota um ciclo de vida ágil baseado no **Scrum**, complementado por práticas do **XP (Extreme Programming)**. O projeto tem várias funcionalidades e a experiência do usuário é foco principal, o que exige validações frequentes.

- Sprints de **7 dias**, com reuniões rápidas de alinhamento, revisão com o cliente e retrospectiva.
- Requisitos priorizados em **Must, Should e Could**.
- Comunicação por Teams ou Discord e versionamento no GitHub.

### Fluxo de trabalho Git

Uma branch para cada sprint, nomeada `sprintN` (`sprint1` a `sprint7`), onde o desenvolvimento é feito e integrado. A `main` é a branch final de entrega: tudo é testado na `sprintN` e, após a confirmação dos testes, a `sprintN` é integrada à `main` ao final da sprint.

## Organização do projeto

| Papel | Atribuições | Responsável |
| ----- | ----------- | ----------- |
| Desenvolvedor | Codificar o produto e os testes unitários, refatorar | Ana Clara e Henrique |
| Dono do Produto | Atualizar o escopo, organizar as sprints, validar entregas | Ricieri |
| Arquiteto de Software | Definir arquitetura, tecnologias e padrões | Arthur Miguel |
| Analista de Requisitos e Documentação | Levantar, analisar e documentar requisitos | Jônatas |
| Analista de Qualidade | Garantir qualidade e o conceito de pronto, inspecionar código | Letícia |
| Engenheiro de Dados | Projetar e manter a estrutura dos dados | Guilherme |
| Cliente | Apresentar necessidades, dar feedback e validar | Gabriel |

## Planejamento das sprints

| Sprint | Entrega | Início | Fim | Requisitos |
| :----: | ------- | :----: | :-: | ---------- |
| 1 | Cadastro e gerenciamento de usuário | 07/10/2026 | 14/10/2026 | R01 a R04 |
| 2 | Gestão de catálogo e avaliação de livros | 14/10/2026 | 21/10/2026 | R05 a R08 |
| 3 | Comunidades | 21/10/2026 | 28/10/2026 | R09 e R10 |
| 4 | Metas de leitura e fóruns | 28/10/2026 | 04/11/2026 | R11 a R14 |
| 5 | Progresso e ofensivas de leitura | 04/11/2026 | 11/11/2026 | R15 a R18 |
| 6 | Conquistas, recomendações e testes | 11/11/2026 | 18/11/2026 | R19 a R22 |
| 7 | Ajustes finais e apresentação | 18/11/2026 | 25/11/2026 | R23 |

## Comunicação

| Descrição | Envolvidos | Periodicidade | Produtos |
| --------- | ---------- | ------------- | -------- |
| Acompanhamento das atividades, riscos, compromissos e indicadores | Equipe do projeto | Semanal | Ata de reunião, relatório de situação |
| Comunicar a situação do projeto | Equipe e professor/monitor | Semanal | Ata de reunião, relatório de situação |
| Comunicação rápida e alinhamentos | Equipe do projeto | Conforme necessidade | Mensagem |

Ferramentas: Teams/Discord para reuniões e WhatsApp para comunicações rápidas.

## Gerenciamento de riscos

| Risco | Exposição | Prevenção | Contingência |
| ----- | :-------: | --------- | ------------ |
| Atraso na entrega por falta de tempo dos membros | Alto | Sprints curtas, escopo reduzido e tarefas conforme disponibilidade | Redefinir prioridades, movendo requisitos menos prioritários |
| Saída ou inatividade de um membro | Médio | Documentação atualizada e revisão de código em pares | Redistribuir tarefas essenciais e ajustar o escopo |
| Dificuldade técnica com banco de dados ou integração | Médio | Testes de integração e das principais rotas no início das sprints | Usar dados simulados nas demonstrações |
| Bugs críticos perto da entrega final | Alto | Testes contínuos de qualidade em todas as sprints | Priorizar login e cadastro e desativar recursos secundários com falha |
| Falta de familiaridade com as tecnologias | Médio | Estudos prévios e alinhamentos técnicos | Apoio dos monitores/professores e reatribuição de tarefas |

## Critérios de replanejamento

- **Atraso no cronograma:** taxa de conclusão inferior a 70% ao final de uma sprint.
- **Riscos mapeados** que se concretizem.
- **Ajuste interno de prioridades:** requisitos Should ou Could são adiados.
- **Incompatibilidade técnica:** adoção de solução alternativa.

A cada revisão de sprint a equipe confere esses critérios e, se necessário, atualiza e versiona este documento no repositório.
