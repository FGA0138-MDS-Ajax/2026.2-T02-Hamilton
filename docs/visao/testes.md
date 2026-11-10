# Testes de Software

A garantia da qualidade do CoLecture apoia-se em um processo estruturado de verificação e validação (Pressman e Maxim, 2016), com múltiplos níveis, tipos e ambientes integrados ao fluxo Git da equipe.

## Níveis

1. **Unitários:** regras de negócio isoladas em Python/Django, como a média de avaliações dos livros, o algoritmo de contagem de ofensivas e as regras de permissão por perfil (Cliente, Moderador e Administrador).
2. **Integração:** comunicação entre os módulos, incluindo persistência e consulta no SQLite, integração das views com as rotas (URLconf) e os models, e sincronização entre ações nos fóruns e as metas de leitura ativas.
3. **Sistema:** comportamento do software como um todo, na perspectiva do usuário final, com jornadas completas (cadastro de novo leitor, entrada em comunidade, registro diário de páginas lidas e alcance de metas colaborativas) pela interface responsiva.

## Tipos

- **Funcionais:** validam as saídas contra os requisitos R01 a R22 (o CT06 cobre o R21). Cobrem autenticação, cadastro e filtragem no catálogo, gerenciamento de membros, moderação de tópicos e concessão de insígnias.
- **Não funcionais:** responsividade da interface em diferentes resoluções, integridade das sementes de inicialização do banco (seeds) e envio correto de notificações e logs (R21).

## Ambientes

| Ambiente | Uso |
| -------- | --- |
| Desenvolvimento local | Desenvolvedores e analistas de qualidade executam testes unitários e de integração antes do commit |
| Branch `sprintN` (`sprint1` a `sprint7`) | Homologação e integração: testes de integração e de sistema validam a fusão dos novos recursos; nada vai à `main` sem aprovação completa |
| Branch `main` | Entrega ao término de cada sprint: recebe apenas código testado, auditado pela qualidade e aprovado pelo Dono do Produto, sem regressões |

## Formas de análise

A eficácia dos testes é acompanhada pelos indicadores do [plano GQM](metricas.md):

- **Taxa de cobertura de requisitos:** requisitos testados ÷ implementados em cada sprint, com meta de 100%.
- **Densidade de defeitos:** tolerância máxima de 0,2 defeito por requisito testado.

## Critério de avaliação (previsto × realizado)

Cada caso de teste define um **resultado previsto**; durante a bateria de testes a equipe registra o **resultado realizado**.

- Previsto = realizado: **teste aprovado** (ausência de defeitos).
- Previsto ≠ realizado: **teste reprovado**; o defeito é registrado no histórico da sprint, corrigido e retestado até que os resultados coincidam, o que autoriza a promoção do código à `main`.

## Roteiro de testes

Os casos CT01 a CT07 derivam dos cenários e requisitos do backlog. Os campos de registro de resultados, reparos e ciclos ficam como "[A preencher]" no documento, pois ele reflete a fase de planejamento; serão alimentados com evidências reais ao longo das sprints.

