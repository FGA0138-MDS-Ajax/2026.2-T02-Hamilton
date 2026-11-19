"""
Cadastra as 35 insígnias da Ata da Reunião 07 (R19) quando o banco é criado.

Assim o `migrate` já deixa as insígnias prontas, sem precisar rodar o
`seed_insignias`. Os dados ficam copiados aqui (e não importados do comando)
para a migration continuar funcionando mesmo que o seed mude no futuro.

Para alterar uma insígnia depois, edite o `seed_insignias.py` e rode
`python manage.py seed_insignias` (ou crie uma nova migration).
"""
from django.db import migrations


INSIGNIAS = [
    # Ofensiva pessoal (1 a 8)
    ('Primeira Faísca', 'Registrar progresso pela primeira vez', 'STREAK', 1),
    ('Chama Acesa', 'Alcançar uma ofensiva de 3 dias', 'STREAK', 3),
    ('Semana em Brasa', 'Alcançar uma ofensiva de 7 dias', 'STREAK', 7),
    ('Quinzena Acesa', 'Alcançar uma ofensiva de 15 dias', 'STREAK', 15),
    ('Fogueira Literária', 'Alcançar uma ofensiva de 30 dias', 'STREAK', 30),
    ('Incêndio de Páginas', 'Alcançar uma ofensiva de 100 dias', 'STREAK', 100),
    ('Meio Ano em Chamas', 'Alcançar uma ofensiva de 180 dias', 'STREAK', 180),
    ('Chama Eterna', 'Alcançar uma ofensiva de 365 dias', 'STREAK', 365),
    # Livros lidos (9 a 14)
    ('Primeira Página Virada', 'Marcar o primeiro livro como lido', 'BOOKS_READ', 1),
    ('Leitor em Formação', 'Leia 5 livros', 'BOOKS_READ', 5),
    ('Estante Crescendo', 'Leia 10 livros', 'BOOKS_READ', 10),
    ('Biblioteca Ambulante', 'Leia 25 livros', 'BOOKS_READ', 25),
    ('Guardião da Estante', 'Leia 50 livros', 'BOOKS_READ', 50),
    ('Explorador de Gêneros', 'Leia 5 livros de gêneros diferentes', 'BOOKS_READ', 5),
    # Progresso diário (15 a 17; a 18 não foi aprovada)
    ('Maratonista', 'Leia 100 páginas em um único dia', 'DAILY_PROGRESS', 100),
    ('Mil Páginas', 'Acumular 1.000 páginas lidas', 'DAILY_PROGRESS', 1000),
    ('Dez Mil Páginas', 'Acumular 10.000 páginas lidas', 'DAILY_PROGRESS', 10000),
    # Horas de leitura (19 a 24), valor em minutos
    ('Primeira Hora', 'Acumular 1 hora de leitura', 'HOURS_READ', 60),
    ('Leitura Profunda', 'Registrar 2 horas de leitura em um único dia', 'HOURS_READ', 120),
    ('Dez Horas de Viagem', 'Acumular 10 horas de leitura', 'HOURS_READ', 600),
    ('Cinquenta Horas', 'Acumular 50 horas de leitura', 'HOURS_READ', 3000),
    ('Centenário das Letras', 'Acumular 100 horas de leitura', 'HOURS_READ', 6000),
    ('Senhor do Tempo', 'Acumular 500 horas de leitura', 'HOURS_READ', 30000),
    # Metas individuais (25 a 29)
    ('Primeiro Plano', 'Criar a primeira meta individual', 'INDIVIDUAL_GOAL', 1),
    ('Missão Cumprida', 'Concluir a primeira meta individual', 'INDIVIDUAL_GOAL', 1),
    ('No Prazo Certo', 'Concluir uma meta individual antes da data limite', 'INDIVIDUAL_GOAL', 1),
    ('Determinação', 'Concluir 5 metas individuais', 'INDIVIDUAL_GOAL', 5),
    ('Mestre das Metas', 'Concluir 20 metas individuais', 'INDIVIDUAL_GOAL', 20),
    # Metas de comunidade (30 a 33)
    ('Primeiro Ciclo', 'Concluir a primeira meta de leitura de uma comunidade', 'COMMUNITY_GOAL', 1),
    ('Pontual', 'Concluir uma meta antes da data limite', 'COMMUNITY_GOAL', 1),
    ('Veterano de Ciclos', 'Concluir 10 metas de comunidade', 'COMMUNITY_GOAL', 10),
    ('Fundador', 'Criar uma comunidade ou ser promovido a moderador', 'COMMUNITY', 1),
    # Social, fórum e avaliações (34 e 35)
    ('Primeira Opinião', 'Publicar a primeira avaliação com resenha', 'SOCIAL', 1),
    ('Crítico Literário', 'Publicar 20 resenhas', 'SOCIAL', 20),
    # Especiais (36)
    ('Fênix', 'Retomar a leitura e alcançar 7 dias de ofensiva após perder uma ofensiva de 30+ dias', 'SPECIAL', 7),
]


def create_insignias(apps, schema_editor):
    Insignia = apps.get_model('rewards', 'Insignia')

    for name, description, criteria_type, criteria_value in INSIGNIAS:
        # Não altera insígnias que já existem (ex.: banco que já rodou o seed)
        Insignia.objects.get_or_create(
            name=name,
            defaults={
                'description': description,
                'criteria_type': criteria_type,
                'criteria_value': criteria_value,
                # Ícone provisório: a arte vem de static/rewards/img/insignias/
                'icon': 'icon/',
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('rewards', '0003_alter_insignia_criteria_type'),
    ]

    operations = [
        # Desfazer não apaga nada, para não perder as insígnias já conquistadas
        migrations.RunPython(create_insignias, migrations.RunPython.noop),
    ]
