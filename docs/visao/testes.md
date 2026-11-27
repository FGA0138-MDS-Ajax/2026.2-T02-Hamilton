# Testes de Software

A garantia da qualidade do CoLecture apoia-se em um processo estruturado de verificação e validação (Pressman e Maxim, 2016), com múltiplos níveis, tipos e ambientes integrados ao fluxo Git da equipe.

## Níveis

1. **Unitários:** regras de negócio isoladas em Python/Django, como a média de avaliações dos livros, o algoritmo de contagem de ofensivas e as regras de permissão por perfil (Cliente, Moderador e Administrador).
2. **Integração:** comunicação entre os módulos, incluindo persistência e consulta no SQLite, integração das views com as rotas (URLconf) e os models, e sincronização entre ações nos fóruns e as metas de leitura ativas. Inclui os testes automatizados que simulam requisições HTTP com o `django.test.Client` (sem navegador nem interface gráfica), como o CT01 e o CT07 (`accounts/tests.py`): eles exercitam rota, view, formulário, model e banco em conjunto, mas não a interface renderizada.
3. **Sistema:** comportamento do software como um todo, na perspectiva do usuário final, com jornadas completas (cadastro de novo leitor, entrada em comunidade, registro diário de páginas lidas e alcance de metas colaborativas) pela interface responsiva. Só é classificado neste nível o teste executado pela interface, seja manualmente no navegador, seja por ferramenta de automação de interface (como Selenium ou Playwright).

## Tipos

- **Funcionais:** validam as saídas contra os requisitos R01 a R22 (o CT06 cobre o R21). Cobrem autenticação, cadastro e filtragem no catálogo, gerenciamento de membros, moderação de tópicos e concessão de insígnias.
- **Não funcionais:** responsividade da interface em diferentes resoluções, integridade das sementes de inicialização do banco (seeds) e envio correto de notificações e logs (R21).

## Técnicas

Os casos de teste combinam técnicas de caixa-preta e de caixa-branca (Pressman e Maxim, 2016):

| Técnica | Como é aplicada | Exemplos no projeto |
| ------- | --------------- | ------------------- |
| **Caixa-preta** | O teste usa apenas as entradas e as saídas previstas nos requisitos, sem depender do código interno. É a base dos testes de integração com o `django.test.Client` e dos testes de sistema pela interface | Login com credenciais válidas e inválidas (CT01); jornadas completas pelo navegador em `system_tests` (CT01 a CT07) |
| **Partição de equivalência** | As entradas são divididas em classes válidas e inválidas, e cada classe é testada com ao menos um valor representativo. Nos testes, os métodos costumam vir em pares `VALID` e `INVALID` | Nota da avaliação: válida (1 a 5) e inválida (texto, `6.0` ou `9.0`) (CT02); criação e edição de meta com dados válidos e inválidos e com e sem permissão (CT04) |
| **Análise de valor-limite** | São testados os valores nas bordas de cada classe, onde os erros são mais frequentes | Notas `1.0` e `5.0` aceitas e `6.0` recusada (CT02); páginas lidas igual a zero e maior que o total do livro, progresso menor ou igual ao anterior e data de amanhã recusados (CT05); ofensiva mantida com leitura de ontem e zerada ao faltar um dia (CT05) |
| **Caixa-branca** | O teste é escrito a partir da lógica interna (models, services e regras de validação), para percorrer os caminhos e as condições do código | Algoritmo de contagem da ofensiva em `ProfileStreakModelTests`; validações do model `ReadingSession` em `ReadingSessionModelTests`; regras de participação em metas do `GoalService` (CT04) |

Os testes de sistema também incluem cenários de robustez (`SiteBreakingEdgeCasesSystemTest`), que tentam quebrar o site com dados duplicados, valores negativos, mensagens em branco e URLs inexistentes ou malformadas.

## Ambientes

| Ambiente | Uso |
| -------- | --- |
| Desenvolvimento local | Desenvolvedores e analistas de qualidade executam testes unitários e de integração antes do commit |
| Branch `sprintN` (`sprint1` a `sprint7`) | Homologação e integração: testes de integração e de sistema validam a fusão dos novos recursos; nada vai à `main` sem aprovação completa |
| Branch `main` | Entrega ao término de cada sprint: recebe apenas código testado, auditado pela qualidade e aprovado pelo Dono do Produto, sem regressões |

## Integração contínua

A validação automática é feita pelo GitHub Actions, no workflow **Testes do Django** (`.github/workflows/django_tests.yml`), adotado a partir da Sprint 7:

