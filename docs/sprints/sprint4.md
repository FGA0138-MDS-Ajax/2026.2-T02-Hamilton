# Sprint 4 - Metas de leitura e fóruns

## 1. Dados

| Título   | Valor                                       |
| -------- | ------------------------------------------- |
| Sprint   | 4                                           |
| Objetivo | Crud Metas, Fórum da comunidade e das metas |
| Período  | 29/10/2026 a 04/11/2026                     |

## 2. Planejamentos e resultados

A Sprint 4 foi dedicada à implementação dos recursos de registro de metas, os fórums de cada meta e de comunidade e a moderação dos fóruns. Houve um debito técnico com a parte de integração do fórum principal da comunidade, e uma refatoração nos campos de entrada para criar uma meta, e o debito tecnico da sprint 3 que era a implementação de entrar em uma comunidade privada via um codigo e confirmação. E uma mudança que adicionou o atributo descrição a meta.

## 3. Requisitos Implementados

O valor esperado de conclusão de cada requisito é de **70%**.

| Requisito | Nome                               | Taxa de Conclusão |
| --------- | ---------------------------------- | ----------------- |
| R11       | Criar meta de leitura              | 75%               |
| R12       | Manter fórum                       | 90%               |
| R13       | Visualizar metas ativas/encerradas | 70%               |
| R14       | Moderar fórum                      | 100%              |
| Média     |                                    | 83,75%            |

## 4. Avaliação da qualidade do Software

| Funcionalidade             | Densidade de Defeitos | Valor máximo de defeitos esperado |
| -------------------------- | --------------------- | --------------------------------- |
| Criação de meta de leitura | 0,1111111111111111    | 0,2                               |
| Fórum da comunidade        | 0                     | 0,2                               |
| Moderação de fórum         | 0                     | 0,2                               |

## 5. Cobertura dos testes

Foram testados **4 dos 4 requisitos planejados**, resultando em uma porcentagem de **100%** dos requisitos testados com um valor mínimo de 100%.

## 6. Entregas

### Feature: Criação de metas de leitura

- **O que foi feito:** Implementação dos modelos `Goal` e `GoalParticipation`, formulários e serviços para criação, edição, adesão e saída de metas de leitura individuais e coletivas com prazo opcional.
- **Arquivos/apps:** `goals/models.py`, `goals/forms.py`, `goals/services.py`, `goals/signals.py`, `goals/views.py`, `goals/urls.py`, `goals/templates/goals/goal_form.html`, `communities/templates/communities/meta_form.html`
- **Requisito:** R11

### Feature: Fórum geral e fórum por meta de leitura

- **O que foi feito:** Desenvolvimento dos modelos `Forum` e `Message` com geração automática de um fórum geral por comunidade e de um fórum específico para cada meta de leitura criada, além do envio de mensagens.
- **Arquivos/apps:** `forums/models.py`, `forums/forms.py`, `forums/services.py`, `forums/views.py`, `forums/urls.py`, `communities/templates/communities/forum.html`, `communities/static/communities/css/forum.css`, `communities/static/communities/js/forum.js`
- **Requisito:** R12

### Feature: Visualização de metas ativas e encerradas

- **O que foi feito:** Implementação da listagem e dos cartões de visualização de metas ativas e concluídas na comunidade, exibindo progresso, data limite e status do ciclo.
- **Arquivos/apps:** `goals/views.py`, `goals/templates/goals/goal_view.html`, `communities/templates/communities/_goal_card.html`, `communities/templates/communities/community_view.html`, `communities/static/communities/css/community_goals.css`
- **Requisito:** R13

### Feature: Moderação de fórum

- **O que foi feito:** Implementação das regras e views de moderação para edição de dados do fórum, validação de estado (ativo ou congelado) antes de postagens e exclusão de mensagens por moderadores.
- **Arquivos/apps:** `forums/services.py`, `forums/views.py`, `forums/forms.py`, `forums/templates/forums/edit_forum.html`, `forums/tests.py`
- **Requisito:** R14

