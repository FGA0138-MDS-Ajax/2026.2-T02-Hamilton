# Sprint 5 - Acompanhamento de progresso e ofensivas

## 1. Dados

| Título   | Valor                   |
| -------- | ----------------------- |
| Sprint   | 5                       |
| Objetivo | Acompanhamento de progresso e ofensivas (R15 a R18) |
| Período  | 05/11/2026 a 11/11/2026 |

## 2. Planejamentos e resultados

A Sprint 5 foi dedicada às funcionalidades de acompanhamento de progresso e ofensivas (R15 a R18: registrar livro como lido, registrar progresso diário, ofensivas e página de leitura). Conforme a Ata de Reunião 07 (11/11/2026), todas as features previstas foram entregues, todos os débitos técnicos de sprints anteriores foram implementados e os testes passaram sem erros.

## 3. Requisitos Implementados

O valor esperado de conclusão de cada requisito é de **70%**.

| Requisito | Nome                                                                 | Taxa de Conclusão |
| --------- | -------------------------------------------------------------------- | ----------------- |
| R08       | Página de registro de livros e avaliação (Débito Técnico – Sprint 2) | 100%              |
| R09       | Manter comunidade (Débito Técnico – Sprint 3)                        | 100%              |
| R11       | Criar meta de leitura (Débito Técnico – Sprint 4)                    | 100%              |
| R12       | Manter fórum (Débito Técnico – Sprint 4)                             | 100%              |
| R13       | Visualizar metas ativas/encerradas (Débito Técnico – Sprint 4)       | 100%              |
| R15       | Registrar livro como lido                                            | 100%              |
| R16       | Registrar progresso diário                                           | 100%              |
| R17       | Ofensivas                                                            | 100%              |
| R18       | Página de leitura                                                    | 100%              |
| Média     | -                                                                    | 100%              |

## 4. Avaliação da qualidade do Software

| Funcionalidade        | Densidade de Defeitos | Valor máximo de defeitos esperado |
| --------------------- | --------------------- | --------------------------------- |
| Registro de progresso | 0,0183486             | 0,2                               |
| Ofensiva pessoal      | 0,028                 | 0,2                               |

Usamos os seguintes testes para os cálculos (executados na pasta `colecture/`):

Registro de progresso:

```bash
python manage.py test books.tests.ReadingSessionModelTests books.tests.ReadingSessionFormTests books.tests.ReadingSessionViewTests books.tests.ReadingSessionStreakViewTests books.tests.ReadingSessionProgressAndGoalTests books.tests.SaveReadingSessionViewTests books.tests.ReadingSessionDataModelTests books.tests.SessionApiBase books.tests.CreateReadingSessionApiTests books.tests.ListReadingSessionsApiTests books.tests.EditReadingSessionApiTests books.tests.RegisterReadingSessionSharedHelperTests books.tests.BookshelfDatabaseSourceTests books.tests.ReadingSessionScriptTests accounts.tests.CTEstantePerfil
```

Ofensiva pessoal:

```bash
python manage.py test accounts.tests.ProfileViewStreakResetTests
```

## 5. Cobertura dos testes

Foram testados **4 dos 4 requisitos planejados** (além da validação dos **5 requisitos de débito técnico** concluídos), resultando em uma porcentagem de **100%** dos requisitos testados com um valor mínimo de 100%.

