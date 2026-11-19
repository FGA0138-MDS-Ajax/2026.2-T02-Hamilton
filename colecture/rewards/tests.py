from django.test import TestCase
from django.contrib.auth import get_user_model

from books.models import Book, ReadingSession
from rewards.models import Insignia, Award, CriteriaType
from rewards.services import check_first_read

User = get_user_model()
class CT01(TestCase):
    
    def setUp(self):
         self.user = User.objects.create_user(
             username='testuser',
             password='test1234'
        )
         
         self.insignia = Insignia.objects.filter(
            name='Primeira Faísca',
            is_active=True
        ).first()
         
         self.book = Book.objects.create(
            title='Livro de Teste',
            author='Autor Teste',
            pages=200,
            isbn='9788532511010'
        )
         
         self.session = ReadingSession.objects.create(
            user=self.user,
            book=self.book,
            pages_read=10,
            minute_count=20
        )
                     
    
# Teste se usuario receber a recompensa após comprir uma conquista

    def test_recebe_insignia(self):
        result = check_first_read(self.user)

        self.assertTrue(result)

        self.assertTrue(
            Award.objects.filter(
                user=self.user,
                insignia=self.insignia
            ).exists()
        )
        # teste se usuario nao recebe conquistas duplicada
    def test_insignia_duplicada(self):
        first_result = check_first_read(self.user)
        second_result = check_first_read(self.user)
        
        self.assertTrue(first_result)
        
        self.assertFalse(second_result)

        self.assertEqual(
            Award.objects.filter(
                user=self.user,
                insignia=self.insignia
            ).count(),
            1
        )
    
    # teste usuario consegue receber novamente a insignia que ele deletou
    def test_recebe_insigna_apos_excluida(self):
        check_first_read(self.user)
        
        award = Award.objects.get(
            user=self.user,
            insignia=self.insignia
        )
        
        award.delete()
        
        result = check_first_read(self.user)
        
        self.assertTrue(result)
        self.assertTrue(
            Award.objects.filter(
                user=self.user,
                insignia=self.insignia
            ).exists()
        )