| Caso | Nome | Requisitos | Nível | Tipo |
| :--: | ---- | ---------- | ----- | ---- |
| [CT01](#ct01) | Validação de Autenticação, Cadastro e Perfil | R01, R02, R03, R04 (Sprint 1) | Sistema | Funcional |
| [CT02](#ct02) | Catálogo, Registro, Busca e Avaliação de Livros | R05, R06, R07, R08 (Sprint 2) | Integrado / Sistema | Funcional |
| [CT03](#ct03) | Manter Comunidade e Interface da Página | R09, R10 (Sprint 3) | Sistema | Funcional |
| [CT04](#ct04) | Metas de Leitura, Manter e Moderar Fórum | R11, R12, R13, R14 (Sprint 4) | Sistema | Funcional |
| [CT05](#ct05) | Registro de Progresso, Livro Lido, Página de Leitura e Ofensivas | R15, R16, R17, R18 (Sprint 5) | Integrado / Sistema | Funcional |
| [CT06](#ct06) | Insígnias, Recomendações por Tema e Notificações | R19, R20, R21 (parte de notificações) (Sprint 6) | Sistema | Funcional e Não Funcional |
| [CT07](#ct07) | Gestão Administrativa e Inicialização via Seed | R02, R03 (Sprint 1 / Gestão Geral) | Sistema | Funcional e Não Funcional |

### CT01

**Validação de Autenticação, Cadastro e Perfil**

| Item | Descrição |
| ---- | --------- |
| Requisitos associados | R01, R02, R03, R04 (Sprint 1) |
| Objetivo do teste | Garantir que o usuário consiga criar uma conta, realizar login com credenciais válidas, efetuar logout e editar suas informações na página de perfil. |
| Nível do teste | Sistema |
| Tipo de teste | Funcional |
| Precondições | Aplicação no ar e página de login/cadastro acessível. |
| Critério de aceito | O usuário cria a conta, acessa a plataforma e atualiza dados do perfil com sucesso. |
| Critério de rejeitado | Erro ao autenticar credenciais válidas ou falha ao salvar alterações de perfil. |

### CT02

**Catálogo, Registro, Busca e Avaliação de Livros**

| Item | Descrição |
| ---- | --------- |
| Requisitos associados | R05, R06, R07, R08 (Sprint 2) |
| Objetivo do teste | Validar as páginas de registro e pesquisa, o cadastro de livros inexistentes, os filtros do catálogo e o sistema de avaliação (nota 1-5, resenhas e média do livro). |
| Nível do teste | Integrado / Sistema |
| Tipo de teste | Funcional |
| Precondições | Usuário autenticado e catálogo populado para buscas. |
| Critério de aceito | O livro é registrado na página dedicada, aparece nos filtros de busca e permite receber nota (1-5) e resenha, calculando a média corretamente. |
| Critério de rejeitado | Livro não cadastrado, falha nos filtros da busca ou erro no cálculo da média das avaliações. |

### CT03

**Manter Comunidade e Interface da Página**

| Item | Descrição |
| ---- | --------- |
| Requisitos associados | R09, R10 (Sprint 3) |
| Objetivo do teste | Validar a página de comunidade e todas as ações de "manter": criação, configuração de privacidade (aberta/fechada), aprovação e remoção de membros e exclusão/arquivamento da comunidade. |
| Nível do teste | Sistema |
| Tipo de teste | Funcional |
| Precondições | Usuário autenticado no sistema com perfil de Leitor/Cliente. |
| Critério de aceito | A página da comunidade exibe todas as informações e o moderador consegue gerenciar membros, aprovar solicitações ou excluir a comunidade. |
| Critério de rejeitado | Falha ao carregar a página da comunidade ou negação de acesso nas funções do moderador. |

### CT04

**Metas de Leitura, Manter e Moderar Fórum**

| Item | Descrição |
| ---- | --------- |
| Requisitos associados | R11, R12, R13, R14 (Sprint 4) |
| Objetivo do teste | Testar a criação de metas por capítulos, a visualização de metas ativas/encerradas, a criação/arquivamento de fóruns por meta e as ferramentas de moderação (fixar, trancar, editar e excluir tópicos). |
| Nível do teste | Sistema |
| Tipo de teste | Funcional |
| Precondições | Comunidade criada e usuário autenticado como Moderador. |
| Critério de aceito | A meta é criada com datas/capítulos, o progresso é listado na visão de metas ativas/encerradas e o moderador consegue fixar/trancar/editar/excluir tópicos do fórum. |
| Critério de rejeitado | Metas não diferenciam status ativo/encerrado ou falha nas permissões de moderação do fórum. |

### CT05

**Registro de Progresso, Livro Lido, Página de Leitura e Ofensivas**

| Item | Descrição |
| ---- | --------- |
| Requisitos associados | R15, R16, R17, R18 (Sprint 5) |
| Objetivo do teste | Validar a página de leitura com abas distintas (leitura do dia vs. livros já lidos), o registro diário de progresso, a marcação do livro como lido e o cálculo das ofensivas (pessoal e da comunidade). |
| Nível do teste | Integrado / Sistema |
| Tipo de teste | Funcional |
| Precondições | Usuário possui livros vinculados à sua conta ("em andamento" ou "lidos"). |
| Critério de aceito | A página de leitura alterna corretamente entre as abas, o progresso/livro lido é registrado com data/porcentagem e a ofensiva (streak) acumula os dias consecutivos. |
| Critério de rejeitado | Erro de navegação entre abas, falha ao registrar status "lido" ou cálculo incorreto da ofensiva. |

### CT06

**Insígnias, Recomendações por Tema e Notificações**

| Item | Descrição |
| ---- | --------- |
| Requisitos associados | R19, R20, R21 (parte de notificações) (Sprint 6) |
| Objetivo do teste | Avaliar a atribuição de insígnias/conquistas, as sugestões do motor de recomendação por temas/tags e o envio de notificações do sistema (aprovações em comunidades, novos ciclos de metas). |
| Nível do teste | Sistema |
| Tipo de teste | Funcional e Não Funcional |
| Precondições | Histórico de leituras/avaliações no perfil e ações disparadoras de notificação disponíveis. |
| Critério de aceito | O leitor recebe insígnias ao bater conquistas, visualiza recomendações alinhadas ao seu perfil e recebe alertas/notificações de aprovações e novos ciclos. |
| Critério de rejeitado | Recomendações desconexas com o perfil, não concessão de insígnias devidas ou falha no envio de notificações. |

### CT07

**Gestão Administrativa e Inicialização via Seed**

| Item | Descrição |
| ---- | --------- |
| Requisitos associados | R02, R03 (Sprint 1 / Gestão Geral) |
| Objetivo do teste | Validar a criação automática do perfil Administrador via seed/migration no banco zerado e testar os privilégios de editar, mesclar duplicados ou bloquear usuários. |
| Nível do teste | Sistema |
| Tipo de teste | Funcional e Não Funcional |
| Precondições | Executando `python manage.py migrate`. |
| Critério de aceito | O admin realiza login com as credenciais padrão do sistema e consegue executar ações restritas (editar, adicionar e remover usuários). |
| Critério de rejeitado | Falha na geração do admin via seed ou ausência de permissões administrativas na interface. |

