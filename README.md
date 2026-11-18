<div align="center">

[![Visão Geral](https://img.shields.io/badge/Aba-Visão_Geral-1f425f?style=for-the-badge)](README.md)
[![Documentação](https://img.shields.io/badge/Aba-Documentação-lightgrey?style=for-the-badge)](DETALHES.md)

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

O **CoLecture** é uma plataforma colaborativa voltada ao incentivo e acompanhamento do hábito de leitura individual e coletivo. Na plataforma, os usuários podem se conectar, criar ou participar de comunidades temáticas, definir e acompanhar metas de leitura em grupo, debater capítulos em fóruns dedicados, manter sua estante virtual organizada, receber recomendações inteligentes e motivar-se por meio de um sistema de ofensiva diária (*streak*) e conquista de 35 insígnias.

> *"Se quer ir rápido, vá sozinho. Se quer ir longe, vá acompanhado."*

---

## Sumário

- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Como Executar o Projeto Localmente](#como-executar-o-projeto-localmente)
  - [Pré-requisitos](#pré-requisitos)
  - [Passo a passo](#1-clone-o-repositório)
  - [Administrador padrão](#administrador-padrão)
  - [Scripts para popular o banco](#scripts-para-popular-o-banco)
- [Configuração e Execução do Celery e Redis](#configuração-e-execução-do-celery-e-redis)
  - [Visão geral](#por-que-o-celery-é-utilizado)
  - [1. Configurando e iniciando o Redis](#1-configuração-e-execução-do-redis-broker)
  - [2. Executando o Celery Worker](#2-execução-do-celery-worker)
  - [3. Executando o Celery Beat](#3-execução-do-celery-beat-agendador)
  - [4. Executando Worker + Beat juntos em desenvolvimento](#4-executando-worker--beat-juntos-em-desenvolvimento)
  - [5. Como testar tarefas manualmente](#5-como-testar-e-disparar-tarefas-manualmente-django-shell)
- [Sistema de Notificações](#sistema-de-notificações)
- [Sistema de Insígnias](#sistema-de-insígnias-r19)
- [Logs de Auditoria](#logs-de-auditoria)
- [Rotas da Aplicação](#rotas-da-aplicação)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Executando os Testes](#executando-os-testes)
- [Padrões de Código](#padrões-de-código)
- [Política de Branches e Commits](#política-de-branches)
- [Equipe](#equipe)

---

## Tecnologias utilizadas

### Back-end

| Tecnologia | Versão | Uso no Projeto |
| :--- | :--- | :--- |
| [Python](https://www.python.org/) | 3.12+ | Linguagem principal do ecossistema back-end. |
| [Django](https://www.djangoproject.com/) | 6.1.2 | Framework web (padrão MTV): rotas, views, formulários, autenticação de sessão, permissões, painel administrativo e segurança (CSRF, XSS, clickjacking). |
| Django ORM | 6.1.2 | Mapeamento objeto-relacional para todas as entidades e consultas do banco de dados. |
| [SQLite](https://www.sqlite.org/) | 3.x | Banco de dados relacional local (`colecture/db.sqlite3`), gerenciado estritamente por migrations. |
| [Celery](https://docs.celeryproject.org/) | 5.7.0 | Fila distribuída de tarefas assíncronas e agendadas em segundo plano. |
| [django-celery-beat](https://django-celery-beat.readthedocs.io/) | 2.1.0 | Extensão para agendamento periódico de tarefas com integração ao Django. |
| [Redis](https://redis.io/) | 8.1.0 (client) | Message Broker e Result Backend do Celery (`redis://localhost:6379/0`). |
| [Pillow](https://python-pillow.org/) | 13.0.0 | Manipulação e validação de imagens (capas de livros e avatares) enviadas via `media/`. |
| Django Forms | 6.1.2 | Validação e sanitização de dados de entrada antes do processamento nas views. |
| Django TestCase | 6.1.2 | Suite de testes unitários e de integração automatizados. |

### Front-end

| Tecnologia | Uso no Projeto |
| :--- | :--- |
| Templates do Django | Renderização de páginas HTML dinâmicas no servidor. |
| HTML5 & CSS3 | Estrutura semântica e estilos modernos, com layout responsivo via flexbox/grid e cores padronizadas em `main/static/main/css/variables.css`. |
| JavaScript (ES6+) | Comportamento dinâmico da interface (estante, cronômetro de leitura, busca, moderação, modais e notificações), modularizado por app em `static/<app>/js/`. |
| [Boxicons](https://boxicons.com/) | Conjunto de ícones vetoriais da interface, importados via CDN. |
| [Google Fonts](https://fonts.google.com/) (Poppins) | Tipografia principal da plataforma, importada via CDN. |

> **Nota de conectividade:** Os ícones e a tipografia utilizam CDN. Em caso de execução totalmente offline, o sistema funciona perfeitamente com fontes nativas do sistema operacional.

---

## Como executar o projeto localmente

O CoLecture foi desenvolvido para execução local. Siga o passo a passo abaixo para configurar o ambiente do zero.

### Pré-requisitos

- [Git](https://git-scm.com/)
- [Python 3.12+](https://www.python.org/downloads/)
- [Docker](https://www.docker.com/) ou [Redis](https://redis.io/) instalado (necessário para a fila de tarefas do Celery; o restante da navegação básica pode rodar sem ele).
- [VS Code](https://code.visualstudio.com/) (recomendado)

---

### 1. Clone o repositório

```bash
git clone https://github.com/FGA0138-MDS-Ajax/2026.2-T02-Hamilton.git
cd 2026.2-T02-Hamilton
```

---

### 2. Crie e ative o ambiente virtual

Crie o ambiente virtual `.venv`:

```bash
python -m venv .venv
```

Ative o ambiente virtual conforme o seu sistema operacional e terminal:

| Sistema Operacional | Terminal / Shell | Comando |
| :--- | :--- | :--- |
| **Linux / macOS** | Bash / Zsh | `source .venv/bin/activate` |
| **Linux** | Fish | `source .venv/bin/activate.fish` |
| **Windows** | PowerShell | `.venv\Scripts\Activate.ps1` |
| **Windows** | Prompt de Comando (CMD) | `.venv\Scripts\activate.bat` |

> Quando o ambiente virtual estiver ativo, o prefixo `(.venv)` será exibido no início da linha do terminal.

---

### 3. Instale as dependências

Certifique-se de que o `.venv` está ativo e instale todos os pacotes:

```bash
pip install -r requirements.txt
```

---

### 4. Configure o banco de dados

Navegue até a pasta da aplicação Django (`colecture/`):

```bash
cd colecture
```

Execute as migrations para gerar o esquema de dados:

```bash
python manage.py migrate
```

O comando `migrate` realiza automaticamente:
1. A criação de todas as tabelas do sistema.
2. A criação do **administrador padrão** inicial (`accounts/migrations/0002_createDefaultAdmin.py`).
3. O cadastro das **35 insígnias** do sistema (`rewards/migrations/0004_seed_insignias.py`).

---

### 5. (Opcional) Popule o banco com dados de demonstração

Para explorar a plataforma já com livros reais, usuários, ofensivas, comunidades ativas e mensagens de fórum, execute:

```bash
python manage.py seed_books
python manage.py seed_demo
```

---

### 6. Inicie o servidor Django

```bash
python manage.py runserver
```

Abra o seu navegador e acesse:
- **Aplicação:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Painel Administrativo:** [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

---

### Administrador padrão

Ao rodar a primeira migração em um banco vazio, o administrador padrão é criado automaticamente com as seguintes credenciais:

| Campo | Valor padrão | Variável de ambiente para sobrescrever |
| :--- | :--- | :--- |
| **Usuário** | `admin` | `COLECTURE_ADMIN_USERNAME` |
| **E-mail** | `admin@colecture.com` | `COLECTURE_ADMIN_EMAIL` |
| **Senha** | `Admin#Colecture2026` | `COLECTURE_ADMIN_PASSWORD` |

> Caso deseje utilizar outras credenciais, configure as variáveis de ambiente indicadas **antes** do primeiro `python manage.py migrate`. Se o usuário já existir no banco, a migração não o substituirá. Você também pode criar superusuários adicionais a qualquer momento via `python manage.py createsuperuser`.

---

### Scripts para popular o banco

Os comandos de carga e manutenção ficam localizados nos diretórios `management/commands/` de seus respectivos apps e devem ser executados a partir da pasta `colecture/`. Todos são idempotentes (podem ser executados repetidamente sem gerar duplicatas):

| Comando | App | Finalidade |
| :--- | :--- | :--- |
| `python manage.py seed_books` | `books` | Popula o catálogo com livros reais (o ISBN é utilizado como chave única). |
| `python manage.py seed_demo` | `books` | Cria 5 usuários de demonstração, 2 comunidades (uma pública e uma privada), mensagens de fórum, metas individuais e coletivas e ofensivas ativas. |
| `python manage.py seed_insignias` | `rewards` | Atualiza ou recarrega as 35 insígnias oficiais com base nas definições de requisitos. |
| `python manage.py purge_archived_communities` | `communities` | Exclui permanentemente comunidades que estejam arquivadas há mais de 60 dias. |

#### Opções do `seed_books`

```bash
python manage.py seed_books              # Insere os livros que ainda não constam no banco
python manage.py seed_books --no-covers  # Insere os livros sem associar URLs de capas
python manage.py seed_books --update     # Atualiza os dados de livros já existentes com mesmo ISBN
```

#### Opções do `seed_demo`

```bash
python manage.py seed_demo
python manage.py seed_demo --password MinhaSenhaCustomizada#123
```

**Dados criados pelo `seed_demo`:**
- **5 Usuários de Teste** (todos com a senha padrão `Senha#123`):
  - `ana`: Criadora da comunidade pública; ofensiva ativa de 5 dias lendo *Duna*.
  - `bruno`: Criador da comunidade privada; moderador da comunidade pública.
  - `carla`: Moderadora da comunidade privada; membro da comunidade pública.
  - `diego`: Membro de ambas as comunidades.
  - `elisa`: Membro da comunidade pública com solicitação pendente na privada.
- **2 Comunidades**:
  - *Clube da Ficção Científica* (Pública | Livro: *Duna* | Meta: 500 páginas em grupo).
  - *Círculo dos Clássicos de Fantasia* (Privada | Livro: *O Hobbit* | Meta: 10 horas de leitura em grupo).
- **Fóruns e Metas**: Fóruns com mensagens reais de debate e metas sincronizadas.

---

## Configuração e Execução do Celery e Redis

### Por que o Celery é utilizado?

No CoLecture, o **Celery** é o mecanismo responsável pelo processamento assíncrono e agendamento de tarefas em segundo plano. Ele opera em conjunto com o **Redis** (Message Broker) e o **django-celery-beat** (Agendador Periódico).

A principal rotina agendada do sistema é:
- **`notifications.tasks.notify_without_reading`**: Tarefa executada diariamente às **20h00** (horário de Brasília). Ela analisa todos os usuários do banco que ainda não registraram sessões de leitura (`ReadingSession`) no dia atual e envia uma notificação no sino do usuário: *"Você já leu hoje? Não se esqueça de registrar sua leitura diária!"*, ajudando a preservar a sequência de dias consecutivos (*streak*).

```
                      +-------------------+
                      |    Celery Beat    | (Agendador diário às 20h00)
                      +---------+---------+
                                | Envia tarefa programada
                                v
+-------------+       +-------------------+       +--------------------+
|   Django    | ----> |   Redis Broker    | ----> |   Celery Worker    |
| Application |       | (localhost:6379)  |       | (Processa tarefas) |
+-------------+       +-------------------+       +---------+----------+
                                                            |
                                                            v
                                                  +--------------------+
                                                  | Notificações / BD  |
                                                  +--------------------+
```

---

### 1. Configuração e execução do Redis (Broker)

O Celery requer um broker Redis ativo escutando na porta padrão `6379`. Escolha a forma de execução mais conveniente para o seu ambiente:

#### Opção A: Via Docker (Recomendada para qualquer sistema)

Se tiver o Docker instalado, basta rodar:

```bash
docker run -d --name colecture-redis -p 6379:6379 redis:alpine
```

Comandos úteis para gerenciar o container:
- Iniciar container existente: `docker start colecture-redis`
- Parar container: `docker stop colecture-redis`
- Ver status: `docker ps`

#### Opção B: No Windows via WSL2 (Ubuntu / Debian)

No terminal WSL:

```bash
sudo apt update && sudo apt install redis-server -y
sudo service redis-server start
```

#### Opção C: No Linux nativo (Ubuntu / Debian)

```bash
sudo apt update && sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### Opção D: No macOS via Homebrew

```bash
brew install redis
brew services start redis
```

#### Testando a conexão com o Redis

Para garantir que o Redis está rodando e aceitando conexões locais:

```bash
redis-cli ping
```

> **Retorno esperado:** `PONG`

---

### 2. Execução do Celery Worker

Abra um novo terminal, ative o ambiente virtual `.venv` e entre na pasta `colecture/`:

```bash
cd colecture
```

Execute o comando conforme o seu sistema operacional:

#### No Linux ou macOS:

```bash
celery -A colecture worker --loglevel=info
```

#### No Windows:

> [!IMPORTANT]
> No Windows, o Celery possui incompatibilidade com o pool multiprocesso padrão (`prefork`) devido à ausência nativa da chamada de sistema `fork()`. Portanto, **no Windows é obrigatório utilizar o pool `solo`** adicionando a flag `-P solo`:

```bash
celery -A colecture worker -l info -P solo
```

Você verá nos logs o Celery conectando-se ao broker `redis://localhost:6379/0` e descobrindo a tarefa `notifications.tasks.notify_without_reading`.

---

### 3. Execução do Celery Beat (Agendador)

O **Celery Beat** monitora os agendamentos definidos em `CELERY_BEAT_SCHEDULE` e despacha as tarefas para a fila no horário correto.

Abra outro terminal, ative o `.venv`, entre em `colecture/` e execute:

```bash
cd colecture
celery -A colecture beat --loglevel=info
```

---

### 4. Executando Worker + Beat juntos em desenvolvimento

Para facilitar o desenvolvimento local sem precisar abrir vários terminais dedicados, você pode executar o Worker e o Beat combinados em um único processo:

- **Linux / macOS:**
  ```bash
  cd colecture
  celery -A colecture worker --beat --loglevel=info
  ```

- **Windows:**
  ```bash
  cd colecture
  celery -A colecture worker --beat -l info -P solo
  ```

---

### 5. Como testar e disparar tarefas manualmente (Django Shell)

Você não precisa esperar o relógio bater 20h00 para verificar se as tarefas e notificações estão funcionando. É possível disparar a rotina manualmente pelo Django Shell.

Com o terminal aberto em `colecture/`:

```bash
python manage.py shell
```

No terminal interativo do Python:

```python
# Importa a tarefa do app notifications
from notifications.tasks import notify_without_reading

# Opção 1: Execução SÍNCRONA imediata (direto no processo do shell, sem precisar do Redis/Worker)
notify_without_reading()

# Opção 2: Execução ASSÍNCRONA via Celery (requer Redis e Celery Worker ativos)
resultado = notify_without_reading.delay()
print("ID da tarefa:", resultado.id)
print("Status:", resultado.status)
```

**O que verificar após executar:**
1. A tarefa verifica se o usuário logado leu hoje. Se não houver sessão de leitura registrada na data de hoje e ele ainda não tiver recebido o aviso hoje, um registro `Notification` é gravado no banco de dados.
2. Acesse a aplicação no navegador em [http://127.0.0.1:8000](http://127.0.0.1:8000):
   - O ícone do sino na barra lateral exibirá o indicador visual de mensagem pendente.
   - O histórico pode ser consultado em `/notifications/history/`.

---

## Sistema de Notificações

O app `notifications` gerencia alertas visuais, avisos de moderação e lembretes aos usuários.

### Como funciona na interface

- **Sino na barra lateral / cabeçalho:** Exibe um contador de mensagens não lidas (`unread_notifications_count`). Ao clicar, um dropdown exibe os alertas mais recentes.
- **Histórico Completo (`/notifications/history/`):** Permite revisar todas as notificações recebidas, com filtros de lidas/não lidas e botão para dispensar.
- **Marcação Automática:** Ao abrir a página de histórico ou clicar no menu, as notificações são marcadas como lidas (`is_read=True`) via AJAX.
- **Ocultação e Exclusão:** É possível ocultar um card do dropdown rápido ou excluí-lo permanentemente do histórico.

### Tipos de notificações disparadas

1. **Lembrete de Leitura / Ofensiva:** Disparado pelo Celery Beat às 20h00 ou na primeira visita do dia ao perfil caso a ofensiva do usuário esteja em risco.
2. **Registro de Leitura:** Emite notificação de confirmação e resumo de páginas/tempo computados na estante.
3. **Comunidades e Moderação:** Notifica o usuário imediatamente quando:
   - Sua solicitação de entrada em comunidade privada é aprovada.
   - Seu cargo é alterado (promovido a moderador ou rebaixado a membro comum).
   - O usuário sofre banimento de uma comunidade.

---

## Sistema de Insígnias (R19)

O CoLecture conta com **35 insígnias** ativas (numeradas de 1 a 36, tendo sido a 18 descontinuada pela equipe).

- **Onde visualizar:** No card do perfil (`/user/profile/`) e na galeria completa dividida por categorias em `/rewards/insignias/`.
- **Conquista em tempo real:** Triggers e services do sistema verificam as condições após ações do usuário (registrar leitura, atingir dias de ofensiva, concluir meta, cadastrar resenhas, fundar comunidades) e concedem a insígnia instantaneamente através da tabela `Award`.

### Categorias de Insígnias

| Categoria | Insígnias | Tema / Representação | Variável CSS |
| :--- | :--- | :--- | :--- |
| **Ofensiva pessoal** | 1 a 8 | Sequência diária ininterrupta de leitura (chama) | `--cat-streak` |
| **Livros lidos** | 9 a 14 | Total de volumes marcados como concluídos | `--cat-books` |
| **Progresso diário** | 15 a 17 | Volume de páginas lidas em um único dia | `--cat-pages` |
| **Horas de leitura** | 19 a 24 | Horas totais acumuladas em sessões | `--cat-hours` |
| **Metas individuais** | 25 a 29 | Metas pessoais atingidas | `--cat-goal` |
| **Metas de comunidade**| 30 a 33 | Metas coletivas cumpridas e liderança | `--cat-community-goal` |
| **Social e Avaliações**| 34 e 35 | Mensagens em fóruns e resenhas avaliativas | `--cat-social` |
| **Especiais** | 36 | Insígnia Fênix (recuperação de hábito) | `--cat-special` |

Os ícones vetoriais estão localizados em `rewards/static/rewards/img/insignias/` no formato `insignia-<id>-<slug>.svg`.

---

## Logs de Auditoria

O app `logs` fornece rastreabilidade completa das ações de usuários e da administração no sistema, gravando registros imutáveis de auditoria (`AuditLog`).

- **Acesso restrito:** Exclusivo para usuários com permissão de superusuário (`is_superuser=True`). O link fica visível diretamente na barra lateral de navegação do administrador.
- **Segurança de dados:** A exclusão ou edição de logs é auditada, gravando snapshots do estado anterior em `metadata["changes"]` ou `metadata["deleted_log"]`.

### Principais eventos auditados

- Criação, edição, arquivamento, desarquivamento e exclusão de comunidades.
- Entrada de membros, pedidos de ingresso aprovados/rejeitados, alteração de cargos (promover/rebaixar) e banimentos.
- Exclusão de mensagens em fóruns de discussão.
- Exclusão e manutenção manual de registros de logs de auditoria.

---

## Rotas da Aplicação

Todas as rotas são relativas a `http://127.0.0.1:8000`. Endpoints protegidos exigem autenticação ativa.

### Páginas gerais (`main`)

| Rota | Descrição | Acesso |
| :--- | :--- | :--- |
| `/` | Página inicial (redireciona para o perfil se o usuário estiver logado) | Público |
| `/search` | Página de busca global de livros e comunidades | Público |
| `/admin/` | Painel administrativo nativo do Django | Administrador |

### Contas e Perfil (`/user/`)

| Rota | Descrição | Acesso |
| :--- | :--- | :--- |
| `/user/register/` | Cadastro de novos usuários | Público |
| `/user/login/` | Autenticação no sistema | Público |
| `/user/logout/` | Encerramento de sessão (POST) | Autenticado |
| `/user/profile/` | Página de perfil do leitor, ofensiva e estante | Autenticado |
| `/user/profile/editProfile/` | Edição de informações cadastrais e bio | Autenticado |
| `/user/streak/` | Calendário mensal de histórico da ofensiva | Autenticado |
| `/user/streak/<day>/` | Detalhamento das leituras de um dia específico | Autenticado |

### Notificações (`/notifications/`)

| Rota | Descrição | Acesso |
| :--- | :--- | :--- |
| `/notifications/` | Retorna lista de notificações do usuário logado (JSON para o sino) | Autenticado |
| `/notifications/history/` | Página com o histórico completo de notificações recebidas | Autenticado |
| `/notifications/mark-read/` | Marca todas as notificações pendentes como lidas (POST) | Autenticado |
| `/notifications/<id>/hide/` | Oculta uma notificação do pop-up rápido do sino (POST) | Autenticado |
| `/notifications/<id>/dismiss/` | Exclui definitivamente uma notificação do histórico (POST) | Autenticado |

### Livros e Leitura (`/books/`)

| Rota | Descrição | Acesso |
| :--- | :--- | :--- |
| `/books/search/` | Busca filtrada no catálogo de livros | Público |
| `/books/<id>/` | Ficha técnica do livro, resenhas e avaliações | Público |
| `/books/register/` | Cadastro de novo livro no catálogo | Autenticado |
| `/books/<id>/edit/` | Edição dos dados de um livro | Criador do livro ou Admin |
| `/books/<id>/delete/` | Exclusão de um livro do catálogo | Criador do livro ou Admin |
| `/books/shelf/` | Gerenciamento da estante do leitor (Lendo, Lidos, Quero Ler, etc.) | Autenticado |
| `/books/shelf/<id>/mark-read/` | Marcar livro da estante como concluído (POST) | Autenticado |
| `/books/shelf/<id>/progress/` | Salvar progresso de páginas/porcentagem (POST) | Autenticado |
| `/books/shelf/<id>/session/` | Registrar sessão de leitura avulsa (POST) | Autenticado |
| `/books/shelf/<id>/sessions/` | Listar sessões de leitura vinculadas a um livro | Autenticado |
| `/books/shelf/<id>/sessions/<session_id>/` | Editar dados de uma sessão de leitura (POST/PATCH) | Autenticado |
| `/books/lookup/` | Consulta rápida de livros em JSON (autocomplete) | Autenticado |
| `/books/reading/` | Interface com cronômetro para sessão de leitura ativa | Autenticado |
| `/books/reading/register/` | Formulário para registrar leitura finalizada | Autenticado |

### Comunidades (`/communities/`)

| Rota | Descrição | Acesso |
| :--- | :--- | :--- |
| `/communities/` | Painel de comunidades do usuário e feed de exploração | Autenticado |
| `/communities/search/` | Busca de comunidades por nome ou tema | Público |
| `/communities/create/` | Criação de uma nova comunidade | Autenticado |
| `/communities/join-by-code/` | Entrada em comunidade privada via código de convite | Autenticado |
| `/communities/<id>` | Página principal da comunidade e detalhes | Autenticado |
| `/communities/<id>/forum/` | Redirecionamento para o fórum geral da comunidade | Membro |
| `/communities/<id>/join` | Solicitar entrada ou entrar diretamente | Autenticado |
| `/communities/<id>/join/<invitation_code>` | Aceite de convite com link codificado | Autenticado |
| `/communities/<id>/leave` | Sair da comunidade | Membro |
| `/communities/<id>/generate_invitation_code` | Gerar novo código de convite compartilhável (JSON) | Criador, Moderador ou Admin |
| `/communities/<id>/manage/` | Painel de gestão e moderação de membros | Criador, Moderador ou Admin |
| `/communities/<id>/edit/` | Edição dos dados e regras da comunidade | Criador, Moderador ou Admin |
| `/communities/<id>/archive/` | Arquivar comunidade | Criador, Moderador ou Admin |
| `/communities/<id>/unarchive/` | Desarquivar comunidade | Criador, Moderador ou Admin |
| `/communities/<id>/delete/` | Exclusão definitiva da comunidade (POST) | Criador ou Admin |
| `/communities/<id>/members/<id>/role/` | Promover a moderador ou rebaixar a membro | Criador ou Admin |
| `/communities/<id>/members/<id>/request/` | Aprovar ou recusar solicitação de ingresso | Criador, Moderador ou Admin |
| `/communities/<id>/members/<id>/ban/` | Banir ou desbanir membro | Criador, Moderador ou Admin |

### Metas (`/goals/`)

| Rota | Descrição | Acesso |
| :--- | :--- | :--- |
| `/goals/create/` | Criar meta individual de leitura | Autenticado |
| `/goals/create/community/<community_id>/` | Criar meta coletiva para uma comunidade | Moderador ou Admin |
| `/goals/<id>/forum/` | Fórum de debate específico daquela meta | Participante |
| `/goals/<id>/edit/` | Edição de prazos e objetivos da meta | Criador da meta |
| `/goals/<id>/delete/` | Exclusão de meta individual (POST) | Dono da meta |
| `/goals/<id>/join/` | Participar de uma meta coletiva (POST) | Membro da comunidade |
| `/goals/<id>/leave/` | Sair de uma meta coletiva (POST) | Participante |
| `/goals/<id>/conclude/` | Concluir meta atingida (POST) | Criador da meta |

### Fóruns (`/forums/`)

| Rota | Descrição | Acesso |
| :--- | :--- | :--- |
| `/forums/<id>` | Visualização de tópicos e envio de mensagens | Membro autorizado |
| `/forums/<id>/edit` | Editar título ou configurações do fórum | Moderador ou Admin |
| `/forums/messages/<id>/delete/` | Excluir mensagem do fórum | Autor ou Moderador |

### Insígnias (`/rewards/`)

| Rota | Descrição | Acesso |
| :--- | :--- | :--- |
| `/rewards/insignias/` | Galeria completa de insígnias conquistadas e bloqueadas | Autenticado |

### Auditoria e Logs (`/logs/`)

| Rota | Descrição | Acesso |
| :--- | :--- | :--- |
| `/logs/` | Listagem com filtros avançados e paginação de auditoria | Administrador |
| `/logs/<id>/` | Detalhes completos e metadados de uma ação auditada | Administrador |
| `/logs/<id>/edit/` | Ajustar notas de um registro de auditoria | Administrador |
| `/logs/<id>/delete/` | Exclusão de registro de auditoria com rastreio reverso (POST) | Administrador |

---

## Estrutura do Projeto

A aplicação adota a arquitetura modular nativa do Django, separando responsabilidades em apps especializados:

```text
2026.2-T02-Hamilton/
├── README.md                          # Visão geral, guia de execução e arquitetura
├── DETALHES.md                        # Portal de documentação detalhada
├── requirements.txt                   # Dependências do Python (Django, Celery, Redis, etc.)
├── .gitignore
└── colecture/                         # Diretório raiz da aplicação Django
    ├── manage.py                      # Utilitário CLI do Django
    ├── colecture/                     # Configurações globais do projeto
    │   ├── __init__.py                # Inicialização do Celery app
    │   ├── settings.py                # Configurações, apps, banco, Celery Beat e rotas
    │   ├── urls.py                    # Roteamento global (URLconf)
    │   ├── celery.py                  # Instância da aplicação Celery
    │   ├── asgi.py
    │   └── wsgi.py
    ├── media/                         # Armazenamento local de uploads de capas e fotos
    ├── main/                          # Páginas públicas (home, busca) e layout compartilhado
    │   ├── views.py
    │   ├── urls.py
    │   ├── templates/main/            # sidebar.html, index.html, search.html
    │   └── static/main/               # css/, js/ e assets de branding
    ├── accounts/                      # Gerenciamento de usuários, perfil e ofensiva
    │   ├── models.py                  # Profile (streak, última leitura, avatar)
    │   ├── services.py                # AccountService
    │   ├── forms.py                   # LoginForm, RegistrationForm, EditUserForm
    │   ├── views.py                   # Telas de login, registro, perfil e calendário
    │   └── templates/accounts/
    ├── books/                         # Catálogo de livros, estante e sessões
    │   ├── models.py                  # Book, BookReview, BookStatus, ReadingSession
    │   ├── services.py                # Recomendações (scores), sessões e cálculo de progresso
    │   ├── forms.py                   # BookForm, ReadingSessionForm
    │   ├── views.py                   # Estante, cronômetro, cadastro e listagem
    │   ├── management/commands/       # seed_books, seed_demo
    │   └── templates/books/
    ├── communities/                   # Comunidades de leitura e moderação
    │   ├── models.py                  # Community, Membership, Invitation
    │   ├── services.py                # MembershipService, CommunityService
    │   ├── views.py                   # Gestão de membros, banimentos e convites
    │   ├── management/commands/       # purge_archived_communities
    │   └── templates/communities/
    ├── goals/                         # Metas individuais e coletivas
    │   ├── models.py                  # Goal, GoalParticipation
    │   ├── services.py                # GoalService
    │   ├── signals.py                 # Sincronização automática de participações
    │   └── templates/goals/
    ├── forums/                        # Fóruns de comunidades e metas
    │   ├── models.py                  # Forum, Message
    │   ├── services.py                # ForumService
    │   └── templates/forums/
    ├── notifications/                 # Sistema de notificações e tarefas periódicas
    │   ├── models.py                  # Notification
    │   ├── services.py                # create_notification helper
    │   ├── tasks.py                   # notify_without_reading (Celery Task)
    │   ├── views.py                   # Listagem JSON, histórico, dismiss e marcação de leitura
    │   └── templates/notifications/   # history.html
    ├── rewards/                       # Sistema de gamificação e 35 insígnias
    │   ├── models.py                  # Insignia, Award, CriteriaType
    │   ├── services.py                # Triggers de concessão automática (check_*)
    │   ├── selectors.py               # Agrupamento e status de desbloqueio
    │   ├── management/commands/       # seed_insignias
    │   ├── static/rewards/img/insignias/ # Ícones vetoriais em SVG
    │   └── templates/rewards/
    └── logs/                          # Trilha de auditoria e segurança
        ├── models.py                  # AuditLog
        ├── services.py                # create_log, log_edit, delete_log
        ├── forms.py                   # AuditLogFilterForm, AuditLogForm
        ├── views.py                   # Visualização tabular, detalhe e edição de logs
        └── templates/logs/
```

---

## Executando os Testes

A suíte de testes unitários e de integração utiliza o framework de testes integrado do Django.

Para rodar todos os testes do projeto:

```bash
cd colecture
python manage.py test
```

Para rodar testes de um app específico:

```bash
python manage.py test accounts       # Testes de autenticação e ofensiva
python manage.py test books          # Testes de livros, estante e sessões
python manage.py test communities    # Testes de comunidades e moderação
python manage.py test goals          # Testes de metas coletivas e individuais
python manage.py test forums         # Testes de mensagens e fóruns
python manage.py test notifications  # Testes de alertas e tasks do Celery
python manage.py test rewards        # Testes de concessão de insígnias
python manage.py test logs           # Testes da trilha de auditoria
```

---

## Padrões de Código

Conforme estabelecido nas restrições de arquitetura do projeto:

- **Arquitetura MTV:** O modelo (M) concentra dados e lógica; os templates (T) renderizam interfaces sem lógica pesada; as views (V) coordenam as requisições.
- **Regras nos Models e Services:** Regras de negócio essenciais são implementadas em classes de serviço (`services.py`) ou métodos de model, permitindo testes rápidos e isolados.
- **Formulários Padronizados:** Validação obrigatória de dados de entrada via Django Forms.
- **Convenção de Idioma:** Código fonte (nomes de variáveis, funções, classes, campos de banco e rotas) padronizado em **inglês**; comentários, documentação e interface de usuário em **português (pt-br)**.
- **Migrações Controladas:** O banco de dados nunca é alterado manualmente; toda mudança de schema é realizada exclusivamente por migrações versionadas do Django.

---

## Política de Branches

O fluxo de trabalho adota o modelo de branches por sprint:

| Branch | Finalidade |
| :--- | :--- |
| `main` | Branch principal de entrega em produção. Recebe somente código testado e revisado. |
| `sprintN` | Branches de integração das sprints (`sprint1`, `sprint2`, ..., `sprint7`), onde as features da sprint são unificadas. |
| `docs` | Branch dedicada à documentação técnica e site MkDocs. |
| `gh-pages` | Branch gerenciada pelo GitHub Pages para publicação da documentação online. |

### Fluxo de Trabalho

1. O desenvolvimento das tarefas da sprint ocorre na respectiva branch `sprintN` ou em branch de feature derivada dela (ex: `feat/nome-da-feature`).
2. Pull requests são submetidos para revisão dos pares e do Dono do Produto.
3. Ao término de cada sprint e após a validação completa da suíte de testes, a branch `sprintN` é mergeada na `main`.

---

## Política Padrão de Commits

O projeto adota o padrão **Conventional Commits**:

```text
tipo(escopo-opcional): descrição no imperativo
```

**Exemplo:** `feat(notifications): implementa alerta diário de ofensiva via Celery`

| Prefixo | Significado |
| :--- | :--- |
| `feat` | Nova funcionalidade implementada |
| `fix` | Correção de bug ou falha de comportamento |
| `docs` | Alterações em arquivos de documentação |
| `style` | Ajustes visuais ou formatação de código sem impacto na lógica |
| `refactor` | Refatoração de código sem alteração funcional |
| `test` | Inclusão ou ajuste de testes automatizados |
| `chore` | Tarefas de manutenção, configurações ou build |
| `perf` | Melhorias focadas em desempenho |
| `ci` | Ajustes em arquivos de integração contínua (GitHub Actions) |

**Regras:**
- Mensagem no **imperativo** em português: *"adiciona"*, *"corrige"*, *"atualiza"*.
- Prefixo (`feat`, `fix`, etc.) em inglês.
- Espaço obrigatório após os dois-pontos: `feat(books): adiciona busca`.

---

## Equipe

**Equipe Hamilton — MDS 2026.2 — UnB FGA**

Papéis definidos no Documento de Visão do Produto. Em **negrito**, a responsabilidade primária de cada membro. Todos os integrantes atuam ativamente como desenvolvedores do sistema.

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

<div align="center">
  <sub>CoLecture • Métodos de Desenvolvimento de Software • 2026.2 • Universidade de Brasília</sub>
</div>
