# CoLecture - Sistema de leitura em comunidades

> Projeto desenvolvido para a disciplina de **Métodos de Desenvolvimento de Software (MDS)**
> Universidade de Brasília — FGA | Prof. Ricardo Ajax Dias Kosloski

O **CoLecture** é uma plataforma onde você pode se conectar, formar comunidades ou entrar em comunidades existentes para manter o hábito de leitura em dia. Ela conta com metas de leitura dos grupos, fóruns para conversar e debater sobre o capítulo do livro, um sistema de ofensiva para motivar a leitura diária e insígnias. E, como diz o ditado popular: "Se quer ir rápido, vá sozinho. Se quer ir longe, vá acompanhado".

---

## Tecnologias utilizadas

### Back-end

| Tecnologia | Uso |
| ---------- | --- |

<!-- # TO-DO: Fazer a tabela de tecnologia e uso -->

### Front-end

| Tecnologia | Uso |
| ---------- | --- |

<!-- # TO-DO: Fazer a tabela de tecnologia e uso -->

---

## Como executar o projeto localmente

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
| Linux / macOS | `source .venv/bin/activate` |
| Arch Linux (e derivadas) | `source .venv/bin/activate` (ou `activate.fish` / `activate.csh`, conforme o seu shell) |
| Windows (CMD) | `.venv\Scripts\activate` |

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

Crie as tabelas iniciais:

```bash
python manage.py migrate
```

### 5. Crie um superusuário (opcional)

O superusuário dá acesso à página de administração (`/admin`).

```bash
python manage.py createsuperuser
```

O terminal pedirá nome de usuário, e-mail e senha (com confirmação). Se a senha for considerada curta, comum ou totalmente numérica, ele perguntará se você deseja continuar: digite `y` para confirmar ou `n` para escolher outra senha.

O superusuário já é salvo no banco ao ser criado, então não é necessário rodar `migrate` novamente.

### 6. Inicie o servidor

```bash
python manage.py runserver
```

Acesse o site em [http://127.0.0.1:8000](http://127.0.0.1:8000) e o painel administrativo em [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin).

---

## Estrutura do Projeto

<!-- # TO-DO: Fazer estrutura do projeto -->

---

## Política de Branches

## Política de Branches

O repositório utiliza as seguintes branches:

| Branch | Finalidade |
|---|---|
| `main` | Branch principal. Recebe o código estável de cada release. |
| `sprint-N` | Uma branch para cada sprint (ex.: `sprint-1`, `sprint-2`), onde o desenvolvimento da sprint é feito. |
| `docs` | Armazena os arquivos de documentação do trabalho. |
| `gh-pages` | Branch usada pelo GitHub Pages para publicar o site do projeto. |

### Fluxo de trabalho

1. O desenvolvimento de cada sprint acontece na sua respectiva branch `sprint-N`.
2. Ao final da sprint, o código estável é integrado à `main`, marcando uma nova release.
3. Os arquivos de documentação são mantidos na branch `docs`, separados do código da aplicação.
4. A `gh-pages` é usada apenas para a publicação do GitHub Pages e não deve receber código de desenvolvimento.


---

## Política Padrão de Commits (Conventional Commits)

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

---

## Equipe

**Equipe Hamilton - MDS 2026.2 - UnB FCTE/FGA**

| Membro | Papel |
|---|---|

<!-- # TO-DO: Fazer tabela de equipe -->