1. **Quando roda:** a cada *push* em qualquer branch, a cada *pull request* e manualmente (`workflow_dispatch`). Assim, todo commit na `sprintN` e o *pull request* da `sprintN` para a `main` disparam os testes.
2. **Testes por app (`test-apps`):** um job para cada app Django (`accounts`, `books`, `communities`, `forums`, `goals`, `logs`, `main`, `notifications` e `rewards`), executados em paralelo com `python manage.py test <app>`. Um app com falha não interrompe os demais (`fail-fast: false`), de modo que o relatório mostra todos os apps reprovados de uma vez.
3. **Testes de sistema (`test-system`):** instala o navegador Chromium do Playwright e executa `python manage.py test system_tests`, que percorre as jornadas dos CT01 a CT07 pela interface.
4. **Ambiente:** Ubuntu com Python 3.14 e as dependências do `requirements.txt`.

O *pull request* da `sprintN` para a `main` só é integrado com todos os jobs aprovados, conforme a regra de que nada vai à `main` sem aprovação completa. Uma falha na CI é tratada como teste reprovado: o defeito é registrado no relatório da sprint, corrigido e retestado até que a execução fique verde.

O workflow `ci.yml` é separado: ele apenas publica este site de documentação a cada *push* na branch `docs` e não executa testes.

## Formas de análise

A eficácia dos testes é acompanhada pelos indicadores do [plano GQM](metricas.md):

- **Taxa de cobertura de requisitos:** requisitos testados ÷ implementados em cada sprint, com meta de 100%.
- **Densidade de defeitos:** nº de testes que falharam ÷ nº de testes da funcionalidade, com tolerância máxima de 0,2.

## Critério de avaliação (previsto × realizado)

Cada caso de teste define um **resultado previsto**; durante a bateria de testes a equipe registra o **resultado realizado**.

- Previsto = realizado: **teste aprovado** (ausência de defeitos).
- Previsto ≠ realizado: **teste reprovado**; o defeito é registrado no histórico da sprint, corrigido e retestado até que os resultados coincidam, o que autoriza a promoção do código à `main`.

## Responsabilidades, registro e esforço

Cada caso de teste é planejado segundo o 5W1H: **o quê** (objetivo e critérios), **por quê** (requisitos associados), **quando** (sprint), **quem** (responsável pela execução e pela auditoria), **onde** (ambiente de execução e local de registro dos resultados) e **quanto** (esforço estimado).

