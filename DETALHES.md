<div align="center">

[![Visão Geral](https://img.shields.io/badge/Aba-Visão_Geral-lightgrey?style=plastic)](README.md)
[![Documentação Detalhada](https://img.shields.io/badge/Aba-Documentação_Detalhada-blue?style=plastic)](DETALHES.md)

</div>

<div align="center">

[![GitHub Pages](https://img.shields.io/badge/Documentação-GitHub_Pages-blue?style=plastic&logo=github)](https://fga0138-mds-ajax.github.io/2026.2-T02-Hamilton/)
[![Repositório](https://img.shields.io/badge/GitHub-Repositório-181717?style=plastic&logo=github)](https://github.com/FGA0138-MDS-Ajax/2026.2-T02-Hamilton)

</div>
---

# Documentação Técnica e Detalhes do Projeto - CoLecture

> Esta página complementa a [Visão Geral (README.md)](README.md), reunindo o detalhamento técnico aprofundado, catálogo de rotas, arquitetura interna de cada app, infraestrutura assíncrona, gamificação e convenções de engenharia de software da equipe.

---

## Sumário

1. [Estrutura Completa de Pastas](#1-estrutura-completa-de-pastas)
2. [Catálogo Completo de Rotas da Aplicação](#2-catálogo-completo-de-rotas-da-aplicação)
   - [Páginas Gerais (`main`)](#páginas-gerais-main)
   - [Contas e Perfil (`/user/`)](#contas-e-perfil-user)
   - [Notificações (`/notifications/`)](#notificações-notifications)
   - [Livros e Leitura (`/books/`)](#livros-e-leitura-books)
   - [Comunidades (`/communities/`)](#comunidades-communities)
   - [Metas (`/goals/`)](#metas-goals)
   - [Fóruns (`/forums/`)](#fóruns-forums)
   - [Insígnias (`/rewards/`)](#insígnias-rewards)
   - [Auditoria e Logs (`/logs/`)](#auditoria-e-logs-logs)
3. [Aprofundamento: Celery, Redis e Tarefas Periódicas](#3-aprofundamento-celery-redis-e-tarefas-periódicas)
   - [Fluxo de Execução da Notificação Diária](#fluxo-de-execução-da-notificação-diária)
   - [Instalação Avançada do Redis por Plataforma](#instalação-avançada-do-redis-por-plataforma)
   - [Por que o Windows exige a flag `-P solo`?](#por-que-o-windows-exige-a-flag--p-solo)
   - [Como testar tarefas do Celery manualmente (Django Shell)](#como-testar-tarefas-do-celery-manualmente-django-shell)
   - [Configurações no Código (`settings.py` e `celery.py`)](#configurações-no-código)
4. [Sistema de Notificações](#4-sistema-de-notificações)
5. [Scripts de Seed e Manutenção (`management/commands`)](#5-scripts-de-seed-e-manutenção)
6. [Sistema de Insígnias e Gamificação (R19)](#6-sistema-de-insígnias-e-gamificação-r19)
7. [Logs de Auditoria](#7-logs-de-auditoria)
8. [Catálogo de Livros e Algoritmo de Recomendação](#8-catálogo-de-livros-e-algoritmo-de-recomendação)
9. [Padrões Arquiteturais e de Código](#9-padrões-arquiteturais-e-de-código)
10. [Políticas de Branches e Conventional Commits](#10-políticas-de-branches-e-conventional-commits)
11. [Histórico de Sprints e Documentação Externa](#11-histórico-de-sprints-e-documentação-externa)

---

## 1. Estrutura Completa de Pastas

A aplicação segue a divisão modular do Django, onde cada módulo possui responsabilidades isoladas com seus próprios models, views, templates, testes e regras de negócio:

```text
2026.2-T02-Hamilton/
├── README.md                          # Visão geral, quickstart e guia rápido
├── DETALHES.md                        # Detalhamento técnico, rotas, Celery e regras de negócio
├── requirements.txt                   # Dependências do projeto (Django, Celery, Redis, etc.)
├── .gitignore
└── colecture/                         # Diretório raiz do projeto Django
    ├── manage.py                      # Utilitário de comandos CLI do Django
    ├── colecture/                     # Configuração global da aplicação
    │   ├── __init__.py                # Exportação da instância do Celery app
    │   ├── settings.py                # Configurações do Django, banco, Celery Beat e rotas
    │   ├── urls.py                    # Roteador central (URLconf)
    │   ├── celery.py                  # Inicialização da aplicação Celery
    │   ├── asgi.py
    │   └── wsgi.py
    ├── media/                         # Armazenamento de arquivos enviados (capas e fotos)
    ├── main/                          # Vitrine inicial, busca global e layout compartilhado
    │   ├── views.py                   # index, search
    │   ├── urls.py
    │   ├── templates/main/            # sidebar.html, index.html, search.html
    │   └── static/main/               # CSS global (variables.css, sidebar.css), JS e logos
    ├── accounts/                      # Gestão de usuários, perfil, autenticação e ofensiva
    │   ├── models.py                  # Profile (streak, last_read_date, bio, foto)
    │   ├── services.py                # Criação e manutenção do perfil do leitor
    │   ├── forms.py                   # Formulários de autenticação e edição
    │   ├── views.py                   # Login, cadastro, perfil e calendário da ofensiva
    │   ├── urls.py
    │   ├── tests.py
    │   └── templates/accounts/
    ├── books/                         # Catálogo de livros, estante e sessões de leitura
    │   ├── models.py                  # Book, BookReview, BookStatus, ReadingSession
    │   ├── services.py                # Recomendações (scores), progresso e sessões de leitura
    │   ├── forms.py                   # Formulários de livros e sessões
    │   ├── views.py                   # Estante, cronômetro, cadastro e busca de livros
    │   ├── urls.py
    │   ├── tests.py
    │   ├── management/commands/       # seed_books.py e seed_demo.py
    │   └── templates/books/
    ├── communities/                   # Clubes de leitura, membros e moderação
    │   ├── models.py                  # Community, Membership, Invitation
    │   ├── services.py                # MembershipService, CommunityService
    │   ├── views.py                   # Gestão de membros, banimentos, cargos e convites
    │   ├── urls.py
    │   ├── tests.py
    │   ├── management/commands/       # purge_archived_communities.py
    │   └── templates/communities/
    ├── goals/                         # Metas individuais e comunitárias
    │   ├── models.py                  # Goal, GoalParticipation
    │   ├── services.py                # GoalService (cálculo de progresso em grupo)
    │   ├── signals.py                 # Sincronização automática entre participações e memberships
    │   ├── views.py                   # Criação, edição, conclusão e adesão a metas
    │   ├── urls.py
    │   ├── tests.py
    │   └── templates/goals/
    ├── forums/                        # Fóruns de comunidades e metas
    │   ├── models.py                  # Forum, Message
    │   ├── services.py                # Regras de acesso e moderação de mensagens
    │   ├── views.py                   # Exibição de tópicos e envio de mensagens
    │   ├── urls.py
    │   ├── tests.py
    │   └── templates/forums/
    ├── notifications/                 # Alertas em tempo real e tarefas agendadas
    │   ├── models.py                  # Notification
    │   ├── services.py                # Função auxiliar create_notification
    │   ├── tasks.py                   # Tarefa agendada notify_without_reading (Celery)
    │   ├── views.py                   # Endpoints JSON, página de histórico e dismiss
    │   ├── urls.py
    │   ├── tests.py
    │   └── templates/notifications/   # history.html
    ├── rewards/                       # Sistema de gamificação e 35 insígnias
    │   ├── models.py                  # Insignia, Award, CriteriaType
    │   ├── services.py                # Triggers de verificação e concessão (check_*)
    │   ├── selectors.py               # Agrupamento por categorias e status de conquista
    │   ├── management/commands/       # seed_insignias.py
    │   ├── static/rewards/img/insignias/ # Ícones vetoriais em formato SVG
    │   └── templates/rewards/         # insignias.html e _insignia_medal.html
    └── logs/                          # Trilha de auditoria administrativa
        ├── models.py                  # AuditLog (registro imutável de ações)
        ├── services.py                # create_log, log_edit, delete_log
        ├── forms.py                   # Formulários de filtro e edição de logs
        ├── views.py                   # Listagem com filtros, detalhes e edição
        ├── urls.py
        ├── tests.py
        └── templates/logs/
```

---

## 2. Catálogo Completo de Rotas da Aplicação

Todas as rotas são relativas ao endereço base `http://127.0.0.1:8000`. Endpoints com controle de acesso exigem login ou permissão administrativa.

### Páginas Gerais (`main`)

| Rota | Descrição | Nível de Acesso |
| :--- | :--- | :--- |
| `/` | Página inicial (se logado, redireciona ao perfil) | Público |
| `/search` | Página de busca global de livros e comunidades | Público |
| `/admin/` | Painel administrativo nativo do Django | Administrador |

### Contas e Perfil (`/user/`)

| Rota | Descrição | Nível de Acesso |
| :--- | :--- | :--- |
| `/user/register/` | Cadastro de nova conta de leitor | Público |
| `/user/login/` | Autenticação no sistema | Público |
| `/user/logout/` | Logout e invalidação de sessão (POST) | Autenticado |
| `/user/profile/` | Página de perfil com estante, ofensiva e insígnias | Autenticado |
| `/user/profile/editProfile/` | Formulário para edição de dados pessoais e bio | Autenticado |
| `/user/streak/` | Calendário mensal de histórico da ofensiva diária | Autenticado |
| `/user/streak/<str:day>/` | Detalhamento dos livros e páginas lidos em um dia específico | Autenticado |

### Notificações (`/notifications/`)

| Rota | Descrição | Nível de Acesso |
| :--- | :--- | :--- |
| `/notifications/` | Retorna notificações em formato JSON para o sino na navbar | Autenticado |
| `/notifications/history/` | Página com o histórico completo de notificações recebidas | Autenticado |
| `/notifications/mark-read/` | Marca todas as notificações como lidas via requisição AJAX (POST) | Autenticado |
| `/notifications/<id>/hide/` | Oculta uma notificação do dropdown rápido do sino (POST) | Autenticado |
| `/notifications/<id>/dismiss/`| Exclui permanentemente uma notificação do histórico (POST) | Autenticado |

### Livros e Leitura (`/books/`)

| Rota | Descrição | Nível de Acesso |
| :--- | :--- | :--- |
| `/books/search/` | Busca filtrada no catálogo de livros | Público |
| `/books/<int:book_id>/` | Ficha técnica do livro, resenhas e avaliações | Público |
| `/books/register/` | Cadastro de novo livro no catálogo | Autenticado |
| `/books/<int:book_id>/edit/` | Edição dos dados de um livro | Criador ou Admin |
| `/books/<int:book_id>/delete/` | Exclusão de um livro do catálogo | Criador ou Admin |
| `/books/shelf/` | Gerenciamento da estante pessoal do leitor | Autenticado |
| `/books/shelf/<int:book_id>/mark-read/` | Marcar livro como lido (POST) | Autenticado |
| `/books/shelf/<int:book_id>/progress/` | Atualizar progresso em páginas ou porcentagem (POST) | Autenticado |
| `/books/shelf/<int:book_id>/session/` | Salvar nova sessão de leitura (POST) | Autenticado |
| `/books/shelf/<int:book_id>/sessions/` | Listar sessões de leitura vinculadas ao livro | Autenticado |
| `/books/shelf/<int:book_id>/sessions/<int:session_id>/` | Editar registro de sessão de leitura (POST/PATCH) | Autenticado |
| `/books/lookup/` | Consulta rápida de livros em JSON (para autocomplete) | Autenticado |
| `/books/reading/` | Interface com cronômetro para sessão de leitura ativa | Autenticado |
| `/books/reading/register/` | Formulário para registrar leitura finalizada | Autenticado |

### Comunidades (`/communities/`)

| Rota | Descrição | Nível de Acesso |
| :--- | :--- | :--- |
| `/communities/` | Painel de comunidades do usuário e exploração | Autenticado |
| `/communities/search/` | Busca de comunidades por título ou descrição | Público |
| `/communities/create/` | Criação de um novo clube de leitura | Autenticado |
| `/communities/join-by-code/` | Entrada em comunidade privada via código de convite | Autenticado |
| `/communities/<int:community_id>` | Página principal e mural da comunidade | Autenticado |
| `/communities/<int:community_id>/forum/` | Redirecionamento para o fórum geral do clube | Membro |
| `/communities/<int:community_id>/join` | Solicitar entrada ou entrar diretamente (se pública) | Autenticado |
| `/communities/<int:community_id>/join/<str:invitation_code>` | Entrada direta via link de convite codificado | Autenticado |
| `/communities/<int:community_id>/leave` | Sair da comunidade | Membro |
| `/communities/<int:community_id>/generate_invitation_code` | Gerar código de convite temporário (JSON) | Criador, Moderador ou Admin |
| `/communities/<int:community_id>/manage/` | Painel de moderação e gestão de membros | Criador, Moderador ou Admin |
| `/communities/<int:community_id>/edit/` | Edição dos dados e regras da comunidade | Criador, Moderador ou Admin |
| `/communities/<int:community_id>/archive/` | Arquivar comunidade | Criador, Moderador ou Admin |
| `/communities/<int:community_id>/unarchive/` | Desarquivar comunidade | Criador, Moderador ou Admin |
| `/communities/<int:community_id>/delete/` | Exclusão definitiva da comunidade (POST) | Criador ou Admin |
| `/communities/<int:community_id>/members/<int:membership_id>/role/` | Promover a moderador ou rebaixar a membro | Criador ou Admin |
| `/communities/<int:community_id>/members/<int:membership_id>/request/`| Aprovar ou recusar solicitação de ingresso | Criador, Moderador ou Admin |
| `/communities/<int:community_id>/members/<int:membership_id>/ban/` | Aplicar ou revogar banimento de membro | Criador, Moderador ou Admin |

### Metas (`/goals/`)

| Rota | Descrição | Nível de Acesso |
| :--- | :--- | :--- |
| `/goals/create/` | Criar nova meta individual de leitura | Autenticado |
| `/goals/create/community/<int:community_id>/` | Criar meta coletiva para uma comunidade | Moderador ou Admin |
| `/goals/<int:goal_id>/forum/` | Fórum de debate específico da meta | Participante |
| `/goals/<int:goal_id>/edit/` | Edição de prazos e objetivos da meta | Criador da meta |
| `/goals/<int:goal_id>/delete/` | Exclusão de meta individual (POST) | Dono da meta |
| `/goals/<int:goal_id>/join/` | Entrar em uma meta coletiva (POST) | Membro da comunidade |
| `/goals/<int:goal_id>/leave/` | Sair de uma meta coletiva (POST) | Participante |
| `/goals/<int:goal_id>/conclude/` | Concluir meta atingida (POST) | Criador da meta |

### Fóruns (`/forums/`)

| Rota | Descrição | Nível de Acesso |
| :--- | :--- | :--- |
| `/forums/<int:forum_id>` | Visualização de mensagens e envio de respostas | Membro autorizado |
| `/forums/<int:forum_id>/edit` | Editar título e configurações do fórum | Moderador ou Admin |
| `/forums/messages/<int:message_id>/delete/` | Excluir mensagem do fórum | Autor ou Moderador |

### Insígnias (`/rewards/`)

| Rota | Descrição | Nível de Acesso |
| :--- | :--- | :--- |
| `/rewards/insignias/` | Galeria de todas as 35 insígnias (conquistadas e bloqueadas) | Autenticado |

### Auditoria e Logs (`/logs/`)

| Rota | Descrição | Nível de Acesso |
| :--- | :--- | :--- |
| `/logs/` | Listagem com filtros avançados e paginação de auditoria | Administrador (`is_superuser`) |
| `/logs/<int:log_id>/` | Detalhes e metadados completos de uma ação auditada | Administrador (`is_superuser`) |
| `/logs/<int:log_id>/edit/` | Ajustar notas de um registro de log | Administrador (`is_superuser`) |
| `/logs/<int:log_id>/delete/` | Exclusão com rastreamento reverso de log (POST) | Administrador (`is_superuser`) |

---

## 3. Aprofundamento: Celery, Redis e Tarefas Periódicas

### Fluxo de Execução da Notificação Diária

A rotina agendada `notifications.tasks.notify_without_reading` opera no seguinte ciclo:

```
[ Celery Beat ] -> Dispara tarefa às 20h00 (horário de Brasília)
       ↓
[ Redis Broker ] -> Enfileira a tarefa na fila padrão
       ↓
[ Celery Worker ] -> Retira e executa o código Python:
       ↓
  1. Obtém a data local de hoje (timezone.localdate())
  2. Itera sobre todos os usuários ativos do sistema
  3. Verifica se o usuário possui registro em ReadingSession na data de hoje
  4. Verifica se o usuário já recebeu o aviso de leitura hoje (evita duplicatas)
  5. Se NÃO leu e NÃO foi notificado:
       Cria registro Notification(target_user=user, content='Você já leu hoje?...')
       ↓
[ Interface do Usuário ] -> Sino atualiza o badge de não lidas e exibe o alerta
```

---

### Instalação Avançada do Redis por Plataforma

O Celery utiliza o endereço padrão `redis://localhost:6379/0`.

#### Docker (Recomendado)
```bash
docker run -d --name colecture-redis -p 6379:6379 redis:alpine
```
Para parar ou reiniciar em sessões futuras:
```bash
docker stop colecture-redis
docker start colecture-redis
```

#### Windows via WSL2 (Ubuntu / Debian)
```bash
sudo apt update
sudo apt install redis-server -y
sudo service redis-server start
```

#### Linux Nativo (Ubuntu / Debian / Pop!_OS)
```bash
sudo apt update
sudo apt install redis-server -y
sudo systemctl enable --now redis-server
```

#### macOS (Homebrew)
```bash
brew install redis
brew services start redis
```

---

### Por que o Windows exige a flag `-P solo`?

Em ambientes Unix (Linux/macOS), o Celery cria processos trabalhadores através da chamada de sistema `fork()`. O Windows não possui implementação nativa de `fork()`, o que faz com que a biblioteca `billiard` (utilizada internamente pelo Celery para multiprocessamento) falhe ao tentar clonar o processo principal.

Ao executar no terminal do Windows sem a flag `-P solo`, erros como `WinError` ou travamentos silenciosos podem ocorrer. A flag `-P solo` instrui o Celery a executar as tarefas no processo atual sem tentar bifurcar processos via `prefork`:

```bash
celery -A colecture worker -l info -P solo
```

---

### Como testar tarefas do Celery manualmente (Django Shell)

Para verificar o processamento de tarefas sem aguardar até as 20h00:

1. Abra o shell interativo do Django:
   ```bash
   cd colecture
   python manage.py shell
   ```

2. Execute o script abaixo:
   ```python
   from notifications.tasks import notify_without_reading

   # 1. Teste SÍNCRONO (executa diretamente no shell sem depender de Redis ou Worker)
   notify_without_reading()

   # 2. Teste ASSÍNCRONO (envia para o Redis e é processado pelo Celery Worker)
   task = notify_without_reading.delay()
   print("Task ID:", task.id)
   print("Status da tarefa:", task.status)
   ```

3. Abra o site em `http://127.0.0.1:8000` com um usuário logado que não tenha leituras hoje:
   - O ícone do sino na barra lateral exibirá a notificação recebida.
   - A notificação também estará listada em `/notifications/history/`.

---

### Configurações no Código

- **`colecture/settings.py`**:
  ```python
  CELERY_BROKER_URL = 'redis://localhost:6379/0'
  CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

  CELERY_BEAT_SCHEDULE = {
      'notify-users-every-10-minutes': {
          'task': 'notifications.tasks.notify_without_reading',
          'schedule': crontab(hour=20, minute=0),
      },
  }
  ```

- **`colecture/celery.py`**:
  ```python
  import os
  from celery import Celery

  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'colecture.settings')
  app = Celery('colecture')
  app.config_from_object('django.conf:settings', namespace='CELERY')
  app.autodiscover_tasks()
  ```

- **`colecture/__init__.py`**:
  ```python
  from .celery import app as celery_app
  __all__ = ('celery_app',)
  ```

---

## 4. Sistema de Notificações

O app `notifications` provê a camada de comunicação assíncrona entre o sistema e o leitor:

- **Contador no Sino (`unread_notifications_count`):** Injetado no contexto da página inicial e do perfil, exibe um badge visual com a quantidade de notificações pendentes.
- **Dropdown Rápido:** Lista as últimas notificações recebidas. O usuário pode clicar no "X" para ocultar um aviso (`hide_notification_from_popup`), que marca como lida sem apagar do histórico.
- **Página de Histórico (`/notifications/history/`):** Exibe todos os alertas recebidos. Ao carregar a página, todas as notificações não lidas são atualizadas para `is_read = True`. É possível dispensar alertas individualmente com exclusão física no banco (`dismiss_notification`).
- **Gatilhos no Sistema:**
  - *Ofensiva em risco:* Ao abrir o perfil no primeiro acesso do dia, o sistema emite aviso de leitura caso o usuário ainda não tenha registrado atividade.
  - *Sessões registradas:* Emissão de confirmação de páginas e tempo computados.
  - *Moderação de Comunidades:* Disparo automático quando o usuário tem pedido aceito, é promovido a moderador, rebaixado a membro ou banido.

---

## 5. Scripts de Seed e Manutenção

Localizados em `management/commands/` de cada app, executados a partir de `colecture/`:

| Comando | App | Parâmetros Disponíveis | O que faz |
| :--- | :--- | :--- | :--- |
| `seed_books` | `books` | `--no-covers`<br>`--update` | Popula o catálogo com livros reais baseados em ISBN único. |
| `seed_demo` | `books` | `--password <senha>` | Cria 5 usuários de demonstração, 2 comunidades, metas e ofensivas ativas. |
| `seed_insignias` | `rewards` | Nenhum | Recarrega e sincroniza a tabela de 35 insígnias oficiais. |
| `purge_archived_communities` | `communities` | Nenhum | Exclui definitivamente comunidades arquivadas há mais de 60 dias. |

---

## 6. Sistema de Insígnias e Gamificação (R19)

O CoLecture possui **35 insígnias** ativas (numeradas de 1 a 36, sendo a de número 18 descontinuada):

### Categorias Oficiais

| Categoria | IDs | Tema Visual | Variável de Cor |
| :--- | :--- | :--- | :--- |
| **Ofensiva pessoal** | 1 a 8 | Chama crescente conforme os dias de ofensiva | `--cat-streak` |
| **Livros lidos** | 9 a 14 | Livros e estante acumulada | `--cat-books` |
| **Progresso diário** | 15 a 17 | Volume de páginas em 24 horas | `--cat-pages` |
| **Horas de leitura** | 19 a 24 | Relógio e ampulheta de dedicação | `--cat-hours` |
| **Metas individuais** | 25 a 29 | Alvos e bandeiras de conquista pessoal | `--cat-goal` |
| **Metas de comunidade**| 30 a 33 | Ciclos em grupo e liderança | `--cat-community-goal` |
| **Social e Avaliações**| 34 e 35 | Balões de diálogo e penas de resenha | `--cat-social` |
| **Especiais** | 36 | Fênix de recuperação de hábito | `--cat-special` |

### Ícones e Armazenamento

Os ícones ficam em `rewards/static/rewards/img/insignias/` e seguem a convenção:
```text
insignia-<id_com_2_digitos>-<slug_do_nome>.svg
Exemplo: insignia-01-primeira-faisca.svg, insignia-36-fenix.svg
```

Cada medalha é composta por um SVG transparente de 64×64 pixels. As bordas, efeitos de iluminação e o estado bloqueado (cinza com cadeado) são gerados inteiramente via CSS.

---

## 7. Logs de Auditoria

O app `logs` registra eventos críticos no banco de dados através da entidade `AuditLog`:

- **Campos do `AuditLog`:**
  - `actor`: Usuário que realizou a operação (nulo em operações do sistema, como `purge_archived_communities`).
  - `action`: Tipo enumerado da ação (`AuditLog.Action.MEMBER_BANNED`, etc.).
  - `content_type`: Modelo Django do alvo da ação (`User`, `Community`, `Message`, etc.).
  - `object_id`: Chave primária numérica do objeto afetado.
  - `created_at`: Carimbo de data/hora do evento.
  - `metadata`: Objeto JSON com dados contextuais (ex: nome da comunidade, campos antes e depois da edição).

### Exemplo de Uso no Código

```python
from logs.models import AuditLog
from logs.services import create_log

create_log(
    actor=request.user,
    action=AuditLog.Action.COMMUNITY_ARCHIVED,
    target=community,
    metadata={"community_name": community.name, "archived_by": request.user.username}
)
```

---

## 8. Catálogo de Livros e Algoritmo de Recomendação

O app `books` gerencia todo o ciclo de leitura e avaliação:

- **Algoritmo de Recomendação (`get_recommended_books` em `books/services.py`):**
  Calcula uma pontuação ponderada para cada livro baseando-se em:
  1. *Tempo dedicado:* Soma de minutos acumulados em sessões de leitura (`add_time_score`).
  2. *Status na estante:* Livros marcados como "Lendo" e "Quero Ler" recebem peso preferencial (`add_status_score`).
  3. *Avaliações dos leitores:* Média e volume de avaliações com estrelas (`add_rating_score`).
- **Sessões e Progresso:**
  O sistema converte automaticamente páginas lidas em porcentagem do livro e atualiza a data da última leitura no `Profile`, garantindo a integridade da sequência de dias consecutivos (*streak*).
- **Processamento de Imagens com Pillow:**
  Capas de livros e avatares passam por validação de formato e tamanho no upload e são servidos sob o prefixo `media/`.

---

## 9. Padrões Arquiteturais e de Código

- **Padrão MTV (Model-Template-View):** Views concentram-se no tratamento da requisição HTTP; regras de negócio complexas são transferidas para a camada de serviços (`services.py`).
- **Encapsulamento de Regras:** Acesso e escrita no banco de dados ocorrem estritamente via Django ORM, prevenindo vulnerabilidades de injeção de SQL.
- **Convenções de Idioma:**
  - Código-fonte (variáveis, métodos, classes, branches, rotas e commits): **Inglês**.
  - Documentação, comentários explicativos e interface do usuário: **Português (pt-br)**.
- **Migrações:** Nenhuma modificação em tabelas de banco é feita manualmente. Toda alteração estrutural deve ser acompanhada por um arquivo de migração versionado (`makemigrations`).

---

## 10. Políticas de Branches e Conventional Commits

### Modelo de Branches

- `main`: Branch estável de produção. Recebe apenas código integrado, revisado e com testes passando.
- `sprintN`: Branches onde o trabalho de cada sprint é integrado (`sprint1` a `sprint7`).
- `docs`: Contém a documentação técnica estática e a configuração do MkDocs.
- `gh-pages`: Publicação automatizada do portal de documentação.

### Conventional Commits

Formato obrigatório:
```text
tipo(escopo-opcional): mensagem descritiva no imperativo
```

*Exemplos:*
- `feat(notifications): adiciona visualização de histórico de notificações`
- `fix(streak): corrige contagem de dias em ano bissexto`
- `docs(readme): detalha passos de execução do celery worker`

---

## 11. Histórico de Sprints e Documentação Externa

O projeto conta com documentação completa em MkDocs hospedada no GitHub Pages:

- 🔗 **[Portal da Documentação no GitHub Pages](https://fga0138-mds-ajax.github.io/2026.2-T02-Hamilton/)**
- 📄 **[Documento de Visão do Produto e Projeto](https://fga0138-mds-ajax.github.io/2026.2-T02-Hamilton/visao/produto/)**
- 🏛️ **[Documento de Arquitetura de Software](https://fga0138-mds-ajax.github.io/2026.2-T02-Hamilton/arquitetura/visoes/)**
- 📋 **[Atas de Reunião da Equipe (Atas 01 a 07)](https://fga0138-mds-ajax.github.io/2026.2-T02-Hamilton/atas-reuniao/)**

Para retornar à visão geral e ao guia de inicialização rápida, consulte o [README.md](README.md).

---

<div align="center">
  <sub>CoLecture • Métodos de Desenvolvimento de Software • 2026.2 • Universidade de Brasília</sub>
</div>
