# CoLecture - Documentação (branch `docs`)

> Projeto desenvolvido para a disciplina de **Métodos de Desenvolvimento de Software (MDS)**
> Universidade de Brasília — FGA | Prof. Ricardo Ajax Dias Kosloski

Esta branch guarda **somente a documentação** do CoLecture, publicada como site com [MkDocs](https://www.mkdocs.org/). O site reúne os documentos de **Visão do Produto e do Projeto** e de **Arquitetura**, além das **atas de reunião** da equipe. O código da aplicação fica nas branches `sprintN` e `main`.

---

## Tecnologias utilizadas

| Tecnologia | Uso |
| ---------- | --- |
| [MkDocs](https://www.mkdocs.org/) | Gera o site estático a partir de arquivos Markdown. |
| [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) | Tema do site, personalizado em preto, branco e cinza (`docs/stylesheets/extra.css`). |
| GitHub Actions | Pipeline que publica o site a cada push na branch `docs`. |
| GitHub Pages | Hospedagem do site, a partir da branch `gh-pages`. |

---

## Como executar o site localmente

### Pré-requisitos

- [Git](https://git-scm.com/)
- [Python 3.10+](https://www.python.org/downloads/)

### 1. Clone o repositório e entre na branch `docs`

```bash
git clone https://github.com/FGA0138-MDS-Ajax/2026.2-T02-Hamilton
cd 2026.2-T02-Hamilton
git checkout docs
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv .venv
```

| Sistema | Comando |
|---|---|
| Linux / macOS (bash/zsh) | `source .venv/bin/activate` |
| Windows (CMD) | `.venv\Scripts\activate` |
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Inicie o servidor de documentação

```bash
mkdocs serve
```

Acesse [http://127.0.0.1:8000](http://127.0.0.1:8000). A página recarrega sozinha a cada arquivo salvo.

> Se a porta 8000 estiver ocupada (por exemplo, pelo `runserver` do Django), use `mkdocs serve -a 127.0.0.1:8001`.

### Comandos do MkDocs

| Comando | O que faz |
|---|---|
| `mkdocs serve` | Inicia o servidor local com recarregamento automático. |
| `mkdocs build` | Gera o site estático na pasta `site/` (não versionada). |
| `mkdocs build --strict` | Gera o site e falha se houver link quebrado ou aviso. |
| `mkdocs -h` | Mostra a ajuda. |

---

## Como editar a documentação

- Cada página é um arquivo `.md` dentro de `docs/`.
- Para o site exibir a página, ela precisa estar listada em `nav` no `mkdocs.yml`.
- Os links entre páginas usam o caminho do arquivo (`[texto](../arquitetura/visoes.md)`).

### Adicionar uma nova ata

1. Crie `docs/atas-reuniao/ata-reuniao-N.md`.
2. Adicione uma linha na tabela de `docs/atas-reuniao/index.md` (data e texto da ata como link; `{ target="_blank" }` abre em nova aba).
3. Registre o arquivo no `nav` do `mkdocs.yml`.

<!-- # TO-DO: Adicionar as figuras (diagramas) dos documentos de Visão e Arquitetura em docs/assets/ -->

---

## Publicação

O arquivo `.github/workflows/ci.yml` roda a cada push na branch `docs`, executa `mkdocs gh-deploy --force` e publica o site na branch `gh-pages`.

Configuração feita uma única vez no GitHub:

1. Acesse as configurações do repositório e abra a aba **Pages**.
2. Em **Source**, escolha **Deploy from a branch**.
3. Em **Branch**, escolha `gh-pages` e salve.

---

## Estrutura da branch

```text
docs/ (branch)
├── README.md
├── mkdocs.yml                    # Configuração do site (menu, tema, extensões)
├── requirements.txt              # Dependências do MkDocs
├── .gitignore
├── .github/workflows/ci.yml      # Pipeline de deploy
└── docs/                         # Conteúdo do site
    ├── index.md                  # Página inicial
    ├── contribuir.md             # Como editar e publicar
    ├── stylesheets/extra.css     # Paleta preto, branco e cinza
    ├── visao/                    # Documento de Visão (produto, projeto, escopo, métricas, testes)
    ├── arquitetura/              # Documento de Arquitetura (representação, metas, visões)
    └── atas-reuniao/             # Tabela de atas (index.md) e uma página por ata
```

---

## Padrões

- Páginas e comentários em **português**.
- Nomes de arquivos em minúsculas, sem acento, separados por hífen (`ata-reuniao-1.md`).
- Commits no padrão **Conventional Commits** (`tipo(escopo): descrição`), em português e no imperativo. Exemplo: `docs(atas): adiciona ata 4`.

---

## Política de Branches

| Branch | Finalidade |
|---|---|
| `main` | Branch final, onde o produto é entregue. Recebe somente código testado. |
| `sprintN` | Uma branch por sprint, de `sprint1` a `sprint7` (sem hífen). |
| `docs` | Armazena os arquivos de documentação do trabalho (esta branch). |
| `gh-pages` | Usada pelo GitHub Pages para publicar o site. Não deve receber edições manuais. |

---

## Equipe

**Equipe Hamilton - MDS 2026.2 - UnB FCTE/FGA**

Ana Clara Teixeira Guimarães, Arthur Miguel Silva Rocha, Gabriel Sayd de Santana Lombas Macedo, Guilherme Ribeiro Almeida, Henrique Catharino Nunes de Mendonça, Jônatas Maciel da Silva Alves, Letícia da Silva Pereira e Ricieri Artur Vasconcellos Vieira.
