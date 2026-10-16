# Visões da Arquitetura

## Visão de uso

Leitores criam e participam de comunidades, registram o progresso diário, interagem em fóruns, avaliam livros, cadastram obras ausentes do catálogo e recebem recomendações por temas preferidos. Moderadores acompanham os fóruns e removem conteúdo inadequado.

Três características influenciaram a escolha do MTV/Django:

1. O sistema é orientado a páginas e formulários, o que combina com a renderização no servidor.
2. Há perfis distintos (leitor, moderador de comunidade e administrador), atendidos pelas permissões nativas e pelo papel do membro na comunidade.
3. A equipe de oito integrantes já conhece Python e Django.

A funcionalidade mais complexa é o **registro do progresso diário**, que envolve validação e atualização da ofensiva, das metas e das conquistas.

## Visão de organização lógica

- **Página inicial:** acesso às comunidades do usuário, busca de comunidades e usuários, conta e configurações, criação de comunidade ou entrada em uma existente.
- **Comunidade:** fórum de mensagens e informações (nome, data de criação, moderadores, livro ou tema atual e participantes).
- **Perfil:** nome, livro favorito, foto, data de entrada, progresso dos livros em leitura, comunidades, avaliações e marcações "Pretendo Ler", "Já Li", "Em Progresso" e "Não Terminei de Ler". O próprio usuário pode editar seu perfil.

## Visão estrutural

Cada módulo é um app Django independente, com seus próprios models, views, templates e testes.

- **User** concentra as relações: possui um **Profile** (ofensiva pessoal e dados de leitura), metas, conquistas, avaliações, mensagens, notificações, entradas na estante (**ShelfEntry**) e participações em comunidades.
- **Book** recebe tags (**Tag**), é avaliado (**Review**) e registrado na estante.
- **Community** reúne usuários por **Membership**, cujo atributo `role` define leitor ou moderador e cujo `status` indica se a entrada foi aprovada.
- A comunidade tem metas de leitura (**Goal**); cada meta (ciclo) possui seu fórum, formado por tópicos (**Topic**) com mensagens (**Message**).

Cada entidade é um model Django persistido no SQLite, com atributos privados acessados por métodos da própria classe, que concentram as regras de negócio.

## Visão de implantação

O CoLecture roda **apenas em ambiente local**, na máquina de cada integrante, sem hospedagem externa.

| Item | Detalhe |
| ---- | ------- |
| Código | Versionado no GitHub (`git clone` e `git pull`) |
| Ambiente | Ambiente virtual Python (`venv`) com dependências do `requirements.txt` |
| Execução | `python manage.py runserver` |
| Banco | Arquivo `db.sqlite3`, criado por `migrate` e não versionado |
| Estáticos | Servidos pelo servidor de desenvolvimento |
| Acesso | `http://127.0.0.1:8000` |

A arquitetura permanece compatível com uma futura implantação em servidor (Gunicorn, Nginx e PostgreSQL).
