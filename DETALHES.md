<div align="center">

[![Visão Geral](https://img.shields.io/badge/Aba-Visão_Geral-lightgrey?style=for-the-badge)](README.md)
[![Documentação](https://img.shields.io/badge/Aba-Documentação-1f425f?style=for-the-badge)](DETALHES.md)

</div>

<div align="center">

[![GitHub Pages](https://img.shields.io/badge/Documentação-GitHub_Pages-blue?style=flat&logo=github)](https://fga0138-mds-ajax.github.io/2026.2-T02-Hamilton/)
[![Repositório](https://img.shields.io/badge/GitHub-Repositório-181717?style=flat&logo=github)](https://github.com/FGA0138-MDS-Ajax/2026.2-T02-Hamilton)

</div>

---

# Documentação Detalhada - CoLecture

> Bem-vindo à central de documentação e detalhamento técnico do projeto **CoLecture**, desenvolvido pela **Equipe Hamilton** na disciplina de Métodos de Desenvolvimento de Software (MDS) da Universidade de Brasília (UnB - FGA).

Para o guia de instalação, execução local e visão geral do sistema, consulte a aba [Visão Geral (README.md)](README.md).

---

## Sumário da Documentação

1. [Portal de Documentação Oficial (MkDocs)](#portal-de-documentação-oficial)
2. [Documentos de Engenharia de Software](#documentos-de-engenharia-de-software)
3. [Planejamento e Acompanhamento de Sprints](#planejamento-e-acompanhamento-de-sprints)
4. [Atas de Reunião da Equipe](#atas-de-reunião)
5. [Arquitetura e Decisões de Projeto](#arquitetura-e-decisões-de-projeto)

---

## Portal de Documentação Oficial

A documentação completa do projeto com todos os diagramas, atas, histórico de sprints e métricas está publicada e acessível online via GitHub Pages:

🔗 **[Acessar Site da Documentação (GitHub Pages)](https://fga0138-mds-ajax.github.io/2026.2-T02-Hamilton/)**

Os arquivos-fonte da documentação são mantidos na branch [`docs`](https://github.com/FGA0138-MDS-Ajax/2026.2-T02-Hamilton/tree/docs) e estruturados pelo gerador estático **MkDocs Material**.

---

## Documentos de Engenharia de Software

| Documento | Descrição |
| :--- | :--- |
| **Documento de Visão do Produto e do Projeto** | Define o problema, escopo, objetivos de negócio, partes interessadas, matriz de comunicação e riscos. |
| **Documento de Arquitetura de Software** | Descreve as visões de casos de uso, lógica, processos, implantação, modelo de dados e restrições arquiteturais (MTV, Celery, SQLite). |
| **Guia de Contribuição** | Políticas de branches, commits padronizados (Conventional Commits), fluxo de trabalho e critérios de aceitação de PRs. |

---

## Planejamento e Acompanhamento de Sprints

O desenvolvimento do CoLecture foi conduzido ao longo de 7 sprints incrementais. O detalhamento do planejamento e dos resultados de cada sprint pode ser acompanhado no portal:

- **Sprint 1:** Definição do escopo, documento de visão inicial, configurações do repositório e identidade do projeto.
- **Sprint 2:** Documento de arquitetura, modelagem de dados, prototipação e configuração do ambiente Django.
- **Sprint 3:** Implementação do módulo de autenticação (`accounts`), perfil do usuário e catálogo básico de livros (`books`).
- **Sprint 4:** Sistema de estante virtual, sessões de leitura, cálculo de ofensiva diária (*streak*) e criação de comunidades (`communities`).
- **Sprint 5:** Fóruns de discussão (`forums`), moderação de comunidades, convites e sistema de metas individuais e coletivas (`goals`).
- **Sprint 6:** Gamificação com 35 insígnias (`rewards`), infraestrutura de auditoria (`logs`), integração do **Celery + Redis** e notificações (`notifications`).
- **Sprint 7:** Refinamentos de interface, correções de usabilidade, documentação final e fechamento das entregas.

---

## Atas de Reunião

Todas as decisões técnicas e organizacionais tomadas pela equipe foram registradas formalmente em atas semanais:

- **Ata 01 a 07:** Alinhamentos de requisitos, aprovação das 35 insígnias oficiais, definição de tecnologias assíncronas (adoção de Celery e Redis) e padronização das entregas.

---

## Arquitetura e Decisões de Projeto

### Separação de Responsabilidades por App

- **`main`:** Vitrine inicial, motor de busca global e folhas de estilo compartilhadas.
- **`accounts`:** Gerenciamento do ciclo de vida do usuário, perfil estendido (`Profile`) e controle temporal de ofensiva diária.
- **`books`:** Catálogo de obras literárias, estante pessoal (lendo, lido, abandonado, quero ler), cronômetro de leitura e algoritmo de recomendação de livros.
- **`communities`:** Criação e gestão de clubes de leitura, moderação de membros, papéis e convites com códigos únicos.
- **`goals`:** Metas de leitura individuais e coletivas (páginas lidas ou tempo acumulado) com fóruns automáticos de acompanhamento.
- **`forums`:** Comunicação assíncrona com tópicos de debate e mensagens moderadas.
- **`notifications`:** Painel em tempo real e histórico de avisos, integrado a rotinas assíncronas do Celery.
- **`rewards`:** Engine de conquistas com 35 insígnias, verificação orientada a eventos e ícones vetoriais customizados.
- **`logs`:** Trilha de auditoria administrativa imutável para eventos críticos do sistema.

Para instruções de configuração e como executar o sistema localmente, acesse a [Visão Geral](README.md).

---

<div align="center">
  <sub>CoLecture • Métodos de Desenvolvimento de Software • 2026.2 • Universidade de Brasília</sub>
</div>
