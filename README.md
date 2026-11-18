<div align="center">

[![Visão Geral](https://img.shields.io/badge/Aba-Visão_Geral-1f425f?style=for-the-badge)](README.md)
[![Documentação Detalhada](https://img.shields.io/badge/Aba-Documentação_Detalhada-lightgrey?style=for-the-badge)](DETALHES.md)

</div>

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.1.2-092E20?style=flat&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Celery](https://img.shields.io/badge/Celery-5.7.0-37814A?style=flat&logo=celery&logoColor=white)](https://docs.celeryproject.org/)
[![Redis](https://img.shields.io/badge/Redis-8.1.0-DC382D?style=flat&logo=redis&logoColor=white)](https://redis.io/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat&logo=sqlite&logoColor=white)](https://www.sqlite.org/)

</div>

---

# CoLecture - Sistema de leitura em comunidades

> Projeto desenvolvido para a disciplina de **Métodos de Desenvolvimento de Software (MDS)**
> Universidade de Brasília — FGA | Prof. Ricardo Ajax Dias Kosloski

O **CoLecture** é uma plataforma colaborativa para incentivo e acompanhamento do hábito de leitura. Nela, leitores podem se conectar, criar e participar de comunidades literárias, estabelecer metas individuais e coletivas, interagir em fóruns por livro ou meta, acompanhar sua estante virtual e manter-se motivados por meio de ofensivas diárias (*streaks*), insígnias e lembretes automáticos.

> *"Se quer ir rápido, vá sozinho. Se quer ir longe, vá acompanhado."*

---

> 📖 **Procurando a documentação completa?**
> Para consultar o mapeamento de todas as rotas, estrutura detalhada de apps, gamificação com 35 insígnias, logs de auditoria e arquitetura, acesse a aba **[DETALHES.md](DETALHES.md)** ou a documentação online no **[GitHub Pages](https://fga0138-mds-ajax.github.io/2026.2-T02-Hamilton/)**.

---

## Sumário

- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Como Executar o Projeto Localmente](#como-executar-o-projeto-localmente)
  - [Pré-requisitos](#pré-requisitos)
  - [1. Clonar o repositório](#1-clone-o-repositório)
  - [2. Ambiente virtual](#2-crie-e-ative-o-ambiente-virtual)
  - [3. Instalar dependências](#3-instale-as-dependências)
  - [4. Banco de dados e migrações](#4-configure-o-banco-de-dados)
  - [5. Popular dados de demonstração](#5-popule-o-banco-com-dados-de-demonstração-opcional)
  - [6. Iniciar o servidor](#6-inicie-o-servidor-django)
  - [Administrador padrão](#administrador-padrão)
- [Configuração do Celery e Redis](#configuração-do-celery-e-redis)
  - [1. Iniciar o Redis](#1-inicie-o-redis-broker)
  - [2. Iniciar o Celery Worker](#2-inicie-o-celery-worker)
  - [3. Iniciar o Celery Beat](#3-inicie-o-celery-beat-agendador)
  - [Atalho: Worker + Beat juntos](#atalho-worker--beat-juntos-para-desenvolvimento)
- [Executando os Testes](#executando-os-testes)
- [Equipe](#equipe)
- [Mais Detalhes](#mais-detalhes)

---

## Tecnologias utilizadas

| Tecnologia | Função no Projeto |
| :--- | :--- |
| **Python 3.12+** | Linguagem principal do ecossistema back-end. |
| **Django 6.1.2** | Framework web (MTV): rotas, ORM, autenticação, forms e admin. |
| **SQLite 3** | Banco de dados relacional local (`colecture/db.sqlite3`). |
| **Celery 5.7.0** | Fila de tarefas assíncronas e agendadas em segundo plano. |
| **django-celery-beat 2.1.0** | Agendador periódico integrado ao Django. |
| **Redis 8.1.0** | Broker de mensagens e backend do Celery (`localhost:6379`). |
| **Pillow 13.0.0** | Upload e processamento de capas de livros e avatares. |
| **HTML5, CSS3 & JS** | Front-end responsivo com temas centralizados e scripts modulares. |

---

## Como executar o projeto localmente

### Pré-requisitos

- [Git](https://git-scm.com/)
- [Python 3.12+](https://www.python.org/downloads/)
- [Docker](https://www.docker.com/) (opção mais rápida para o Redis) ou [Redis](https://redis.io/) instalado localmente
- [VS Code](https://code.visualstudio.com/) (recomendado)

---

### 1. Clone o repositório

```bash
git clone https://github.com/FGA0138-MDS-Ajax/2026.2-T02-Hamilton.git
cd 2026.2-T02-Hamilton
```

---

### 2. Crie e ative o ambiente virtual

```bash
python -m venv .venv
```

Ativação conforme o terminal:

| Sistema | Terminal | Comando |
| :--- | :--- | :--- |
| **Linux / macOS** | Bash / Zsh | `source .venv/bin/activate` |
| **Windows** | PowerShell | `.venv\Scripts\Activate.ps1` |
| **Windows** | CMD | `.venv\Scripts\activate.bat` |

---

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

---

### 4. Configure o banco de dados

Entre na pasta do projeto Django:

```bash
cd colecture
python manage.py migrate
```

> O `migrate` cria as tabelas, cadastra automaticamente as **35 insígnias** e gera o **administrador padrão**.

---

### 5. Popule o banco com dados de demonstração (opcional)

Para testar a plataforma com livros reais, usuários, comunidades e ofensivas:

```bash
python manage.py seed_books
python manage.py seed_demo
```

---

### 6. Inicie o servidor Django

```bash
python manage.py runserver
```

Acesse:
- **Aplicação:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Painel Administrativo:** [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

---

### Administrador padrão

Credenciais criadas na primeira migração:

| Campo | Valor padrão | Variável de ambiente para alterar |
| :--- | :--- | :--- |
| **Usuário** | `admin` | `COLECTURE_ADMIN_USERNAME` |
| **E-mail** | `admin@colecture.com` | `COLECTURE_ADMIN_EMAIL` |
| **Senha** | `Admin#Colecture2026` | `COLECTURE_ADMIN_PASSWORD` |

---

## Configuração do Celery e Redis

O **Celery** gerencia tarefas em segundo plano no CoLecture. Sua rotina principal é a **notificação diária às 20h00** (`notify_without_reading`), que avisa usuários que ainda não registraram leitura no dia para não perderem sua sequência (*streak*).

### 1. Inicie o Redis (Broker)

A maneira mais rápida em qualquer sistema operacional é via Docker:

```bash
docker run -d --name colecture-redis -p 6379:6379 redis:alpine
```

*(Ou no Linux/WSL: `sudo service redis-server start`)*

Teste se o Redis está ativo:
```bash
redis-cli ping
# Resposta esperada: PONG
```

---

### 2. Inicie o Celery Worker

Em um novo terminal (com `.venv` ativo e dentro da pasta `colecture/`):

- **Linux / macOS:**
  ```bash
  celery -A colecture worker --loglevel=info
  ```

- **Windows:**
  > [!IMPORTANT]
  > No Windows, adicione obrigatoriamente a flag `-P solo` para compatibilidade de processos:
  ```bash
  celery -A colecture worker -l info -P solo
  ```

---

### 3. Inicie o Celery Beat (Agendador)

Em outro terminal (com `.venv` ativo e dentro de `colecture/`):

```bash
celery -A colecture beat --loglevel=info
```

---

### Atalho: Worker + Beat juntos para desenvolvimento

Em desenvolvimento, você pode rodar ambos em um único processo:

- **Linux / macOS:** `celery -A colecture worker --beat --loglevel=info`
- **Windows:** `celery -A colecture worker --beat -l info -P solo`

> 💡 **Como testar o envio de lembretes agora mesmo?**  
> Veja no [DETALHES.md](DETALHES.md#como-testar-tarefas-do-celery-manualmente-django-shell) como disparar a tarefa sob demanda pelo `python manage.py shell`.

---

## Executando os Testes

Execute a suíte completa de testes automatizados dentro da pasta `colecture/`:

```bash
python manage.py test
```

Ou execute testes de um app específico:

```bash
python manage.py test accounts
python manage.py test notifications
python manage.py test books
```

---

## Equipe

**Equipe Hamilton — MDS 2026.2 — UnB FGA**

| Integrante | Papéis no Projeto |
| :--- | :--- |
| Ana Clara Teixeira Guimarães | **Desenvolvedora**, Engenheira de Dados |
| Arthur Miguel Silva Rocha | **Arquiteto de Software**, Desenvolvedor, Dono do Produto, Analista de Requisitos |
| Gabriel Sayd de Santana Lombas Macedo | **Desenvolvedor**, Analista de Qualidade, Engenheiro de Dados |
| Guilherme Ribeiro Almeida | **Engenheiro de Dados**, Desenvolvedor |
| Henrique Catharino Nunes de Mendonça | **Desenvolvedor**, Arquiteto de Software |
| Jônatas Maciel da Silva Alves | **Analista de Requisitos e Documentação**, Desenvolvedor |
| Letícia da Silva Pereira | **Analista de Qualidade**, Desenvolvedora, Dono do Produto |
| Ricieri Artur Vasconcellos Vieira | **Dono do Produto**, Desenvolvedor, Analista de Qualidade, Engenheiro de Dados |

---

## Mais Detalhes

Para informações técnicas aprofundadas, consulte:

- 📑 **[DETALHES.md](DETALHES.md):** Mapeamento completo de todas as rotas da aplicação, estrutura interna dos apps, sistema das 35 insígnias, trilha de auditoria (logs), rotinas do Celery e políticas de commit e branch.
- 🌐 **[Portal MkDocs no GitHub Pages](https://fga0138-mds-ajax.github.io/2026.2-T02-Hamilton/):** Documento de Visão, Documento de Arquitetura, Atas de Reunião e histórico das Sprints.

---

<div align="center">
  <sub>CoLecture • Métodos de Desenvolvimento de Software • 2026.2 • Universidade de Brasília</sub>
</div>
