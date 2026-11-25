# Sprint 4 - Metas de leitura e fóruns

## 1. Dados

| Título   | Valor                                       |
| -------- | ------------------------------------------- |
| Sprint   | 4                                           |
| Objetivo | Crud Metas, Fórum da comunidade e das metas |
| Período  | 29/10/2026 a 04/11/2026                     |

## 2. Planejamentos e resultados

A Sprint 4 foi dedicada à implementação das metas de leitura, dos fóruns gerais e por ciclo de meta e das ferramentas de moderação (R11 a R14), além de quitar o débito técnico da Sprint 3 referente à conexão da página do moderador com a página da comunidade.

Conforme registrado na Ata de Reunião 06 (04/11/2026), permaneceram como débitos técnicos para a Sprint 5:

1. Implementar a entrada em comunidade privada por código de convite e substituir o código provisório exibido na caixa de cópia da comunidade (R09 – débito remanescente da Sprint 3);
2. Integrar o card do Fórum Geral e as views do app `forums` ao template definitivo `communities/forum.html` no front-end (R12 – 90%);
3. Corrigir a exibição das metas coletivas na página da comunidade e conectar os cards de metas ativas/encerradas aos respectivos fóruns e à rota de edição (R11, R12, R13 – 70%);
4. Refatorar o formulário de criar/editar meta: atribuir automaticamente o livro da comunidade sem campo de seleção manual, traduzir rótulos para português, dispor os tipos de meta em cards lado a lado e validar o limite de páginas (R11 – 75%);
5. Adicionar o atributo opcional `description` (descrição) ao modelo `Goal` e ao `GoalForm` (R11 – 75%).

## 3. Requisitos Implementados

O valor esperado de conclusão de cada requisito é de **70%**.

| Requisito | Nome                                               | Taxa de Conclusão |
| --------- | -------------------------------------------------- | ----------------- |
| R09       | Manter comunidade (Débito Técnico – Sprint 3)      | 90%               |
| R10       | Página de comunidade (Débito Técnico – Sprint 3)   | 100%              |
| R11       | Criar meta de leitura                              | 75%               |
| R12       | Manter fórum                                       | 90%               |
| R13       | Visualizar metas ativas/encerradas                 | 70%               |
| R14       | Moderar fórum                                      | 100%              |
| Média     | -                                                  | 87,5%             |

## 4. Avaliação da qualidade do Software

| Funcionalidade             | Densidade de Defeitos | Valor máximo de defeitos esperado |
| -------------------------- | --------------------- | --------------------------------- |
| Criação de meta de leitura | 0,1111111111111111    | 0,2                               |
| Fórum da comunidade        | 0                     | 0,2                               |
| Moderação de fórum         | 0                     | 0,2                               |

## 5. Cobertura dos testes

Foram testados **4 dos 4 requisitos planejados**, resultando em uma porcentagem de **100%** dos requisitos testados com um valor mínimo de 100%.

## 6. Entregas

**Feature: Criação e edição de metas**

- **O que foi feito:** Implementação dos modelos `Goal` e `GoalParticipation`, serviços e template `goal_form.html` com aviso quando a comunidade não possui livro definido, validação de data futura, toasts e modo de edição.
- **Arquivos/apps:** `goals/models.py`, `goals/forms.py`, `goals/services.py`, `goals/signals.py`, `goals/views.py`, `goals/templates/...`
- **Requisito:** R11

**Feature: Fóruns geral e de metas**

- **O que foi feito:** Desenvolvimento dos modelos `Forum` e `Message` com relacionamento `OneToOneField`, geração automática de um fórum geral por comunidade e de um fórum por meta criada, além do envio de mensagens.
- **Arquivos/apps:** `forums/models.py`, `forums/forms.py`, `forums/services.py`, `forums/views.py`, `communities/templates/forum.html`
- **Requisito:** R12

**Feature: Visualização de metas**

- **O que foi feito:** Implementação das abas *Ativas* e *Encerradas*, dos cards com barra de progresso, dias restantes, contador de conclusões, truncamento de textos longos e botão de concluir meta.
- **Arquivos/apps:** `goals/views.py`, `goals/services.py`, `communities/views.py`, `communities/templates/...`, `communities/static/...`
- **Requisito:** R13

**Feature: Moderação de fórum**

- **O que foi feito:** Implementação das regras e views de moderação para edição de dados do fórum, validação de estado (ativo ou trancado) antes de postagens e exclusão de mensagens por moderadores.
- **Arquivos/apps:** `forums/services.py`, `forums/views.py`, `forums/forms.py`, `forums/templates/...`, `forums/tests.py`
- **Requisito:** R14

**Feature: Integração do painel do moderador**

- **O que foi feito:** Resolve o débito técnico da Sprint 3 ao conectar a página da comunidade à rota `<int:community_id>/manage/` e integrar `moderator.html` ao `MembershipService`, permitindo listar membros ativos, aceitar/rejeitar solicitações de entrada, promover/rebaixar moderadores e banir membros.
- **Arquivos/apps:** `communities/views.py`, `communities/urls.py`, `communities/services.py`, `communities/templates/moderator.html`, `communities/static/...`
- **Requisito:** R09, R10

## 7. Débito Técnico

**Feature: Refatoração do formulário de metas**

- **O que foi feito:** Ficou pendente adicionar o atributo opcional `description` ao modelo `Goal` e ao `GoalForm`, traduzir os rótulos de entrada para português, atribuir automaticamente o livro vinculado à comunidade nas metas coletivas e organizar os tipos de meta em cards com validação do limite de páginas.
- **Arquivos/apps:** `goals/models.py`, `goals/forms.py`, `goals/services.py`, `goals/templates/goal_form.html`, `communities/static/...`
- **Requisito:** R11

**Feature: Integração dos fóruns e cards de metas**

- **O que foi feito:** Ficou pendente unificar as views do app `forums` com o template estilizado `communities/forum.html`, corrigir a listagem das metas coletivas na página da comunidade e conectar os cards de metas (`_goal_card.html`) ao fórum de cada meta e à rota de edição.
- **Arquivos/apps:** `forums/views.py`, `forums/services.py`, `communities/templates/forum.html`, `communities/templates/_goal_card.html`, `communities/templates/community_view.html`
- **Requisito:** R11, R12, R13

**Feature: Convite para comunidades privadas**

- **O que foi feito:** Permaneceu pendente da Sprint 3 a geração do código fixo de convite das comunidades privadas e a implementação da rota de solicitação de entrada via código no modal da página de comunidades.
- **Arquivos/apps:** `communities/models.py`, `communities/services.py`, `communities/views.py`, `communities/templates/community_view.html`, `communities/templates/home_community.html`
- **Requisito:** R09

