# Sprint 2 - Gestão de catálogo e avaliação de livros

## 1. Dados

| Título   | Valor                         |
| -------- | ----------------------------- |
| Sprint   | 2                             |
| Objetivo | Registro de livro e avaliação |
| Período  | 15/10/2026 a 21/10/2026       |

## 2. Planejamentos e resultados

A Sprint 2 foi dedicada à implementação do catálogo de livros, busca com filtros e avaliações com resenhas (R05 a R08). Todos os recursos de back-end e as páginas principais foram entregues, restando como débito técnico na interface (R08 – 95%) o menu de acesso à edição na página de detalhes do livro e a adaptação visual do formulário `book_form.html` para o modo de edição (título, botão de atualização e redirecionamento para os detalhes da obra).

## 3. Requisitos Implementados

O valor esperado de conclusão de cada requisito é de **70%**.

| Requisito | Nome                                     | Taxa de Conclusão |
| --------- | ---------------------------------------- | ----------------- |
| R05       | Registrar livro inexistente              | 100%              |
| R06       | Pesquisar e filtrar catálogo             | 100%              |
| R07       | Avaliar livros                           | 100%              |
| R08       | Página de registro de livros e avaliação | 95%               |
| Média     |                                          | 98,75%            |

## 4. Avaliação da qualidade do Software

| Funcionalidade                | Densidade de Defeitos | Valor máximo de defeitos esperado |
| ----------------------------- | --------------------- | --------------------------------- |
| Registro de livro             | 0                     | 0,2                               |
| Pesquisa e filtro do catálogo | 0                     | 0,2                               |
| Avaliação de livros           | 0                     | 0,2                               |

## 5. Cobertura dos testes

Foram testados **4 dos 4 requisitos planejados**, resultando em uma porcentagem de **100%** dos requisitos testados com um valor mínimo de 100%.

**Critério de cobertura:** um requisito é considerado testado quando está associado a um caso de teste do [roteiro de testes](../visao/testes.md#roteiro-de-testes) cujos testes foram executados e aprovados (resultado previsto igual ao realizado). A cobertura é calculada pela métrica [M3](../visao/metricas.md) (requisitos testados ÷ requisitos implementados).

| Requisito | Caso de teste |
| --------- | ------------- |
| R05       | [CT02](../visao/testes.md#ct02) |
| R06       | [CT02](../visao/testes.md#ct02) |
| R07       | [CT02](../visao/testes.md#ct02) |
| R08       | [CT02](../visao/testes.md#ct02) |

## 6. Entregas

**Feature: Registro de livros**

- **O que foi feito:** Implementação do modelo `Book` e das views de cadastro, edição e exclusão de livros por usuários autenticados, incluindo validação de ISBN-10/13, gênero, número de páginas, sinopse e capa.
- **Arquivos/apps:** `books/models.py`, `books/forms.py`, `books/views.py`, `books/urls.py`, `books/tests.py`
- **Requisito:** R05

**Feature: Pesquisa e filtro do catálogo**

- **O que foi feito:** Desenvolvimento da busca de livros no banco de dados com filtragem combinada por título, autor, editora e tags de gênero literário, retornando os resultados em JSON para a interface.
- **Arquivos/apps:** `main/views.py`, `books/views.py`, `main/templates/search.html`, `main/static/...`
- **Requisito:** R06

**Feature: Avaliação e resenha de livros**

- **O que foi feito:** Implementação do modelo `BookReview` e do formulário integrado à página de detalhes para atribuição de nota de 1 a 5 estrelas e publicação de resenhas, com cálculo automático da média do livro.
- **Arquivos/apps:** `books/models.py`, `books/forms.py`, `books/views.py`, `books/tests.py`
- **Requisito:** R07

**Feature: Páginas de livros e busca**

- **O que foi feito:** Construção das interfaces de cadastro de livros, pesquisa com filtros e página de detalhes da obra com ficha técnica e listagem de avaliações.
- **Arquivos/apps:** `books/templates/...`, `books/static/...`, `main/templates/search.html`
- **Requisito:** R08

## 7. Débito Técnico

**Feature: Interface de edição de livros**

- **O que foi feito:** Ficou pendente adicionar o menu de acesso à edição na página de detalhes do livro (`book_detail.html`) e adaptar o formulário `book_form.html` para exibir título (`Editar Livro`), descrição e botão (`Atualizar`) dinâmicos no modo de edição, redirecionando para a página de detalhes após salvar.
- **Arquivos/apps:** `books/views.py`, `books/templates/book_detail.html`, `books/templates/book_form.html`
- **Requisito:** R08