- **Quem:** a execução e a auditoria dos testes cabem aos Analistas de Qualidade (ver [Organização do projeto](projeto.md#organizacao-do-projeto)). Por definição do Dono do Produto, a líder de Qualidade (Letícia) executa e audita todos os casos. A auditoria confere se há evidência da execução, se os testes automatizados cobrem o que cada caso promete, se o previsto × realizado foi registrado corretamente e se as métricas do relatório da sprint batem com os testes executados, os testes reprovados e os requisitos testados.
- **Onde:** os testes automatizados são executados no ambiente local, dentro da pasta `colecture/`, com `python manage.py test`, e novamente na branch `sprintN` após a integração dos recursos da sprint. Os resultados (previsto × realizado, defeitos, reparos e retestes) são registrados no relatório da sprint correspondente (`docs/sprints/sprintN.md`), e cada defeito é aberto como *issue* no GitHub.
- **Quanto:** o esforço de cada caso é a soma de 30 minutos de preparação (ambiente, banco de testes e leitura dos critérios), do tempo de execução medido da suíte automatizada e de cerca de 2 minutos por método de teste para a conferência do previsto × realizado e o registro, arredondada para a meia hora seguinte. Os tempos de execução foram medidos em 23/11/2026, na branch `sprint7` (commit `5fe1e41`), em ambiente local, com todos os 362 métodos dos CT01 a CT07 aprovados. Retestes de defeitos não estão incluídos e são contabilizados no relatório da sprint. O esforço total previsto é de 17 horas.

## Roteiro de testes

Os casos CT01 a CT07 derivam dos cenários e requisitos do backlog. Os quadros abaixo registram o planejamento de cada caso (objetivo, critérios, responsáveis, ambiente e esforço); os resultados de cada execução (previsto × realizado, defeitos encontrados, reparos e ciclos de reteste) são registrados no relatório da sprint indicada em cada quadro, em `docs/sprints/sprintN.md`.

| Caso | Nome | Requisitos | Nível | Tipo |
| :--: | ---- | ---------- | ----- | ---- |
| [CT01](#ct01) | Validação de Autenticação, Cadastro e Perfil | R01, R02, R03, R04 (Sprint 1) | Integração | Funcional |
| [CT02](#ct02) | Catálogo, Registro, Busca e Avaliação de Livros | R05, R06, R07, R08 (Sprint 2) | Integrado / Sistema | Funcional |
| [CT03](#ct03) | Manter Comunidade e Interface da Página | R09, R10 (Sprint 3) | Sistema | Funcional |
| [CT04](#ct04) | Metas de Leitura, Manter e Moderar Fórum | R11, R12, R13, R14 (Sprint 4) | Sistema | Funcional |
| [CT05](#ct05) | Registro de Progresso, Livro Lido, Página de Leitura e Ofensivas | R15, R16, R17, R18 (Sprint 5) | Integrado / Sistema | Funcional |
| [CT06](#ct06) | Insígnias, Recomendações por Tema e Notificações | R19, R20, R21 (parte de notificações) (Sprint 6) | Sistema | Funcional e Não Funcional |
| [CT07](#ct07) | Gestão Administrativa e Inicialização via Seed | R02, R03 (Sprint 1 / Gestão Geral) | Integração | Funcional e Não Funcional |

### CT01

**Validação de Autenticação, Cadastro e Perfil**

| Item | Descrição |
| ---- | --------- |
| Requisitos associados | R01, R02, R03, R04 (Sprint 1) |
| Objetivo do teste | Garantir que o usuário consiga criar uma conta, realizar login com credenciais válidas, efetuar logout e editar suas informações na página de perfil. |
| Nível do teste | Integração (requisições simuladas com `django.test.Client`, sem interface) |
| Tipo de teste | Funcional |
| Precondições | Banco de testes criado pelo `TestCase` do Django e rotas de cadastro, login, logout e perfil (`accounts`) configuradas. |
| Critério de aceito | O usuário cria a conta, acessa a plataforma e atualiza dados do perfil com sucesso. |
| Critério de rejeitado | Erro ao autenticar credenciais válidas ou falha ao salvar alterações de perfil. |
| Responsável pela execução (Quem) | Letícia (líder de Qualidade) |
| Auditoria (Quem) | Letícia (líder de Qualidade) |
| Ambiente de execução (Onde) | Local (`python manage.py test accounts.tests.CT01`) e branch `sprint1` |
| Registro dos resultados (Onde) | `docs/sprints/sprint1.md` e *issues* do GitHub para os defeitos |
| Testes automatizados | `accounts/tests.py`: `CT01` (11 métodos) |
| Tempo de execução medido | 17 s (11 de 11 aprovados) |
| Esforço estimado (Quanto) | 1 h |

### CT02

**Catálogo, Registro, Busca e Avaliação de Livros**

| Item | Descrição |
| ---- | --------- |
| Requisitos associados | R05, R06, R07, R08 (Sprint 2) |
| Objetivo do teste | Validar as páginas de registro e pesquisa, o cadastro de livros inexistentes, os filtros do catálogo e o sistema de avaliação (nota 1-5, resenhas e média do livro). |
| Nível do teste | Integrado / Sistema |
| Tipo de teste | Funcional |
| Precondições | Usuário autenticado e catálogo populado para buscas. |
| Critério de aceito | O livro é registrado na página dedicada, aparece nos filtros de busca e permite receber nota (1-5) e resenha, calculando a média corretamente. |
| Critério de rejeitado | Livro não cadastrado, falha nos filtros da busca ou erro no cálculo da média das avaliações. |
| Responsável pela execução (Quem) | Letícia (líder de Qualidade) |
| Auditoria (Quem) | Letícia (líder de Qualidade) |
| Ambiente de execução (Onde) | Local (`python manage.py test books.tests.CT02 books.tests.CT02_BookStatus`) e branch `sprint2` |
| Registro dos resultados (Onde) | `docs/sprints/sprint2.md` e *issues* do GitHub para os defeitos |
| Testes automatizados | `books/tests.py`: `CT02` (11) e `CT02_BookStatus` (5), total de 16 métodos |
| Tempo de execução medido | 5 s (16 de 16 aprovados) |
| Esforço estimado (Quanto) | 1,5 h |

### CT03

**Manter Comunidade e Interface da Página**

| Item | Descrição |
| ---- | --------- |
| Requisitos associados | R09, R10 (Sprint 3) |
| Objetivo do teste | Validar a página de comunidade e todas as ações de "manter": criação, configuração de privacidade (aberta/fechada), aprovação e remoção de membros e exclusão/arquivamento da comunidade. |
| Nível do teste | Sistema |
| Tipo de teste | Funcional |
| Precondições | Usuário autenticado no sistema com perfil de Leitor/Cliente. |
| Critério de aceito | A página da comunidade exibe todas as informações e o moderador consegue gerenciar membros, aprovar solicitações ou excluir a comunidade. |
| Critério de rejeitado | Falha ao carregar a página da comunidade ou negação de acesso nas funções do moderador. |
| Responsável pela execução (Quem) | Letícia (líder de Qualidade) |
| Auditoria (Quem) | Letícia (líder de Qualidade) |
| Ambiente de execução (Onde) | Local (`python manage.py test communities`) e branch `sprint3` |
| Registro dos resultados (Onde) | `docs/sprints/sprint3.md` e *issues* do GitHub para os defeitos |
| Testes automatizados | `communities/tests.py`: `CT03` (5), `CreateCommunityTest` (1), `ViewCommunityTest` (4), `MembershipRequestTest` (17), `MemberRoleEditTest` (16), `ManageMemberBanTest` (6), `DeleteCommunityTest` (2) e `PurgeArchivedCommunitiesTest` (5), total de 56 métodos |
| Tempo de execução medido | 3 min 48 s (56 de 56 aprovados) |
| Esforço estimado (Quanto) | 2,5 h |

### CT04

**Metas de Leitura, Manter e Moderar Fórum**

| Item | Descrição |
| ---- | --------- |
| Requisitos associados | R11, R12, R13, R14 (Sprint 4) |
| Objetivo do teste | Testar a criação de metas por capítulos, a visualização de metas ativas/encerradas, a criação/arquivamento de fóruns por meta e as ferramentas de moderação (fixar, trancar, editar e excluir tópicos). |
| Nível do teste | Sistema |
| Tipo de teste | Funcional |
| Precondições | Comunidade criada e usuário autenticado como Moderador. |
| Critério de aceito | A meta é criada com datas/capítulos, o progresso é listado na visão de metas ativas/encerradas e o moderador consegue fixar/trancar/editar/excluir tópicos do fórum. |
| Critério de rejeitado | Metas não diferenciam status ativo/encerrado ou falha nas permissões de moderação do fórum. |
| Responsável pela execução (Quem) | Letícia (líder de Qualidade) |
| Auditoria (Quem) | Letícia (líder de Qualidade) |
| Ambiente de execução (Onde) | Local (`python manage.py test goals forums communities.tests.CT_CommunityGoalsPage`) e branch `sprint4` |
| Registro dos resultados (Onde) | `docs/sprints/sprint4.md` e *issues* do GitHub para os defeitos |
| Testes automatizados | `goals/tests.py`: `CT04GoalCreation` (16), `CT04GoalEdit` (6), `CT04GoalParticipation` (11), `CT04GoalAutoParticipation` (17) e `CT_GoalConclude` (7); `communities/tests.py`: `CT_CommunityGoalsPage` (11); `forums/tests.py`: `ForumCreation` (2), `ForumCreationRules` (2), `ForumAccess` (28) e `ForumMessages` (14), total de 114 métodos |
| Tempo de execução medido | 3 min 51 s (114 de 114 aprovados) |
| Esforço estimado (Quanto) | 4,5 h |

### CT05

**Registro de Progresso, Livro Lido, Página de Leitura e Ofensivas**

| Item | Descrição |
| ---- | --------- |
| Requisitos associados | R15, R16, R17, R18 (Sprint 5) |
| Objetivo do teste | Validar a página de leitura com abas distintas (leitura do dia vs. livros já lidos), o registro diário de progresso, a marcação do livro como lido e o cálculo das ofensivas (pessoal e da comunidade). |
| Nível do teste | Integrado / Sistema |
| Tipo de teste | Funcional |
| Precondições | Usuário possui livros vinculados à sua conta ("em andamento" ou "lidos"). |
| Critério de aceito | A página de leitura alterna corretamente entre as abas, o progresso/livro lido é registrado com data/porcentagem e a ofensiva (streak) acumula os dias consecutivos. |
| Critério de rejeitado | Erro de navegação entre abas, falha ao registrar status "lido" ou cálculo incorreto da ofensiva. |
| Responsável pela execução (Quem) | Letícia (líder de Qualidade) |
| Auditoria (Quem) | Letícia (líder de Qualidade) |
| Ambiente de execução (Onde) | Local (`python manage.py test books accounts.tests.CTEstantePerfil accounts.tests.ProfileViewStreakResetTests goals.tests.ProfileStreakModelTests goals.tests.GoalReadingSessionApiTests`) e branch `sprint5` |
| Registro dos resultados (Onde) | `docs/sprints/sprint5.md` e *issues* do GitHub para os defeitos |
| Testes automatizados | `books/tests.py`: classes de sessão de leitura (`ReadingSession*`, `CreateReadingSessionApiTests`, `EditReadingSessionApiTests`, `ListReadingSessionsApiTests`, `SaveReadingSessionViewTests`), 82 métodos, e `BookshelfDatabaseSourceTests` (23); `accounts/tests.py`: `CTEstantePerfil` (11) e `ProfileViewStreakResetTests` (2); `goals/tests.py`: `ProfileStreakModelTests` (9) e `GoalReadingSessionApiTests` (5), total de 132 métodos |
| Tempo de execução medido | 3 min 15 s (132 de 132 aprovados) |
| Esforço estimado (Quanto) | 5 h |

### CT06

**Insígnias, Recomendações por Tema e Notificações**

| Item | Descrição |
| ---- | --------- |
| Requisitos associados | R19, R20, R21 (parte de notificações) (Sprint 6) |
| Objetivo do teste | Avaliar a atribuição de insígnias/conquistas, as sugestões do motor de recomendação por temas/tags e o envio de notificações do sistema (aprovações em comunidades, novos ciclos de metas). |
| Nível do teste | Sistema |
| Tipo de teste | Funcional e Não Funcional |
| Precondições | Histórico de leituras/avaliações no perfil e ações disparadoras de notificação disponíveis. |
| Critério de aceito | O leitor recebe insígnias ao bater conquistas, visualiza recomendações alinhadas ao seu perfil e recebe alertas/notificações de aprovações e novos ciclos. |
| Critério de rejeitado | Recomendações desconexas com o perfil, não concessão de insígnias devidas ou falha no envio de notificações. |
| Responsável pela execução (Quem) | Letícia (líder de Qualidade) |
| Auditoria (Quem) | Letícia (líder de Qualidade) |
| Ambiente de execução (Onde) | Local (`python manage.py test books.tests.CT06_BookRecommendation rewards notifications`) e branch `sprint6` |
| Registro dos resultados (Onde) | `docs/sprints/sprint6.md` e *issues* do GitHub para os defeitos |
| Testes automatizados | `books/tests.py`: `CT06_BookRecommendation` (4); `rewards/tests.py`: `CT01` (3); `notifications/tests.py`: `Notification_Task_Tests` (4) e `NotificationProfileAndHistoryTests` (11), total de 22 métodos |
| Tempo de execução medido | 26 s (22 de 22 aprovados) |
| Esforço estimado (Quanto) | 1,5 h |

### CT07

**Gestão Administrativa e Inicialização via Seed**

| Item | Descrição |
| ---- | --------- |
| Requisitos associados | R02, R03 (Sprint 1 / Gestão Geral) |
| Objetivo do teste | Validar a criação automática do perfil Administrador via seed/migration no banco zerado e testar os privilégios de editar, mesclar duplicados ou bloquear usuários. |
| Nível do teste | Integração (requisições simuladas com `django.test.Client`, sem interface) |
| Tipo de teste | Funcional e Não Funcional |
| Precondições | Banco de testes criado pelo `TestCase` do Django, com as migrations aplicadas (incluindo a seed do admin). |
| Critério de aceito | O admin realiza login com as credenciais padrão do sistema e consegue executar ações restritas (editar, adicionar e remover usuários). |
| Critério de rejeitado | Falha na geração do admin via seed ou ausência de permissões administrativas nas rotas do painel (`/admin/`). |
| Responsável pela execução (Quem) | Letícia (líder de Qualidade) |
| Auditoria (Quem) | Letícia (líder de Qualidade) |
| Ambiente de execução (Onde) | Local (`python manage.py test accounts.tests.CT07`) e branch `sprint1` |
| Registro dos resultados (Onde) | `docs/sprints/sprint1.md` e *issues* do GitHub para os defeitos |
| Testes automatizados | `accounts/tests.py`: `CT07` (11 métodos) |
| Tempo de execução medido | 9 s (11 de 11 aprovados) |
| Esforço estimado (Quanto) | 1 h |

