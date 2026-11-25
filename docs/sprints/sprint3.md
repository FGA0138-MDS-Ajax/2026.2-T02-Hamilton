# Sprint 3 - Manter comunidades

## 1. Dados

| Título   | Valor                                             |
| -------- | ------------------------------------------------- |
| Sprint   | 3                                                 |
| Objetivo | Permitir a criação e gerenciamento de comunidades |
| Período  | 22/10/2026 a 28/10/2026                           |

## 2. Planejamentos e resultados
A sprint 3 foi dedicada à implementação do ciclo de vida das comunidades, contemplando seu CRUD completo. Foram entregues:

- Lista de comunidades nas quais o usuário participa; e
- Recursos de edição, saída e arquivamento de comunidades;

Tarefas pendentes:

- Conectar a página do moderador à página de comunidade;
- Implementação de código de solicitação de entrada nas comunidades privadas.

## 3. Requisitos Implementados

O valor esperado de conclusão de cada requisito é de **70%**.

| Requisito | Nome                 | Taxa de Conclusão |
| --------- | -------------------- | ----------------- |
| R09       | Manter comunidade    | 80%               |
| R10       | Página de comunidade | 100%              |
| Média     |                      | 90%               |

## 4. Avaliação da qualidade do Software

| Funcionalidade              | Densidade de Defeitos | Valor máximo de defeitos esperado |
| --------------------------- | --------------------- | --------------------------------- |
| Criação de comunidade       | 0,0                   | 0,2                               |
| Gerenciamento da comunidade | 0,0                   | 0,2                               |

## 5. Cobertura dos testes

Foram testados **2 dos 2 requisitos planejados**, resultando em uma porcentagem de **100%** dos requisitos testados com um valor mínimo de 100%.

## 6. Entregas

### Feature: Criação e gerenciamento de comunidades

- **O que foi feito:** Implementação do CRUD de comunidades públicas e privadas (`Community` e `Membership`), incluindo ingresso e saída de membros, aprovação de solicitações, promoção/rebaixamento de moderadores e arquivamento com comando de expurgo após 60 dias.
- **Arquivos/apps:** `communities/models.py`, `communities/forms.py`, `communities/views.py`, `communities/urls.py`, `communities/admin.py`, `communities/management/commands/purge_archived_communities.py`, `communities/tests.py`
- **Requisito:** R09

### Feature: Páginas de comunidade e navegação lateral

- **O que foi feito:** Desenvolvimento das interfaces de listagem e busca de comunidades, criação e edição de clubes, página principal da comunidade, tela do moderador e barra lateral de navegação (`sidebar`).
- **Arquivos/apps:** `communities/templates/communities/home_community.html`, `communities/templates/communities/community_view.html`, `communities/templates/communities/create_community.html`, `communities/templates/communities/edit_community.html`, `communities/templates/communities/moderator.html`, `communities/static/communities/css/community_view.css`, `communities/static/communities/js/community_view.js`, `main/templates/sidebar.html`
- **Requisito:** R10

