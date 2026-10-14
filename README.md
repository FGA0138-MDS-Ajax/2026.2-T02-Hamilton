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

### Front-end

| Tecnologia | Uso |
| ---------- | --- |
| Templates do Django | Renderização das páginas no servidor (HTML). |
| HTML e CSS | Estrutura e estilo das páginas, com layout responsivo (`@media`) e cores centralizadas em `variables.css`. |
| JavaScript | Comportamento da interface. Previsto no projeto, ainda sem uso na Sprint 1 (`script.js` vazio). |
| [Boxicons](https://boxicons.com/) | Ícones, carregados por CDN. |
| [Google Fonts](https://fonts.google.com/) (Poppins) | Fonte do site, carregada por CDN. |

> Os ícones e a fonte são carregados da internet. Sem conexão, o site funciona, mas com a aparência padrão do navegador.

---

## Como executar o projeto localmente

O CoLecture roda apenas em ambiente local, sem hospedagem em provedor externo.

### Pré-requisitos

- [Git](https://git-scm.com/)
- [Python 3.10+](https://www.python.org/downloads/)
- [VS Code](https://code.visualstudio.com/) (opcional, mas recomendado)

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

### Executando os testes

Dentro da pasta `colecture`:

```bash
python manage.py test
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
├── requirements.txt              # Dependências (Django)
├── .gitignore
├── .prettierrc.json
└── colecture/                    # Projeto Django
    ├── manage.py
    ├── colecture/                # Configuração do projeto
    │   ├── settings.py           # Apps instalados, banco SQLite, idioma pt-br
    │   ├── urls.py               # Rotas principais (URLconf)
    │   ├── asgi.py
    │   └── wsgi.py
    ├── main/                     # App da página inicial e estilos compartilhados
    │   ├── views.py
    │   ├── urls.py
    │   ├── templates/main/       # index.html
    │   └── static/main/          # css/ (index, variables) e img/ (biblioteca.svg)
    └── accounts/                 # App de contas e perfis (Sprint 1)
        ├── models.py             # Profile (ofensiva e dados de leitura)
        ├── forms.py              # LoginForm, RegistrationForm, EditUserForm
        ├── views.py              # Cadastro, login, logout, perfil e edição
        ├── signals.py            # Cria o Profile de todo novo usuário
        ├── urls.py
        ├── tests.py              # CT01
        ├── migrations/           # 0001 (Profile), 0002 (admin padrão)
        ├── templates/accounts/   # login, register, profile e profileEdit
        └── static/accounts/      # css/ e js/
```

### Rotas

| Rota | View | Acesso |
|---|---|---|
| `/` | Página inicial (redireciona ao perfil se o usuário estiver logado) | Público |
| `/user/register/` | Cadastro | Público |
| `/user/login/` | Login | Público |
| `/user/logout/` | Logout (somente `POST`) | Usuário logado |
| `/user/profile/` | Perfil do usuário | Usuário logado |
| `/user/profile/editProfile/` | Edição do perfil | Usuário logado |
| `/admin/` | Painel administrativo do Django | Administrador |

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
| Gabriel Sayd de Santana Lombas Macedo | **Cliente**, Desenvolvedor, Analista de Qualidade, Engenheiro de Dados |
| Guilherme Ribeiro Almeida | **Engenheiro de Dados**, Desenvolvedor |
| Henrique Catharino Nunes de Mendonça | **Desenvolvedor**, Arquiteto de Software |
| Jônatas Maciel da Silva Alves | **Analista de Requisitos e Documentação**, Desenvolvedor |
| Letícia da Silva Pereira | **Analista de Qualidade**, Desenvolvedora, Dono do Produto |
| Ricieri Artur Vasconcellos Vieira | **Dono do Produto**, Desenvolvedor, Analista de Qualidade, Engenheiro de Dados |