# Visão do Produto

Resumo do documento *CoLecture: Visão do Produto e do Projeto* (Grupo Hamilton, 2026).

## Problema

Segundo a pesquisa Panorama do Consumo de Livros (Rádio Senado), 18% dos brasileiros acima de 18 anos compraram ao menos um livro em 2025, 2 pontos percentuais a mais que no ano anterior (3 milhões de novos leitores). Há, portanto, um público interessado em leitura, mesmo em meio às distrações digitais.

As tecnologias existentes acompanham o progresso individual, mas pouco fazem pelo lado social. Zhou et al. (2023) mostram que quem estuda em grupo tem maior senso de pertencimento e melhor desempenho, o que pode se aplicar à leitura.

Manter o hábito depende de rotina, ambiente, motivação e da forma como o progresso é acompanhado. A falta de um ambiente social de troca entre leitores limita o incentivo mútuo, importante para o novo leitor.

## Solução proposta

Uma plataforma com foco no incentivo ao hábito da leitura individual e coletiva, que permite ao usuário encontrar títulos e comunidades alinhados aos seus gostos, registrar seu progresso e participar de atividades com outros leitores.

| Problema identificado | Capacidade do software | Efeito pretendido |
| --------------------- | ---------------------- | ----------------- |
| Má organização | Metas de leitura | Auxiliar o leitor a orientar sua rotina |
| Pouco envolvimento social | Comunidades, fóruns e objetivos coletivos | Aproximar leitores e estimular a participação |
| Feedback insuficiente | Acompanhamento e retorno de progresso | Tornar a evolução mais perceptível |
| Baixo engajamento / temas incompatíveis | Descoberta de títulos e comunidades | Manter o usuário envolvido e interessado |

## Posição do produto

| | |
| --- | --- |
| **Para** | Pessoas interessadas em desenvolver e/ou manter o hábito da leitura |
| **Necessidade** | Estabelecer e acompanhar metas, descobrir livros, interagir com outros leitores e obter estímulos por objetivos colaborativos |
| **O CoLecture** | É uma aplicação web responsiva voltada ao desenvolvimento e manutenção do hábito da leitura |
| **Que** | Permite registrar o progresso individual e coletivo, descobrir livros e comunidades e participar de objetivos compartilhados |
| **Ao contrário de** | Planilhas, registros pessoais ou plataformas que concentram metas e progresso no usuário individual |
| **Nosso produto** | Integra acompanhamento individual, objetivos coletivos e interação social em um só ambiente |

**Diferencial:** concorrentes como Goodreads, StoryGraph, Literal e Fable já oferecem acompanhamento, recomendação, avaliação e interação social. O diferencial do CoLecture é a ênfase em objetivos de leitura coletivos e na relação próxima entre o progresso coletivo e o individual.

## Objetivos

**Principal:** apoiar o desenvolvimento e a manutenção do hábito de leitura por meio de acompanhamento individual, interação social e objetivos coletivos.

**Secundários:**

1. Permitir o estabelecimento e o acompanhamento de metas de leitura individuais e coletivas.
2. Fornecer ferramentas de controle do progresso individual e coletivo.
3. Facilitar a interação entre leitores de interesses semelhantes.
4. Oferecer mecanismos de descoberta de títulos e comunidades.
5. Prover estímulos sociais que favoreçam a continuidade da leitura.

## Tecnologias

| Tecnologia | Finalidade | Justificativa |
| ---------- | ---------- | ------------- |
| Python | Linguagem principal do back-end | Familiaridade da equipe e integração com o framework |
| Django | Back-end e estrutura da aplicação web | Estrutura integrada, com recursos prontos como o painel administrativo |
| JavaScript | Comportamentos do front-end | Familiaridade dos integrantes e adequação a interfaces interativas |
| HTML/CSS | Estrutura e apresentação da interface | Base da interface web responsiva |
| SQL | Consulta de dados via ORM do Django | Conhecimento prévio e necessidade de persistência |
| SQLite | Persistência dos dados | Compatibilidade com o framework |
