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

| Requisito | Nome                       | Taxa de Conclusão |
| --------- | -------------------------- | ----------------- |
| R15       | Registrar livro como lido  | 100%              |
| R16       | Registrar progresso diário | 100%              |
| R17       | Ofensivas                  | 100%              |
| R18       | Página de leitura          | 100%              |
| Média     |                            | 100%              |

## 4. Avaliação da qualidade do Software

| Funcionalidade        | Densidade de Defeitos | Valor máximo de defeitos esperado |
| --------------------- | --------------------- | --------------------------------- |
| Registro de progresso | 0                     | 0,2                               |
| Ofensiva pessoal      | 0                     | 0,2                               |

## 5. Cobertura dos testes

Foram testados **4 dos 4 requisitos planejados**, resultando em uma porcentagem de **100%** dos requisitos testados com um valor mínimo de 100%.

## 6. Entregas

### Feature: Registro de livro como lido e estante pessoal

- **O que foi feito:** Implementação do modelo `BookStatus` para gerenciar os livros da estante (*Quero Ler*, *Lendo* e *Lido*), com transição automática para *Lido* ao atingir 100% de progresso.
- **Arquivos/apps:** `books/models.py`, `books/services.py`, `books/views.py`, `books/urls.py`, `accounts/templates/accounts/_shelf_book_card.html`, `accounts/static/accounts/js/profile_shelf.js`
- **Requisito:** R15

### Feature: Registro de progresso diário e sessões de leitura

- **O que foi feito:** Desenvolvimento da persistência em banco de dados e endpoints JSON para sessões diárias de leitura (`ReadingSession`), registrando páginas lidas, percentual acumulado e tempo gasto com atualização em cascata nas metas.
- **Arquivos/apps:** `books/models.py`, `books/forms.py`, `books/services.py`, `books/views.py`, `goals/services.py`, `books/tests.py`
- **Requisito:** R16

### Feature: Ofensivas diárias (streaks) e lembretes agendados

- **O que foi feito:** Implementação do cálculo e validação de dias consecutivos de leitura (`streak` e `last_read_date` no `Profile`), páginas de calendário e histórico diário da ofensiva, além da rotina periódica com Celery e Redis para lembretes diários.
- **Arquivos/apps:** `accounts/models.py`, `accounts/views.py`, `accounts/templates/accounts/streak_calendar.html`, `accounts/templates/accounts/streak_day_history.html`, `accounts/static/accounts/css/streak.css`, `notifications/tasks.py`, `colecture/celery.py`
- **Requisito:** R17

### Feature: Página de sessão de leitura e abas da estante

- **O que foi feito:** Construção da página de registro de leitura com cronômetro e histórico de sessões, integrada às abas da estante virtual no perfil e aos atalhos de acesso na barra lateral.
- **Arquivos/apps:** `books/templates/books/reading_session.html`, `books/static/books/css/reading_session.css`, `books/static/books/js/reading_session.js`, `accounts/templates/accounts/profile.html`, `accounts/static/accounts/css/profile.css`
- **Requisito:** R18

### Feature: Convites para comunidades privadas e conclusão de débitos técnicos

- **O que foi feito:** Implementação do ingresso em comunidades privadas via código de convite (`Invitation`), adição do atributo descrição nas metas e integração final entre cards de metas e fóruns no front-end.
- **Arquivos/apps:** `communities/models.py`, `communities/services.py`, `communities/views.py`, `goals/models.py`, `goals/forms.py`, `forums/views.py`, `communities/templates/communities/community_view.html`
- **Requisito:** R09, R11, R12, R13
