# Representação Arquitetural

Resumo do documento *CoLecture: Arquitetura do Produto de Software* (Grupo Hamilton, 2026, versão 1.1).

## Propósito e escopo

Descreve as decisões arquiteturais, tecnologias e restrições do CoLecture, como referência para implementação e manutenção. O sistema é uma plataforma web de leitura social, com cadastro de usuários e livros, comunidades e fóruns, progresso e ofensiva, metas individuais e coletivas, avaliações, conquistas e controle de conteúdo por nível de acesso.

## Glossário

| Termo | Definição |
| ----- | --------- |
| Comunidade | Grupo de usuários que leem e discutem o mesmo livro ou tema. Substitui "grupo", "sala" e "sala de leitura" |
| Leitor | Usuário autenticado comum |
| Moderador | Usuário com permissão para remover conteúdo e gerenciar as comunidades que modera |
| Administrador | Usuário distinto do leitor, que gerencia comunidades, usuários e livros |
| Ofensiva | Número de dias consecutivos em que o leitor registrou progresso de leitura |
| MTV | Model-Template-View, variação do MVC adotada pelo Django |

## Estilo arquitetural

Monolítico em camadas, cliente-servidor. O Django organiza a aplicação no padrão **MTV (Model-Template-View)**, de base conceitual MVC. O roteador de URLs (URLconf) cumpre parte do papel do controller, e a View concentra o tratamento das requisições.

- **Model:** entidades do domínio, persistência e regras de negócio como métodos (média de avaliações, contagem da ofensiva, progresso de uma meta). Entidades: User, Profile, Book, Tag, Review, ShelfEntry, Community, Membership, Goal, Topic, Message, Achievement e Notification.
- **Template:** interface gráfica (HTML, CSS e JavaScript): login, catálogo, página de leitura e página da comunidade.
- **View:** recebe as requisições HTTP, valida a entrada (Django Forms), consulta ou altera os Models e renderiza o Template.

Fluxo de uma requisição: navegador → roteador de URLs → View → Model → Template → HTML ao navegador.

## Justificativa da escolha

1. **Experiência da equipe** com Python e Django, reduzindo a curva de aprendizado.
2. **Recursos nativos** do Django: autenticação, permissões, painel administrativo, proteção contra CSRF e ORM para o SQLite.
3. **Separação em camadas**, que permite aos oito integrantes trabalhar em paralelo em templates, views/forms e models.
4. **Aderência às metas:** renderização no servidor e ORM atendem à meta de desempenho com baixa complexidade.

## Elementos do estilo

| Elemento | Responsabilidade | Regras de uso |
| -------- | ---------------- | ------------- |
| Navegador | Interface com o usuário; envia requisições e exibe HTML | Layout adaptativo |
| URLs (`urls.py`) | Mapear rotas para views | Toda rota exposta deve estar mapeada; rotas protegidas exigem login |
| View (`views.py`) | Validar a requisição, acionar os models e escolher o template | Sem SQL direto (usa o ORM); regras de negócio nos models; entradas validadas com Django Forms |
| Model (`models.py`) | Entidades do domínio, regras de negócio e persistência | Esquema alterado somente por migrations; regras testáveis sem requisição HTTP |
| Template | Apresentar dados em HTML, CSS e JavaScript | Sem regra de negócio, apenas lógica de exibição |
| Banco de dados (SQLite) | Armazenamento persistente | Acesso apenas via ORM |

!!! note
    "Template (Visão)" e "View (Controle)" são analogias ao MVC e devem ser entendidas como aproximações.
