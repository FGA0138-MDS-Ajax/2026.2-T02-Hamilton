# Sprint 2 - Gestão de catálogo e avaliação de livros

## 1. Dados

| Título   | Valor                         |
| -------- | ----------------------------- |
| Sprint   | 2                             |
| Objetivo | Registro de livro e avaliação |
| Período  | 15/10/2026 a 21/10/2026       |

## 2. Planejamentos e resultados

A Sprint 2 foi dedicada à implementação dos recursos de registro de livros e avaliações dos mesmo, tendo um pequeno debito técnico do UI para editar os livros.

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

## 6. Entregas

### Feature: Registro de livros no catálogo

- **O que foi feito:** Implementação do modelo `Book` e do fluxo de cadastro, edição e exclusão de livros por usuários autenticados, incluindo validação de ISBN, gênero, número de páginas, sinopse e capa.
- **Arquivos/apps:** `books/models.py`, `books/forms.py`, `books/views.py`, `books/urls.py`, `books/admin.py`, `books/tests.py`
- **Requisito:** R05

### Feature: Pesquisa e filtragem do catálogo

- **O que foi feito:** Desenvolvimento da busca de livros no banco de dados com filtragem combinada por título, autor, editora e tags de gênero literário.
- **Arquivos/apps:** `main/views.py`, `main/urls.py`, `books/views.py`, `main/templates/main/search.html`, `main/static/main/js/search.js`, `main/static/main/css/search.css`
- **Requisito:** R06

### Feature: Avaliação e resenha de livros

- **O que foi feito:** Implementação do modelo `BookReview` e do formulário para atribuição de nota de 1 a 5 estrelas e publicação de resenhas, com cálculo automático da média de avaliações do livro.
- **Arquivos/apps:** `books/models.py`, `books/forms.py`, `books/views.py`, `books/admin.py`, `books/tests.py`
- **Requisito:** R07

### Feature: Páginas de registro, busca e detalhes de livros

- **O que foi feito:** Construção das interfaces para o formulário de cadastro de livros, página de pesquisa com filtros e página de detalhes da obra com ficha técnica e listagem de avaliações.
- **Arquivos/apps:** `books/templates/books/book_form.html`, `books/templates/books/book_detail.html`, `main/templates/main/search.html`, `books/static/books/css/book_form.css`, `books/static/books/css/book_detail.css`, `books/static/books/js/book_detail.js`
- **Requisito:** R08

