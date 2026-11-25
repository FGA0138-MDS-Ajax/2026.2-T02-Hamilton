# Sprint 6 - Conquistas, recomendações e testes

## 1. Dados

| Título   | Valor                   |
| -------- | ----------------------- |
| Sprint   | 6                       |
| Objetivo | Implementação de insígnias, Notificações e Recomendações. (R19-R22)         |
| Período  | 12/11/2026 a 18/11/2026 |

## 2. Planejamentos e resultados

Era planejado implementar insígnias (COULD) para quando usuários realizarem certas conquistas em ofensivas; recomendações por temas de livros já lidos (MUST), para que usuários possam encontrar mais livros de interesse; notificações de aviso para retomada de ofensiva(SHOULD), para encorajar o retorno a leitura. A função de documentação e testes foi transferida para a sprint 7.

## 3. Requisitos Implementados

O valor esperado de conclusão de cada requisito é de **70%**.

| Requisito | Nome                   | Taxa de Conclusão |
| --------- | ---------------------- | ----------------- |
| R19       | Insígnias              | 100%     |
| R20       | Recomendações por tema | 100%     |
| R21       | Notificações e logs    | 100%     |
| R22       | Teste e documentação   | 0%     |
| Média     |                        | 100%     |

## 4. Avaliação da qualidade do Software

| Funcionalidade         | Densidade de Defeitos | Valor máximo de defeitos esperado |
| ---------------------- | --------------------- | --------------------------------- |
| Insígnias              | 100%         | 100%                     |
| Recomendação por temas | 100%         | 100%                     |
| Notificações           | 100%         | 100%                     |

## 5. Cobertura dos testes

Foram testados **3 dos 4 requisitos planejados**, resultando em uma porcentagem de **100%** dos requisitos testados com um valor mínimo de 100%.

## 6. Entregas

### Feature: Sistema de insígnias e conquistas

- **O que foi feito:** Implementação dos modelos `Insignia` e `Award` com 35 conquistas cadastradas via migração/seed em 8 categorias, concessão automática por gatilhos de atividade e página de galeria com medalhas em SVG.
- **Arquivos/apps:** `rewards/models.py`, `rewards/services.py`, `rewards/selectors.py`, `rewards/views.py`, `rewards/urls.py`, `rewards/management/commands/seed_insignias.py`, `rewards/templates/rewards/insignias.html`, `rewards/static/rewards/css/insignias.css`, `rewards/tests.py`
- **Requisito:** R19

### Feature: Recomendação de livros por tema

- **O que foi feito:** Desenvolvimento do serviço de recomendação (`get_recommended_books`) que pontua livros a partir dos gêneros lidos, tempo de leitura, status na estante e avaliações, exibindo a seção de recomendados na página de busca.
- **Arquivos/apps:** `books/services.py`, `books/views.py`, `books/tests.py`, `main/views.py`, `main/templates/main/search.html`, `main/static/main/css/search.css`
- **Requisito:** R20

### Feature: Centro de notificações e logs de auditoria

- **O que foi feito:** Implementação do dropdown de notificações no sino da barra lateral, página de histórico de alertas e módulo administrativo de logs (`AuditLog`) para registro automático, filtragem e consulta de ações críticas.
- **Arquivos/apps:** `notifications/models.py`, `notifications/services.py`, `notifications/views.py`, `notifications/templates/notifications/history.html`, `logs/models.py`, `logs/services.py`, `logs/views.py`, `logs/forms.py`, `logs/templates/logs/log_list.html`, `logs/templates/logs/log_detail.html`, `logs/tests.py`
- **Requisito:** R21

### Feature: Resposta a mensagens no fórum

- **O que foi feito:** Adição do relacionamento `reply_to` no modelo `Message`, formulário e integração visual no front-end para permitir responder diretamente a mensagens específicas dentro dos fóruns.
- **Arquivos/apps:** `forums/models.py`, `forums/forms.py`, `forums/views.py`, `forums/tests.py`, `communities/templates/communities/forum.html`, `communities/static/communities/js/forum.js`
- **Requisito:** R12, R14

### Feature: Testes unitários e reestruturação da documentação do repositório

- **O que foi feito:** Adição de suítes de testes para insígnias, recomendações, logs e respostas no fórum, além da divisão da documentação técnica do código entre `README.md` e `DETALHES.md`.
- **Arquivos/apps:** `README.md`, `DETALHES.md`, `rewards/tests.py`, `books/tests.py`, `logs/tests.py`, `forums/tests.py`
- **Requisito:** R22

