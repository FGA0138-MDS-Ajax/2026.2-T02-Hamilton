# Sprint 3 - Manter comunidades

## 1. Dados

| Título   | Valor                                             |
| -------- | ------------------------------------------------- |
| Sprint   | 3                                                 |
| Objetivo | Permitir a criação e gerenciamento de comunidades |
| Período  | 22/10/2026 a 28/10/2026                           |

## 2. Planejamentos e resultados
A Sprint 3 foi dedicada à implementação do ciclo de vida das comunidades (R09 e R10), contemplando seu CRUD completo, além de avançar na correção do menu de ações de livros pendente da Sprint 2. Foram entregues:

- Criação, edição, exclusão e arquivamento de comunidades (com expurgo após 60 dias);
- Lista de comunidades das quais o usuário participa, busca de comunidades públicas e barra lateral de navegação (`sidebar`);
- Regras de back-end para ingresso, saída, aprovação/rejeição de solicitações, promoção/rebaixamento de moderadores e banimento;
- Menu kebab (três pontinhos) com atalho para edição na página de detalhes do livro.

Débitos técnicos gerados na Sprint 3 (R09 – 80%):

- Conectar a página do moderador (`moderator.html`) à página de comunidade e integrar na interface as ações de aceitar/rejeitar solicitações de entrada, promover/rebaixar cargos e expulsar/banir membros — resolvido na Sprint 4 e refinado na Sprint 5;
- Implementar o código de convite e solicitação de entrada nas comunidades privadas — resolvido na Sprint 5.

## 3. Requisitos Implementados

O valor esperado de conclusão de cada requisito é de **70%**.

| Requisito | Nome                                                                 | Taxa de Conclusão |
| --------- | -------------------------------------------------------------------- | ----------------- |
| R08       | Página de registro de livros e avaliação (Débito Técnico – Sprint 2) | 98%               |
| R09       | Manter comunidade                                                    | 80%               |
| R10       | Página de comunidade                                                 | 90%               |
| Média     | -                                                                    | 89,33%            |

## 4. Avaliação da qualidade do Software

| Funcionalidade              | Densidade de Defeitos | Valor máximo de defeitos esperado |
| --------------------------- | --------------------- | --------------------------------- |
| Criação de comunidade       | 0,0                   | 0,2                               |
| Gerenciamento da comunidade | 0,0                   | 0,2                               |

## 5. Cobertura dos testes

Foram testados **2 dos 2 requisitos planejados**, resultando em uma porcentagem de **100%** dos requisitos testados com um valor mínimo de 100%.

## 6. Entregas

**Feature: CRUD de comunidades**

- **O que foi feito:** Implementação do CRUD de comunidades públicas e privadas (`Community` e `Membership`) e das regras de back-end para ingresso, saída, aprovação/rejeição de solicitações, edição de cargos, banimento e expurgo após 60 dias de arquivamento.
- **Arquivos/apps:** `communities/models.py`, `communities/forms.py`, `communities/views.py`, `communities/management/...`, `communities/tests.py`
- **Requisito:** R09

**Feature: Páginas de comunidade e sidebar**

- **O que foi feito:** Desenvolvimento das interfaces de listagem e busca de comunidades, criação e edição de clubes, página principal da comunidade (`community_view.html`), estrutura visual inicial da tela do moderador (`moderator.html`) e barra lateral de navegação (`sidebar.html`).
- **Arquivos/apps:** `communities/templates/...`, `communities/static/...`, `main/templates/sidebar.html`
- **Requisito:** R10

**Feature: Menu de opções do livro**

- **O que foi feito:** Resolve parcialmente o débito técnico da Sprint 2 com a adição do menu kebab (três pontinhos) e atalho para a rota de edição na página de detalhes do livro, além da organização do formulário de cadastro em colunas responsivas com seletor de gêneros.
- **Arquivos/apps:** `books/templates/book_detail.html`, `books/templates/book_form.html`, `books/forms.py`, `books/static/...`
- **Requisito:** R05, R08

## 7. Débito Técnico

**Feature: Integração do painel do moderador**

- **O que foi feito:** O template `moderator.html` foi criado apenas como estrutura estática, ficando pendente conectá-lo à rota `<int:community_id>/manage/` na página da comunidade e integrar na interface a listagem real de membros, aprovação/rejeição de solicitações e gestão de cargos e banimentos.
- **Arquivos/apps:** `communities/views.py`, `communities/urls.py`, `communities/templates/community_view.html`, `communities/templates/moderator.html`
- **Requisito:** R09, R10

**Feature: Convite para comunidades privadas**

- **O que foi feito:** Ficou pendente implementar a geração e validação do código de convite para comunidades privadas e integrar o modal de solicitação de entrada por código na página inicial de comunidades.
- **Arquivos/apps:** `communities/models.py`, `communities/services.py`, `communities/views.py`, `communities/templates/home_community.html`
- **Requisito:** R09

