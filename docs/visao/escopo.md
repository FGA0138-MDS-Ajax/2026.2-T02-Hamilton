# Escopo e Backlog

## Classificação dos requisitos

- **Must:** obrigatórios e essenciais ao funcionamento da plataforma; prioridade máxima.
- **Should:** desejáveis e importantes, mas sua ausência não impede o funcionamento geral.
- **Could:** menor prioridade; implementados se houver prazo após os Must e Should.

O levantamento foi feito por brainstorm entre os integrantes, considerando necessidades do usuário e requisitos funcionais e não funcionais.

## Perfis de acesso

| Perfil | Características | Permissões |
| ------ | --------------- | ---------- |
| Cliente (Leitor) | Usuário autenticado | Criar/excluir comunidades, registrar livros inexistentes, sugerir edições, interagir no fórum, avaliar, registrar progresso |
| Moderador (papel do cliente) | Criador ou promovido em uma comunidade | Gerenciar membros, metas e fórum da comunidade |
| Administrador | Gestor do site | Gerenciar comunidades, editar usuários e livros, aprovar livros e edições |

## Cenários funcionais

| Cenário | Nome | Sprint |
| :-----: | ---- | :----: |
| C01 | Cadastro, login e perfil | 1 |
| C02 | Admin editar usuários | 1 |
| C03 | Registro de livro | 2 |
| C04 | Avaliação de livros | 2 |
| C05 | Criação de comunidade | 3 |
| C06 | Gerenciamento da comunidade | 3 |
| C07 | Criação de meta de leitura com capítulos | 4 |
| C08 | Perfil com tags e livros lidos | 4 |
| C09 | Fórum da comunidade por ciclo | 4 |
| C10 | Registro de progresso diário e livro já lido | 5 |
| C11 | Ofensiva pessoal | 5 |
| C12 | Insígnias de comunidade | 6 |
| C13 | Recomendação por temas | 6 |

## Backlog do produto

| Req. | Sprint | Nome | Tipo | Prioridade | Descrição | US |
| :--: | :----: | ---- | ---- | :--------: | --------- | :-: |
| R01 | 1 | Cadastro e login | Funcional | Must | Cadastro, login, logout, editar perfil | US01 |
| R02 | 1 | Admin editar usuários | Funcional | Must | Editar, adicionar e excluir usuários | US02 |
| R03 | 1 | Admin inicial via seed | Não funcional | Must | Criar admin padrão via migration/seed, pois o banco inicia vazio | US03 |
| R04 | 1 | Página de login | Funcional | Must | Páginas de login, cadastro e edição de perfil | US04 |
| R05 | 2 | Registrar livro inexistente | Funcional | Must | Formulário de livro | US05 |
| R06 | 2 | Pesquisar e filtrar catálogo | Funcional | Must | Busca por título, autor, tema, tag | US06 |
| R07 | 2 | Avaliar livros | Funcional | Should | Nota 1-5, resenha, média | US07 |
| R08 | 2 | Página de registro de livros e avaliação | Funcional | Must | Página de registro, avaliação e pesquisa | US08 |
| R09 | 3 | Manter comunidade | Funcional | Must | Nome, descrição, criador moderador; moderadores podem excluir/arquivar a comunidade, aprovar e remover membros e promover moderador; comunidade aberta ou fechada (a fechada exige aprovação) | US09 |
| R10 | 3 | Página de comunidade | Funcional | Must | Página web com o R09 | US10 |
| R11 | 4 | Criar meta de leitura | Funcional | Must | Livro, data limite, fórum automático | US11 |
| R12 | 4 | Manter fórum | Funcional | Must | Criar fórum novo e arquivar o antigo, se existir, vinculado ao ciclo; cada comunidade tem um fórum geral e um fórum por meta | US12 |
| R13 | 4 | Visualizar metas ativas/encerradas | Funcional | Must | Listar progresso, data, status | US13 |
| R14 | 4 | Moderar fórum | Funcional | Should | Editar, fixar, trancar (silenciar o chat) | US14 |
| R15 | 5 | Registrar livro como lido | Funcional | Must | Status lido, data, páginas/percentual | US15 |
| R16 | 5 | Registrar progresso diário | Funcional | Must | Sessão do dia, páginas/% acumulado e tempo gasto estimado | US16 |
| R17 | 5 | Ofensivas | Funcional | Should | Dias consecutivos, calendário, notificações | US17 |
| R18 | 5 | Página de leitura | Funcional | Must | Abas distintas: registrar leitura, e botão de registrar na aba de perfil ou sidebar | US18 |
| R19 | 6 | Insígnias | Funcional | Could | Conquistas automáticas/manuais | US19 |
| R20 | 6 | Recomendações por tema | Funcional | Must | Baseada em tags, lidos e avaliações | US20 |
| R21 | 6 | Notificações e logs | Não funcional | Should | Notificar aprovações e novos ciclos, logs de ações | US21 |
| R22 | 6 | Teste e documentação | Não funcional | Must | Roteiro de testes, cobertura, manual | US22 |
| R23 | 7 | Ajustes finais e apresentação | Não funcional | Must | Correções | – |

## Critérios de pronto

Para padronizar o que se espera dos itens do backlog antes e depois do desenvolvimento, a equipe definiu a Definição de Preparado (*Definition of Ready*, DoR) e a Definição de Pronto (*Definition of Done*, DoD).

### Definição de Preparado (DoR)

Um requisito só entra no planejamento de uma sprint se:

1. Possui prioridade definida (Must, Should ou Could);
2. Possui critérios de aceitação claros e verificáveis;
3. Tem dependências com outros requisitos identificadas e resolvidas ou planejadas;
4. Foi estimado e cabe no tempo da sprint (7 dias);
5. Foi compreendido pela equipe e validado pelo Dono do Produto.

### Definição de Pronto (DoD)

Um requisito só é considerado concluído se:

1. O código foi implementado e atende aos critérios de aceitação da user story;
2. Os testes unitários das regras de negócio foram escritos e executam com sucesso;
3. O caso de teste correspondente do [Roteiro de Testes](testes.md#roteiro-de-testes) foi executado e aprovado;
4. O código passou por revisão (*pull request*) de pelo menos dois outros integrantes;
5. Os commits seguem o padrão Conventional Commits e o código foi integrado à branch `sprintN`;
6. Nenhum defeito crítico permanece em aberto;
7. A documentação afetada (README e documentos de Visão e Arquitetura) foi atualizada;
8. O Dono do Produto validou a entrega na reunião de revisão da sprint.
