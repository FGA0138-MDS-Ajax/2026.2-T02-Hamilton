# Metas e Restrições Arquiteturais

## Metas

- **Desempenho:** páginas principais processadas e enviadas em até 0,8 segundo (sem contar o recebimento pelo cliente), medido no ambiente local.
- **Testabilidade:** regras de negócio (ofensivas, média de avaliações) testáveis de forma unitária e isolada; por isso ficam nos models e não nas views.
- **Responsividade:** interface adaptável a diferentes resoluções de tela.
- **Segurança:** autenticação obrigatória, senhas com hash, proteção contra CSRF e XSS e permissões por perfil.
- **Manutenibilidade:** cada módulo é um app Django independente, com baixo acoplamento e sem dependências circulares.

## Restrições

- Back-end em Python com o framework Django.
- Front-end servido por templates do Django (HTML, CSS e JavaScript).
- Requisições analisadas e validadas antes do processamento (por exemplo, com Django Forms).
- Banco de dados inicial SQLite, pela simplicidade e por dispensar servidor de banco.
- Commits no padrão **Conventional Commits**.
- Identificadores (variáveis, funções, classes e tabelas) em **inglês**; comentários e documentação em **português**.

## Restrições adicionais

O CoLecture é executado em ambiente local e acessado por navegador, exigindo autenticação para interagir em fóruns e comunidades.

- **Segurança:** dados pessoais, como a foto de perfil, tratados conforme a LGPD (Lei nº 13.709/2018).
- **Portabilidade e responsividade:** layout adaptável a diferentes tamanhos de tela.
- **Usabilidade:** interface simples, utilizável por pessoas com pouca experiência digital.

### Permissões por perfil

| Perfil | Permissões |
| ------ | ---------- |
| Visitante | Visualizar páginas públicas, cadastrar-se e entrar |
| Leitor | Tudo do visitante, além de criar e entrar em comunidades, registrar progresso, avaliar e cadastrar livros e participar de fóruns |
| Moderador | Tudo do leitor, além de remover conteúdo e gerenciar membros das comunidades que modera |
| Administrador | Gerenciar comunidades, usuários e livros (editar e aprovar livros e edições) pelo painel administrativo |
