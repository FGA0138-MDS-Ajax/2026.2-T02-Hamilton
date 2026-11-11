# CoLecture - Sistema de leitura em comunidades

> Projeto desenvolvido para a disciplina de **Métodos de Desenvolvimento de Software (MDS)**
> Universidade de Brasília — FGA | Prof. Ricardo Ajax Dias Kosloski

O **CoLecture** é uma plataforma onde você pode se conectar, formar comunidades ou entrar em comunidades existentes para manter o hábito de leitura em dia. Ela conta com metas de leitura dos grupos, fóruns para conversar e debater sobre o capítulo do livro, um sistema de ofensiva para motivar a leitura diária e insígnias. E, como diz o ditado popular: "Se quer ir rápido, vá sozinho. Se quer ir longe, vá acompanhado".

---

## Tecnologias utilizadas

### Back-end

| Tecnologia | Uso |
| ---------- | --- |
| [Python](https://www.python.org/) 3.12+ | Linguagem principal do back-end. |
| [Django](https://www.djangoproject.com/) 6.1.2 | Framework web (padrão MTV): rotas, views, formulários, autenticação, permissões, painel administrativo e proteção contra CSRF e XSS. |
| Django ORM | Acesso aos dados. As views não escrevem SQL diretamente. |
| [SQLite](https://www.sqlite.org/) | Banco de dados local (`db.sqlite3`), criado pelo `migrate` e não versionado. |
| Django Forms | Validação das requisições antes do processamento (cadastro, login e edição de perfil). |
| Django TestCase | Testes automatizados, executados com `python manage.py test`. |
| [Celery](https://docs.celeryproject.org/) + [django-celery-beat](https://django-celery-beat.readthedocs.io/) | Tarefas agendadas (lembrete diário de leitura às 20h). **Opcional** para rodar o site. |
| [Redis](https://redis.io/) | Broker do Celery (`redis://localhost:6379/0`). **Opcional**, só necessário para as notificações agendadas. |

### Front-end

| Tecnologia | Uso |
| ---------- | --- |
| Templates do Django | Renderização das páginas no servidor (HTML). |
| HTML e CSS | Estrutura e estilo das páginas, com layout responsivo (`@media`) e cores centralizadas em `variables.css`. |
| JavaScript | Comportamento da interface (fórum, comunidades, estante, sessões de leitura, metas e busca), organizado por app em `static/<app>/js/`. |
| [Boxicons](https://boxicons.com/) | Ícones, carregados por CDN. |
| [Google Fonts](https://fonts.google.com/) (Poppins) | Fonte do site, carregada por CDN. |

> Os ícones e a fonte são carregados da internet. Sem conexão, o site funciona, mas com a aparência padrão do navegador.

---

## Como executar o projeto localmente

O CoLecture roda apenas em ambiente local, sem hospedagem em provedor externo.

### Pré-requisitos

- [Git](https://git-scm.com/)
- [Python 3.12+](https://www.python.org/downloads/)
- [VS Code](https://code.visualstudio.com/) (opcional, mas recomendado)
- [Redis](https://redis.io/) (opcional): só é necessário para as notificações agendadas via Celery. O restante do sistema funciona sem ele.

<!-- # TO-DO: Confirmar a versão mínima do Python e do Django usadas no projeto -->

### 1. Clone o repositório

```bash
git clone https://github.com/FGA0138-MDS-Ajax/2026.2-T02-Hamilton
cd 2026.2-T02-Hamilton
```

Se preferir, abra a pasta `2026.2-T02-Hamilton` no VS Code e use o terminal integrado para os próximos passos.

### 2. Crie e ative o ambiente virtual

Crie o ambiente virtual:

```bash
python -m venv .venv
```

Ative-o de acordo com o seu sistema operacional:

| Sistema | Comando |
|---|---|
| Linux / macOS (bash/zsh) | `source .venv/bin/activate` |
| Linux (fish) | `source .venv/bin/activate.fish` |
| Linux (csh) | `source .venv/bin/activate.csh` |
| Windows (CMD) | `.venv\Scripts\activate` |
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |

Quando o ambiente estiver ativo, o terminal mostrará `(.venv)` no início da linha.

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure o banco de dados

Entre na pasta do projeto Django:

```bash
cd colecture
```

Crie as tabelas e o administrador padrão:

```bash
python manage.py migrate
```

O `migrate` também cria o **administrador padrão** (R03), já que o banco começa vazio. Veja a seção [Administrador padrão](#administrador-padrão).

Opcionalmente, popule o catálogo e os dados de demonstração (veja [Scripts para popular o banco](#scripts-para-popular-o-banco)):

```bash
python manage.py seed_books
python manage.py seed_demo
```

### 5. Inicie o servidor

```bash
python manage.py runserver
```

Acesse o site em [http://127.0.0.1:8000](http://127.0.0.1:8000) e o painel administrativo em [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin).

### Administrador padrão

A migration `accounts/migrations/0002_createDefaultAdmin.py` cria um administrador quando o banco é criado. Os valores padrão são:

| Campo | Valor padrão | Variável de ambiente para alterar |
|---|---|---|
| Usuário | `admin` | `COLECTURE_ADMIN_USERNAME` |
| E-mail | `admin@colecture.com` | `COLECTURE_ADMIN_EMAIL` |
| Senha | `Admin#Colecture2026` | `COLECTURE_ADMIN_PASSWORD` |

Para usar outros valores, defina as variáveis **antes** do primeiro `migrate`. Se o administrador já existir, a migration não o altera.

> Essas credenciais são apenas para desenvolvimento local. Não use esses valores em qualquer ambiente acessível pela internet.

Se preferir outro superusuário, também é possível criá-lo com `python manage.py createsuperuser`. O perfil (`Profile`) é criado automaticamente para todo novo usuário.

### Scripts para popular o banco

Os comandos abaixo ficam em `management/commands/` e são executados dentro da pasta `colecture`, depois do `migrate`. Todos podem ser rodados mais de uma vez sem duplicar dados.

| Comando | App | O que faz |
|---|---|---|
| `python manage.py seed_books` | `books` | Popula o catálogo com livros reais (o ISBN é a chave). |
| `python manage.py seed_demo` | `books` | Cria usuários, comunidades, mensagens de fórum, metas e uma ofensiva de demonstração. |
| `python manage.py purge_archived_communities` | `communities` | Exclui as comunidades arquivadas há mais de 60 dias. |

#### `seed_books`

```bash
python manage.py seed_books              # insere os livros que ainda não existem
python manage.py seed_books --no-covers  # insere sem URL de capa
python manage.py seed_books --update     # também atualiza livros já existentes (mesmo ISBN)
```

#### `seed_demo`

Para testar o sistema com dados prontos, rode:

```bash
python manage.py seed_demo
python manage.py seed_demo --password outra_senha   # usa outra senha para os usuários
```

O comando cria:

- **5 usuários**, todos com `Profile` e a senha `Senha#123` (ou a informada em `--password`);
- **2 comunidades**: uma pública e uma privada, esta com um pedido de entrada pendente;
- **mensagens** no fórum geral de cada comunidade;
- **1 meta coletiva** por comunidade (com fórum automático) e **1 meta individual** por usuário;
- **ofensiva de 5 dias** para `ana`, registrada pelo mesmo serviço da tela de registrar leitura.

| Usuário | Papel nos dados de demonstração |
|---|---|
| `ana` | Criadora da comunidade pública; ofensiva de 5 dias lendo *Duna* |
| `bruno` | Criador da comunidade privada; moderador da pública |
| `carla` | Moderadora da privada; membro da pública |
| `diego` | Membro das duas comunidades |
| `elisa` | Membro da pública; pedido pendente na privada |

| Comunidade | Acesso | Livro | Meta coletiva |
|---|---|---|---|
| Clube da Ficção Científica | Pública | *Duna* | Ler 500 páginas juntos |
| Círculo dos Clássicos de Fantasia | Privada | *O Hobbit* | 10 horas de leitura em grupo |

Se o catálogo não tiver os livros usados nas comunidades, o `seed_demo` executa o `seed_books` antes.

> Os dados de demonstração são apenas para desenvolvimento local e não devem ser usados em ambientes acessíveis pela internet.


### Executando os testes

Dentro da pasta `colecture`:

```bash
python manage.py test            # todos os apps
python manage.py test books      # apenas um app (accounts, books, communities, forums, goals, main, notifications)
```

---

### Atualizando o banco após um `git pull`

Quando alguém da equipe alterar os models, aplique as novas migrations:

```bash
python manage.py migrate
```

Se você alterar um model, gere a migration com `python manage.py makemigrations` e versione o arquivo gerado. Alterações de esquema são feitas somente por migrations.

---

## Estrutura do Projeto

Cada módulo é um app Django independente, com seus próprios models, views, templates e testes (Documento de Arquitetura, Seção 2.5.3).

```text
2026.2-T02-Hamilton/
├── README.md
├── requirements.txt               # Dependências (Django, Celery, Redis etc.)
├── .gitignore
└── colecture/                     # Projeto Django
    ├── manage.py
    ├── colecture/                 # Configuração do projeto
    │   ├── settings.py            # Apps instalados, SQLite, pt-br, Celery e agenda (beat)
    │   ├── urls.py                # Rotas principais (URLconf)
    │   ├── celery.py              # Aplicação Celery
    │   ├── asgi.py
    │   └── wsgi.py
    ├── main/                      # Página inicial, busca e estilos compartilhados
    │   ├── views.py
    │   ├── urls.py
    │   ├── templates/             # sidebar.html e main/ (index, search)
    │   └── static/main/           # css/ (index, search, sidebar, toast, variables), js/ e img/
    ├── accounts/                  # Contas, perfis e ofensiva
    │   ├── models.py              # Profile (ofensiva e última leitura)
    │   ├── services.py            # AccountService (criação do perfil)
    │   ├── forms.py               # LoginForm, RegistrationForm, EditUserForm
    │   ├── views.py               # Cadastro, login, logout, perfil, edição e calendário da ofensiva
    │   ├── urls.py
    │   ├── tests.py
    │   ├── migrations/            # 0001_initial e 0002_createDefaultAdmin (admin padrão)
    │   ├── templates/accounts/
    │   └── static/accounts/       # css/ e js/
    ├── books/                     # Catálogo, estante e sessões de leitura
    │   ├── models.py              # Book, BookReview, BookStatus, ReadingSession
    │   ├── services.py            # Regras das sessões de leitura (persist_reading_session)
    │   ├── forms.py
    │   ├── views.py
    │   ├── urls.py
    │   ├── tests.py
    │   ├── management/commands/   # seed_books e seed_demo
    │   ├── migrations/
    │   ├── templates/books/
    │   └── static/books/          # css/, js/ e img/
    ├── communities/               # Comunidades, membros e convites
    │   ├── models.py              # Community, Membership, Invitation
    │   ├── services.py            # MembershipService e CommunityService
    │   ├── forms.py
    │   ├── views.py
    │   ├── urls.py
    │   ├── tests.py
    │   ├── management/commands/   # purge_archived_communities
    │   ├── migrations/
    │   ├── templates/communities/
    │   └── static/communities/    # css/, js/ e img/
    ├── goals/                     # Metas individuais e coletivas
    │   ├── models.py              # Goal, GoalParticipation
    │   ├── services.py            # GoalService (participação e progresso)
    │   ├── signals.py             # Sincroniza participações com a Membership
    │   ├── forms.py
    │   ├── views.py
    │   ├── urls.py
    │   ├── tests.py
    │   ├── migrations/
    │   ├── templates/goals/
    │   └── static/goals/          # css/ e js/
    ├── forums/                    # Fóruns (geral da comunidade e de cada meta)
    │   ├── models.py              # Forum, Message
    │   ├── services.py            # ForumService (permissões e dados da página)
    │   ├── forms.py
    │   ├── views.py
    │   ├── urls.py
    │   ├── tests.py
    │   ├── migrations/
    │   └── templates/forums/
    └── notifications/             # Notificações e tarefas agendadas
        ├── models.py              # Notification
        ├── tasks.py               # notify_without_reading (Celery)
        ├── views.py
        ├── urls.py
        ├── tests.py
        └── migrations/
```

### Rotas

Todas as rotas abaixo são relativas a `http://127.0.0.1:8000`. "Logado" significa que a rota exige login (usuários não autenticados são redirecionados para `/user/login/`).

#### Páginas gerais (`main`)

| Rota | Descrição | Acesso |
|---|---|---|
| `/` | Página inicial (redireciona ao perfil se o usuário estiver logado) | Público |
| `/search` | Página de pesquisa | Público |
| `/admin/` | Painel administrativo do Django | Administrador |

#### Contas (`/user/`)

| Rota | Descrição | Acesso |
|---|---|---|
| `/user/register/` | Cadastro | Público |
| `/user/login/` | Login | Público |
| `/user/logout/` | Logout (somente `POST`) | Logado |
| `/user/profile/` | Perfil do usuário | Logado |
| `/user/profile/editProfile/` | Edição do perfil | Logado |
| `/user/streak/` | Calendário da ofensiva | Logado |
| `/user/streak/<day>/` | Histórico de leitura de um dia | Logado |

#### Livros (`/books/`)

| Rota | Descrição | Acesso |
|---|---|---|
| `/books/search/` | Busca de livros (GET) | Público |
| `/books/<id>/` | Página do livro e avaliações | Público |
| `/books/register/` | Cadastro de livro | Logado |
| `/books/<id>/edit/` | Edição do livro | Administrador ou usuário criador |
| `/books/<id>/delete/` | Exclusão do livro | Administrador ou usuário criador |
| `/books/lookup/` | Consulta de livros (JSON, GET) | Logado |
| `/books/shelf/` | Gerenciar a estante (GET/POST) | Logado |
| `/books/shelf/<id>/mark-read/` | Marcar livro como lido (POST) | Logado |
| `/books/shelf/<id>/progress/` | Salvar progresso de leitura (POST) | Logado |
| `/books/shelf/<id>/session/` | Registrar sessão de leitura (POST) | Logado |
| `/books/shelf/<id>/sessions/` | Listar sessões de leitura (GET) | Logado |
| `/books/shelf/<id>/sessions/<session_id>/` | Editar sessão de leitura (POST/PATCH) | Logado |
| `/books/reading/` | Página de leitura | Logado |
| `/books/reading/register/` | Registrar leitura | Logado |

#### Comunidades (`/communities/`)

| Rota | Descrição | Acesso |
|---|---|---|
| `/communities/` | Início das comunidades (as minhas e busca) | Logado |
| `/communities/search/` | Busca de comunidades | Público |
| `/communities/create/` | Criar comunidade | Logado |
| `/communities/join-by-code/` | Pedir entrada com o código da comunidade | Logado |
| `/communities/<id>` | Página da comunidade | Logado |
| `/communities/<id>/forum/` | Redireciona para o fórum geral | Logado |
| `/communities/<id>/join` | Entrar ou pedir entrada | Logado |
| `/communities/<id>/join/<invitation_code>` | Entrar com convite | Logado |
| `/communities/<id>/leave` | Sair da comunidade | Logado |
| `/communities/<id>/generate_invitation_code` | Gerar convite (JSON) | Criador, moderador ou administrador |
| `/communities/<id>/manage/` | Painel de moderação | Criador, moderador ou administrador |
| `/communities/<id>/edit/` | Editar comunidade | Criador, moderador ou administrador |
| `/communities/<id>/archive/` e `/unarchive/` | Arquivar e desarquivar | Criador, moderador ou administrador |
| `/communities/<id>/delete/` | Excluir comunidade (POST) | Criador, moderador ou administrador |
| `/communities/<id>/members/<membership_id>/role/` | Alterar o cargo de um membro | Criador, moderador ou administrador |
| `/communities/<id>/members/<membership_id>/request/` | Aprovar ou recusar pedido de entrada | Criador, moderador ou administrador |
| `/communities/<id>/members/<membership_id>/ban/` | Banir ou desbanir membro | Criador, moderador ou administrador |

#### Metas (`/goals/`)

| Rota | Descrição | Acesso |
|---|---|---|
| `/goals/create/` | Criar meta individual | Logado |
| `/goals/create/community/<community_id>/` | Criar meta da comunidade | Criador, moderador ou administrador |
| `/goals/<id>/forum/` | Fórum da meta | Participante da meta |
| `/goals/<id>/edit/` | Editar meta | Dono da meta ou gestor da comunidade |
| `/goals/<id>/delete/` | Excluir meta individual (POST); metas coletivas não podem ser excluídas | Dono da meta |
| `/goals/<id>/conclude/` | Concluir meta (POST) | Dono da meta ou gestor da comunidade |
| `/goals/<id>/join/` | Entrar na meta (POST) | Membro da comunidade |
| `/goals/<id>/leave/` | Sair da meta (POST) | Participante da meta |

#### Fóruns (`/forums/`)

| Rota | Descrição | Acesso |
|---|---|---|
| `/forums/<id>` | Ver e enviar mensagens no fórum | Membro da comunidade ou participante da meta |
| `/forums/<id>/edit` | Editar o fórum | Criador, moderador ou administrador |
| `/forums/messages/<id>/delete/` | Excluir mensagem | Autor ou gestor da comunidade |

---

## Padrões de código

Definidos nas restrições arquiteturais (Documento de Arquitetura, Seção 2.4.2):

- Back-end em Python com Django, e front-end com templates do Django (HTML, CSS e JavaScript).
- Requisições validadas antes do processamento, com Django Forms.
- Regras de negócio em métodos dos models, e não nas views, para poderem ser testadas sem uma requisição HTTP.
- Identificadores (variáveis, funções, classes e tabelas) em **inglês**; comentários e documentação em **português**.
- Banco SQLite e alterações de esquema somente por migrations.

---

## Política de Branches

O fluxo de trabalho segue a Seção 3 do documento de Visão. O repositório utiliza as seguintes branches:

| Branch | Finalidade |
|---|---|
| `main` | Branch final, onde o produto é entregue. Recebe somente código testado. |
| `sprintN` | Uma branch para cada sprint, de `sprint1` a `sprint7` (sem hífen), onde o desenvolvimento da sprint é feito e integrado. |
| `docs` | Armazena os arquivos de documentação do trabalho. |
| `gh-pages` | Usada pelo GitHub Pages para publicar o site do projeto. |

### Fluxo de trabalho

1. O desenvolvimento de cada sprint acontece na sua respectiva branch `sprintN`, para que erros e conflitos entre o código de diferentes membros sejam resolvidos sem afetar a entrega.
2. Tudo é testado na `sprintN`. Após a confirmação dos testes e a aprovação do Dono do Produto, a `sprintN` é integrada à `main` ao final da sprint.
3. Os arquivos de documentação são mantidos na branch `docs`, separados do código da aplicação.
4. A `gh-pages` é usada apenas para a publicação do GitHub Pages e não deve receber código de desenvolvimento.

---

## Política Padrão de Commits (Conventional Commits)

Formato: `tipo(escopo opcional): descrição`

Exemplo: `feat(accounts): adiciona edição de perfil`

```bash
feat      → nova funcionalidade
fix       → correção de bug
docs      → mudança em documentação
style     → formatação sem mudança de lógica
refactor  → refatoração sem nova feature e sem bug fix
test      → adição ou correção de testes
chore     → configuração e manutenção
perf      → melhoria de performance
ci        → mudanças no pipeline CI/CD
build     → mudanças que afetam o build
```

### Regras de Commit

- Mensagem no **imperativo** — "adiciona", "corrige", "atualiza"
- Sempre em **português** no corpo da mensagem
- Prefixo sempre em **inglês**
- Um espaço após os dois-pontos (`feat: texto`, e não `feat:texto`)

---

## Equipe

**Equipe Hamilton - MDS 2026.2 - UnB FCTE/FGA**

Papéis conforme o Quadro 5 do documento de Visão. Em **negrito**, o papel em que o integrante é o responsável. Todos os integrantes também atuam como desenvolvedores.

| Membro | Papéis |
|---|---|
| Ana Clara Teixeira Guimarães | **Desenvolvedora**, Engenheira de Dados |
| Arthur Miguel Silva Rocha | **Arquiteto de Software**, Desenvolvedor, Dono do Produto, Analista de Requisitos e Documentação |
| Gabriel Sayd de Santana Lombas Macedo | **Desenvolvedor**, Analista de Qualidade, Engenheiro de Dados |
| Guilherme Ribeiro Almeida | **Engenheiro de Dados**, Desenvolvedor |
| Henrique Catharino Nunes de Mendonça | **Desenvolvedor**, Arquiteto de Software |
| Jônatas Maciel da Silva Alves | **Analista de Requisitos e Documentação**, Desenvolvedor |
| Letícia da Silva Pereira | **Analista de Qualidade**, Desenvolvedora, Dono do Produto |
| Ricieri Artur Vasconcellos Vieira | **Dono do Produto**, Desenvolvedor, Analista de Qualidade, Engenheiro de Dados |