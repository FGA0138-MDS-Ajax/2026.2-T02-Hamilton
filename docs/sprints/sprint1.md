# Sprint 1 - Cadastro e Autenticação

## 1. Dados

| Título   | Valor                                                           |
| -------- | --------------------------------------------------------------- |
| Sprint   | 1                                                               |
| Objetivo | Permitir que usuários registrem contas e se façam autenticação. |
| Período  | 08/10/2026 a 15/10/2026                                         |

## 2. Planejamentos e resultados

A Sprint 1 foi dedicada à implementação dos recursos de registro de conta e autenticação, bem como aos controles básicos de admin.

## 3. Requisitos Implementados

O valor esperado de conclusão de cada requisito é de **70%**.

| Requisito | Nome                   | Taxa de Conclusão |
| --------- | ---------------------- | ----------------- |
| R01       | Cadastro e login       | 100%              |
| R02       | Admin editar usuários  | 100%              |
| R03       | Admin inicial via seed | 100%              |
| R04       | Página de login        | 100%              |
| Média     | -                      | 100%              |

## 4. Avaliação da qualidade do Software

| Funcionalidade        | Densidade de Defeitos | Valor máximo de defeitos esperado |
| --------------------- | --------------------- | --------------------------------- |
| Cadastro              | 0,05                  | 0,2                               |
| Login                 | 0                     | 0,2                               |
| Admin editar usuários | 0                     | 0,2                               |

## 5. Cobertura dos testes

Foram testados **4 dos 4 requisitos planejados**, resultando em uma porcentagem de **100%** dos requisitos testados com um valor mínimo de 100%.

**Critério de cobertura:** um requisito é considerado testado quando está associado a um caso de teste do [roteiro de testes](../visao/testes.md#roteiro-de-testes) cujos testes foram executados e aprovados (resultado previsto igual ao realizado). A cobertura é calculada pela métrica [M3](../visao/metricas.md) (requisitos testados ÷ requisitos implementados).

| Requisito | Caso de teste |
| --------- | ------------- |
| R01       | [CT01](../visao/testes.md#ct01) |
| R02       | [CT01](../visao/testes.md#ct01), [CT07](../visao/testes.md#ct07) |
| R03       | [CT01](../visao/testes.md#ct01), [CT07](../visao/testes.md#ct07) |
| R04       | [CT01](../visao/testes.md#ct01) |

## 6. Entregas

**Feature: Cadastro, autenticação e perfil**

- **O que foi feito:** Implementação do fluxo de criação de conta, login, logout e edição de dados do perfil do leitor (`Profile`), com validação de e-mail único e testes unitários do ciclo de vida do usuário.
- **Arquivos/apps:** `accounts/models.py`, `accounts/views.py`, `accounts/forms.py`, `accounts/urls.py`, `accounts/tests.py`
- **Requisito:** R01

**Feature: Gestão administrativa de usuários**

- **O que foi feito:** Configuração do painel administrativo do Django para permitir que administradores consultem, criem, editem e removam contas de usuários e perfis.
- **Arquivos/apps:** `accounts/admin.py`, `colecture/urls.py`, `accounts/tests.py`
- **Requisito:** R02

**Feature: Administrador inicial via seed**

- **O que foi feito:** Criação de migração de dados que provisiona automaticamente o superusuário administrador padrão (`admin`) ao inicializar o banco de dados vazio com `migrate`.
- **Arquivos/apps:** `accounts/migrations/0002_createDefaultAdmin.py`, `colecture/settings.py`
- **Requisito:** R03

**Feature: Páginas de login, cadastro e perfil**

- **O que foi feito:** Desenvolvimento das interfaces responsivas de login, registro de usuário, visualização e edição de perfil, além da página inicial da aplicação.
- **Arquivos/apps:** `accounts/templates/...`, `accounts/static/...`, `main/templates/index.html`
- **Requisito:** R04

