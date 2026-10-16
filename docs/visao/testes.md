# Testes de Software

A estratégia de verificação e validação segue Pressman e Maxim (2016) e abrange múltiplos níveis, tipos e ambientes integrados ao fluxo Git da equipe.

## Níveis

1. **Unitários:** regras de negócio isoladas em Python/Django, como média de avaliações, contagem de ofensivas e permissões por perfil.
2. **Integração:** comunicação entre módulos, persistência no SQLite, views e rotas (URLconf) e sincronização entre fóruns e metas.
3. **Sistema:** jornadas completas pela interface responsiva, como cadastro, entrada em comunidade, registro diário e metas colaborativas.

## Tipos

- **Funcionais:** validam as saídas contra os requisitos R01 a R22.
- **Não funcionais:** carga e estresse (Objetivo 5 do GQM), responsividade, integridade das seeds e notificações/logs (R21).

## Ambientes

| Ambiente | Uso |
| -------- | --- |
| Desenvolvimento local | Testes unitários e de integração antes do commit |
| Branch `sprintN` | Homologação: testes de integração e de sistema antes de integrar |
| Branch `main` | Entrega: recebe apenas código testado, auditado e aprovado pelo Dono do Produto |

## Critério de avaliação

- Resultado previsto = resultado realizado: **teste aprovado**.
- Resultado previsto ≠ resultado realizado: **teste reprovado** (defeito registrado, corrigido e retestado).

## Roteiro de testes

Os campos de resultados, reparos e ciclos serão preenchidos durante a execução ao longo das sprints.

| Caso | Nome | Requisitos | Sprint | Nível | Tipo |
| :--: | ---- | ---------- | :----: | ----- | ---- |
| CT01 | Autenticação, cadastro e perfil | R01 a R04 | 1 | Sistema | Funcional |
| CT02 | Catálogo, registro, busca e avaliação de livros | R05 a R08 | 2 | Integrado / Sistema | Funcional |
| CT03 | Manter comunidade e interface da página | R09, R10 | 3 | Sistema | Funcional |
| CT04 | Metas de leitura, manter e moderar fórum | R11 a R14 | 4 | Sistema | Funcional |
| CT05 | Progresso, livro lido, página de leitura e ofensivas | R15 a R18 | 5 | Integrado / Sistema | Funcional |
| CT06 | Insígnias, recomendações e notificações | R19, R20, R21 | 6 | Sistema | Funcional e não funcional |
| CT07 | Gestão administrativa e inicialização via seed | R02, R03 | 1 | Sistema | Funcional e não funcional |
