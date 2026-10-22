# Ata 4 – Reunião da Sprint 3 (Comunidades)

| Item | Detalhe |
|---|---|
| **Projeto** | CoLecture – Grupo Hamilton |
| **Data** | 21/10/2026 |
| **Horário** | 21h às 22h |
| **Presença** | Todos os membros do grupo estavam presentes |
| **Pauta** | Regras de negócio (back-end) e páginas (front-end) da Sprint 3: R09 – Manter comunidade e R10 – Página de comunidade |

---

## 1. Back-end

### 1.1 Livros (alteração de regra)

- O usuário que cadastrou o livro pode **editá-lo**, mas **não pode excluí-lo**.

### 1.2 Comunidades

- Operações previstas: **criar, editar, excluir e moderar**.
- **Visibilidade:** comunidades públicas ou privadas. Nas privadas, o moderador deve **aceitar ou recusar solicitações** de entrada.
- **Livro opcional:** a comunidade não depende obrigatoriamente de um livro, para não ser quebrada caso o livro seja excluído.
- **Saída do último membro:** se restar apenas um membro e ele sair, a comunidade é **excluída**.

### 1.3 Papéis

- Existe o cargo de **Moderador**.
- Um membro pode ser **promovido a moderador**, e um moderador pode ser **rebaixado a membro**.

### 1.4 Arquivamento

- Os fóruns da comunidade são **congelados**.
- Os dados permanecem no banco por **60 dias**; após esse prazo, são **excluídos definitivamente**.
- A comunidade **deixa de aparecer** para usuários comuns, que apenas **recebem uma notificação** do arquivamento.

### 1.5 Busca

- A aba de pesquisa passa a permitir a **busca por comunidades**.

---

## 2. Front-end

### 2.1 Ajustes em páginas existentes

- **Login, registro de livro e avaliação de livro:** padronizar as mensagens de erro e sucesso com um visual mais cuidado.
- **Detalhe do livro (`book_detail`):**
    - botão de **lápis** para ir à edição;
    - botão de **lixeira** para apagar o livro;
    - visíveis **apenas para o criador do livro a aba de editar (lápis) do e ambas para o administrador**.

### 2.2 Novas páginas

| Página | Conteúdo |
|---|---|
| **Página inicial** | Listagem das comunidades de que o usuário participa (no estilo da listagem de livros), com botão **Entrar na comunidade**. |
| **Comunidade (por ID)** | Nome da comunidade; livro como atributo; espaço do **fórum** com identificação do capítulo do livro; menu de três pontinhos com **Editar** (moderador), **Sair** (todos) e **Arquivar**. |
| **Criar comunidade** | Formulário com os campos necessários para a criação. |
| **Gerenciar comunidade** | Gerenciamento de **membros, metas e capítulo**. |

---

## 3. Pendências

- Fazer separação das atividades do Back-end e Front-end
- Fazer as Issues no GitHub para auditoria