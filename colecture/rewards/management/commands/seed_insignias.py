from django.core.management.base import BaseCommand
from rewards.models import Insignia, CriteriaType


class Command(BaseCommand):
    help = 'Cadastra as insígnias iniciais'

    INSIGNIAS = [
    {
        'name': 'Primeira Faísca',
        'description': 'Registrar progresso pela primeira vez',
        'criteria_type': CriteriaType.STREAK,
        'criteria_value': 1,
        'icon': 'icon/'
    },
    {
        'name': 'Chama Acesa',
        'description': 'Alcançar uma ofensiva de 3 dias',
        'criteria_type': CriteriaType.STREAK,
        'criteria_value': 3,
        'icon': 'icon/'
    },
    {
        'name': 'Semana em Brasa',
        'description': 'Alcançar uma ofensiva de 7 dias',
        'criteria_type': CriteriaType.STREAK,
        'criteria_value': 7,
        'icon': 'icon/'
    },
    
    {
        'name': 'Quinzena Acesa',
        'description': 'Alcançar uma ofensiva de 15 dias',
        'criteria_type': CriteriaType.STREAK,
        'criteria_value': 15,
        'icon': 'icon/'
    },
    
    {
        'name': 'Fogueira Literária',
        'description': 'Alcançar uma ofensiva de 30 dias',
        'criteria_type': CriteriaType.STREAK,
        'criteria_value': 30,
        'icon': 'icon/'
    },
    
    {
        'name': 'Incêndio de Páginas',
        'description': 'Alcançar uma ofensiva de 100 dias',
        'criteria_type': CriteriaType.STREAK,
        'criteria_value': 100,
        'icon': 'icon/'
    },
    
    {
        'name': 'Meio Ano em Chamas',
        'description': 'Alcançar uma ofensiva de 180 dias',
        'criteria_type': CriteriaType.STREAK,
        'criteria_value': 180,
        'icon': 'icon/'
    },
    
    {
        'name': 'Chama Eterna',
        'description': 'Alcançar uma ofensiva de 365 dias',
        'criteria_type': CriteriaType.STREAK,
        'criteria_value': 365,
        'icon': 'icon/'
    },
    {
        'name': 'Primeira Página Virada',
        'description': 'Marcar o primeiro livro como lido',
        'criteria_type': CriteriaType.BOOKS_READ,
        'criteria_value': 1,
        'icon': 'icon/'
    },
    {
            'name': 'Leitor em Formação',
            'description': 'Leia 5 livros',
            'criteria_type': CriteriaType.BOOKS_READ,
            'criteria_value': 5,
            'icon': 'icon/'
    },
    {
            'name': 'Estante Crescendo',
            'description': 'Leia 10 livros',
            'criteria_type': CriteriaType.BOOKS_READ,
            'criteria_value': 10,
            'icon': 'icon/'
    },
    {
            'name': 'Biblioteca Ambulante',
            'description': 'Leia 25 livros',
            'criteria_type': CriteriaType.BOOKS_READ,
            'criteria_value': 25,
            'icon': 'icon/'
    },    
    {
            'name': 'Guardião da Estante',
            'description': 'Leia 50 livros',
            'criteria_type': CriteriaType.BOOKS_READ,
            'criteria_value': 50,
            'icon': 'icon/'
    },
    {
            'name': 'Explorador de Gêneros',
            'description': 'Leia 5 livros de gêneros diferentes',
            'criteria_type': CriteriaType.BOOKS_READ,
            'criteria_value': 5,
            'icon': 'icon/'
    },
    {
            'name': 'Maratonista',
            'description': 'Leia 100 páginas em um único dia',
            'criteria_type': CriteriaType.DAILY_PROGRESS,
            'criteria_value': 100,
            'icon': 'icon/'
    },
    {
            'name': 'Mil Páginas',
            'description': 'Acumular 1.000 páginas lidas',
            'criteria_type': CriteriaType.DAILY_PROGRESS,
            'criteria_value': 1000,
            'icon': 'icon/'
    },
    {
            'name': 'Dez Mil Páginas',
            'description': 'Acumular 10.000 páginas lidas',
            'criteria_type': CriteriaType.DAILY_PROGRESS,
            'criteria_value': 10000,
            'icon': 'icon/'
    },
    {
            'name': 'Primeira Hora',
            'description': 'Acumular 1 hora de leitura',
            'criteria_type': CriteriaType.HOURS_READ,
            'criteria_value': 60,
            'icon': 'icon/'
    },
    {
            'name': 'Leitura Profunda',
            'description': 'Registrar 2 horas de leitura em um único dia',
            'criteria_type': CriteriaType.HOURS_READ,
            'criteria_value': 120,
            'icon': 'icon/'
    },
    {
            'name': 'Dez Horas de Viagem',
            'description': 'Acumular 10 horas de leitura',
            'criteria_type': CriteriaType.HOURS_READ,
            'criteria_value': 600,
            'icon': 'icon/'
    },
    {
            'name': 'Cinquenta Horas',
            'description': 'Acumular 50 horas de leitura',
            'criteria_type': CriteriaType.HOURS_READ,
            'criteria_value': 3000,
            'icon': 'icon/'
    },
    {
            'name': 'Centenário das Letras',
            'description': 'Acumular 100 horas de leitura',
            'criteria_type': CriteriaType.HOURS_READ,
            'criteria_value': 6000,
            'icon': 'icon/'
    },
    {
            'name': 'Senhor do Tempo',
            'description': 'Acumular 500 horas de leitura',
            'criteria_type': CriteriaType.HOURS_READ,
            'criteria_value': 30000,
            'icon': 'icon/'
    },
    {
            'name': 'Primeiro Plano',
            'description': 'Criar a primeira meta individual',
            'criteria_type': CriteriaType.INDIVIDUAL_GOAL,
            'criteria_value': 1,
            'icon': '/icon/test.png'
    },
    {
            'name': 'Missão Cumprida',
            'description': 'Conluir a primeira meta individual',
            'criteria_type': CriteriaType.INDIVIDUAL_GOAL,
            'criteria_value': 1,
            'icon': 'icon/'
    },
    {
            'name': 'No Prazo Certo',
            'description': 'Concluir uma meta individual antes da data limite',
            'criteria_type': CriteriaType.INDIVIDUAL_GOAL,
            'criteria_value': 1,
            'icon': 'icon/'
    },
    {
            'name': 'Determinação',
            'description': 'Concluir 5 metas individuais',
            'criteria_type': CriteriaType.INDIVIDUAL_GOAL,
            'criteria_value': 5,
            'icon': 'icon/'
    },
    {
            'name': 'Mestre das Metas',
            'description': 'Concluir 20 metas individuais',
            'criteria_type': CriteriaType.INDIVIDUAL_GOAL,
            'criteria_value': 20,
            'icon': 'icon/'
    },
    {
            'name': 'Primeiro Ciclo',
            'description': 'Concluir a primeira meta de leitura de uma comunidade',
            'criteria_type': CriteriaType.COMMUNITY_GOAL,
            'criteria_value': 1,
            'icon': 'icon/'
    },
    {
            'name': 'Pontual',
            'description': 'Concluir uma meta antes da data limite',
            'criteria_type': CriteriaType.COMMUNITY_GOAL,
            'criteria_value': 1,
            'icon': 'icon/'
    },
    {
            'name': 'Veterano de Ciclos',
            'description': 'Concluir 10 metas de comunidade',
            'criteria_type': CriteriaType.COMMUNITY_GOAL,
            'criteria_value': 10,
            'icon': 'icon/'
    },
    {
            'name': 'Fundador',
            'description': 'Criar uma comunidade ou ser promovido a moderador',
            'criteria_type': CriteriaType.COMMUNITY,
            'criteria_value': 1,
            'icon': 'icon/'
    },
    {
            'name': 'Primeira Opinião',
            'description': 'Publicar a primeira avaliação com resenha',
            'criteria_type': CriteriaType.SOCIAL,
            'criteria_value': 1,
            'icon': 'icon/'       
    },
    {
            'name': 'Crítico Literário',
            'description': 'Publicar 20 resenhas',
            'criteria_type': CriteriaType.SOCIAL,
            'criteria_value': 20,
            'icon': 'icon/'     
    },
    {
            'name': 'Fênix',
            'description': 'Retomar a leitura e alcançar 7 dias de ofensiva após perder uma ofensiva de 30+ dias',
            'criteria_type': CriteriaType.SPECIAL,
            'criteria_value': 7,
            'icon': 'icon/'
    }
    ]
    
    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for insignia_data in self.INSIGNIAS:
            _, created = Insignia.objects.update_or_create(
                name=insignia_data['name'],
                defaults=insignia_data
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'{created_count} insígnias cadastradas.'
            )
        )

        self.stdout.write(
            f'{updated_count} insígnias atualizadas!'
        )