**Critério de cobertura:** um requisito é considerado testado quando está associado a um caso de teste do [roteiro de testes](../visao/testes.md#roteiro-de-testes) cujos testes foram executados e aprovados (resultado previsto igual ao realizado). A cobertura é calculada pela métrica [M3](../visao/metricas.md) (requisitos testados ÷ requisitos implementados).

| Requisito | Caso de teste |
| --------- | ------------- |
| R08 (débito técnico – Sprint 2) | [CT02](../visao/testes.md#ct02) |
| R09 (débito técnico – Sprint 3) | [CT03](../visao/testes.md#ct03) |
| R11 (débito técnico – Sprint 4) | [CT04](../visao/testes.md#ct04) |
| R12 (débito técnico – Sprint 4) | [CT04](../visao/testes.md#ct04) |
| R13 (débito técnico – Sprint 4) | [CT04](../visao/testes.md#ct04) |
| R15       | [CT05](../visao/testes.md#ct05) |
| R16       | [CT05](../visao/testes.md#ct05) |
| R17       | [CT05](../visao/testes.md#ct05) |
| R18       | [CT05](../visao/testes.md#ct05) |

## 6. Entregas

**Feature: Estante pessoal e livro lido**

- **O que foi feito:** Implementação do modelo `BookStatus` no banco de dados (substituindo o armazenamento provisório em `localStorage`) para gerenciar os livros da estante (*Quero Ler*, *Lendo* e *Lido*), com integração às tags do perfil e transição automática para *Lido* ao atingir 100% de progresso.
- **Arquivos/apps:** `books/models.py`, `books/services.py`, `books/views.py`, `accounts/templates/...`, `accounts/static/...`
- **Requisito:** R15

**Feature: Sessões e progresso diário**

- **O que foi feito:** Consolidação do modelo `ReadingSession` e `RecordType` no app `books` com persistência em banco de dados e endpoints JSON para criar, listar e editar sessões diárias de leitura, atualizando em cascata o progresso nas metas, a estante e a ofensiva.
- **Arquivos/apps:** `books/models.py`, `books/forms.py`, `books/services.py`, `books/views.py`, `goals/services.py`
- **Requisito:** R16

**Feature: Ofensivas diárias e lembretes**

- **O que foi feito:** Implementação do cálculo, validação e reset automático de dias consecutivos de leitura (`streak` e `last_read_date` no `Profile`), páginas de calendário e histórico diário da ofensiva, além da rotina periódica com Celery e Redis para envio de lembretes diários.
- **Arquivos/apps:** `accounts/models.py`, `accounts/views.py`, `accounts/templates/...`, `notifications/tasks.py`, `colecture/celery.py`
- **Requisito:** R17

**Feature: Página de sessão de leitura**

- **O que foi feito:** Construção da página de registro de leitura com cronômetro e modal de histórico e edição de sessões, integrada às abas da estante virtual no perfil e aos atalhos de acesso.
- **Arquivos/apps:** `books/templates/reading_session.html`, `books/static/...`, `accounts/templates/profile.html`
- **Requisito:** R18

**Feature: Interface de edição de livros**

- **O que foi feito:** Resolve o débito técnico da Sprint 2 ao adaptar o template `book_form.html` para reutilização no fluxo de edição com título (`Editar Livro`), descrição e botão (`Atualizar`) dinâmicos, além de corrigir o redirecionamento em `edit_book` para retornar à página de detalhes da obra (`book_detail`).
- **Arquivos/apps:** `books/views.py`, `books/templates/book_form.html`
- **Requisito:** R05, R08

**Feature: Convites para comunidades privadas**

- **O que foi feito:** Resolve o débito técnico da Sprint 3 com a implementação do modelo `Invitation` e do código fixo de 8 caracteres (`Community.code`) exibido para cópia na comunidade privada e validado no modal da home (`JoinByCodeView`), além de confirmação ao promover/rebaixar moderadores, desarquivamento de comunidades e tela de bloqueio para banidos.
- **Arquivos/apps:** `communities/models.py`, `communities/services.py`, `communities/views.py`, `communities/urls.py`, `communities/templates/...`, `communities/static/...`, `communities/tests.py`
- **Requisito:** R09, R10

**Feature: Refatoração do formulário de metas**

- **O que foi feito:** Resolve o débito técnico da Sprint 4 com a adição do campo opcional `description` ao modelo `Goal` e ao `GoalForm`, tradução dos rótulos para português, atribuição automática do livro da comunidade às metas coletivas, layout em duas colunas com cards de tipo, limite de páginas pelo tamanho do livro e inscrição automática de membros.
- **Arquivos/apps:** `goals/models.py`, `goals/forms.py`, `goals/services.py`, `goals/views.py`, `goals/templates/...`, `communities/static/...`, `goals/tests.py`
- **Requisito:** R11, R13

**Feature: Integração dos fóruns e cards de metas**

- **O que foi feito:** Resolve o débito técnico da Sprint 4 ao unificar as views de `forums` com o template `communities/forum.html`, criar migração para gerar fóruns ausentes, corrigir a listagem e o botão *Editar* nos cards de metas da comunidade (`_goal_card.html`), redirecionar os cards para o fórum da meta e adicionar o pop-up de edição do fórum para moderadores.
- **Arquivos/apps:** `forums/views.py`, `forums/services.py`, `forums/migrations/...`, `communities/templates/forum.html`, `communities/templates/_goal_card.html`, `communities/static/...`, `forums/tests.py`
- **Requisito:** R11, R12, R13, R14

## 7. Análise dos resultados

Comparação dos valores registrados neste relatório com as metas do [plano GQM](../visao/metricas.md):

| Métrica | Meta | Resultado | Situação |
| ------- | ---- | --------- | -------- |
| M1 – Taxa de conclusão | No mínimo 70% | 100% (requisitos planejados e débitos técnicos) | Atingida |
| M2 – Densidade de defeitos | No máximo 0,2 | 0,0183486 (Registro de progresso); 0,028 (Ofensiva pessoal) | Atingida |
| M3 – Cobertura de requisitos | 100% | 100% (4 de 4 planejados e 5 de débito técnico) | Atingida |

Nenhum [critério de replanejamento](../visao/projeto.md#criterios-de-replanejamento) foi acionado.

**Decisões e encaminhamentos** (Ata 7, 11/11/2026):

- Todas as features da sprint e todos os débitos técnicos das sprints anteriores foram entregues, e os testes passaram sem erros.
- Além de R19 a R22, a Sprint 6 passou a contemplar: corrigir a cor da sidebar na aba de comunidades, corrigir a resposta às mensagens do fórum, criar o pop-up de notificações com sino e exibir o botão de concluir meta só quando os requisitos da meta forem atingidos.
- As insígnias do sistema foram definidas na própria reunião.
