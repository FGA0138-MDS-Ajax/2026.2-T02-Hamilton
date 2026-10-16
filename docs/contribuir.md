# Como contribuir

Esta documentação é gerada com [MkDocs](https://www.mkdocs.org/) e o tema [Material](https://squidfunk.github.io/mkdocs-material/). Ela vive na branch `docs`.

## Ver o site localmente

```bash
pip install -r requirements.txt
mkdocs serve
```

Abra [http://127.0.0.1:8000](http://127.0.0.1:8000). A página recarrega a cada alteração salva.

## Adicionar uma nova ata

1. Crie `docs/atas-reuniao/ata-reuniao-N.md`.
2. Adicione uma linha na tabela de `docs/atas-reuniao/index.md`, com a data e o texto da ata como link.
3. Registre o arquivo no `nav` do `mkdocs.yml`.

## Publicar

Basta fazer o push na branch `docs`. A pipeline gera o site e o publica na branch `gh-pages`.

Os commits seguem o padrão Conventional Commits, por exemplo: `docs(atas): adiciona ata 4`.
